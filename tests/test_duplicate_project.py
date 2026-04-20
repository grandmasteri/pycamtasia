from __future__ import annotations

import shutil

import pytest

from camtasia.operations.template import _walk_clips, duplicate_project
from camtasia.project import load_project


@pytest.fixture
def source_project(project, tmp_path):
    """Save the fixture project to a temp location so we have a real .cmproj bundle to duplicate."""
    src = tmp_path / "source.cmproj"
    shutil.copytree(project.file_path, src)
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


def test_duplicate_clear_media_removes_media_dir(source_project, tmp_path):
    dst = tmp_path / "copy.cmproj"
    # Ensure source has a media dir
    assert (source_project.file_path / "media").exists()
    duplicate_project(source_project.file_path, dst, clear_media=True)
    # Media dir should exist but be empty (recreated after rmtree)
    assert (dst / "media").exists()
    assert list((dst / "media").iterdir()) == []


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


class TestWalkClipsUnifiedMedia:
    def test_yields_unified_media_children(self):
        tracks = [{
            'medias': [{
                '_type': 'UnifiedMedia', 'id': 1,
                'video': {'_type': 'VMFile', 'id': 2, 'src': 10},
                'audio': {'_type': 'AMFile', 'id': 3, 'src': 10},
            }],
        }]
        clips = list(_walk_clips(tracks))
        ids = [c.get('id') for c in clips]
        assert 1 in ids
        assert 2 in ids
        assert 3 in ids

    def test_unified_media_without_audio(self):
        tracks = [{
            'medias': [{
                '_type': 'UnifiedMedia', 'id': 1,
                'video': {'_type': 'VMFile', 'id': 2, 'src': 10},
            }],
        }]
        clips = list(_walk_clips(tracks))
        ids = [c.get('id') for c in clips]
        assert 2 in ids
        assert len(ids) == 2
