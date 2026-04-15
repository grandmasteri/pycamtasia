"""Round-trip validation for ALL TechSmith sample projects.

Loads each project's JSON, passes it through load_project → save,
and verifies the output JSON is identical to the input.  This is the
ultimate proof that pycamtasia does not corrupt data.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from camtasia import load_project

FIXTURES = Path(__file__).parent / "fixtures"

# ---------------------------------------------------------------------------
# Collect every sample file we can find
# ---------------------------------------------------------------------------

def _collect_samples() -> list[Path]:
    paths: list[Path] = []

    # .assetproj files in /tmp dirs
    for tmp_dir in (Path("/tmp/techsmith_extra"), Path("/tmp/techsmith_samples")):
        if tmp_dir.is_dir():
            paths.extend(tmp_dir.rglob("*.assetproj"))

    # .tscproj fixtures shipped with the repo
    if FIXTURES.is_dir():
        paths.extend(FIXTURES.glob("*.tscproj"))

    return sorted(paths)


ALL_SAMPLES = _collect_samples()


def _sample_id(p: Path) -> str:
    """Short human-readable id for parametrize."""
    return p.stem


# ---------------------------------------------------------------------------
# Test
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("sample_path", ALL_SAMPLES, ids=_sample_id)
def test_roundtrip_json_preserved(sample_path: Path, tmp_path: Path) -> None:
    """load_project → save must produce JSON identical to the original."""
    if not sample_path.exists():
        pytest.skip(f"File not found: {sample_path}")

    original_json = json.loads(sample_path.read_text())
    original_serialized = json.dumps(original_json, sort_keys=True)

    # Copy the bundle (or standalone file) so save() doesn't touch the original.
    parent = sample_path.parent
    if parent.suffix in (".asset", ".cmproj"):
        # Bundle directory — copy the whole bundle
        dst_bundle = tmp_path / parent.name
        shutil.copytree(parent, dst_bundle)
        project_file = dst_bundle / sample_path.name
    else:
        # Standalone file
        project_file = tmp_path / sample_path.name
        shutil.copy2(sample_path, project_file)

    proj = load_project(str(project_file))
    proj.save()

    saved_json = json.loads(project_file.read_text())
    saved_serialized = json.dumps(saved_json, sort_keys=True)

    assert saved_serialized == original_serialized, (
        f"Round-trip mismatch for {sample_path.name}"
    )
