"""Round-trip validation for ALL TechSmith sample projects.

Loads each project's JSON, passes it through load_project → save,
and verifies the output JSON is identical to the input.  This is the
ultimate proof that pycamtasia does not corrupt data.

Extended samples
~~~~~~~~~~~~~~~~
To test against additional TechSmith projects beyond the bundled fixtures,
place ``.assetproj`` files in one of these directories:

- ``/tmp/techsmith_extra``
- ``/tmp/techsmith_samples``

The test count varies by environment — bundled fixtures always run,
``/tmp`` samples are additive.  See D-010 in design-decisions.md.
"""
from __future__ import annotations

import json
from pathlib import Path
import shutil

import pytest

from camtasia import load_project

FIXTURES = Path(__file__).parent / "fixtures"

# Optional /tmp directories for extended sample coverage (see module docstring).
_EXTRA_DIRS = (Path("/tmp/techsmith_extra"), Path("/tmp/techsmith_samples"))


def _collect_samples() -> list[Path]:
    paths: list[Path] = []

    for tmp_dir in _EXTRA_DIRS:
        if tmp_dir.is_dir():
            paths.extend(tmp_dir.rglob("*.assetproj"))

    if FIXTURES.is_dir():
        paths.extend(FIXTURES.glob("*.tscproj"))

    return sorted(paths)


ALL_SAMPLES = _collect_samples()


def _sample_id(p: Path) -> str:
    """Short human-readable id for parametrize."""
    return p.stem


@pytest.mark.parametrize("sample_path", ALL_SAMPLES, ids=_sample_id)
def test_roundtrip_json_preserved(sample_path: Path, tmp_path: Path) -> None:
    """load_project → save must produce JSON identical to the original."""
    if not sample_path.exists():
        pytest.skip(f"File not found: {sample_path}")

    original_json = json.loads(sample_path.read_text())
    original_serialized = json.dumps(original_json, sort_keys=True)

    parent = sample_path.parent
    if parent.suffix in (".asset", ".cmproj"):
        dst_bundle = tmp_path / parent.name
        shutil.copytree(parent, dst_bundle)
        project_file = dst_bundle / sample_path.name
    else:
        project_file = tmp_path / sample_path.name
        shutil.copy2(sample_path, project_file)

    proj = load_project(str(project_file))
    proj.save()

    saved_json = json.loads(project_file.read_text())
    saved_serialized = json.dumps(saved_json, sort_keys=True)

    assert saved_serialized == original_serialized, (
        f"Round-trip mismatch for {sample_path.name}"
    )
