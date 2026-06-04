from pathlib import Path

import pytest

from scripts.sw_models import (
    ComponentSpec,
    InterfaceSpec,
    MateEndpoint,
    PartSpec,
    ToolResult,
    TransformSpec,
)
from scripts.sw_selection import SelectionResolver


def test_part_spec_validates_rgb_and_units():
    spec = PartSpec(
        name="plate",
        template="mounting_plate",
        color_rgb=(12, 128, 255),
        parameters={"width_mm": 120, "height_mm": 80, "thickness": 10},
    )

    assert spec.unit == "mm"
    assert spec.parameters["width_mm"] == 120

    with pytest.raises(ValueError):
        PartSpec(name="bad", color_rgb=(999, 0, 0))


def test_transform_translates_public_mm_to_api_meters():
    transform = TransformSpec(translation_mm=(50, 25, 10))

    assert transform.translation_m == (0.05, 0.025, 0.01)


def test_tool_result_shape_is_agent_friendly(tmp_path: Path):
    artifact = tmp_path / "part.step"
    artifact.write_text("step", encoding="utf-8")

    result = ToolResult.success(
        doc_id="doc-1",
        artifacts=[],
        data={"hello": "world"},
    )

    payload = result.as_dict()
    assert payload["ok"] is True
    assert payload["doc_id"] == "doc-1"
    assert payload["errors"] == []
    assert payload["data"] == {"hello": "world"}

    failure = ToolResult.failure("boom", "Something failed", recoverable=True)
    assert failure.as_dict()["errors"][0]["recoverable"] is True


def test_selection_resolver_prefers_semantic_interfaces():
    part = PartSpec(
        name="base",
        interfaces=[
            InterfaceSpec(
                id="datum_top",
                kind="mounting_face",
                target_name="Top Plane",
                target_aliases=["datum_top_feature"],
                entity_type="PLANE",
            )
        ],
    )
    component = ComponentSpec(name="base-1", part=part)
    resolver = SelectionResolver([component])

    candidate = resolver.require_one(
        MateEndpoint(component="base-1", interface_id="datum_top")
    )

    assert candidate.target_name == "Top Plane@base-1"
    assert candidate.entity_type == "PLANE"
    assert candidate.reason == "interface:datum_top"

    candidates = resolver.resolve(MateEndpoint(component="base-1", interface_id="datum_top"))
    assert [item.target_name for item in candidates] == [
        "Top Plane@base-1",
        "datum_top_feature@base-1",
        "datum_top@base-1",
    ]
