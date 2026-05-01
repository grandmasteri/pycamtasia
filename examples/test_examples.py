"""Pytest smoke tests that run each example script via subprocess."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

EXAMPLES_DIR = Path(__file__).parent
FIXTURE = EXAMPLES_DIR.parent / "tests" / "fixtures" / "test_project_a.tscproj"


def _run_example(script_name: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, script_name],
        cwd=EXAMPLES_DIR,
        capture_output=True,
        text=True,
        timeout=30,
    )


def test_00_hello_world():
    result = _run_example("00_hello_world.py")
    assert result.returncode == 0, result.stderr


@pytest.mark.skipif(not FIXTURE.exists(), reason="fixture not present")
def test_01_inspect_project():
    result = _run_example("01_inspect_project.py")
    assert result.returncode == 0, result.stderr


def test_02_add_clips():
    result = _run_example("02_add_clips.py")
    assert result.returncode == 0, result.stderr


@pytest.mark.skipif(not FIXTURE.exists(), reason="fixture not present")
def test_03_add_captions():
    result = _run_example("03_add_captions.py")
    assert result.returncode == 0, result.stderr


@pytest.mark.skipif(not FIXTURE.exists(), reason="fixture not present")
def test_04_template_workflow():
    result = _run_example("04_template_workflow.py")
    assert result.returncode == 0, result.stderr
