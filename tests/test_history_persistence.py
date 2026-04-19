"""Tests for Project.save_with_history and Project.load_history."""
from __future__ import annotations

from pathlib import Path
import shutil

import pytest

from camtasia.project import Project, load_project

RESOURCES: Path = Path(__file__).parent.parent / 'src' / 'camtasia' / 'resources'


@pytest.fixture
def tmp_project(tmp_path: Path) -> Project:
    """Copy the new.cmproj fixture into tmp_path and return a loaded Project."""
    src: Path = RESOURCES / 'new.cmproj'
    dst: Path = tmp_path / 'new.cmproj'
    shutil.copytree(src, dst)
    return load_project(dst)


def test_save_with_history_creates_sidecar(tmp_project: Project) -> None:
    """save_with_history writes a .pycamtasia_history.json sidecar file."""
    with tmp_project.track_changes("test edit"):
        tmp_project._data["title"] = "changed"

    tmp_project.save_with_history()

    sidecar: Path = tmp_project.file_path / '.pycamtasia_history.json'
    assert sidecar.exists()
    content: str = sidecar.read_text()
    assert "test edit" in content


def test_load_history_restores_state(tmp_project: Project) -> None:
    """load_history restores undo stack from a previously saved sidecar."""
    with tmp_project.track_changes("first change"):
        tmp_project._data["title"] = "v1"
    with tmp_project.track_changes("second change"):
        tmp_project._data["title"] = "v2"

    tmp_project.save_with_history()

    # Load a fresh project from the same path
    fresh: Project = load_project(tmp_project.file_path)
    assert fresh.history.undo_count == 0

    fresh.load_history()
    assert fresh.history.undo_count == 2
    assert fresh.history.descriptions == ["first change", "second change"]


def test_load_history_missing_file_is_noop(tmp_project: Project) -> None:
    """load_history does nothing when no sidecar file exists."""
    sidecar: Path = tmp_project.file_path / '.pycamtasia_history.json'
    assert not sidecar.exists()

    tmp_project.load_history()

    # History should remain at its default (lazy-initialized empty)
    assert tmp_project.history.undo_count == 0
