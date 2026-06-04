"""Stable semantic selection helpers for SolidWorks automation."""
from __future__ import annotations

from typing import Dict, Iterable, List, Optional

try:
    from .sw_models import (
        ComponentSpec,
        InterfaceSpec,
        MateEndpoint,
        SelectionCandidate,
    )
except ImportError:  # pragma: no cover - direct scripts path compatibility
    from sw_models import ComponentSpec, InterfaceSpec, MateEndpoint, SelectionCandidate


DEFAULT_ENTITY_BY_KIND = {
    "datum": "PLANE",
    "mounting_face": "FACE",
    "hole_axis": "AXIS",
    "hole_pattern": "SKETCH",
    "axis": "AXIS",
    "mate_connector": "COORDSYS",
    "bounding_box": "BODYFEATURE",
}


class SelectionResolver:
    """Resolve semantic interfaces into SolidWorks selection candidates.

    Resolution order:
    1. endpoint target_name/entity_type
    2. component interface target_name and aliases
    3. component-scoped interface id / target aliases for named features
    4. globally registered interface target_name and aliases
    """

    def __init__(
        self,
        components: Optional[Iterable[ComponentSpec]] = None,
        interfaces: Optional[Iterable[InterfaceSpec]] = None,
    ) -> None:
        self._interfaces_by_id: Dict[str, InterfaceSpec] = {}
        self._interfaces_by_component: Dict[str, Dict[str, InterfaceSpec]] = {}

        for interface in interfaces or []:
            self.register_interface(interface)

        for component in components or []:
            self.register_component(component)

    def register_component(self, component: ComponentSpec) -> None:
        bucket = self._interfaces_by_component.setdefault(component.name, {})
        for interface in component.interfaces:
            bucket[interface.id] = interface
            self.register_interface(interface)
        if component.part:
            for interface in component.part.interfaces:
                bucket[interface.id] = interface
                self.register_interface(interface)

    def register_interface(self, interface: InterfaceSpec) -> None:
        self._interfaces_by_id[interface.id] = interface

    def resolve(self, endpoint: MateEndpoint) -> List[SelectionCandidate]:
        candidates: List[SelectionCandidate] = []

        if endpoint.target_name and endpoint.entity_type:
            candidates.append(
                SelectionCandidate(
                    target_name=self._component_scoped_name(
                        endpoint.target_name, endpoint.component
                    ),
                    entity_type=endpoint.entity_type,
                    score=1.0,
                    reason="endpoint_explicit",
                    interface_id=endpoint.interface_id,
                    component=endpoint.component,
                )
            )

        interface = self._find_interface(endpoint.component, endpoint.interface_id)
        if interface:
            entity_type = interface.entity_type or DEFAULT_ENTITY_BY_KIND.get(interface.kind)
            if entity_type:
                candidates.extend(self._interface_candidates(interface, entity_type, endpoint.component))

        return self._dedupe(candidates)

    def require_one(self, endpoint: MateEndpoint) -> SelectionCandidate:
        candidates = self.resolve(endpoint)
        if not candidates:
            raise ValueError(
                "Unable to resolve mate endpoint. Provide interface_id with a "
                "target_name/entity_type, or use explicit target_name/entity_type."
            )
        return candidates[0]

    def _find_interface(
        self, component: Optional[str], interface_id: Optional[str]
    ) -> Optional[InterfaceSpec]:
        if not interface_id:
            return None
        if component:
            by_component = self._interfaces_by_component.get(component, {})
            if interface_id in by_component:
                return by_component[interface_id]
        return self._interfaces_by_id.get(interface_id)

    @staticmethod
    def _component_scoped_name(target_name: str, component: Optional[str]) -> str:
        if not component or "@" in target_name:
            return target_name
        return f"{target_name}@{component}"

    def _interface_candidates(
        self,
        interface: InterfaceSpec,
        entity_type: str,
        component: Optional[str],
    ) -> List[SelectionCandidate]:
        raw_names = []
        if interface.target_name:
            raw_names.append(interface.target_name)
        raw_names.extend(interface.target_aliases)
        if interface.id:
            raw_names.append(interface.id)

        candidates: List[SelectionCandidate] = []
        for index, raw_name in enumerate(raw_names):
            if not raw_name:
                continue
            candidates.append(
                SelectionCandidate(
                    target_name=self._component_scoped_name(raw_name, component),
                    entity_type=entity_type,
                    score=max(0.55, 0.95 - (index * 0.05)),
                    reason=f"interface:{interface.id}",
                    interface_id=interface.id,
                    component=component,
                )
            )
        return candidates

    @staticmethod
    def _dedupe(candidates: Iterable[SelectionCandidate]) -> List[SelectionCandidate]:
        seen = set()
        result = []
        for candidate in sorted(candidates, key=lambda item: item.score, reverse=True):
            key = (candidate.target_name, candidate.entity_type)
            if key in seen:
                continue
            seen.add(key)
            result.append(candidate)
        return result
