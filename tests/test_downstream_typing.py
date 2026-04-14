"""Verify that downstream consumers can type-check against pycamtasia.

This test runs mypy on a sample consumer script to ensure our py.typed
marker and type annotations work correctly for external users.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import pytest


SAMPLE_CONSUMER_SCRIPT: str = '''
from camtasia import load_project, Project
from camtasia.types import ClipType, EffectName, TransitionType

def process_project(path: str) -> None:
    project: Project = load_project(path)
    title: str = project.title
    width: int = project.width
    is_empty: bool = project.is_empty

    for track in project.timeline.tracks:
        name: str = track.name
        for clip in track.clips:
            clip_type: str = clip.clip_type
            if clip.matches_type(ClipType.VIDEO):
                clip.add_drop_shadow()
'''


@pytest.mark.skipif(
    sys.version_info < (3, 11),
    reason="mypy consumer test only runs on 3.11+ (Self type)",
)
def test_downstream_mypy_type_checking(tmp_path: Path) -> None:
    """A consumer script type-checks cleanly against our library."""
    consumer_script_path: Path = tmp_path / "consumer.py"
    consumer_script_path.write_text(SAMPLE_CONSUMER_SCRIPT)

    mypy_result: subprocess.CompletedProcess[str] = subprocess.run(
        [sys.executable, "-m", "mypy", str(consumer_script_path), "--ignore-missing-imports"],
        capture_output=True,
        text=True,
    )
    assert mypy_result.returncode == 0, f"mypy failed:\n{mypy_result.stdout}\n{mypy_result.stderr}"
