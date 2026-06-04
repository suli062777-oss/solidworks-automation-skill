from dataclasses import dataclass
from pathlib import Path

from scripts.sw_models import (
    Artifact,
    AssemblySpec,
    ComponentSpec,
    DocumentInfo,
    ExportSpec,
    InterfaceSpec,
    MateEndpoint,
    MateSpec,
    PartSpec,
    ReviewSpec,
    TransformSpec,
)
from scripts.sw_service import SolidWorksAutomationService
from scripts.sw_workflows import BENCHMARK_NAMES, build_benchmark_specs


@dataclass
class FakePreflight:
    missing_packages: list
    dependencies_ready: bool
    solidworks_ready: bool


@dataclass
class FakeModel:
    title: str
    path: str = ""
    doc_type: str = "part"


class FakeBackend:
    def __init__(self, root: Path):
        self.root = root
        self.calls = []
        self.counter = 0

    def preflight(self, allow_install=False, check_solidworks=True):
        self.calls.append(("preflight", allow_install, check_solidworks))
        return FakePreflight([], True, check_solidworks)

    def connect(self, version=None, wait_seconds=5, visible=True):
        self.calls.append(("connect", version, wait_seconds, visible))
        return "fake-sw", None

    def document_info(self, model, doc_id, active=False, fallback_type=None):
        return DocumentInfo(
            doc_id=doc_id,
            title=model.title,
            path=model.path,
            doc_type=model.doc_type or fallback_type,
            active=active,
        )

    def new_document(self, sw, doc_type, template_path=None):
        self.counter += 1
        return FakeModel(f"{doc_type}-{self.counter}", doc_type=doc_type)

    def open_document(self, sw, file_path, read_only=False, silent=False):
        return FakeModel(Path(file_path).stem, path=file_path, doc_type="part")

    def save_document(self, model, file_path=None):
        path = Path(file_path or model.path or self.root / f"{model.title}.sldprt")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(model.title, encoding="utf-8")
        model.path = str(path)
        return True

    def export_document(self, model, spec):
        path = Path(spec.output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"export:{model.title}", encoding="utf-8")
        return True

    def save_preview(self, model, path, view="isometric"):
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(b"BM" + bytes(range(64)))
        return str(output)

    def run_review(self, model, spec):
        output_dir = Path(spec.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        preview = output_dir / f"{spec.basename}_isometric.bmp"
        preview.write_bytes(b"BM" + bytes(range(64)))
        report_path = output_dir / f"{spec.basename}_review_report.json"
        summary_path = output_dir / f"{spec.basename}_review_summary.md"
        report_path.write_text("{}", encoding="utf-8")
        summary_path.write_text("# summary\n", encoding="utf-8")
        return {
            "evaluation": {"status": "pass", "score": 100},
            "summary_path": str(summary_path),
            "previews": [{"path": str(preview)}],
        }, str(report_path)

    def create_part(self, sw, spec):
        model = FakeModel(spec.name, doc_type="part")
        if spec.output_path:
            self.save_document(model, spec.output_path)
        self.calls.append(("part", spec.name))
        return model

    def create_assembly(self, sw, spec):
        model = FakeModel(spec.name, doc_type="assembly")
        if spec.output_path:
            self.save_document(model, spec.output_path)
        self.calls.append(("assembly", spec.name, len(spec.components), len(spec.mates)))
        return model

    def create_drawing(self, sw, spec, source_path):
        model = FakeModel(spec.name, doc_type="drawing")
        if spec.output_path:
            self.save_document(model, spec.output_path)
        if spec.pdf_output_path:
            pdf = Path(spec.pdf_output_path)
            pdf.parent.mkdir(parents=True, exist_ok=True)
            pdf.write_text("pdf", encoding="utf-8")
        self.calls.append(("drawing", spec.name, source_path))
        return model

    def inspect_assembly(self, model):
        return {
            "status": "pass",
            "checks": {
                "components_present": True,
                "component_count": 2,
                "mate_feature_count": 1,
                "interference_count": 0,
                "rebuild_ok": True,
                "inspection_complete": True,
            },
            "components": [
                {"name": "base-1", "path": "base.sldprt", "suppressed": False, "visible": True},
                {"name": "bracket-1", "path": "bracket.sldprt", "suppressed": False, "visible": True},
            ],
            "mates": [{"name": "mate-1", "type": "MateGroup"}],
            "errors": [],
        }


def test_service_exposes_structured_connection_status(tmp_path: Path):
    service = SolidWorksAutomationService(
        backend=FakeBackend(tmp_path),
        output_root=tmp_path / "runs",
    )

    assert service.preflight(check_solidworks=False).ok is True
    connect = service.connect()
    status = service.session_status().as_dict()

    assert connect.ok is True
    assert status["data"]["connected"] is True
    assert status["data"]["active_doc_id"] is None


def test_service_runs_part_assembly_export_review_with_fake_backend(tmp_path: Path):
    backend = FakeBackend(tmp_path)
    service = SolidWorksAutomationService(backend=backend, output_root=tmp_path / "runs")
    service.connect()

    base = PartSpec(
        name="base",
        output_path=str(tmp_path / "base.sldprt"),
        interfaces=[
            InterfaceSpec(
                id="datum_top",
                kind="mounting_face",
                target_name="Top Plane",
                entity_type="PLANE",
            )
        ],
    )
    bracket = PartSpec(
        name="bracket",
        output_path=str(tmp_path / "bracket.sldprt"),
        interfaces=[
            InterfaceSpec(
                id="datum_bottom",
                kind="mounting_face",
                target_name="Top Plane",
                entity_type="PLANE",
            )
        ],
    )

    assembly = AssemblySpec(
        name="asm",
        output_path=str(tmp_path / "asm.sldasm"),
        components=[
            ComponentSpec(name="base-1", part=base, fixed=True),
            ComponentSpec(
                name="bracket-1",
                part=bracket,
                transform=TransformSpec(translation_mm=(0, 0, 10)),
            ),
        ],
        mates=[
            MateSpec(
                id="mate-1",
                mate_type="coincident",
                a=MateEndpoint(component="base-1", interface_id="datum_top"),
                b=MateEndpoint(component="bracket-1", interface_id="datum_bottom"),
            )
        ],
    )

    assembly_result = service.assembly_create(assembly)
    assert assembly_result.ok is True
    assert assembly_result.doc_id is not None
    assert Path(tmp_path / "asm.sldasm").exists()
    assert any(item.kind == "sldasm" for item in assembly_result.artifacts)

    inspect_result = service.assembly_inspect(assembly_result.doc_id)
    assert inspect_result.ok is True
    assert inspect_result.data["assembly_inspection"]["status"] == "pass"

    export_result = service.export(
        ExportSpec(
            doc_id=assembly_result.doc_id,
            output_path=str(tmp_path / "asm.step"),
        )
    )
    assert export_result.ok is True
    assert Path(tmp_path / "asm.step").exists()

    review_result = service.review(
        ReviewSpec(
            doc_id=assembly_result.doc_id,
            output_dir=str(tmp_path / "review"),
            basename="asm",
        )
    )
    assert review_result.ok is True
    assert review_result.review["status"] == "pass"
    assert review_result.data["assembly_inspection"]["status"] == "pass"


def test_all_benchmark_specs_are_buildable(tmp_path: Path):
    for name in BENCHMARK_NAMES:
        spec = build_benchmark_specs(name, tmp_path / name)
        assert spec["name"] == name
        assert "review" in spec
        assert "part" in spec or "assembly" in spec
