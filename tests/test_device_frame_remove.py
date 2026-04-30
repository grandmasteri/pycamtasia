"""Tests for remove_device_frame builder function."""
from __future__ import annotations

import sys
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from camtasia import Project
from camtasia.builders import add_device_frame, remove_device_frame


@pytest.fixture
def proj_with_frame(tmp_path, monkeypatch):
    """Project with a device frame overlay already applied."""
    mock_mi = MagicMock()
    mock_mi.MediaInfo.parse.return_value = SimpleNamespace(tracks=[
        SimpleNamespace(track_type='Image', width=1920, height=1080),
    ])
    monkeypatch.setitem(sys.modules, 'pymediainfo', mock_mi)
    proj_dir = tmp_path / 'test.cmproj'
    proj = Project.new(str(proj_dir))
    img = tmp_path / 'bg.png'
    img.write_bytes(b'\x89PNG\r\n\x1a\n')
    media = proj.import_media(img)
    track = proj.timeline.get_or_create_track('Content')
    clip = track.add_image(media.id, start_seconds=0.0, duration_seconds=5.0)
    frame_img = tmp_path / 'iphone.png'
    frame_img.write_bytes(b'\x89PNG\r\n\x1a\n')
    add_device_frame(proj, frame_img, clip)
    return proj


class TestRemoveDeviceFrame:

    def test_removes_default_track(self, proj_with_frame):
        assert proj_with_frame.timeline.find_track_by_name('Device Frame') is not None
        remove_device_frame(proj_with_frame)
        assert proj_with_frame.timeline.find_track_by_name('Device Frame') is None

    def test_removes_custom_named_track(self, tmp_path, monkeypatch):
        mock_mi = MagicMock()
        mock_mi.MediaInfo.parse.return_value = SimpleNamespace(tracks=[
            SimpleNamespace(track_type='Image', width=1920, height=1080),
        ])
        monkeypatch.setitem(sys.modules, 'pymediainfo', mock_mi)
        proj_dir = tmp_path / 'test.cmproj'
        proj = Project.new(str(proj_dir))
        img = tmp_path / 'bg.png'
        img.write_bytes(b'\x89PNG\r\n\x1a\n')
        media = proj.import_media(img)
        track = proj.timeline.get_or_create_track('Content')
        clip = track.add_image(media.id, start_seconds=0.0, duration_seconds=5.0)
        frame_img = tmp_path / 'laptop.png'
        frame_img.write_bytes(b'\x89PNG\r\n\x1a\n')
        add_device_frame(proj, frame_img, clip, track_name='Laptop Bezel')
        assert proj.timeline.find_track_by_name('Laptop Bezel') is not None
        remove_device_frame(proj, track_name='Laptop Bezel')
        assert proj.timeline.find_track_by_name('Laptop Bezel') is None

    def test_raises_on_missing_track(self, proj_with_frame):
        with pytest.raises(ValueError, match='No track named'):
            remove_device_frame(proj_with_frame, track_name='NonExistent')

    def test_raises_after_already_removed(self, proj_with_frame):
        remove_device_frame(proj_with_frame)
        with pytest.raises(ValueError, match='No track named'):
            remove_device_frame(proj_with_frame)

    def test_track_count_decreases(self, proj_with_frame):
        initial_count = len(list(proj_with_frame.timeline.tracks))
        remove_device_frame(proj_with_frame)
        assert len(list(proj_with_frame.timeline.tracks)) == initial_count - 1

    def test_content_track_preserved(self, proj_with_frame):
        remove_device_frame(proj_with_frame)
        assert proj_with_frame.timeline.find_track_by_name('Content') is not None

    def test_content_clips_preserved(self, proj_with_frame):
        content_track = proj_with_frame.timeline.find_track_by_name('Content')
        clips_before = list(content_track.clips)
        remove_device_frame(proj_with_frame)
        content_track = proj_with_frame.timeline.find_track_by_name('Content')
        clips_after = list(content_track.clips)
        assert len(clips_after) == len(clips_before)
