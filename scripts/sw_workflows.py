"""High-level CAD workflows used as demos and regression benchmarks."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from .sw_models import (
        AssemblySpec,
        ComponentSpec,
        DrawingSpec,
        ExportSpec,
        InterfaceSpec,
        MateEndpoint,
        MateSpec,
        PartSpec,
        ReviewSpec,
        ToolResult,
        TransformSpec,
    )
    from .sw_service import SolidWorksAutomationService
except ImportError:  # pragma: no cover - direct scripts path compatibility
    from sw_models import (
        AssemblySpec,
        ComponentSpec,
        DrawingSpec,
        ExportSpec,
        InterfaceSpec,
        MateEndpoint,
        MateSpec,
        PartSpec,
        ReviewSpec,
        ToolResult,
        TransformSpec,
    )
    from sw_service import SolidWorksAutomationService


BENCHMARK_NAMES = (
    "enterprise_thin_slice",
    "mounting_plate_only",
    "shaft_and_sleeve",
    "bracket_on_base_assembly",
)


def build_enterprise_thin_slice_specs(output_dir: str | Path) -> Dict[str, Any]:
    """Build a small enterprise-style assembly benchmark spec.

    The benchmark is intentionally simple enough for broad SolidWorks versions:
    a mounting plate, a bracket block, and a shaft. Semantic interfaces are
    included so assembly mates can reference stable IDs instead of raw Face1
    names where possible.
    """
    root = Path(output_dir)
    parts_dir = root / "parts"
    drawings_dir = root / "drawings"
    exports_dir = root / "exports"

    base = PartSpec(
        name="base_plate",
        template="mounting_plate",
        parameters={"width_mm": 160, "height_mm": 90, "thickness": 10},
        material="Plain Carbon Steel",
        properties={"PartNo": "ASM-DEMO-001-BASE", "Description": "Mounting base plate"},
        output_path=str(parts_dir / "base_plate.sldprt"),
        interfaces=[
            InterfaceSpec(
                id="datum_top",
                kind="mounting_face",
                target_name="Top Plane",
                target_aliases=["datum_top"],
                entity_type="PLANE",
            ),
            InterfaceSpec(
                id="datum_front",
                kind="datum",
                target_name="Front Plane",
                target_aliases=["datum_front"],
                entity_type="PLANE",
            ),
        ],
    )

    bracket = PartSpec(
        name="support_bracket",
        template="bracket",
        parameters={"width_mm": 60, "height_mm": 70, "thickness": 18},
        material="Aluminum 6061",
        properties={"PartNo": "ASM-DEMO-002-BRACKET", "Description": "Support bracket"},
        output_path=str(parts_dir / "support_bracket.sldprt"),
        interfaces=[
            InterfaceSpec(
                id="datum_bottom",
                kind="mounting_face",
                target_name="Top Plane",
                target_aliases=["datum_bottom"],
                entity_type="PLANE",
            ),
            InterfaceSpec(
                id="datum_front",
                kind="datum",
                target_name="Front Plane",
                target_aliases=["datum_front"],
                entity_type="PLANE",
            ),
        ],
    )

    shaft = PartSpec(
        name="demo_shaft",
        template="shaft",
        parameters={"diameter_mm": 20, "length_mm": 120},
        material="Alloy Steel",
        properties={"PartNo": "ASM-DEMO-003-SHAFT", "Description": "Demo shaft"},
        output_path=str(parts_dir / "demo_shaft.sldprt"),
        interfaces=[
            InterfaceSpec(
                id="shaft_axis",
                kind="axis",
                target_name="Front Plane",
                target_aliases=["shaft_axis"],
                entity_type="PLANE",
            )
        ],
    )

    assembly = AssemblySpec(
        name="enterprise_thin_slice",
        output_path=str(root / "enterprise_thin_slice.sldasm"),
        components=[
            ComponentSpec(
                name="base_plate-1",
                part=base,
                fixed=True,
                transform=TransformSpec(translation_mm=(0, 0, 0)),
            ),
            ComponentSpec(
                name="support_bracket-1",
                part=bracket,
                transform=TransformSpec(translation_mm=(0, 0, 12)),
            ),
            ComponentSpec(
                name="demo_shaft-1",
                part=shaft,
                transform=TransformSpec(translation_mm=(0, 45, 50)),
            ),
        ],
        mates=[
            MateSpec(
                id="bracket_on_base",
                mate_type="coincident",
                a=MateEndpoint(component="base_plate-1", interface_id="datum_top"),
                b=MateEndpoint(component="support_bracket-1", interface_id="datum_bottom"),
            ),
            MateSpec(
                id="front_planes_aligned",
                mate_type="coincident",
                a=MateEndpoint(component="base_plate-1", interface_id="datum_front"),
                b=MateEndpoint(component="support_bracket-1", interface_id="datum_front"),
            ),
        ],
        properties={"Project": "Enterprise thin-slice benchmark"},
    )

    drawing = DrawingSpec(
        name="enterprise_thin_slice_drawing",
        source_path=assembly.output_path,
        include_standard_views=True,
        include_isometric=True,
        include_bom=False,
        output_path=str(drawings_dir / "enterprise_thin_slice.slddrw"),
        pdf_output_path=str(exports_dir / "enterprise_thin_slice.pdf"),
    )

    return {
        "name": "enterprise_thin_slice",
        "parts": [base, bracket, shaft],
        "assembly": assembly,
        "drawing": drawing,
        "exports": [
            ExportSpec(output_path=str(exports_dir / "enterprise_thin_slice.step")),
        ],
        "review": ReviewSpec(
            output_dir=str(root / "review"),
            basename="enterprise_thin_slice",
            expected_outputs=[
                str(root / "enterprise_thin_slice.sldasm"),
                str(exports_dir / "enterprise_thin_slice.step"),
                str(exports_dir / "enterprise_thin_slice.pdf"),
            ],
        ),
    }


def build_mounting_plate_only_specs(output_dir: str | Path) -> Dict[str, Any]:
    root = Path(output_dir)
    exports_dir = root / "exports"
    plate = PartSpec(
        name="mounting_plate_only",
        template="mounting_plate",
        parameters={"width_mm": 120, "height_mm": 80, "thickness": 10},
        material="Plain Carbon Steel",
        properties={"PartNo": "BENCH-PLATE-001", "Description": "Mounting plate benchmark"},
        output_path=str(root / "mounting_plate_only.sldprt"),
        interfaces=[
            InterfaceSpec(
                id="datum_top",
                kind="mounting_face",
                target_name="Top Plane",
                target_aliases=["datum_top"],
                entity_type="PLANE",
            )
        ],
    )
    return {
        "name": "mounting_plate_only",
        "part": plate,
        "exports": [ExportSpec(output_path=str(exports_dir / "mounting_plate_only.step"))],
        "review": ReviewSpec(
            output_dir=str(root / "review"),
            basename="mounting_plate_only",
            expected_outputs=[
                str(root / "mounting_plate_only.sldprt"),
                str(exports_dir / "mounting_plate_only.step"),
            ],
        ),
    }


def build_shaft_and_sleeve_specs(output_dir: str | Path) -> Dict[str, Any]:
    root = Path(output_dir)
    parts_dir = root / "parts"
    exports_dir = root / "exports"
    shaft = PartSpec(
        name="benchmark_shaft",
        template="shaft",
        parameters={"diameter_mm": 18, "length_mm": 120},
        material="Alloy Steel",
        output_path=str(parts_dir / "benchmark_shaft.sldprt"),
        interfaces=[
            InterfaceSpec(
                id="front_datum",
                kind="datum",
                target_name="Front Plane",
                target_aliases=["front_datum"],
                entity_type="PLANE",
            )
        ],
    )
    sleeve = PartSpec(
        name="benchmark_sleeve",
        template="sleeve",
        parameters={"diameter_mm": 32, "length_mm": 70},
        material="Bronze",
        output_path=str(parts_dir / "benchmark_sleeve.sldprt"),
        interfaces=[
            InterfaceSpec(
                id="front_datum",
                kind="datum",
                target_name="Front Plane",
                target_aliases=["front_datum"],
                entity_type="PLANE",
            )
        ],
    )
    assembly = AssemblySpec(
        name="shaft_and_sleeve",
        output_path=str(root / "shaft_and_sleeve.sldasm"),
        components=[
            ComponentSpec(name="benchmark_shaft-1", part=shaft, fixed=True),
            ComponentSpec(
                name="benchmark_sleeve-1",
                part=sleeve,
                transform=TransformSpec(translation_mm=(0, 0, 8)),
            ),
        ],
        mates=[
            MateSpec(
                id="front_datums_aligned",
                mate_type="coincident",
                a=MateEndpoint(component="benchmark_shaft-1", interface_id="front_datum"),
                b=MateEndpoint(component="benchmark_sleeve-1", interface_id="front_datum"),
            )
        ],
    )
    return {
        "name": "shaft_and_sleeve",
        "parts": [shaft, sleeve],
        "assembly": assembly,
        "exports": [ExportSpec(output_path=str(exports_dir / "shaft_and_sleeve.step"))],
        "review": ReviewSpec(
            output_dir=str(root / "review"),
            basename="shaft_and_sleeve",
            expected_outputs=[
                str(root / "shaft_and_sleeve.sldasm"),
                str(exports_dir / "shaft_and_sleeve.step"),
            ],
        ),
    }


def build_bracket_on_base_assembly_specs(output_dir: str | Path) -> Dict[str, Any]:
    root = Path(output_dir)
    specs = build_enterprise_thin_slice_specs(root)
    assembly: AssemblySpec = specs["assembly"]
    assembly = assembly.model_copy(
        update={
            "name": "bracket_on_base_assembly",
            "components": assembly.components[:2],
            "output_path": str(root / "bracket_on_base_assembly.sldasm"),
        }
    )
    return {
        "name": "bracket_on_base_assembly",
        "parts": specs["parts"][:2],
        "assembly": assembly,
        "exports": [ExportSpec(output_path=str(root / "exports" / "bracket_on_base_assembly.step"))],
        "review": ReviewSpec(
            output_dir=str(root / "review"),
            basename="bracket_on_base_assembly",
            expected_outputs=[
                str(root / "bracket_on_base_assembly.sldasm"),
                str(root / "exports" / "bracket_on_base_assembly.step"),
            ],
        ),
    }


def build_benchmark_specs(name: str, output_dir: str | Path) -> Dict[str, Any]:
    if name == "enterprise_thin_slice":
        return build_enterprise_thin_slice_specs(output_dir)
    if name == "mounting_plate_only":
        return build_mounting_plate_only_specs(output_dir)
    if name == "shaft_and_sleeve":
        return build_shaft_and_sleeve_specs(output_dir)
    if name == "bracket_on_base_assembly":
        return build_bracket_on_base_assembly_specs(output_dir)
    raise ValueError(f"Unknown benchmark: {name}. Choose one of: {', '.join(BENCHMARK_NAMES)}")


def run_benchmark(
    name: str,
    output_dir: str | Path,
    service: Optional[SolidWorksAutomationService] = None,
) -> List[ToolResult]:
    active_service = service or SolidWorksAutomationService()
    specs = build_benchmark_specs(name, output_dir)
    results: List[ToolResult] = []

    connect = active_service.connect()
    results.append(connect)
    if not connect.ok:
        return results

    if "part" in specs:
        part_result = active_service.part_create(specs["part"])
        results.append(part_result)
        if not part_result.ok:
            return results
        source_doc_id = part_result.doc_id
    else:
        assembly_result = active_service.assembly_create(specs["assembly"])
        results.append(assembly_result)
        if not assembly_result.ok:
            return results
        source_doc_id = assembly_result.doc_id
        results.append(active_service.assembly_inspect(source_doc_id))

    for export_spec in specs.get("exports", []):
        export_spec.doc_id = source_doc_id
        results.append(active_service.export(export_spec))

    drawing_spec = specs.get("drawing")
    if drawing_spec is not None:
        drawing_spec.source_doc_id = source_doc_id
        results.append(active_service.drawing_create(drawing_spec))

    review_spec: ReviewSpec = specs["review"]
    review_spec.doc_id = source_doc_id
    results.append(active_service.review(review_spec))
    return results


def run_enterprise_thin_slice(
    output_dir: str | Path,
    service: Optional[SolidWorksAutomationService] = None,
) -> List[ToolResult]:
    """Run the full M2 benchmark through the service layer."""
    return run_benchmark("enterprise_thin_slice", output_dir, service=service)


def summarize_results(results: List[ToolResult]) -> Dict[str, Any]:
    return {
        "ok": all(result.ok for result in results),
        "steps": len(results),
        "failed": [result.as_dict() for result in results if not result.ok],
        "artifacts": [
            artifact.model_dump(mode="json")
            for result in results
            for artifact in result.artifacts
        ],
    }
