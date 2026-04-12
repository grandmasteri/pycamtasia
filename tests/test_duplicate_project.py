from __future__ import annotations

import pytest
from pathlib import Path

from camtasia.operations.template import duplicate_project


@pytest.fixture
def source_project(project, tmp_path):
    """Save the fixture project to a temp location so we have a real .cmproj bundle to duplicate."""
    import shutil

    src = tmp_path / "source.cmproj"
    shutil.copytree(project.file_path, src)
    from camtasia.project import load_project

    return load_project(str(src))


def test_duplicate_creates_copy(source_project, tmp_path):
    dst = tmp_path / "copy.cmproj"
    duplicate_project(source_project.file_path, dst)
    assert dst.exists()


def test_duplicate_preserves_settings(source_project, tmp_path):
    dst = tmp_path / "copy.cmproj"
    copy = duplicate_project(source_project.file_path, dst)
    assert copy.width == source_project.width
    assert copy.height == source_project.height
    assert copy.edit_rate == source_project.edit_rate


def test_duplicate_preserves_clips(source_project, tmp_path):
    original_clips = list(source_project.timeline.all_clips())
    dst = tmp_path / "copy.cmproj"
    copy = duplicate_project(source_project.file_path, dst)
    assert len(list(copy.timeline.all_clips())) == len(original_clips)


def test_duplicate_clear_media(source_project, tmp_path):
    dst = tmp_path / "copy.cmproj"
    copy = duplicate_project(source_project.file_path, dst, clear_media=True)
    assert len(list(copy.timeline.all_clips())) == 0
    assert len(list(copy.media_bin)) == 0


def test_duplicate_existing_dest_raises(source_project, tmp_path):
    dst = tmp_path / "copy.cmproj"
    dst.mkdir()
    with pytest.raises(FileExistsError):
        duplicate_project(source_project.file_path, dst)


# ---------------------------------------------------------------------------
# Project.copy_to
# ---------------------------------------------------------------------------


def test_copy_to_creates_copy(source_project, tmp_path):
    dst = tmp_path / "copy_to_dest.cmproj"
    copy = source_project.copy_to(dst)
    assert dst.exists()
    assert copy.file_path == dst.resolve()
    assert copy.width == source_project.width


def test_copy_to_existing_raises(source_project, tmp_path):
    dst = tmp_path / "copy_to_dest.cmproj"
    dst.mkdir()
    with pytest.raises(FileExistsError):
        source_project.copy_to(dst)