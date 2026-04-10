"""Tests for camtasia.project — ffprobe helpers, import_media, find_media, save."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any
from unittest.mock import patch, MagicMock

import pytest

from camtasia.project import (
    Project,
    _probe_media,
    _probe_media_ffprobe,
)
from camtasia.media_bin import MediaType


MINIMAL_PROJECT_DATA: dict[str, Any] = {
    "editRate": 30,
    "authoringClientName": {"name": "Camtasia", "platform": "Mac", "version": "2020.0.8"},
    "sourceBin": [],
    "timeline": {
        "id": 1,
        "sceneTrack": {"scenes": [{"csml": {"tracks": [{"trackIndex": 0, "medias": []}]}}]},
        "trackAttributes": [{"ident": "", "audioMuted": False, "videoHidden": False,
                              "magnetic": False, "metadata": {"IsLocked": "False"}}],
    },
}


def _create_project(tmp_path: Path, data: dict | None = None) -> Project:
    proj_dir = tmp_path / "test.cmproj"
    proj_dir.mkdir()
    (proj_dir / "project.tscproj").write_text(json.dumps(data or MINIMAL_PROJECT_DATA))
    return Project(proj_dir)


# ===================================================================
# ffprobe helpers
# ===================================================================


class TestProbeImageDimensions:
    def test_success(self):
        mock_result = MagicMock(stdout="1280,720\n")
        dur_result = MagicMock(stdout="")
        with patch("camtasia.project._sp.run", side_effect=[mock_result, dur_result]):
            actual = _probe_media_ffprobe(Path("img.png"))
        assert (actual['width'], actual['height']) == (1280, 720)

    def test_fallback_on_exception(self):
        with patch("camtasia.project._sp.run", side_effect=FileNotFoundError):
            actual = _probe_media_ffprobe(Path("img.png"))
        assert 'width' not in actual

    def test_fallback_on_bad_output(self):
        mock_result = MagicMock(stdout="garbage")
        dur_result = MagicMock(stdout="")
        with patch("camtasia.project._sp.run", side_effect=[mock_result, dur_result]):
            actual = _probe_media_ffprobe(Path("img.png"))
        assert 'width' not in actual


class TestProbeAudioDuration:
    def test_success(self):
        stream_result = MagicMock(stdout="")
        dur_result = MagicMock(stdout="120.5\n")
        with patch("camtasia.project._sp.run", side_effect=[stream_result, dur_result]):
            actual = _probe_media_ffprobe(Path("audio.wav"))
        assert actual['duration_seconds'] == 120.5

    def test_fallback_on_exception(self):
        with patch("camtasia.project._sp.run", side_effect=OSError):
            actual = _probe_media_ffprobe(Path("audio.wav"))
        assert 'duration_seconds' not in actual


class TestProbeVideoDuration:
    def test_success(self):
        stream_result = MagicMock(stdout="")
        dur_result = MagicMock(stdout="30.0\n")
        with patch("camtasia.project._sp.run", side_effect=[stream_result, dur_result]):
            actual = _probe_media_ffprobe(Path("video.mp4"))
        assert actual['duration_seconds'] == 30.0

    def test_fallback_on_exception(self):
        with patch("camtasia.project._sp.run", side_effect=TimeoutError):
            actual = _probe_media_ffprobe(Path("video.mp4"))
        assert 'duration_seconds' not in actual


# ===================================================================
# import_media
# ===================================================================


class TestImportMedia:
    def test_import_image_with_probe(self, tmp_path: Path):
        project = _create_project(tmp_path)
        media_file = tmp_path / "photo.png"
        media_file.write_bytes(b"\x89PNG")
        with patch("camtasia.project._probe_media", return_value={'width': 800, 'height': 600, '_backend': 'ffprobe'}):
            actual_media = project.import_media(media_file)
        assert actual_media.type == MediaType.Image
        assert actual_media.dimensions == (800, 600)

    def test_import_image_with_explicit_dims(self, tmp_path: Path):
        project = _create_project(tmp_path)
        media_file = tmp_path / "photo.jpg"
        media_file.write_bytes(b"\xff\xd8")
        actual_media = project.import_media(media_file, width=640, height=480)
        assert actual_media.dimensions == (640, 480)

    def test_import_audio_with_probe(self, tmp_path: Path):
        project = _create_project(tmp_path)
        media_file = tmp_path / "sound.wav"
        media_file.write_bytes(b"RIFF")
        with patch("camtasia.project._probe_media", return_value={'duration_seconds': 2.0, '_backend': 'ffprobe'}):
            actual_media = project.import_media(media_file)
        assert actual_media.type == MediaType.Audio

    def test_import_video_with_probe(self, tmp_path: Path):
        project = _create_project(tmp_path)
        media_file = tmp_path / "clip.mp4"
        media_file.write_bytes(b"\x00\x00")
        with patch("camtasia.project._probe_media", return_value={'duration_seconds': 30.0, '_backend': 'ffprobe'}):
            actual_media = project.import_media(media_file)
        assert actual_media.type == MediaType.Video

    def test_import_unknown_extension_raises(self, tmp_path: Path):
        project = _create_project(tmp_path)
        media_file = tmp_path / "data.xyz"
        media_file.write_bytes(b"\x00")
        with pytest.raises(ValueError, match="Cannot determine media type"):
            project.import_media(media_file)

    def test_import_with_explicit_media_type(self, tmp_path: Path):
        project = _create_project(tmp_path)
        media_file = tmp_path / "custom.dat"
        media_file.write_bytes(b"\x00")
        actual_media = project.import_media(
            media_file, media_type=MediaType.Image, width=100, height=100,
        )
        assert actual_media.type == MediaType.Image


# ===================================================================
# find_media methods
# ===================================================================


class TestFindMedia:
    def test_find_media_by_name_found(self, tmp_path: Path):
        project = _create_project(tmp_path)
        media_file = tmp_path / "intro.png"
        media_file.write_bytes(b"\x89PNG")
        project.import_media(media_file, width=100, height=100)
        actual_media = project.find_media_by_name("intro")
        assert actual_media is not None
        assert actual_media.identity == "intro"

    def test_find_media_by_name_not_found(self, tmp_path: Path):
        project = _create_project(tmp_path)
        assert project.find_media_by_name("nonexistent") is None

    def test_find_media_by_suffix(self, tmp_path: Path):
        project = _create_project(tmp_path)
        for name in ("a.png", "b.png", "c.jpg"):
            f = tmp_path / name
            f.write_bytes(b"\x00")
            project.import_media(f, media_type=MediaType.Image, width=10, height=10)
        actual_pngs = project.find_media_by_suffix(".png")
        actual_sources = [str(m.source) for m in actual_pngs]
        assert all(s.endswith(".png") for s in actual_sources)
        assert len(actual_pngs) == 2

    def test_find_media_by_suffix_no_match(self, tmp_path: Path):
        project = _create_project(tmp_path)
        assert project.find_media_by_suffix(".webm") == []


# ===================================================================
# save formatting
# ===================================================================


class TestSaveFormatting:
    def test_save_replaces_infinity(self, tmp_path: Path):
        data = dict(MINIMAL_PROJECT_DATA)
        data["extremeVal"] = float("-inf")
        project = _create_project(tmp_path, data)
        project.save()
        text = (tmp_path / "test.cmproj" / "project.tscproj").read_text()
        assert "-Infinity" not in text
        assert "-1.79769313486232e+308" in text

    def test_save_adds_trailing_newline(self, tmp_path: Path):
        project = _create_project(tmp_path)
        project.save()
        text = (tmp_path / "test.cmproj" / "project.tscproj").read_text()
        assert text.endswith("\n")

    def test_save_nsjson_colon_spacing(self, tmp_path: Path):
        project = _create_project(tmp_path)
        project.save()
        text = (tmp_path / "test.cmproj" / "project.tscproj").read_text()
        # NSJSONSerialization style: "key" : value
        assert '" :' in text

    def test_save_trailing_comma_space(self, tmp_path: Path):
        project = _create_project(tmp_path)
        project.save()
        text = (tmp_path / "test.cmproj" / "project.tscproj").read_text()
        assert ", \n" in text

    def test_repr(self, tmp_path: Path):
        project = _create_project(tmp_path)
        assert "test.cmproj" in repr(project)


# ===================================================================
# total_duration_seconds
# ===================================================================


class TestTotalDurationSeconds:
    def test_delegates_to_timeline(self, tmp_path: Path):
        project = _create_project(tmp_path)
        assert project.total_duration_seconds() == 0.0


# ===================================================================
# save: scalar array collapse and empty object expansion
# ===================================================================


class TestSaveScalarArrayCollapse:
    def test_scalar_arrays_collapsed_to_single_line(self, tmp_path: Path):
        data = dict(MINIMAL_PROJECT_DATA)
        data["rect"] = [0, 0, 1920, 1080]
        project = _create_project(tmp_path, data)
        project.save()
        text = (tmp_path / "test.cmproj" / "project.tscproj").read_text()
        # The rect array should be on a single line
        assert "[0, 0, 1920, 1080]" in text

    def test_empty_object_expanded(self, tmp_path: Path):
        data = dict(MINIMAL_PROJECT_DATA)
        data["timeline"]["parameters"] = {}
        project = _create_project(tmp_path, data)
        project.save()
        text = (tmp_path / "test.cmproj" / "project.tscproj").read_text()
        # Empty objects should be expanded to multi-line
        assert "{\n" in text


# ===================================================================
# add_gradient_background
# ===================================================================


class TestAddGradientBackground:
    def test_creates_source_entry_and_clip(self, tmp_path: Path):
        data = dict(MINIMAL_PROJECT_DATA)
        # Need at least 2 tracks for default track_index=1
        data["timeline"]["sceneTrack"]["scenes"][0]["csml"]["tracks"].append(
            {"trackIndex": 1, "medias": [], "parameters": {}, "transitions": []}
        )
        data["timeline"]["trackAttributes"].append(
            {"ident": "Track 1", "audioMuted": False, "videoHidden": False,
             "magnetic": False, "metadata": {"IsLocked": "False"}}
        )
        project = _create_project(tmp_path, data)
        actual_clip = project.add_gradient_background(duration_seconds=5.0)
        assert actual_clip is not None
        assert actual_clip.duration > 0
        # Source bin should have the gradient entry
        actual_sources = list(project.media_bin)
        assert len(actual_sources) == 1
        assert "tscshadervid" in str(actual_sources[0].source)

    def test_custom_colors(self, tmp_path: Path):
        data = dict(MINIMAL_PROJECT_DATA)
        data["timeline"]["sceneTrack"]["scenes"][0]["csml"]["tracks"].append(
            {"trackIndex": 1, "medias": [], "parameters": {}, "transitions": []}
        )
        data["timeline"]["trackAttributes"].append(
            {"ident": "Track 1", "audioMuted": False, "videoHidden": False,
             "magnetic": False, "metadata": {"IsLocked": "False"}}
        )
        project = _create_project(tmp_path, data)
        actual_clip = project.add_gradient_background(
            duration_seconds=3.0,
            color0=(1.0, 0.0, 0.0, 1.0),
            color1=(0.0, 0.0, 1.0, 1.0),
            track_index=1,
        )
        assert actual_clip is not None
