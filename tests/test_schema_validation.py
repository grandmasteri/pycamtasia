"""Validate that pycamtasia-generated projects conform to the JSON Schema.

The schema at src/camtasia/resources/camtasia-project-schema.json was built
from 93 real TechSmith projects with strict enums, required fields, and
additionalProperties:false.  Any violation means our library is producing
invalid output.
"""
from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from camtasia import load_project, new_project
from camtasia.validation import ValidationIssue, validate_against_schema

if TYPE_CHECKING:
    from pathlib import Path

try:
    import jsonschema  # noqa: F401
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False

pytestmark = pytest.mark.skipif(not HAS_JSONSCHEMA, reason="jsonschema not installed")


@pytest.fixture
def built_project(tmp_path: Path) -> dict:
    """Create a project using the high-level API, save it, and return the saved JSON."""
    proj_path = tmp_path / "schema_test.cmproj"
    new_project(proj_path)
    proj = load_project(proj_path)

    # -- tracks & clips --
    track_a = proj.timeline.add_track("Video")
    clip1 = track_a.add_clip("VMFile", 1, 0, 705600000)
    clip2 = track_a.add_clip("VMFile", 1, 705600000, 705600000)

    track_b = proj.timeline.add_track("Audio")
    track_b.add_clip("AMFile", 1, 0, 705600000 * 2)

    # -- effect on a clip --
    clip1.add_drop_shadow()

    # -- transition between two clips --
    track_a.add_transition("FadeThroughBlack", clip1, clip2, duration_seconds=0.5)

    # -- group two clips --
    track_c = proj.timeline.add_track("Grouped")
    g1 = track_c.add_clip("VMFile", 1, 0, 705600000)
    g2 = track_c.add_clip("VMFile", 1, 705600000, 705600000)
    track_c.group_clips([g1.id, g2.id])

    proj.save()

    # Re-read the saved JSON from disk
    project_json_path = proj_path / "project.tscproj"
    return json.loads(project_json_path.read_text(encoding="utf-8"))


@pytest.mark.filterwarnings("ignore::UserWarning")
def test_generated_project_is_schema_valid(built_project: dict) -> None:
    """Library output must produce zero schema violations."""
    issues = validate_against_schema(built_project)
    errors = [i for i in issues if i.level == "error"]
    assert errors == [], (
        f"{len(errors)} schema violation(s):\n"
        + "\n".join(f"  • {e.message}" for e in errors)
    )


@pytest.mark.filterwarnings("ignore::UserWarning")
def test_schema_validation_reports_errors_for_invalid_data() -> None:
    """Cover validation.py lines 376-377: schema violation loop body."""
    issues = validate_against_schema({"invalid_key": True})
    actual_errors = {i for i in issues if i.level == "error"}
    expected_errors = {
        ValidationIssue("error", "Schema violation at (root): 'editRate' is a required property"),
        ValidationIssue("error", "Schema violation at (root): 'height' is a required property"),
        ValidationIssue("error", "Schema violation at (root): 'sourceBin' is a required property"),
        ValidationIssue("error", "Schema violation at (root): 'timeline' is a required property"),
        ValidationIssue("error", "Schema violation at (root): 'version' is a required property"),
        ValidationIssue("error", "Schema violation at (root): 'width' is a required property"),
        ValidationIssue("error", "Schema violation at (root): Additional properties are not allowed ('invalid_key' was unexpected)"),
    }
    assert actual_errors == expected_errors
