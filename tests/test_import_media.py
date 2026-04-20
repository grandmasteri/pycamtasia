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


def _probe_fake_24fps(path):
    """Fake _probe_media returning 24fps video metadata."""
    return {
        "width": 1280,
        "height": 720,
        "duration_seconds": 10.0,
        "frame_rate": 24.0,
        "_backend": "fake",
    }


def test_video_import_passes_edit_rate_to_media_bin(project, dummy_mp4):
    """Bug 1: edit_rate kwarg should be forwarded so MediaBin uses it instead of 30."""
    with patch("camtasia.project._probe_media", _probe_fake_24fps):
        media = project.import_media(dummy_mp4)
    st = media._data["sourceTracks"][0]
    assert st["editRate"] == 24


class TestImportMediaExplicitZeroSampleRate:
    """Bug fix: import_media must not use `or` for sample_rate/num_channels since 0 is falsy."""

    def test_explicit_zero_sample_rate_not_overwritten_by_pymediainfo(self, project, tmp_path):
        """Passing sample_rate=0 should not be overwritten by pymediainfo's value."""
        from unittest.mock import MagicMock

        audio_file = tmp_path / 'test.wav'
        audio_file.write_bytes(b'\x00' * 100)

        track_data = {
            'kind_of_stream': 'Audio',
            'sampling_rate': 48000,
            'channel_s': 2,
            'bit_depth': 16,
            'duration': 5000,
        }
        mock_mi = MagicMock()
        mock_mi.MediaInfo.parse.return_value = MagicMock(
            tracks=[MagicMock(), MagicMock(to_data=MagicMock(return_value=track_data))]
        )

        with patch.dict('sys.modules', {'pymediainfo': mock_mi}):
            # sample_rate=0 is falsy; with `or` it would fall through to 48000
            # With explicit None check, 0 is preserved through the detection path
            media = project.media_bin.import_media(audio_file, sample_rate=0)
        st = media._data['sourceTracks'][0]
        # The detection path preserves 0, but the audio JSON builder uses `sample_rate or 44100`
        # which is a separate concern. The key fix is that 0 doesn't become 48000 (pymediainfo value).
        # Since 0 is passed to _audio_track_to_json as sample_rate=0, and that function uses it directly,
        # the editRate should be 0 (not 48000 from pymediainfo).
        assert st['editRate'] != 48000

    def test_explicit_zero_num_channels_not_overwritten_by_pymediainfo(self, project, tmp_path):
        """Passing num_channels=0 should not be overwritten by pymediainfo's value."""
        from unittest.mock import MagicMock

        audio_file = tmp_path / 'test.wav'
        audio_file.write_bytes(b'\x00' * 100)

        track_data = {
            'kind_of_stream': 'Audio',
            'sampling_rate': 44100,
            'channel_s': 6,
            'bit_depth': 16,
            'duration': 5000,
        }
        mock_mi = MagicMock()
        mock_mi.MediaInfo.parse.return_value = MagicMock(
            tracks=[MagicMock(), MagicMock(to_data=MagicMock(return_value=track_data))]
        )

        with patch.dict('sys.modules', {'pymediainfo': mock_mi}):
            # Without the fix, num_channels=0 (falsy) would fall through to 6 (pymediainfo)
            # With the fix, 0 is preserved, then the builder defaults it to 2 (or 2)
            # The key assertion: it should NOT be 6 (the pymediainfo value)
            media = project.media_bin.import_media(audio_file, num_channels=0)
        st = media._data['sourceTracks'][0]
        assert st['numChannels'] != 6
