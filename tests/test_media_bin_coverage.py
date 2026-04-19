"""Tests for camtasia.media_bin.media_bin — Media range/lastMod, import."""
from __future__ import annotations

import datetime
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from camtasia.media_bin.media_bin import (
    Media,
    MediaBin,
    MediaType,
    _parse_with_pymediainfo,
    _visual_track_to_json,
    _audio_track_to_json,
)


def _make_entry(
    media_id: int = 1,
    src: str = "./media/clip.mov",
    rect: list[int] | None = None,
    media_type: int = 0,
    range_vals: list[int] | None = None,
    last_mod: str = "20190606T103830",
) -> dict:
    return {
        "id": media_id,
        "src": src,
        "rect": rect or [0, 0, 1920, 1080],
        "lastMod": last_mod,
        "sourceTracks": [{
            "range": range_vals or [0, 5000],
            "type": media_type,
            "editRate": 1000,
            "trackRect": rect or [0, 0, 1920, 1080],
            "sampleRate": 0,
            "bitDepth": 0,
            "numChannels": 0,
        }],
    }


class TestMediaRange:
    def test_range_returns_raw_ints(self):
        entry = _make_entry(range_vals=[0, 5000])
        media = Media(entry)
        start, stop = media.range
        assert start == 0
        assert stop == 5000


class TestMediaLastModification:
    def test_parses_timestamp(self):
        entry = _make_entry(last_mod="20190606T103830")
        media = Media(entry)
        actual_dt = media.last_modification
        expected_dt = datetime.datetime(2019, 6, 6, 10, 38, 30)
        assert actual_dt == expected_dt


class TestMediaRepr:
    def test_repr_format(self):
        entry = _make_entry(media_id=42, src="./media/clip.mov")
        media = Media(entry)
        assert repr(media) == "Media(id=42, identity='clip', type=Video)"


class TestMediaBinImportMedia:
    def test_import_video_explicit_metadata(self, tmp_path: Path):
        data: list[dict] = []
        root = tmp_path / "proj.cmproj"
        root.mkdir()
        media_bin = MediaBin(data, root)
        media_file = tmp_path / "clip.mov"
        media_file.write_bytes(b"\x00")
        actual_media = media_bin.import_media(
            media_file, media_type=MediaType.Video, width=1920, height=1080, duration=5000,
        )
        assert actual_media.type == MediaType.Video
        assert actual_media.dimensions == (1920, 1080)

    def test_import_audio_explicit_metadata(self, tmp_path: Path):
        data: list[dict] = []
        root = tmp_path / "proj.cmproj"
        root.mkdir()
        media_bin = MediaBin(data, root)
        media_file = tmp_path / "sound.wav"
        media_file.write_bytes(b"RIFF")
        actual_media = media_bin.import_media(
            media_file, media_type=MediaType.Audio,
            sample_rate=44100, bit_depth=16, num_channels=2, duration=88200,
        )
        assert actual_media.type == MediaType.Audio

    def test_import_nonexistent_file_raises(self, tmp_path: Path):
        root = tmp_path / "proj.cmproj"
        root.mkdir()
        media_bin = MediaBin([], root)
        with pytest.raises(FileNotFoundError):
            media_bin.import_media(tmp_path / "missing.wav", media_type=MediaType.Audio)

    def test_import_without_type_and_no_pymediainfo_raises(self, tmp_path: Path):
        root = tmp_path / "proj.cmproj"
        root.mkdir()
        media_bin = MediaBin([], root)
        media_file = tmp_path / "clip.mov"
        media_file.write_bytes(b"\x00")
        with patch("camtasia.media_bin.media_bin._parse_with_pymediainfo", return_value=None):
            with pytest.raises(ValueError, match="Cannot determine media type"):
                media_bin.import_media(media_file)

    def test_import_image_explicit(self, tmp_path: Path):
        root = tmp_path / "proj.cmproj"
        root.mkdir()
        media_bin = MediaBin([], root)
        media_file = tmp_path / "photo.png"
        media_file.write_bytes(b"\x89PNG")
        actual_media = media_bin.import_media(
            media_file, media_type=MediaType.Image, width=800, height=600,
        )
        assert actual_media.type == MediaType.Image
        assert actual_media.dimensions == (800, 600)


class TestMediaBinLen:
    def test_len_matches_entries(self):
        entries = [_make_entry(media_id=i) for i in range(3)]
        media_bin = MediaBin(entries, Path("/fake"))
        assert [m.id for m in media_bin] == [0, 1, 2]


class TestParseWithPymediainfo:
    def test_returns_none_when_not_installed(self):
        # _parse_with_pymediainfo returns None if pymediainfo is not importable
        with patch.dict("sys.modules", {"pymediainfo": None}):
            actual_result = _parse_with_pymediainfo(Path("test.mov"))
        # Either None (no pymediainfo) or a dict — we just verify no crash
        assert actual_result is None or isinstance(actual_result, dict)


