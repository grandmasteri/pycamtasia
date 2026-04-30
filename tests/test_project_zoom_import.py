"""Tests for Project.import_zoom_recording, import_libzip_library, and save_timeline_group_to_library."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

if TYPE_CHECKING:
    from camtasia.project import Project


def _probe_fake(path):
    return {
        'width': 1920, 'height': 1080,
        'duration_seconds': 60.0, 'frame_rate': 30.0,
        '_backend': 'fake',
    }


@pytest.fixture
def dummy_mp4(tmp_path):
    p = tmp_path / 'zoom_recording.mp4'
    p.write_bytes(b'\x00' * 64)
    return p


class TestImportZoomRecording:
    """Tests for Project.import_zoom_recording()."""

    def test_imports_mp4_and_returns_media(self, project: Project, dummy_mp4):
        with patch('camtasia.project._probe_media', _probe_fake):
            media = project.import_zoom_recording(dummy_mp4)
        assert media is not None

    def test_attaches_all_metadata(self, project: Project, dummy_mp4):
        with patch('camtasia.project._probe_media', _probe_fake):
            media = project.import_zoom_recording(
                dummy_mp4, meeting_id='123', host='Alice',
                topic='Demo', date='2026-01-01',
            )
        meta = media._data['_zoomMeta']
        assert meta == {
            'meeting_id': '123', 'host': 'Alice',
            'topic': 'Demo', 'date': '2026-01-01',
        }

    def test_partial_metadata(self, project: Project, dummy_mp4):
        with patch('camtasia.project._probe_media', _probe_fake):
            media = project.import_zoom_recording(dummy_mp4, meeting_id='456')
        assert media._data['_zoomMeta'] == {'meeting_id': '456'}

    def test_no_metadata_no_key(self, project: Project, dummy_mp4):
        with patch('camtasia.project._probe_media', _probe_fake):
            media = project.import_zoom_recording(dummy_mp4)
        assert '_zoomMeta' not in media._data

    def test_media_added_to_bin(self, project: Project, dummy_mp4):
        initial_count = len(project.media_bin)
        with patch('camtasia.project._probe_media', _probe_fake):
            project.import_zoom_recording(dummy_mp4, host='Bob')
        assert len(project.media_bin) == initial_count + 1


class TestImportLibzipLibrary:
    """Tests for Project.import_libzip_library()."""

    def test_import_creates_library(self, project: Project, tmp_path):
        from camtasia.library import Library, export_libzip

        lib = Library('test')
        lib.add_asset({'kind': 'clip'}, 'asset1')
        archive = export_libzip(lib, tmp_path / 'test.libzip')

        result = project.import_libzip_library(archive)
        assert len(result.assets) == 1
        assert result.assets[0].name == 'asset1'

    def test_import_merges_into_existing(self, project: Project, tmp_path):
        from camtasia.library import Library, Libraries, export_libzip

        # Set up existing library on project
        project._libraries = Libraries()
        existing = project._libraries.create('Default')
        existing.add_asset({'kind': 'clip'}, 'existing_asset')

        lib = Library('incoming')
        lib.add_asset({'kind': 'clip'}, 'new_asset')
        archive = export_libzip(lib, tmp_path / 'incoming.libzip')

        result = project.import_libzip_library(archive)
        assert result is existing
        assert len(result.assets) == 2

    def test_import_nonexistent_raises(self, project: Project, tmp_path):
        with pytest.raises(FileNotFoundError):
            project.import_libzip_library(tmp_path / 'missing.libzip')


class TestSaveTimelineGroupToLibrary:
    """Tests for Project.save_timeline_group_to_library()."""

    def _make_group(self, project: Project):
        """Create a group clip on the project timeline."""
        track = project.timeline.tracks[0]
        c1 = track.add_clip('IMFile', 1, 0, 30)
        c2 = track.add_clip('IMFile', 1, 30, 30)
        group = project.timeline.group_clips_across_tracks(
            [c1.id, c2.id], 0,
        )
        return group

    def test_saves_group_to_default_library(self, project: Project):
        group = self._make_group(project)
        asset = project.save_timeline_group_to_library(group, 'MyGroup')
        assert asset.name == 'MyGroup'
        assert asset.kind in ('clip', 'group')

    def test_saves_to_explicit_library(self, project: Project):
        from camtasia.library import Library

        group = self._make_group(project)
        lib = Library('Custom')
        asset = project.save_timeline_group_to_library(group, 'G', library=lib)
        assert len(lib.assets) == 1
        assert asset.name == 'G'

    def test_creates_default_library_if_none(self, project: Project):
        group = self._make_group(project)
        project.save_timeline_group_to_library(group, 'First')
        assert project._libraries.default.name == 'Default'
