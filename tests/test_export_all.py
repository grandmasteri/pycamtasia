"""Tests for Project.export_all."""
from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from camtasia.project import Project

if TYPE_CHECKING:
    from pathlib import Path

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


EXPECTED_FILES = {"report.md", "report.json", "timeline.json", "markers.srt", "timeline.edl"}


class TestExportAll:
    def test_export_all_creates_files(self, tmp_path: Path):
        proj = _create_project(tmp_path)
        out_dir = tmp_path / "exports"
        proj.export_all(out_dir)
        created = {f.name for f in out_dir.iterdir()}
        assert created == EXPECTED_FILES

    def test_export_all_returns_paths(self, tmp_path: Path):
        proj = _create_project(tmp_path)
        out_dir = tmp_path / "exports"
        results = proj.export_all(out_dir)
        assert set(results.keys()) == {"report_md", "report_json", "timeline_json", "markers_srt", "edl"}
        for _key, path in results.items():
            assert path.exists()
