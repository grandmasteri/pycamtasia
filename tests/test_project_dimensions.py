"""Tests for Project.width and Project.height properties."""
from __future__ import annotations

import json
from pathlib import Path

from camtasia.project import Project


MINIMAL_PROJECT_DATA = {
    "editRate": 30,
    "authoringClientName": {"name": "Camtasia", "platform": "Mac", "version": "2020.0.8"},
    "sourceBin": [],
    "timeline": {
        "id": 1,
        "sceneTrack": {"scenes": [{"csml": {"tracks": [
            {"trackIndex": 0, "medias": [], "parameters": {}},
        ]}}]},
        "trackAttributes": [
            {"ident": "", "audioMuted": False, "videoHidden": False,
             "magnetic": False, "metadata": {"IsLocked": "False"}},
        ],
    },
}


def _make_project(tmp_path: Path, data: dict | None = None) -> Project:
    proj_dir = tmp_path / "test.cmproj"
    proj_dir.mkdir()
    (proj_dir / "project.tscproj").write_text(json.dumps(data or MINIMAL_PROJECT_DATA))
    return Project(proj_dir)


class TestWidth:
    def test_default_is_1920(self, tmp_path: Path):
        actual_width = _make_project(tmp_path).width
        assert actual_width == 1920

    def test_setter(self, tmp_path: Path):
        proj = _make_project(tmp_path)
        proj.width = 3840
        actual_width = proj.width
        assert actual_width == 3840


class TestTitle:
    def test_default_empty(self, tmp_path: Path):
        assert _make_project(tmp_path).title == ''

    def test_setter(self, tmp_path: Path):
        proj = _make_project(tmp_path)
        proj.title = 'My Project'
        assert proj.title == 'My Project'


class TestDescription:
    def test_default_empty(self, tmp_path: Path):
        assert _make_project(tmp_path).description == ''


class TestAuthor:
    def test_default_empty(self, tmp_path: Path):
        assert _make_project(tmp_path).author == ''


class TestTargetLoudness:
    def test_default(self, tmp_path: Path):
        assert _make_project(tmp_path).target_loudness == -18.0


class TestFrameRate:
    def test_default(self, tmp_path: Path):
        assert _make_project(tmp_path).frame_rate == 30


class TestSampleRate:
    def test_default(self, tmp_path: Path):
        assert _make_project(tmp_path).sample_rate == 44100


class TestAllSetters:
    def test_all_setters_work(self, tmp_path: Path):
        proj = _make_project(tmp_path)
        proj.title = 'T'
        proj.description = 'D'
        proj.author = 'A'
        proj.target_loudness = -24.0
        proj.frame_rate = 60
        proj.sample_rate = 48000
        assert proj.title == 'T'
        assert proj.description == 'D'
        assert proj.author == 'A'
        assert proj.target_loudness == -24.0
        assert proj.frame_rate == 60
        assert proj.sample_rate == 48000


class TestHeight:
    def test_default_is_1080(self, tmp_path: Path):
        actual_height = _make_project(tmp_path).height
        assert actual_height == 1080

    def test_setter(self, tmp_path: Path):
        proj = _make_project(tmp_path)
        proj.height = 2160
        actual_height = proj.height
        assert actual_height == 2160
