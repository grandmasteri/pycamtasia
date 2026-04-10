"""Tests for idempotent gradient background shader reuse."""
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
            {"trackIndex": 0, "medias": []},
            {"trackIndex": 1, "medias": [], "parameters": {}, "transitions": []},
        ]}}]},
        "trackAttributes": [
            {"ident": "", "audioMuted": False, "videoHidden": False,
             "magnetic": False, "metadata": {"IsLocked": "False"}},
            {"ident": "Track 1", "audioMuted": False, "videoHidden": False,
             "magnetic": False, "metadata": {"IsLocked": "False"}},
        ],
    },
}


def _make_project(tmp_path: Path) -> Project:
    proj_dir = tmp_path / "test.cmproj"
    proj_dir.mkdir()
    (proj_dir / "project.tscproj").write_text(json.dumps(MINIMAL_PROJECT_DATA))
    return Project(proj_dir)


class TestAddGradientBackgroundIdempotent:
    def test_creates_shader_when_none_exists(self, tmp_path: Path):
        project = _make_project(tmp_path)
        project.add_gradient_background(duration_seconds=5.0)

        shader_sources = project.find_media_by_suffix('.tscshadervid')
        actual_shader_count = len(shader_sources)
        assert actual_shader_count == 1
        assert '.tscshadervid' in str(shader_sources[0].source)

    def test_reuses_existing_shader(self, tmp_path: Path):
        project = _make_project(tmp_path)
        project.add_gradient_background(duration_seconds=5.0)
        expected_source_id = project.find_media_by_suffix('.tscshadervid')[0].id

        project.add_gradient_background(duration_seconds=5.0)

        shader_sources = project.find_media_by_suffix('.tscshadervid')
        actual_shader_count = len(shader_sources)
        assert actual_shader_count == 1
        assert shader_sources[0].id == expected_source_id

    def test_different_duration_reuses_shader(self, tmp_path: Path):
        project = _make_project(tmp_path)
        project.add_gradient_background(duration_seconds=5.0)
        expected_source_id = project.find_media_by_suffix('.tscshadervid')[0].id

        project.add_gradient_background(duration_seconds=10.0)

        shader_sources = project.find_media_by_suffix('.tscshadervid')
        actual_shader_count = len(shader_sources)
        assert actual_shader_count == 1
        assert shader_sources[0].id == expected_source_id
