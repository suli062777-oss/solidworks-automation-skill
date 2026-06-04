"""Typed CAD domain models and unified tool results.

These models form the stable layer between an agent/MCP client and the
lower-level SolidWorks COM calls. Length values in public specs are expressed
in millimeters unless a field name explicitly says otherwise.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Sequence, Tuple
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


LengthUnit = Literal["mm", "m"]
PartTemplate = Literal[
    "mounting_plate",
    "bracket",
    "shaft",
    "sleeve",
    "flange",
    "box",
    "sheet_metal_panel",
    "generic_block",
]
InterfaceKind = Literal[
    "datum",
    "mounting_face",
    "hole_axis",
    "hole_pattern",
    "axis",
    "mate_connector",
    "bounding_box",
]
MateType = Literal[
    "coincident",
    "concentric",
    "distance",
    "angle",
    "parallel",
    "perpendicular",
    "width",
    "lock",
    "limit_distance",
    "limit_angle",
]
DocumentType = Literal["part", "assembly", "drawing"]
ArtifactKind = Literal[
    "sldprt",
    "sldasm",
    "slddrw",
    "step",
    "stl",
    "iges",
    "parasolid",
    "pdf",
    "dxf",
    "dwg",
    "preview",
    "review_json",
    "review_markdown",
    "bom",
    "log",
]


def mm_to_m(value: float) -> float:
    """Convert millimeters to SolidWorks API meters."""
    return float(value) / 1000.0


def deg_to_rad(value: float) -> float:
    """Convert degrees to radians."""
    import math

    return float(value) * math.pi / 180.0


def new_run_id(prefix: str = "sw") -> str:
    """Return a stable, sortable run id."""
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{prefix}-{stamp}-{uuid4().hex[:8]}"


class StrictModel(BaseModel):
    """Base model with predictable dumping and unknown-field rejection."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class Artifact(StrictModel):
    """A file, report, or generated preview returned by a tool."""

    kind: ArtifactKind
    path: str
    exists: bool = False
    size_bytes: int = 0
    label: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_path(
        cls,
        kind: ArtifactKind,
        path: str | Path,
        label: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "Artifact":
        file_path = Path(path)
        return cls(
            kind=kind,
            path=str(file_path),
            exists=file_path.exists(),
            size_bytes=file_path.stat().st_size if file_path.exists() else 0,
            label=label,
            metadata=metadata or {},
        )


class ToolError(StrictModel):
    """A structured error returned by MCP tools and service calls."""

    code: str
    message: str
    detail: Optional[str] = None
    recoverable: bool = False


class ToolResult(StrictModel):
    """Unified result shape for every public operation."""

    ok: bool
    run_id: str = Field(default_factory=new_run_id)
    doc_id: Optional[str] = None
    active_doc_id: Optional[str] = None
    artifacts: List[Artifact] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    errors: List[ToolError] = Field(default_factory=list)
    review: Optional[Dict[str, Any]] = None
    data: Dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def success(
        cls,
        *,
        run_id: Optional[str] = None,
        doc_id: Optional[str] = None,
        active_doc_id: Optional[str] = None,
        artifacts: Optional[Sequence[Artifact]] = None,
        warnings: Optional[Sequence[str]] = None,
        review: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> "ToolResult":
        return cls(
            ok=True,
            run_id=run_id or new_run_id(),
            doc_id=doc_id,
            active_doc_id=active_doc_id,
            artifacts=list(artifacts or []),
            warnings=list(warnings or []),
            review=review,
            data=data or {},
        )

    @classmethod
    def failure(
        cls,
        code: str,
        message: str,
        *,
        run_id: Optional[str] = None,
        detail: Optional[str] = None,
        recoverable: bool = False,
        warnings: Optional[Sequence[str]] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> "ToolResult":
        return cls(
            ok=False,
            run_id=run_id or new_run_id(),
            warnings=list(warnings or []),
            errors=[
                ToolError(
                    code=code,
                    message=message,
                    detail=detail,
                    recoverable=recoverable,
                )
            ],
            data=data or {},
        )

    def as_dict(self) -> Dict[str, Any]:
        """Return a JSON-serializable dict for MCP responses."""
        return self.model_dump(mode="json")


class InterfaceSpec(StrictModel):
    """A stable semantic reference to geometry used for mates or drawings."""

    id: str
    kind: InterfaceKind
    target_name: Optional[str] = None
    target_aliases: List[str] = Field(default_factory=list)
    entity_type: Optional[str] = None
    component_ref: Optional[str] = None
    location_mm: Optional[Tuple[float, float, float]] = None
    normal: Optional[Tuple[float, float, float]] = None
    axis: Optional[Tuple[float, float, float]] = None
    diameter_mm: Optional[float] = None
    radius_mm: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class FeatureSpec(StrictModel):
    """A named modeling operation that preserves design intent."""

    name: str
    kind: str
    parameters: Dict[str, Any] = Field(default_factory=dict)


class PartSpec(StrictModel):
    """High-level parameterized part request."""

    name: str
    template: PartTemplate = "generic_block"
    unit: LengthUnit = "mm"
    parameters: Dict[str, float] = Field(default_factory=dict)
    material: Optional[str] = None
    color_rgb: Optional[Tuple[int, int, int]] = None
    features: List[FeatureSpec] = Field(default_factory=list)
    interfaces: List[InterfaceSpec] = Field(default_factory=list)
    properties: Dict[str, str] = Field(default_factory=dict)
    output_path: Optional[str] = None

    @field_validator("color_rgb")
    @classmethod
    def _valid_rgb(
        cls, value: Optional[Tuple[int, int, int]]
    ) -> Optional[Tuple[int, int, int]]:
        if value is None:
            return None
        if any(channel < 0 or channel > 255 for channel in value):
            raise ValueError("color_rgb channels must be in the 0-255 range")
        return value


class TransformSpec(StrictModel):
    """Initial component placement."""

    translation_mm: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    rotation_deg: Tuple[float, float, float] = (0.0, 0.0, 0.0)

    @property
    def translation_m(self) -> Tuple[float, float, float]:
        return tuple(mm_to_m(value) for value in self.translation_mm)  # type: ignore[return-value]


class ComponentSpec(StrictModel):
    """A component or subassembly in an AssemblySpec."""

    name: str
    part_path: Optional[str] = None
    part: Optional[PartSpec] = None
    configuration: str = ""
    transform: TransformSpec = Field(default_factory=TransformSpec)
    fixed: bool = False
    interfaces: List[InterfaceSpec] = Field(default_factory=list)
    properties: Dict[str, str] = Field(default_factory=dict)


class MateEndpoint(StrictModel):
    """Reference to an interface or fallback SolidWorks selection target."""

    component: Optional[str] = None
    interface_id: Optional[str] = None
    target_name: Optional[str] = None
    entity_type: Optional[str] = None


class MateSpec(StrictModel):
    """A semantic assembly mate."""

    id: str
    mate_type: MateType
    a: MateEndpoint
    b: MateEndpoint
    distance_mm: Optional[float] = None
    angle_deg: Optional[float] = None
    alignment: Literal["aligned", "anti_aligned", "closest"] = "aligned"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AssemblySpec(StrictModel):
    """High-level assembly request."""

    name: str
    components: List[ComponentSpec]
    mates: List[MateSpec] = Field(default_factory=list)
    properties: Dict[str, str] = Field(default_factory=dict)
    output_path: Optional[str] = None


class DrawingSpec(StrictModel):
    """Drawing and BOM output request."""

    name: str
    source_doc_id: Optional[str] = None
    source_path: Optional[str] = None
    template_path: Optional[str] = None
    sheet_format_path: Optional[str] = None
    include_standard_views: bool = True
    include_isometric: bool = True
    include_bom: bool = True
    bom_template_path: Optional[str] = None
    output_path: Optional[str] = None
    pdf_output_path: Optional[str] = None


class ExportSpec(StrictModel):
    """File export request."""

    doc_id: Optional[str] = None
    output_path: str
    format_ext: Optional[str] = None
    options: Dict[str, Any] = Field(default_factory=dict)


class ReviewSpec(StrictModel):
    """Preview and engineering review request."""

    doc_id: Optional[str] = None
    output_dir: str
    basename: str = "review"
    views: List[str] = Field(default_factory=lambda: ["isometric", "front", "top", "right"])
    expected_outputs: List[str] = Field(default_factory=list)
    fail_on_warn: bool = False


class DocumentInfo(StrictModel):
    """A serializable reference to an open SolidWorks document."""

    doc_id: str
    title: Optional[str] = None
    path: Optional[str] = None
    doc_type: Optional[DocumentType] = None
    active: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SelectionCandidate(StrictModel):
    """Resolved fallback target for SelectByID2."""

    target_name: str
    entity_type: str
    score: float = 1.0
    reason: str = "explicit"
    interface_id: Optional[str] = None
    component: Optional[str] = None
