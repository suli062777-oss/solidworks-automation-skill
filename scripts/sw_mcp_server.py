"""MCP server exposing SolidWorks automation as structured tools."""
from __future__ import annotations

from typing import Any, Dict, Optional

try:
    from .sw_models import AssemblySpec, DrawingSpec, ExportSpec, PartSpec, ReviewSpec
    from .sw_service import SolidWorksAutomationService
except ImportError:  # pragma: no cover - direct scripts path compatibility
    from sw_models import AssemblySpec, DrawingSpec, ExportSpec, PartSpec, ReviewSpec
    from sw_service import SolidWorksAutomationService


SERVICE = SolidWorksAutomationService()


def _missing_mcp_error() -> RuntimeError:
    return RuntimeError(
        "The MCP runtime is not installed. Install with: "
        "python -m pip install 'solidworks-automation[mcp]'"
    )


try:
    from mcp.server.fastmcp import FastMCP
except Exception:  # pragma: no cover - exercised only without optional dep
    FastMCP = None  # type: ignore[assignment]


def create_mcp(service: Optional[SolidWorksAutomationService] = None):
    """Create and configure the SolidWorks MCP server."""
    if FastMCP is None:
        raise _missing_mcp_error()

    active_service = service or SERVICE
    mcp = FastMCP("solidworks-automation")

    @mcp.tool()
    def sw_preflight(
        allow_install: bool = False,
        check_solidworks: bool = True,
    ) -> Dict[str, Any]:
        """Check Python COM dependencies and SolidWorks availability."""
        return active_service.preflight(
            allow_install=allow_install,
            check_solidworks=check_solidworks,
        ).as_dict()

    @mcp.tool()
    def sw_connect(
        version: Optional[int] = None,
        wait_seconds: int = 5,
        visible: bool = True,
    ) -> Dict[str, Any]:
        """Connect to a running SolidWorks instance or start one."""
        return active_service.connect(
            version=version,
            wait_seconds=wait_seconds,
            visible=visible,
        ).as_dict()

    @mcp.tool()
    def sw_session_status() -> Dict[str, Any]:
        """Return connection state, open document handles, and output root."""
        return active_service.session_status().as_dict()

    @mcp.tool()
    def sw_document_new(
        doc_type: str,
        template_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new SolidWorks part, assembly, or drawing."""
        return active_service.document_new(
            doc_type=doc_type,
            template_path=template_path,
        ).as_dict()

    @mcp.tool()
    def sw_document_open(
        file_path: str,
        read_only: bool = False,
        silent: bool = False,
    ) -> Dict[str, Any]:
        """Open an existing SolidWorks document."""
        return active_service.document_open(
            file_path=file_path,
            read_only=read_only,
            silent=silent,
        ).as_dict()

    @mcp.tool()
    def sw_document_save(
        doc_id: Optional[str] = None,
        file_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Save a document by handle or save the active document."""
        return active_service.document_save(
            doc_id=doc_id,
            file_path=file_path,
        ).as_dict()

    @mcp.tool()
    def sw_part_create(spec: Dict[str, Any]) -> Dict[str, Any]:
        """Create a parameterized part from a PartSpec."""
        return active_service.part_create(PartSpec.model_validate(spec)).as_dict()

    @mcp.tool()
    def sw_assembly_create(spec: Dict[str, Any]) -> Dict[str, Any]:
        """Create an assembly from components, semantic interfaces, and mates."""
        return active_service.assembly_create(AssemblySpec.model_validate(spec)).as_dict()

    @mcp.tool()
    def sw_assembly_inspect(doc_id: Optional[str] = None) -> Dict[str, Any]:
        """Inspect assembly components, mate summary, interference, and rebuild health."""
        return active_service.assembly_inspect(doc_id=doc_id).as_dict()

    @mcp.tool()
    def sw_drawing_create(spec: Dict[str, Any]) -> Dict[str, Any]:
        """Create a drawing and optional PDF/BOM output."""
        return active_service.drawing_create(DrawingSpec.model_validate(spec)).as_dict()

    @mcp.tool()
    def sw_export(spec: Dict[str, Any]) -> Dict[str, Any]:
        """Export a document to STEP, STL, IGES, PDF, DXF/DWG, or Parasolid."""
        return active_service.export(ExportSpec.model_validate(spec)).as_dict()

    @mcp.tool()
    def sw_preview(
        doc_id: Optional[str] = None,
        output_path: Optional[str] = None,
        view: str = "isometric",
    ) -> Dict[str, Any]:
        """Export a single preview image for a document."""
        return active_service.preview(
            doc_id=doc_id,
            output_path=output_path,
            view=view,
        ).as_dict()

    @mcp.tool()
    def sw_review(spec: Dict[str, Any]) -> Dict[str, Any]:
        """Run multi-view preview export and rule-based CAD review."""
        return active_service.review(ReviewSpec.model_validate(spec)).as_dict()

    return mcp


def main() -> None:
    """CLI entrypoint used by the package script."""
    mcp = create_mcp()
    mcp.run()


if __name__ == "__main__":
    main()
