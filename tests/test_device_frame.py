"""Tests for the device_frame builder."""
from __future__ import annotations

from pathlib import Path
import tempfile
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from camtasia import Project
from camtasia.builders import add_device_frame


@pytest.fixture
def proj_with_clip(tmp_path, monkeypatch):
    import sys
    mock_mi = MagicMock()
    mock_mi.MediaInfo.parse.return_value = SimpleNamespace(tracks=[
        SimpleNamespace(track_type='Image', width=1920, height=1080),
    ])
    monkeypatch.setitem(sys.modules, 'pymediainfo', mock_mi)
    tmp = Path(tempfile.mkdtemp()) / 'test.cmproj'
    proj = Project.new(str(tmp))
    # Import an underlying media file and place a clip
    img = tmp_path / 'bg.png'
    img.write_bytes(b'\x89PNG\r\n\x1a\n')
    media = proj.import_media(img)
    track = proj.timeline.get_or_create_track('Content')
    clip = track.add_image(media.id, start_seconds=0.0, duration_seconds=5.0)
    return proj, clip


def test_add_device_frame_creates_overlay_clip(proj_with_clip, tmp_path):
    proj, clip = proj_with_clip
    frame = tmp_path / 'iphone.png'
    frame.write_bytes(b'\x89PNG\r\n\x1a\n')
    result = add_device_frame(proj, frame, clip)
    assert result.clip_type == 'IMFile'
    # Frame duration/start matches wrapped clip
    assert result.start == clip.start
    assert result.duration == clip.duration


def test_add_device_frame_custom_track_name(proj_with_clip, tmp_path):
    proj, clip = proj_with_clip
    frame = tmp_path / 'laptop.png'
    frame.write_bytes(b'\x89PNG\r\n\x1a\n')
    add_device_frame(proj, frame, clip, track_name='Laptop Bezel')
    assert proj.timeline.find_track_by_name('Laptop Bezel') is not None


def test_add_device_frame_applies_scale(proj_with_clip, tmp_path):
    proj, clip = proj_with_clip
    frame = tmp_path / 'tablet.png'
    frame.write_bytes(b'\x89PNG\r\n\x1a\n')
    result = add_device_frame(proj, frame, clip, scale=0.8)
    assert result.scale == (0.8, 0.8)
