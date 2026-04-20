"""Tests for Project.import_media() — video frame_rate and dimensions."""
from __future__ import annotations

from unittest.mock import patch

import pytest


@pytest.fixture
def dummy_mp4(tmp_path):
    """Create a dummy .mp4 file for import_media to find."""
    p = tmp_path / "clip.mp4"
    p.write_bytes(b"\x00" * 64)
    return p


def _probe_fake(path):
    """Fake _probe_media returning known video metadata."""
    return {
        "width": 1280,
        "height": 720,
        "duration_seconds": 10.0,
        "frame_rate": 24.0,
        "_backend": "fake",
    }


def test_video_import_passes_sample_rate(project, dummy_mp4):
    """Bug 1: video branch should pass sample_rate (frame_rate) to MediaBin kwargs."""
    with patch("camtasia.project._probe_media", _probe_fake):
        media = project.import_media(dummy_mp4)
    # editRate in sourceTracks should default to 30 (MediaBin internal default
    # when _detected_fps is None), but duration should use the probed frame_rate
    entry = media._data
    st = entry["sourceTracks"][0]
    # Duration should be frame_rate * duration_seconds = 24 * 10 = 240
    assert st["range"][1] == 240


def test_video_import_passes_dimensions(project, dummy_mp4):
    """Bug 2: video branch should pass width/height to MediaBin."""
    with patch("camtasia.project._probe_media", _probe_fake):
        media = project.import_media(dummy_mp4)
    entry = media._data
    assert entry["rect"][2] == 1280
    assert entry["rect"][3] == 720


def test_video_import_default_dimensions_when_probe_empty(project, dummy_mp4):
    """When probe returns no dimensions, defaults to 1920x1080."""
    def _probe_no_dims(path):
        return {"duration_seconds": 5.0, "_backend": "fake"}

    with patch("camtasia.project._probe_media", _probe_no_dims):
        media = project.import_media(dummy_mp4)
    entry = media._data
    assert entry["rect"][2] == 1920
    assert entry["rect"][3] == 1080
