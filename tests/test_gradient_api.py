"""Tests for proj.add_four_corner_gradient() high-level API."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from camtasia.project import Project


MINIMAL_PROJECT_DATA: dict[str, Any] = {
    "editRate": 30,
    "authoringClientName": {"name": "Camtasia", "platform": "Mac", "version": "2020.0.8"},
    "sourceBin": [],
    "timeline": {
        "id": 1,
        "sceneTrack": {"scenes": [{"csml": {"tracks": [
            {"trackIndex": 0, "medias": [], "parameters": {}},
        ]}}]},
        "trackAttributes": [
            {"ident": "Track 0", "audioMuted": False, "videoHidden": False,
             "magnetic": False, "metadata": {"IsLocked": "False"}},
        ],
    },
}


def _make_project(tmp_path: Path) -> Project:
    proj_dir = tmp_path / "test.cmproj"
    proj_dir.mkdir()
    (proj_dir / "project.tscproj").write_text(json.dumps(MINIMAL_PROJECT_DATA))
    return Project(proj_dir)


def _make_shader(tmp_path: Path) -> Path:
    shader = tmp_path / "gradient.tscshadervid"
    shader.write_text("shader")
    return shader


class TestAddFourCornerGradient:
    def test_imports_and_places_clip(self, tmp_path: Path):
        proj = _make_project(tmp_path)
        shader = _make_shader(tmp_path)
        clip = proj.add_four_corner_gradient(shader, duration_seconds=10.0)

        assert clip is not None
        assert clip._data['_type'] == 'VMFile'
        # Shader was imported
        assert len(proj.find_media_by_suffix('.tscshadervid')) == 1

    def test_reuses_existing_shader(self, tmp_path: Path):
        proj = _make_project(tmp_path)
        shader = _make_shader(tmp_path)
        clip1 = proj.add_four_corner_gradient(shader, duration_seconds=5.0)
        source_id = proj.find_media_by_suffix('.tscshadervid')[0].id

        clip2 = proj.add_four_corner_gradient(shader, duration_seconds=10.0)

        # Still only one shader in the bin
        assert len(proj.find_media_by_suffix('.tscshadervid')) == 1
        assert clip2._data['src'] == source_id

    def test_creates_named_track(self, tmp_path: Path):
        proj = _make_project(tmp_path)
        shader = _make_shader(tmp_path)
        proj.add_four_corner_gradient(shader, duration_seconds=5.0)

        track_names = [t.name for t in proj.timeline.tracks]
        assert 'Background' in track_names

    def test_custom_track_name(self, tmp_path: Path):
        proj = _make_project(tmp_path)
        shader = _make_shader(tmp_path)
        proj.add_four_corner_gradient(shader, duration_seconds=5.0, track_name='BG')

        track_names = [t.name for t in proj.timeline.tracks]
        assert 'BG' in track_names

    def test_clip_starts_at_zero(self, tmp_path: Path):
        proj = _make_project(tmp_path)
        shader = _make_shader(tmp_path)
        clip = proj.add_four_corner_gradient(shader, duration_seconds=5.0)

        assert clip.start == 0

    def test_accepts_path_object(self, tmp_path: Path):
        proj = _make_project(tmp_path)
        shader = _make_shader(tmp_path)
        clip = proj.add_four_corner_gradient(Path(shader), duration_seconds=5.0)

        assert clip is not None

    def test_accepts_string_path(self, tmp_path: Path):
        proj = _make_project(tmp_path)
        shader = _make_shader(tmp_path)
        clip = proj.add_four_corner_gradient(str(shader), duration_seconds=5.0)

        assert clip is not None
