"""SolidWorks Automation Python helper package.

The package exposes legacy script helpers and the newer enterprise service
layer. COM-heavy modules are imported lazily so schema/tests can run on
machines without SolidWorks or pywin32 installed.
"""
from __future__ import annotations

from importlib import import_module
from typing import Dict, Tuple


_LAZY_EXPORTS: Dict[str, Tuple[str, str]] = {
    "AssemblySpec": (".sw_models", "AssemblySpec"),
    "DrawingSpec": (".sw_models", "DrawingSpec"),
    "ExportSpec": (".sw_models", "ExportSpec"),
    "PartSpec": (".sw_models", "PartSpec"),
    "ReviewSpec": (".sw_models", "ReviewSpec"),
    "ToolResult": (".sw_models", "ToolResult"),
    "BENCHMARK_NAMES": (".sw_workflows", "BENCHMARK_NAMES"),
    "SolidWorksAutomationService": (".sw_service", "SolidWorksAutomationService"),
    "SolidWorksSession": (".sw_session", "SolidWorksSession"),
    "build_prompt": (".sw_macro_guard", "build_prompt"),
    "connect_solidworks": (".sw_connect", "connect_solidworks"),
    "deg": (".sw_connect", "deg"),
    "generate_macro_with_guard": (".sw_macro_guard", "generate_macro_with_guard"),
    "mm": (".sw_connect", "mm"),
    "new_document": (".sw_connect", "new_document"),
    "open_document": (".sw_connect", "open_document"),
    "run_preflight": (".sw_preflight", "run_preflight"),
    "run_benchmark": (".sw_workflows", "run_benchmark"),
    "save_document": (".sw_connect", "save_document"),
    "session": (".sw_session", "session"),
    "validate_vba_macro": (".sw_macro_guard", "validate_vba_macro"),
}


def __getattr__(name: str):
    if name not in _LAZY_EXPORTS:
        raise AttributeError(name)
    module_name, attr_name = _LAZY_EXPORTS[name]
    module = import_module(module_name, __name__)
    value = getattr(module, attr_name)
    globals()[name] = value
    return value


__all__ = sorted(_LAZY_EXPORTS)
