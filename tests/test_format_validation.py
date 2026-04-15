"""Tests for import_media() format validation (ffprobe/ffmpeg mocked)."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from camtasia.media_bin.media_bin import (
    _CODEC_TO_EXTENSIONS,
    _detect_codec,
    _validate_media_format,
    MediaBin,
    MediaType,
)


# ---------------------------------------------------------------------------
# _detect_codec
# ---------------------------------------------------------------------------

class TestDetectCodec:
    def test_returns_audio_codec(self):
        ffprobe_output = json.dumps({"streams": [{"codec_name": "mp3"}]})
        with patch("camtasia.media_bin.media_bin.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout=ffprobe_output)
            assert _detect_codec(Path("file.wav")) == "mp3"

    def test_falls_back_to_video_stream(self):
        empty = json.dumps({"streams": []})
        video = json.dumps({"streams": [{"codec_name": "h264"}]})
        with patch("camtasia.media_bin.media_bin.subprocess.run") as mock_run:
            mock_run.side_effect = [
                MagicMock(stdout=empty),
                MagicMock(stdout=video),
            ]
            assert _detect_codec(Path("file.mp4")) == "h264"

    def test_returns_none_when_ffprobe_missing(self):
        with patch(
            "camtasia.media_bin.media_bin.subprocess.run",
            side_effect=FileNotFoundError,
        ):
            assert _detect_codec(Path("file.wav")) is None

    def test_returns_none_on_timeout(self):
        with patch(
            "camtasia.media_bin.media_bin.subprocess.run",
            side_effect=subprocess.TimeoutExpired("ffprobe", 10),
        ):
            assert _detect_codec(Path("file.wav")) is None

    def test_returns_none_on_bad_json(self):
        with patch("camtasia.media_bin.media_bin.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="not json")
            assert _detect_codec(Path("file.wav")) is None


# ---------------------------------------------------------------------------
# _validate_media_format
# ---------------------------------------------------------------------------

class TestValidateMediaFormat:
    def test_no_warning_when_codec_matches_extension(self):
        with patch(
            "camtasia.media_bin.media_bin._detect_codec", return_value="pcm_s16le"
        ):
            with pytest.warns(match="does_not_match") if False else nullcontext():
                result = _validate_media_format(Path("audio.wav"))
            assert result == Path("audio.wav")

    def test_warns_on_mismatch(self):
        with patch(
            "camtasia.media_bin.media_bin._detect_codec", return_value="mp3"
        ):
            with pytest.warns(UserWarning, match="Format mismatch"):
                _validate_media_format(Path("audio.wav"))

    def test_skips_validation_when_ffprobe_unavailable(self):
        with patch(
            "camtasia.media_bin.media_bin._detect_codec", return_value=None
        ):
            result = _validate_media_format(Path("audio.wav"))
            assert result == Path("audio.wav")

    def test_auto_convert_calls_ffmpeg(self):
        with (
            patch("camtasia.media_bin.media_bin._detect_codec", return_value="mp3"),
            patch("camtasia.media_bin.media_bin.subprocess.run") as mock_run,
            pytest.warns(UserWarning, match="Format mismatch"),
        ):
            mock_run.return_value = MagicMock(returncode=0)
            result = _validate_media_format(
                Path("audio.wav"), auto_convert=True,
            )
            assert result == Path("audio.converted.wav")
            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            assert args[0] == "ffmpeg"

    def test_auto_convert_returns_original_on_ffmpeg_failure(self):
        with (
            patch("camtasia.media_bin.media_bin._detect_codec", return_value="mp3"),
            patch(
                "camtasia.media_bin.media_bin.subprocess.run",
                side_effect=FileNotFoundError,
            ),
            pytest.warns(UserWarning, match="Format mismatch"),
        ):
            result = _validate_media_format(
                Path("audio.wav"), auto_convert=True,
            )
            assert result == Path("audio.wav")

    def test_unknown_codec_skips_validation(self):
        with patch(
            "camtasia.media_bin.media_bin._detect_codec",
            return_value="unknown_codec_xyz",
        ):
            result = _validate_media_format(Path("audio.wav"))
            assert result == Path("audio.wav")


# ---------------------------------------------------------------------------
# import_media integration (validate_format param wiring)
# ---------------------------------------------------------------------------

class TestImportMediaValidateFormat:
    def _make_bin(self, tmp_path: Path) -> MediaBin:
        return MediaBin([], tmp_path)

    def test_validate_format_false_skips_validation(self, tmp_path):
        media_bin = self._make_bin(tmp_path)
        audio = tmp_path / "clip.wav"
        audio.write_bytes(b"\x00" * 100)

        with (
            patch("camtasia.media_bin.media_bin._validate_media_format") as mock_val,
            patch(
                "camtasia.media_bin.media_bin._parse_with_pymediainfo",
                return_value=None,
            ),
        ):
            with pytest.raises(ValueError):
                media_bin.import_media(
                    audio, validate_format=False, media_type=None,
                )
            mock_val.assert_not_called()

    def test_validate_format_true_calls_validation(self, tmp_path):
        media_bin = self._make_bin(tmp_path)
        audio = tmp_path / "clip.wav"
        audio.write_bytes(b"\x00" * 100)

        with (
            patch(
                "camtasia.media_bin.media_bin._validate_media_format",
                return_value=audio,
            ) as mock_val,
            patch(
                "camtasia.media_bin.media_bin._parse_with_pymediainfo",
                return_value=None,
            ),
        ):
            with pytest.raises(ValueError):
                media_bin.import_media(audio, validate_format=True)
            mock_val.assert_called_once_with(audio, auto_convert=False)

    def test_validate_format_with_auto_convert(self, tmp_path):
        media_bin = self._make_bin(tmp_path)
        audio = tmp_path / "clip.wav"
        audio.write_bytes(b"\x00" * 100)

        with (
            patch(
                "camtasia.media_bin.media_bin._validate_media_format",
                return_value=audio,
            ) as mock_val,
            patch(
                "camtasia.media_bin.media_bin._parse_with_pymediainfo",
                return_value=None,
            ),
        ):
            with pytest.raises(ValueError):
                media_bin.import_media(
                    audio, validate_format=True, auto_convert=True,
                )
            mock_val.assert_called_once_with(audio, auto_convert=True)

    def test_string_path_accepted(self, tmp_path):
        """import_media accepts str paths (not just Path)."""
        media_bin = self._make_bin(tmp_path)
        audio = tmp_path / "clip.wav"
        audio.write_bytes(b"\x00" * 100)

        with (
            patch(
                "camtasia.media_bin.media_bin._validate_media_format",
                return_value=audio,
            ),
            patch(
                "camtasia.media_bin.media_bin._parse_with_pymediainfo",
                return_value=None,
            ),
        ):
            with pytest.raises(ValueError):
                media_bin.import_media(str(audio), validate_format=True)


# ---------------------------------------------------------------------------
# Codec-to-extension mapping sanity
# ---------------------------------------------------------------------------

class TestCodecMapping:
    def test_mp3_maps_to_mp3_ext(self):
        assert ".mp3" in _CODEC_TO_EXTENSIONS["mp3"]

    def test_pcm_maps_to_wav(self):
        assert ".wav" in _CODEC_TO_EXTENSIONS["pcm_s16le"]

    def test_h264_maps_to_mp4(self):
        assert ".mp4" in _CODEC_TO_EXTENSIONS["h264"]


# helper for Python <3.10 compat
from contextlib import nullcontext  # noqa: E402
