"""Tests for _probe_media: pymediainfo path and ffprobe fallback."""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from camtasia.project import _probe_media, load_project, new_project


def _make_track(track_type: str, **attrs):
    """Build a fake pymediainfo track object."""
    defaults = {
        'width': None, 'height': None, 'duration': None,
        'frame_rate': None, 'sampling_rate': None,
        'channel_s': None, 'bit_depth': None,
    }
    defaults.update(attrs)
    defaults['track_type'] = track_type
    return SimpleNamespace(**defaults)


def _make_mediainfo_result(tracks):
    """Build a fake MediaInfo.parse() return value."""
    result = MagicMock()
    result.tracks = tracks
    return result


class TestProbeWithPymediainfo:

    @pytest.mark.parametrize("width,height", [(1920, 1080), (3840, 2160), (640, 480)])
    def test_probe_image_dimensions_with_pymediainfo(self, width, height):
        tracks = [
            _make_track('General'),
            _make_track('Image', width=width, height=height),
        ]
        mock_mi = MagicMock()
        mock_mi.MediaInfo.parse.return_value = _make_mediainfo_result(tracks)

        with patch.dict('sys.modules', {'pymediainfo': mock_mi}):
            actual_metadata = _probe_media(Path('/fake/image.png'))

        expected_dimensions = (width, height)
        assert (actual_metadata['width'], actual_metadata['height']) == expected_dimensions
        assert actual_metadata['_backend'] == 'pymediainfo'

    @pytest.mark.parametrize("duration_ms,expected_seconds", [
        (5000, 5.0), (12345, 12.345), (500, 0.5),
    ])
    def test_probe_audio_duration_with_pymediainfo(self, duration_ms, expected_seconds):
        tracks = [
            _make_track('General', duration=duration_ms),
            _make_track('Audio', duration=duration_ms, sampling_rate=48000,
                        channel_s=2, bit_depth=24),
        ]
        mock_mi = MagicMock()
        mock_mi.MediaInfo.parse.return_value = _make_mediainfo_result(tracks)

        with patch.dict('sys.modules', {'pymediainfo': mock_mi}):
            actual_metadata = _probe_media(Path('/fake/audio.wav'))

        assert actual_metadata['duration_seconds'] == expected_seconds
        assert actual_metadata['_backend'] == 'pymediainfo'

    def test_probe_audio_metadata_accuracy(self):
        tracks = [
            _make_track('General', duration=10000),
            _make_track('Audio', duration=10000, sampling_rate=48000,
                        channel_s=2, bit_depth=24),
        ]
        mock_mi = MagicMock()
        mock_mi.MediaInfo.parse.return_value = _make_mediainfo_result(tracks)

        with patch.dict('sys.modules', {'pymediainfo': mock_mi}):
            actual_metadata = _probe_media(Path('/fake/audio.wav'))

        assert actual_metadata['sample_rate'] == 48000
        assert actual_metadata['channels'] == 2
        assert actual_metadata['bit_depth'] == 24


class TestProbeFallbackToFfprobe:

    @pytest.mark.parametrize("width,height", [(1920, 1080), (640, 480)])
    def test_probe_image_dimensions_fallback_to_ffprobe(self, width, height):
        stream_out = MagicMock(stdout=f'{width},{height}\n', returncode=0)
        dur_out = MagicMock(stdout='', returncode=1)

        with patch.dict('sys.modules', {'pymediainfo': None}), \
             patch('camtasia.project._sp.run', side_effect=[stream_out, dur_out]):
            actual_metadata = _probe_media(Path('/fake/image.png'))

        expected_dimensions = (width, height)
        assert (actual_metadata['width'], actual_metadata['height']) == expected_dimensions
        assert actual_metadata['_backend'] == 'ffprobe'

    @pytest.mark.parametrize("duration_str,expected_seconds", [
        ('5.000000', 5.0), ('12.345000', 12.345),
    ])
    def test_probe_audio_duration_fallback_to_ffprobe(self, duration_str, expected_seconds):
        stream_out = MagicMock(stdout='', returncode=1)
        dur_out = MagicMock(stdout=f'{duration_str}\n', returncode=0)

        with patch.dict('sys.modules', {'pymediainfo': None}), \
             patch('camtasia.project._sp.run', side_effect=[stream_out, dur_out]):
            actual_metadata = _probe_media(Path('/fake/audio.wav'))

        assert actual_metadata['duration_seconds'] == expected_seconds
        assert actual_metadata['_backend'] == 'ffprobe'


class TestImportMediaUsesPymediainfo:

    def test_import_media_uses_pymediainfo_when_available(self, tmp_path):
        """Verify import_media passes pymediainfo metadata to the media bin."""
        proj_path = tmp_path / 'test.cmproj'
        new_project(proj_path)
        proj = load_project(proj_path)

        audio_file = tmp_path / 'test.wav'
        audio_file.write_bytes(b'\x00' * 100)

        tracks = [
            _make_track('General', duration=5000),
            _make_track('Audio', duration=5000, sampling_rate=48000,
                        channel_s=2, bit_depth=24),
        ]
        mock_mi = MagicMock()
        mock_mi.MediaInfo.parse.return_value = _make_mediainfo_result(tracks)

        with patch.dict('sys.modules', {'pymediainfo': mock_mi}):
            media = proj.import_media(audio_file)

        actual_metadata = media._data['sourceTracks'][0]
        assert actual_metadata['sampleRate'] == 48000
        assert actual_metadata['numChannels'] == 2
        assert actual_metadata['bitDepth'] == 24
        assert actual_metadata['editRate'] == 48000


class TestProbeAudioOnlyDuration:
    """Cover project.py line 55: audio-only duration when no video track."""

    def test_audio_only_sets_duration(self):
        tracks = [
            _make_track('Audio', duration=7000, sampling_rate=44100,
                        channel_s=1, bit_depth=16),
        ]
        mock_mi = MagicMock()
        mock_mi.MediaInfo.parse.return_value = _make_mediainfo_result(tracks)
        with patch.dict('sys.modules', {'pymediainfo': mock_mi}):
            result = _probe_media(Path('/fake/audio_only.wav'))
        assert result['duration_seconds'] == 7.0
