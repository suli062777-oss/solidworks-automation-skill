"""Service layer for enterprise SolidWorks automation and MCP tools."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple, Type, TypeVar

try:
    from .sw_models import (
        Artifact,
        AssemblySpec,
        ComponentSpec,
        DocumentInfo,
        DrawingSpec,
        ExportSpec,
        PartSpec,
        ReviewSpec,
        ToolResult,
        deg_to_rad,
        mm_to_m,
        new_run_id,
    )
    from .sw_selection import SelectionResolver
except ImportError:  # pragma: no cover - direct scripts path compatibility
    from sw_models import (
        Artifact,
        AssemblySpec,
        ComponentSpec,
        DocumentInfo,
        DrawingSpec,
        ExportSpec,
        PartSpec,
        ReviewSpec,
        ToolResult,
        deg_to_rad,
        mm_to_m,
        new_run_id,
    )
    from sw_selection import SelectionResolver


T = TypeVar("T")


DOC_TYPE_BY_SW_INT = {1: "part", 2: "assembly", 3: "drawing"}
ARTIFACT_BY_EXT = {
    ".sldprt": "sldprt",
    ".sldasm": "sldasm",
    ".slddrw": "slddrw",
    ".step": "step",
    ".stp": "step",
    ".stl": "stl",
    ".iges": "iges",
    ".igs": "iges",
    ".x_t": "parasolid",
    ".x_b": "parasolid",
    ".pdf": "pdf",
    ".dxf": "dxf",
    ".dwg": "dwg",
    ".bmp": "preview",
    ".png": "preview",
    ".json": "review_json",
    ".md": "review_markdown",
}


def _coerce(model_type: Type[T], value: T | Dict[str, Any]) -> T:
    if isinstance(value, model_type):
        return value
    return model_type.model_validate(value)  # type: ignore[attr-defined]


def _artifact_for_path(path: str | Path, label: Optional[str] = None) -> Artifact:
    suffix = Path(path).suffix.lower()
    kind = ARTIFACT_BY_EXT.get(suffix, "log")
    return Artifact.from_path(kind, path, label=label)  # type: ignore[arg-type]


@dataclass
class _DocumentRecord:
    doc_id: str
    model: Any
    info: DocumentInfo


class RealSolidWorksBackend:
    """Adapter that talks to the existing Python COM helper modules.

    Imports are deliberately lazy, so tests and non-Windows environments can
    import the service without importing pywin32/comtypes.
    """

    def preflight(self, allow_install: bool = False, check_solidworks: bool = True) -> Any:
        try:
            from .sw_preflight import run_preflight
        except ImportError:  # pragma: no cover
            from sw_preflight import run_preflight

        return run_preflight(
            allow_install=allow_install,
            check_solidworks=check_solidworks,
        )

    def connect(
        self,
        version: Optional[int] = None,
        wait_seconds: int = 5,
        visible: bool = True,
    ) -> Tuple[Any, Any]:
        try:
            from .sw_connect import connect_solidworks
        except ImportError:  # pragma: no cover
            from sw_connect import connect_solidworks

        return connect_solidworks(
            version=version,
            wait_seconds=wait_seconds,
            visible=visible,
        )

    def document_info(
        self,
        model: Any,
        doc_id: str,
        active: bool = False,
        fallback_type: Optional[str] = None,
    ) -> DocumentInfo:
        try:
            from .sw_connect import get_com_member
        except ImportError:  # pragma: no cover
            from sw_connect import get_com_member

        title = None
        path = None
        doc_type = fallback_type
        try:
            title = get_com_member(model, "GetTitle")
        except Exception:
            title = None
        try:
            path = get_com_member(model, "GetPathName")
        except Exception:
            path = None
        try:
            doc_type = DOC_TYPE_BY_SW_INT.get(get_com_member(model, "GetType"), doc_type)
        except Exception:
            pass

        return DocumentInfo(
            doc_id=doc_id,
            title=title,
            path=path,
            doc_type=doc_type,  # type: ignore[arg-type]
            active=active,
        )

    def new_document(
        self,
        sw: Any,
        doc_type: str,
        template_path: Optional[str] = None,
    ) -> Any:
        try:
            from .sw_connect import new_document
        except ImportError:  # pragma: no cover
            from sw_connect import new_document

        return new_document(sw, doc_type=doc_type, template_path=template_path)

    def open_document(
        self,
        sw: Any,
        file_path: str,
        read_only: bool = False,
        silent: bool = False,
    ) -> Any:
        try:
            from .sw_connect import open_document
        except ImportError:  # pragma: no cover
            from sw_connect import open_document

        return open_document(
            sw,
            file_path,
            read_only=read_only,
            silent=silent,
            raise_on_error=True,
        )

    def save_document(self, model: Any, file_path: Optional[str] = None) -> bool:
        try:
            from .sw_connect import save_document
        except ImportError:  # pragma: no cover
            from sw_connect import save_document

        return bool(save_document(model, file_path=file_path))

    def export_document(self, model: Any, spec: ExportSpec) -> bool:
        try:
            from .sw_session import EXPORTERS
        except ImportError:  # pragma: no cover
            from sw_session import EXPORTERS

        output = Path(spec.output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        ext = (spec.format_ext or output.suffix).lower()
        if not ext.startswith("."):
            ext = f".{ext}"
        exporter = EXPORTERS.get(ext)
        if not exporter:
            raise ValueError(f"Unsupported export format: {ext}")
        return bool(exporter(model, str(output), **spec.options))

    def save_preview(self, model: Any, path: str, view: str = "isometric") -> str:
        try:
            from .sw_review import save_preview
        except ImportError:  # pragma: no cover
            from sw_review import save_preview

        return save_preview(model, path, view_name=view)

    def run_review(self, model: Any, spec: ReviewSpec) -> Tuple[Dict[str, Any], str]:
        try:
            from .sw_review import run_review
        except ImportError:  # pragma: no cover
            from sw_review import run_review

        return run_review(
            model,
            output_dir=spec.output_dir,
            basename=spec.basename,
            views=spec.views,
            expected_outputs=spec.expected_outputs,
        )

    def create_part(self, sw: Any, spec: PartSpec) -> Any:
        try:
            from .sw_connect import save_document
            from .sw_part import (
                end_sketch,
                extrude_boss,
                sketch_circle,
                sketch_rectangle,
                start_sketch,
            )
        except ImportError:  # pragma: no cover
            from sw_connect import save_document
            from sw_part import (
                end_sketch,
                extrude_boss,
                sketch_circle,
                sketch_rectangle,
                start_sketch,
            )

        model = self.new_document(sw, "part")
        params = spec.parameters

        if spec.template in {"shaft", "sleeve"}:
            radius = mm_to_m(params.get("diameter", params.get("diameter_mm", 20.0)) / 2.0)
            length = mm_to_m(params.get("length", params.get("length_mm", 80.0)))
            start_sketch(model, "Front Plane")
            sketch_circle(model, 0, 0, radius)
            end_sketch(model)
            feature = extrude_boss(model, "Sketch1", length)
            if feature:
                feature.Name = f"{spec.name}_body"
        else:
            width = mm_to_m(params.get("width", params.get("width_mm", 100.0)))
            height = mm_to_m(params.get("height", params.get("height_mm", 60.0)))
            depth = mm_to_m(params.get("thickness", params.get("depth_mm", 10.0)))
            start_sketch(model, "Top Plane")
            sketch_rectangle(model, 0, 0, width, height)
            end_sketch(model)
            feature = extrude_boss(model, "Sketch1", depth)
            if feature:
                feature.Name = f"{spec.name}_body"

        self._apply_properties(model, spec.properties, spec.material)
        if spec.output_path:
            save_document(model, spec.output_path)
        return model

    def create_assembly(self, sw: Any, spec: AssemblySpec) -> Any:
        try:
            from .sw_assembly import (
                add_component,
                add_mate_coincident,
                add_mate_concentric,
                add_mate_distance,
                add_mate_parallel,
            )
            from .sw_connect import save_document
        except ImportError:  # pragma: no cover
            from sw_assembly import (
                add_component,
                add_mate_coincident,
                add_mate_concentric,
                add_mate_distance,
                add_mate_parallel,
            )
            from sw_connect import save_document

        asm = self.new_document(sw, "assembly")
        for component in spec.components:
            if not component.part_path:
                raise ValueError(f"Component {component.name} is missing part_path")
            x, y, z = component.transform.translation_m
            add_component(asm, component.part_path, x, y, z, component.configuration)

        resolver = SelectionResolver(spec.components)
        for mate in spec.mates:
            a = resolver.require_one(mate.a)
            b = resolver.require_one(mate.b)
            if mate.mate_type == "coincident":
                add_mate_coincident(asm, a.target_name, a.entity_type, b.target_name, b.entity_type)
            elif mate.mate_type == "concentric":
                add_mate_concentric(asm, a.target_name, b.target_name)
            elif mate.mate_type == "distance":
                distance = mm_to_m(mate.distance_mm or 0.0)
                add_mate_distance(asm, a.target_name, a.entity_type, b.target_name, b.entity_type, distance)
            elif mate.mate_type == "parallel":
                add_mate_parallel(asm, a.target_name, b.target_name)
            else:
                raise NotImplementedError(f"Mate type not implemented in v1 backend: {mate.mate_type}")

        if spec.output_path:
            save_document(asm, spec.output_path)
        return asm

    def create_drawing(self, sw: Any, spec: DrawingSpec, source_path: Optional[str]) -> Any:
        try:
            from .sw_connect import save_document
            from .sw_drawing import (
                add_view,
                create_standard_views,
                export_sheet_to_pdf,
                insert_bom_table,
            )
        except ImportError:  # pragma: no cover
            from sw_connect import save_document
            from sw_drawing import (
                add_view,
                create_standard_views,
                export_sheet_to_pdf,
                insert_bom_table,
            )

        if not source_path:
            raise ValueError("DrawingSpec requires source_path or source_doc_id with a saved path")

        drawing = self.new_document(sw, "drawing", template_path=spec.template_path)
        if spec.include_standard_views:
            create_standard_views(drawing, source_path)
        if spec.include_isometric:
            add_view(drawing, source_path, "*Isometric", 0.22, 0.16, scale=0.5)
        if spec.include_bom and spec.bom_template_path:
            insert_bom_table(drawing, spec.bom_template_path, 0.02, 0.25)
        if spec.output_path:
            save_document(drawing, spec.output_path)
        if spec.pdf_output_path:
            export_sheet_to_pdf(drawing, spec.pdf_output_path)
        return drawing

    def inspect_assembly(self, model: Any) -> Dict[str, Any]:
        """Collect lightweight assembly health data.

        The SolidWorks API exposes richer mate diagnostics than this v1 helper
        uses. This method intentionally stays conservative and catches partial
        failures so inspection never hides the generated assembly itself.
        """
        try:
            from .sw_assembly import get_components, get_interference_detection
            from .sw_connect import get_com_member
        except ImportError:  # pragma: no cover
            from sw_assembly import get_components, get_interference_detection
            from sw_connect import get_com_member

        checks: Dict[str, Any] = {}
        errors: List[Dict[str, str]] = []

        components: List[Dict[str, Any]] = []
        try:
            components = get_components(model, top_level_only=False)
        except Exception as exc:
            errors.append({"code": "components_unavailable", "message": str(exc)})

        features: List[Dict[str, Any]] = []
        try:
            feature = get_com_member(model, "FirstFeature")
            while feature:
                feature_info = {
                    "name": get_com_member(feature, "Name"),
                    "type": get_com_member(feature, "GetTypeName2"),
                }
                features.append(feature_info)
                feature = get_com_member(feature, "GetNextFeature")
        except Exception as exc:
            errors.append({"code": "feature_tree_unavailable", "message": str(exc)})

        mate_features = [
            feature for feature in features
            if "mate" in str(feature.get("type", "")).lower()
            or "mate" in str(feature.get("name", "")).lower()
        ]

        interference_count = None
        try:
            interference_count = get_interference_detection(model)
        except Exception as exc:
            errors.append({"code": "interference_unavailable", "message": str(exc)})

        rebuild_ok = None
        try:
            rebuild_ok = bool(get_com_member(model, "ForceRebuild3", False))
        except Exception as exc:
            errors.append({"code": "rebuild_unavailable", "message": str(exc)})

        checks["components_present"] = len(components) > 0
        checks["component_count"] = len(components)
        checks["mate_feature_count"] = len(mate_features)
        checks["interference_count"] = interference_count
        checks["rebuild_ok"] = rebuild_ok
        checks["inspection_complete"] = not errors

        if interference_count is None:
            status = "warn"
        elif interference_count > 0:
            status = "fail"
        elif errors:
            status = "warn"
        else:
            status = "pass"

        return {
            "status": status,
            "checks": checks,
            "components": components,
            "mates": mate_features,
            "errors": errors,
        }

    def _apply_properties(
        self,
        model: Any,
        properties: Dict[str, str],
        material: Optional[str],
    ) -> None:
        if not properties and not material:
            return
        try:
            custom_props = model.Extension.CustomPropertyManager("")
            for key, value in properties.items():
                custom_props.Add3(key, 30, value, 2)
            if material:
                custom_props.Add3("Material", 30, material, 2)
        except Exception:
            # Property write failures should not block geometry creation.
            return


class SolidWorksAutomationService:
    """Stateful service used by the MCP server and high-level workflows."""

    def __init__(
        self,
        backend: Optional[RealSolidWorksBackend] = None,
        output_root: Optional[str | Path] = None,
    ) -> None:
        self.backend = backend or RealSolidWorksBackend()
        self.output_root = Path(output_root or ".solidworks-runs")
        self.sw: Any = None
        self.documents: Dict[str, _DocumentRecord] = {}
        self.active_doc_id: Optional[str] = None
        self._doc_counter = 0

    def preflight(
        self,
        allow_install: bool = False,
        check_solidworks: bool = True,
    ) -> ToolResult:
        run_id = new_run_id("preflight")
        try:
            result = self.backend.preflight(
                allow_install=allow_install,
                check_solidworks=check_solidworks,
            )
            data = {
                "missing_packages": list(getattr(result, "missing_packages", [])),
                "dependencies_ready": bool(getattr(result, "dependencies_ready", True)),
                "solidworks_ready": getattr(result, "solidworks_ready", None),
            }
            return ToolResult.success(run_id=run_id, data=data)
        except Exception as exc:
            return self._failure("preflight_failed", exc, run_id=run_id, recoverable=True)

    def connect(
        self,
        version: Optional[int] = None,
        wait_seconds: int = 5,
        visible: bool = True,
    ) -> ToolResult:
        run_id = new_run_id("connect")
        try:
            self.sw, model = self.backend.connect(
                version=version,
                wait_seconds=wait_seconds,
                visible=visible,
            )
            doc_id = self._record_document(model).doc_id if model is not None else None
            warnings = [] if model is not None else ["Connected, but no active document is open."]
            return ToolResult.success(
                run_id=run_id,
                doc_id=doc_id,
                active_doc_id=self.active_doc_id,
                warnings=warnings,
                data=self.session_data(),
            )
        except Exception as exc:
            return self._failure("connect_failed", exc, run_id=run_id, recoverable=True)

    def session_status(self) -> ToolResult:
        return ToolResult.success(
            run_id=new_run_id("status"),
            active_doc_id=self.active_doc_id,
            data=self.session_data(),
        )

    def document_new(
        self,
        doc_type: str,
        template_path: Optional[str] = None,
    ) -> ToolResult:
        run_id = new_run_id("newdoc")
        try:
            self._ensure_connected()
            model = self.backend.new_document(self.sw, doc_type, template_path=template_path)
            record = self._record_document(model, fallback_type=doc_type)
            return ToolResult.success(
                run_id=run_id,
                doc_id=record.doc_id,
                active_doc_id=self.active_doc_id,
                data={"document": record.info.model_dump(mode="json")},
            )
        except Exception as exc:
            return self._failure("document_new_failed", exc, run_id=run_id, recoverable=True)

    def document_open(
        self,
        file_path: str,
        read_only: bool = False,
        silent: bool = False,
    ) -> ToolResult:
        run_id = new_run_id("opendoc")
        try:
            self._ensure_connected()
            model = self.backend.open_document(
                self.sw,
                file_path,
                read_only=read_only,
                silent=silent,
            )
            record = self._record_document(model)
            return ToolResult.success(
                run_id=run_id,
                doc_id=record.doc_id,
                active_doc_id=self.active_doc_id,
                data={"document": record.info.model_dump(mode="json")},
            )
        except Exception as exc:
            return self._failure("document_open_failed", exc, run_id=run_id, recoverable=True)

    def document_save(
        self,
        doc_id: Optional[str] = None,
        file_path: Optional[str] = None,
    ) -> ToolResult:
        run_id = new_run_id("save")
        try:
            record = self._get_record(doc_id)
            ok = self.backend.save_document(record.model, file_path=file_path)
            if not ok:
                return ToolResult.failure(
                    "document_save_failed",
                    "SolidWorks returned false from save.",
                    run_id=run_id,
                    recoverable=True,
                )
            artifact_path = file_path or record.info.path
            artifacts = [_artifact_for_path(artifact_path)] if artifact_path else []
            self._refresh_record(record.doc_id)
            return ToolResult.success(
                run_id=run_id,
                doc_id=record.doc_id,
                active_doc_id=self.active_doc_id,
                artifacts=artifacts,
            )
        except Exception as exc:
            return self._failure("document_save_failed", exc, run_id=run_id, recoverable=True)

    def part_create(self, spec: PartSpec | Dict[str, Any]) -> ToolResult:
        run_id = new_run_id("part")
        try:
            part_spec = _coerce(PartSpec, spec)
            self._ensure_connected()
            model = self.backend.create_part(self.sw, part_spec)
            record = self._record_document(model, fallback_type="part")
            artifacts = []
            if part_spec.output_path:
                artifacts.append(_artifact_for_path(part_spec.output_path, label=part_spec.name))
                self._refresh_record(record.doc_id)
            return ToolResult.success(
                run_id=run_id,
                doc_id=record.doc_id,
                active_doc_id=self.active_doc_id,
                artifacts=artifacts,
                data={
                    "part": part_spec.model_dump(mode="json"),
                    "document": self.documents[record.doc_id].info.model_dump(mode="json"),
                },
            )
        except Exception as exc:
            return self._failure("part_create_failed", exc, run_id=run_id, recoverable=True)

    def assembly_create(self, spec: AssemblySpec | Dict[str, Any]) -> ToolResult:
        run_id = new_run_id("assembly")
        artifacts: List[Artifact] = []
        try:
            assembly_spec = _coerce(AssemblySpec, spec)
            self._ensure_connected()
            assembly_spec = self._materialize_embedded_parts(assembly_spec, run_id, artifacts)
            model = self.backend.create_assembly(self.sw, assembly_spec)
            record = self._record_document(model, fallback_type="assembly")
            if assembly_spec.output_path:
                artifacts.append(_artifact_for_path(assembly_spec.output_path, label=assembly_spec.name))
                self._refresh_record(record.doc_id)
            return ToolResult.success(
                run_id=run_id,
                doc_id=record.doc_id,
                active_doc_id=self.active_doc_id,
                artifacts=artifacts,
                data={
                    "assembly": assembly_spec.model_dump(mode="json"),
                    "document": self.documents[record.doc_id].info.model_dump(mode="json"),
                },
            )
        except Exception as exc:
            return self._failure(
                "assembly_create_failed",
                exc,
                run_id=run_id,
                recoverable=True,
                data={"artifacts_before_failure": [item.model_dump(mode="json") for item in artifacts]},
            )

    def drawing_create(self, spec: DrawingSpec | Dict[str, Any]) -> ToolResult:
        run_id = new_run_id("drawing")
        try:
            drawing_spec = _coerce(DrawingSpec, spec)
            self._ensure_connected()
            source_path = drawing_spec.source_path
            if drawing_spec.source_doc_id:
                source_path = self._get_record(drawing_spec.source_doc_id).info.path
            model = self.backend.create_drawing(self.sw, drawing_spec, source_path)
            record = self._record_document(model, fallback_type="drawing")
            artifacts = []
            if drawing_spec.output_path:
                artifacts.append(_artifact_for_path(drawing_spec.output_path, label=drawing_spec.name))
            if drawing_spec.pdf_output_path:
                artifacts.append(_artifact_for_path(drawing_spec.pdf_output_path, label=f"{drawing_spec.name} PDF"))
            return ToolResult.success(
                run_id=run_id,
                doc_id=record.doc_id,
                active_doc_id=self.active_doc_id,
                artifacts=artifacts,
                data={
                    "drawing": drawing_spec.model_dump(mode="json"),
                    "document": record.info.model_dump(mode="json"),
                },
            )
        except Exception as exc:
            return self._failure("drawing_create_failed", exc, run_id=run_id, recoverable=True)

    def export(self, spec: ExportSpec | Dict[str, Any]) -> ToolResult:
        run_id = new_run_id("export")
        try:
            export_spec = _coerce(ExportSpec, spec)
            record = self._get_record(export_spec.doc_id)
            ok = self.backend.export_document(record.model, export_spec)
            if not ok:
                return ToolResult.failure(
                    "export_failed",
                    "SolidWorks returned false from export.",
                    run_id=run_id,
                    recoverable=True,
                )
            return ToolResult.success(
                run_id=run_id,
                doc_id=record.doc_id,
                active_doc_id=self.active_doc_id,
                artifacts=[_artifact_for_path(export_spec.output_path)],
                data={"export": export_spec.model_dump(mode="json")},
            )
        except Exception as exc:
            return self._failure("export_failed", exc, run_id=run_id, recoverable=True)

    def preview(
        self,
        doc_id: Optional[str] = None,
        output_path: Optional[str] = None,
        view: str = "isometric",
    ) -> ToolResult:
        run_id = new_run_id("preview")
        try:
            record = self._get_record(doc_id)
            preview_path = output_path or str(self._run_dir(run_id) / f"{record.doc_id}_{view}.bmp")
            actual_path = self.backend.save_preview(record.model, preview_path, view=view)
            return ToolResult.success(
                run_id=run_id,
                doc_id=record.doc_id,
                active_doc_id=self.active_doc_id,
                artifacts=[_artifact_for_path(actual_path, label=f"{view} preview")],
            )
        except Exception as exc:
            return self._failure("preview_failed", exc, run_id=run_id, recoverable=True)

    def review(self, spec: ReviewSpec | Dict[str, Any]) -> ToolResult:
        run_id = new_run_id("review")
        try:
            review_spec = _coerce(ReviewSpec, spec)
            record = self._get_record(review_spec.doc_id)
            report, report_path = self.backend.run_review(record.model, review_spec)
            assembly_inspection = None
            if record.info.doc_type == "assembly":
                try:
                    assembly_inspection = self.backend.inspect_assembly(record.model)
                    report["assembly_inspection"] = assembly_inspection
                except Exception as exc:
                    assembly_inspection = {
                        "status": "warn",
                        "errors": [{"code": "assembly_inspection_failed", "message": str(exc)}],
                    }
            artifacts = [_artifact_for_path(report_path, label="review report")]
            summary_path = report.get("summary_path")
            if summary_path:
                artifacts.append(_artifact_for_path(summary_path, label="review summary"))
            for preview in report.get("previews", []):
                artifacts.append(_artifact_for_path(preview["path"], label="review preview"))
            return ToolResult.success(
                run_id=run_id,
                doc_id=record.doc_id,
                active_doc_id=self.active_doc_id,
                artifacts=artifacts,
                review=report.get("evaluation", report),
                data={
                    "report_path": report_path,
                    "assembly_inspection": assembly_inspection,
                },
            )
        except Exception as exc:
            return self._failure("review_failed", exc, run_id=run_id, recoverable=True)

    def assembly_inspect(self, doc_id: Optional[str] = None) -> ToolResult:
        run_id = new_run_id("asm-inspect")
        try:
            record = self._get_record(doc_id)
            if record.info.doc_type != "assembly":
                return ToolResult.failure(
                    "not_an_assembly",
                    "assembly_inspect requires an assembly document.",
                    run_id=run_id,
                    recoverable=True,
                    data={"document": record.info.model_dump(mode="json")},
                )
            inspection = self.backend.inspect_assembly(record.model)
            warnings = []
            if inspection.get("status") != "pass":
                warnings.append("Assembly inspection reported warnings or failures.")
            return ToolResult.success(
                run_id=run_id,
                doc_id=record.doc_id,
                active_doc_id=self.active_doc_id,
                warnings=warnings,
                data={"assembly_inspection": inspection},
            )
        except Exception as exc:
            return self._failure("assembly_inspect_failed", exc, run_id=run_id, recoverable=True)

    def session_data(self) -> Dict[str, Any]:
        return {
            "connected": self.sw is not None,
            "active_doc_id": self.active_doc_id,
            "documents": [
                record.info.model_dump(mode="json")
                for record in self.documents.values()
            ],
            "output_root": str(self.output_root),
        }

    def _ensure_connected(self) -> None:
        if self.sw is None:
            result = self.connect()
            if not result.ok:
                message = result.errors[0].message if result.errors else "connect failed"
                raise RuntimeError(message)

    def _record_document(
        self,
        model: Any,
        fallback_type: Optional[str] = None,
    ) -> _DocumentRecord:
        self._doc_counter += 1
        doc_id = f"doc-{self._doc_counter}"
        for record in self.documents.values():
            record.info.active = False
        info = self.backend.document_info(
            model,
            doc_id=doc_id,
            active=True,
            fallback_type=fallback_type,
        )
        record = _DocumentRecord(doc_id=doc_id, model=model, info=info)
        self.documents[doc_id] = record
        self.active_doc_id = doc_id
        return record

    def _refresh_record(self, doc_id: str) -> None:
        record = self.documents[doc_id]
        record.info = self.backend.document_info(
            record.model,
            doc_id=doc_id,
            active=(doc_id == self.active_doc_id),
            fallback_type=record.info.doc_type,
        )

    def _get_record(self, doc_id: Optional[str] = None) -> _DocumentRecord:
        target_id = doc_id or self.active_doc_id
        if not target_id or target_id not in self.documents:
            raise ValueError("No active document. Provide doc_id or open/create a document first.")
        return self.documents[target_id]

    def _run_dir(self, run_id: str) -> Path:
        path = self.output_root / run_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _materialize_embedded_parts(
        self,
        spec: AssemblySpec,
        run_id: str,
        artifacts: List[Artifact],
    ) -> AssemblySpec:
        run_dir = self._run_dir(run_id) / "parts"
        run_dir.mkdir(parents=True, exist_ok=True)
        materialized_components: List[ComponentSpec] = []
        for component in spec.components:
            if component.part_path or not component.part:
                materialized_components.append(component)
                continue
            part_spec = component.part.model_copy(deep=True)
            part_spec.output_path = part_spec.output_path or str(run_dir / f"{part_spec.name}.sldprt")
            part_model = self.backend.create_part(self.sw, part_spec)
            self._record_document(part_model, fallback_type="part")
            artifacts.append(_artifact_for_path(part_spec.output_path, label=part_spec.name))
            component = component.model_copy(update={"part_path": part_spec.output_path, "part": part_spec})
            materialized_components.append(component)
        return spec.model_copy(update={"components": materialized_components})

    @staticmethod
    def _failure(
        code: str,
        exc: Exception,
        *,
        run_id: str,
        recoverable: bool,
        data: Optional[Dict[str, Any]] = None,
    ) -> ToolResult:
        return ToolResult.failure(
            code,
            str(exc),
            run_id=run_id,
            detail=exc.__class__.__name__,
            recoverable=recoverable,
            data=data,
        )
