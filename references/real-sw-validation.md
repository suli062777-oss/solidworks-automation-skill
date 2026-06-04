# Real SolidWorks Validation Log

Use this document when validating the M2/M3 workflow on a Windows machine with
SolidWorks installed. The goal is to prove the MCP/service workflow works
without Codex writing one-off COM scripts.

## Environment

Fill this in during validation:

- Date:
- Machine:
- Windows version:
- SolidWorks version/year:
- SolidWorks language:
- Python version:
- Repository commit:
- Install command:

## Setup Commands

```bash
python -m pip install -e ".[mcp]"
solidworks-mcp-server
```

Optional CLI benchmark:

```bash
solidworks-thin-slice --benchmark enterprise_thin_slice --output-dir output/enterprise_thin_slice --json
```

Run the smaller benchmarks independently:

```bash
solidworks-thin-slice --benchmark mounting_plate_only --output-dir output/mounting_plate_only --json
solidworks-thin-slice --benchmark shaft_and_sleeve --output-dir output/shaft_and_sleeve --json
solidworks-thin-slice --benchmark bracket_on_base_assembly --output-dir output/bracket_on_base_assembly --json
```

## MCP Tool Sequence

Run these through an MCP client:

1. `sw_preflight(allow_install=false, check_solidworks=true)`
2. `sw_connect()`
3. `sw_assembly_create(spec=enterprise_thin_slice assembly spec)`
4. `sw_assembly_inspect(doc_id=<assembly doc id>)`
5. `sw_export(spec={"doc_id": "...", "output_path": "...step"})`
6. `sw_drawing_create(spec={...})`
7. `sw_review(spec={...})`

## Expected Artifacts

The enterprise thin-slice benchmark should produce:

- `parts/base_plate.sldprt`
- `parts/support_bracket.sldprt`
- `parts/demo_shaft.sldprt`
- `enterprise_thin_slice.sldasm`
- `exports/enterprise_thin_slice.step`
- `drawings/enterprise_thin_slice.slddrw`
- `exports/enterprise_thin_slice.pdf`
- `review/enterprise_thin_slice_review_report.json`
- `review/enterprise_thin_slice_review_summary.md`
- `review/*_isometric.bmp`, `*_front.bmp`, `*_top.bmp`, `*_right.bmp`

## Validation Results

| Step | Status | Notes / failure code |
|---|---|---|
| Install dependencies | Not run | |
| `sw_preflight` | Not run | |
| `sw_connect` | Not run | |
| `sw_assembly_create` | Not run | |
| `sw_assembly_inspect` | Not run | |
| `sw_export` | Not run | |
| `sw_drawing_create` | Not run | |
| `sw_review` | Not run | |

## Failure Capture

For every failure, capture:

- MCP tool name
- `run_id`
- `errors[0].code`
- `errors[0].message`
- `errors[0].detail`
- `recoverable`
- SolidWorks visible error dialog text, if any
- Whether rerunning the same tool changes the result

## Acceptance Criteria

Validation passes when:

- Codex/MCP completes the flow without direct Python COM script generation.
- `sw_assembly_inspect` returns `status=pass` or an explained `warn`.
- Generated files exist and have nonzero size.
- `sw_review` returns previews and a review report.
- Any failure is reported as structured JSON, not only console `print` output.

