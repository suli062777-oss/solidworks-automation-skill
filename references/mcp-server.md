# SolidWorks MCP Server

The enterprise upgrade exposes SolidWorks automation through MCP tools so
Codex can call structured operations instead of generating one-off COM scripts.

## Install

```bash
python -m pip install -e ".[mcp]"
```

For development and tests:

```bash
python -m pip install -e ".[dev]"
```

## Start

```bash
solidworks-mcp-server
```

Equivalent direct module form:

```bash
python -m solidworks_automation.sw_mcp_server
```

## Tool Result Shape

Every tool returns:

```json
{
  "ok": true,
  "run_id": "sw-...",
  "doc_id": "doc-1",
  "active_doc_id": "doc-1",
  "artifacts": [],
  "warnings": [],
  "errors": [],
  "review": null,
  "data": {}
}
```

On failure, `ok` is false and `errors[0]` contains `code`, `message`, `detail`,
and `recoverable`.

## Public Tools

| Tool | Purpose |
|---|---|
| `sw_preflight` | Check COM dependencies and SolidWorks availability |
| `sw_connect` | Connect to or start SolidWorks |
| `sw_session_status` | List open document handles and active document |
| `sw_document_new` | Create a part, assembly, or drawing |
| `sw_document_open` | Open a SolidWorks file |
| `sw_document_save` | Save active or named document handle |
| `sw_part_create` | Create a parameterized part from `PartSpec` |
| `sw_assembly_create` | Create an assembly from `AssemblySpec` |
| `sw_assembly_inspect` | Inspect components, mate summary, interference, and rebuild health |
| `sw_drawing_create` | Create drawing/PDF/BOM outputs from `DrawingSpec` |
| `sw_export` | Export a document from `ExportSpec` |
| `sw_preview` | Export one preview image |
| `sw_review` | Export multi-view previews and review report |

## Recommended Agent Flow

1. Call `sw_preflight(allow_install=false)`.
2. Call `sw_connect()`.
3. Use typed specs for part, assembly, drawing, export, and review.
4. Inspect `ok`, `warnings`, `errors`, and `artifacts` after every step.
5. If a tool fails, use the structured error code before trying a repair.
6. Only write direct COM scripts for debugging or for an API not yet wrapped.

## Thin-Slice Benchmark

```bash
solidworks-thin-slice --benchmark enterprise_thin_slice --output-dir output/enterprise_thin_slice --json
```

The benchmark generates a small assembly workflow:

- mounting base plate
- support bracket
- shaft
- assembly mates
- drawing/PDF
- STEP export
- review report and preview images

Additional regression benchmarks:

```bash
solidworks-thin-slice --list
solidworks-thin-slice --benchmark mounting_plate_only --output-dir output/mounting_plate_only --json
solidworks-thin-slice --benchmark shaft_and_sleeve --output-dir output/shaft_and_sleeve --json
solidworks-thin-slice --benchmark bracket_on_base_assembly --output-dir output/bracket_on_base_assembly --json
```
