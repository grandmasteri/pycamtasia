"""Tests for the compressed-audio duration fix in import_media().

When pymediainfo reports metadata for compressed formats (MP3, AAC, etc.)
the raw sample count is unreliable.  The fix derives the sample count from
``duration_ms * sample_rate / 1000`` for those formats.
"""
from __future__ import annotations

from unittest.mock import patch

import pytest

from camtasia.media_bin.media_bin import _compute_audio_duration


class TestComputeAudioDuration:
    """Unit tests for _compute_audio_duration."""

    @pytest.mark.parametrize(("fmt", "duration_ms", "sample_rate", "expected"), [
        ("MPEG Audio", 5000.0, 44100, 220500),
        ("AAC", 3000.0, 48000, 144000),
        ("Vorbis", 2000.0, 44100, 88200),
        ("Opus", 1500.0, 48000, 72000),
    ], ids=["mp3", "aac", "vorbis", "opus"])
    def test_compressed_format_uses_duration_times_sample_rate(self, fmt, duration_ms, sample_rate, expected):
        track = {"format": fmt, "duration": duration_ms}
        assert _compute_audio_duration(track, sample_rate) == expected

    def test_uncompressed_pcm_uses_raw_duration(self):
        track = {"format": "PCM", "duration": 220500}
        assert _compute_audio_duration(track, 44100) == 9724050  # 220500ms * 44100 / 1000

    def test_unknown_format_uses_raw_duration(self):
        track = {"format": "FLAC", "duration": 441000}
        assert _compute_audio_duration(track, 44100) == 19448100  # 441000ms * 44100 / 1000

    def test_missing_format_uses_raw_duration(self):
        track = {"duration": 100000}
        assert _compute_audio_duration(track, 44100) == 4410000  # 100000ms * 44100 / 1000

    def test_compressed_with_no_sample_rate_falls_back_to_raw(self):
        track = {"format": "MPEG Audio", "duration": 5000.0}
        assert _compute_audio_duration(track, None) == 0


class TestImportMediaCompressedAudio:
    """Integration test: import_media uses corrected duration for compressed audio."""

    def test_mp3_range_uses_computed_sample_count(self, project, tmp_path):
        mp3_file = tmp_path / "song.mp3"
        mp3_file.write_bytes(b"\x00")

        fake_track = {
            "kind_of_stream": "Audio",
            "format": "MPEG Audio",
            "duration": 10000.0,   # 10 000 ms
            "sampling_rate": 44100,
            "bit_depth": 16,
            "channel_s": 2,
        }

        with patch(
            "camtasia.media_bin.media_bin._parse_with_pymediainfo",
            return_value=fake_track,
        ):
            media = project.media_bin.import_media(mp3_file)

        expected_samples = int(10000.0 * 44100 / 1000)  # 441000
        actual_range = media._data["sourceTracks"][0]["range"]
        assert actual_range == [0, expected_samples]
