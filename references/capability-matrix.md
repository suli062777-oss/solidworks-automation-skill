# Capability Matrix

This matrix is the M0 baseline for the enterprise upgrade. It separates
implemented behavior from roadmap items so future agents do not confuse
README claims with production-ready CAD capability.

## Implemented In Current Code

| Area | Current capability | Main module |
|---|---|---|
| Connection | Connect to running SolidWorks or start via COM ProgID | `sw_connect.py` |
| Documents | New/open/save part, assembly, drawing | `sw_connect.py`, `sw_session.py` |
| Units | `mm()` and `deg()` helpers | `sw_connect.py` |
| Basic sketches | Lines, rectangles, circles, arcs, polygons, slots, splines | `sw_part.py` |
| Basic features | Extrude boss/cut, mid-plane extrude, revolve, fillet, chamfer, shell, rib, mirror, patterns | `sw_part.py` |
| Assemblies | Add components, basic coincident/concentric/distance/parallel mates, list components, suppress/replace, interference count | `sw_assembly.py` |
| Drawings | Standard views, view insertion, simple section/detail hooks, model annotations, BOM insertion when template is supplied, PDF export | `sw_drawing.py` |
| Export | STEP, STL, IGES, Parasolid, PDF, DXF/DWG | `sw_export.py` |
| Review | BMP previews, feature summary, file-existence checks, JSON/Markdown report | `sw_review.py` |
| Agent guardrails | Macro prompt/validation/fallback helpers | `sw_macro_guard.py` |

## Implemented In Enterprise Upgrade v1

| Area | New capability | Main module |
|---|---|---|
| Typed specs | `PartSpec`, `AssemblySpec`, `InterfaceSpec`, `MateSpec`, `DrawingSpec`, `ExportSpec`, `ReviewSpec` | `sw_models.py` |
| Uniform tool result | `ok`, `doc_id`, `run_id`, `artifacts`, `warnings`, `errors`, `review`, `data` | `sw_models.py` |
| Stable selection layer | Semantic interface ID resolution before fallback raw `SelectByID2` names | `sw_selection.py` |
| Stateful service | Session state, document handles, structured errors, artifact collection | `sw_service.py` |
| MCP tools | `sw_preflight`, `sw_connect`, `sw_session_status`, document, part, assembly, assembly inspection, drawing, export, preview, review tools | `sw_mcp_server.py` |
| Thin-slice benchmark | Parameterized parts -> assembly -> inspection -> drawing/export/review workflow | `sw_workflows.py`, `sw_benchmark.py` |
| Regression benchmarks | `mounting_plate_only`, `shaft_and_sleeve`, `bracket_on_base_assembly`, `enterprise_thin_slice` | `sw_workflows.py` |

## Known Gaps To Close Next

| Gap | Why it matters | Suggested milestone |
|---|---|---|
| Geometry-based selection | `Face1@component` names are unstable after topology changes | M3 |
| Full Hole Wizard wrapper | Industrial holes, tapped holes, countersinks, counterbores need reliable parameter mapping | M4 |
| Robust mate diagnostics | Real assemblies need under/over-constrained and failed-mate reporting | M5 |
| Standard fastener workflow | Production assemblies need screw/washer/nut placement and BOM fields | M5 |
| Drawing quality checks | PDF exists is not enough; dimensions, title block, BOM rows, scale need verification | M6/M7 |
| Engineering review rules | Need mass/CoG, bounding boxes, interference bodies, rebuild errors, material/property coverage | M7 |
| Enterprise configuration | Templates, materials, naming, output policy, BOM fields should be project-configurable | M8 |
| PDM/PLM integration | Enterprise release workflows need vault paths, revisions, approval state | M8+ |

## Acceptance Rule

A capability should not be advertised as enterprise-ready until it has:

- A typed public spec or MCP tool.
- A real SolidWorks implementation path.
- A fake-COM unit test or deterministic static test.
- A benchmark or example that exercises it.
- Structured failure output when the operation cannot complete.