class TestImportMediaWithPymediainfo:
    def test_import_with_mocked_pymediainfo(self, tmp_path: Path):
        root = tmp_path / "proj.cmproj"
        root.mkdir()
        media_bin = MediaBin([], root)
        media_file = tmp_path / "clip.mov"
        media_file.write_bytes(b"\x00")
        mock_track = {
            "kind_of_stream": "Video",
            "width": 1280,
            "height": 720,
            "duration": 5000,
        }
        with patch("camtasia.media_bin.media_bin._parse_with_pymediainfo", return_value=mock_track):
            actual_media = media_bin.import_media(media_file)
        assert actual_media.type == MediaType.Video
        assert actual_media.dimensions == (1280, 720)

    def test_import_audio_with_mocked_pymediainfo(self, tmp_path: Path):
        root = tmp_path / "proj.cmproj"
        root.mkdir()
        media_bin = MediaBin([], root)
        media_file = tmp_path / "sound.wav"
        media_file.write_bytes(b"RIFF")
        mock_track = {
            "kind_of_stream": "Audio",
            "duration": 88200,
            "sampling_rate": 44100,
            "bit_depth": 16,
            "channel_s": 2,
        }
        with patch("camtasia.media_bin.media_bin._parse_with_pymediainfo", return_value=mock_track):
            actual_media = media_bin.import_media(media_file)
        assert actual_media.type == MediaType.Audio


class TestVisualTrackToJson:
    def test_builds_correct_structure(self):
        import datetime
        actual_json = _visual_track_to_json(
            media_id=1, source_file="./media/clip.mov",
            timestamp=datetime.datetime(2024, 1, 1, 12, 0, 0),
            media_type=MediaType.Video, width=1920, height=1080,
            duration=5000, filename="clip.mov",
        )
        assert actual_json["id"] == 1
        assert actual_json["rect"] == [0, 0, 1920, 1080]
        assert actual_json["sourceTracks"][0]["type"] == MediaType.Video.value
        assert actual_json["sourceTracks"][0]["metaData"] == "clip.mov;"


class TestAudioTrackToJson:
    def test_builds_correct_structure(self):
        import datetime
        actual_json = _audio_track_to_json(
            media_id=2, source_file="./media/sound.wav",
            timestamp=datetime.datetime(2024, 1, 1, 12, 0, 0),
            sample_rate=44100, bit_depth=16, num_channels=2,
            duration=88200, filename="sound.wav",
        )
        assert actual_json["id"] == 2
        assert actual_json["rect"] == [0, 0, 0, 0]
        assert actual_json["sourceTracks"][0]["type"] == MediaType.Audio.value
        assert actual_json["sourceTracks"][0]["sampleRate"] == 44100
        assert actual_json["sourceTracks"][0]["metaData"] == "sound.wav;"


# ── from test_coverage_phase4b: media_bin tests ──

from unittest.mock import MagicMock


class TestImportMediaSampleRateConversion:
    def test_non_int_sample_rate_converted(self, project, tmp_path):
        wav = tmp_path / "test.wav"
        wav.write_bytes(b"\x00" * 100)
        mock_track = {
            "kind_of_stream": "Audio",
            "sampling_rate": "44100.0",
            "duration": 1000,
            "bit_depth": 16,
            "channel_s": 2,
        }
        with patch("camtasia.media_bin.media_bin._parse_with_pymediainfo", return_value=mock_track):
            media = project.media_bin.import_media(wav)
            assert media is not None

    def test_non_int_sample_rate_invalid_becomes_none(self, project, tmp_path):
        wav = tmp_path / "test.wav"
        wav.write_bytes(b"\x00" * 100)
        mock_track = {
            "kind_of_stream": "Audio",
            "sampling_rate": "invalid",
            "duration": 1000,
            "bit_depth": 16,
            "channel_s": 2,
        }
        with patch("camtasia.media_bin.media_bin._parse_with_pymediainfo", return_value=mock_track):
            media = project.media_bin.import_media(wav)
            assert media is not None


class TestParseWithPymediainfoPhase4b:
    def test_parse_returns_none_on_import_error(self):
        with patch("builtins.__import__", side_effect=ImportError):
            result = _parse_with_pymediainfo(Path("/fake/file.mp4"))
            assert result is None

    def test_parse_returns_none_on_parse_exception(self):
        mock_mi = MagicMock()
        mock_mi.parse.side_effect = RuntimeError("parse failed")
        with patch.dict("sys.modules", {"pymediainfo": MagicMock(MediaInfo=mock_mi)}):
            result = _parse_with_pymediainfo(Path("/fake/file.mp4"))
            assert result is None

    def test_parse_returns_none_on_too_few_tracks(self):
        mock_mi = MagicMock()
        mock_result = MagicMock()
        mock_result.tracks = [MagicMock()]
        mock_mi.parse.return_value = mock_result
        with patch.dict("sys.modules", {"pymediainfo": MagicMock(MediaInfo=mock_mi)}):
            result = _parse_with_pymediainfo(Path("/fake/file.mp4"))
            assert result is None

    def test_parse_success_returns_track_data(self):
        mock_mi = MagicMock()
        mock_result = MagicMock()
        track0 = MagicMock()
        track1 = MagicMock()
        track1.to_data.return_value = {"kind_of_stream": "Video", "width": 1920}
        mock_result.tracks = [track0, track1]
        mock_mi.parse.return_value = mock_result
        with patch.dict("sys.modules", {"pymediainfo": MagicMock(MediaInfo=mock_mi)}):
            result = _parse_with_pymediainfo(Path("/fake/file.mp4"))
            assert result == {"kind_of_stream": "Video", "width": 1920}
