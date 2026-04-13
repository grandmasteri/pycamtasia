from __future__ import annotations

import json
from pathlib import Path

import pytest

from camtasia.project import Project, load_project, use_project, new_project
from camtasia.media_bin import MediaBin
from camtasia.timeline import Timeline


MINIMAL_PROJECT_DATA = {
    "editRate": 30,
    "authoringClientName": {
        "name": "Camtasia",
        "platform": "Mac",
        "version": "2020.0.8",
    },
    "sourceBin": [],
    "timeline": {
        "id": 1,
        "sceneTrack": {
            "scenes": [
                {
                    "csml": {
                        "tracks": [
                            {"trackIndex": 0, "medias": []},
                        ]
                    }
                }
            ]
        },
        "trackAttributes": [
            {
                "ident": "",
                "audioMuted": False,
                "videoHidden": False,
                "magnetic": False,
                "metadata": {"IsLocked": "False"},
            }
        ],
    },
}


def _create_cmproj(tmp_path: Path, data: dict | None = None) -> Path:
    """Create a minimal .cmproj bundle in tmp_path and return its path."""
    proj_dir = tmp_path / "test.cmproj"
    proj_dir.mkdir()
    tscproj = proj_dir / "project.tscproj"
    tscproj.write_text(json.dumps(data or MINIMAL_PROJECT_DATA))
    return proj_dir


class TestProjectLoad:
    def test_load_from_cmproj_directory(self, tmp_path: Path):
        proj_dir = _create_cmproj(tmp_path)
        project = Project(proj_dir)
        assert project.file_path == proj_dir

    def test_load_from_tscproj_file(self, tmp_path: Path):
        proj_dir = _create_cmproj(tmp_path)
        tscproj = proj_dir / "project.tscproj"
        project = Project(tscproj)
        assert project.file_path == tscproj

    def test_load_missing_tscproj_raises(self, tmp_path: Path):
        empty_dir = tmp_path / "empty.cmproj"
        empty_dir.mkdir()
        with pytest.raises(FileNotFoundError):
            Project(empty_dir)


class TestProjectProperties:
    def test_edit_rate(self, tmp_path: Path):
        project = Project(_create_cmproj(tmp_path))
        assert project.edit_rate == 30

    def test_edit_rate_default_when_missing(self, tmp_path: Path):
        data = {k: v for k, v in MINIMAL_PROJECT_DATA.items() if k != "editRate"}
        data["authoringClientName"] = MINIMAL_PROJECT_DATA["authoringClientName"]
        data["timeline"] = MINIMAL_PROJECT_DATA["timeline"]
        project = Project(_create_cmproj(tmp_path, data))
        assert project.edit_rate == 705_600_000

    def test_media_bin_returns_media_bin(self, tmp_path: Path):
        project = Project(_create_cmproj(tmp_path))
        assert isinstance(project.media_bin, MediaBin)
        assert list(project.media_bin) is not None

    def test_timeline_returns_timeline(self, tmp_path: Path):
        project = Project(_create_cmproj(tmp_path))
        assert isinstance(project.timeline, Timeline)
        assert project.timeline.track_count >= 0

    def test_authoring_client(self, tmp_path: Path):
        project = Project(_create_cmproj(tmp_path))
        actual_client = project.authoring_client
        assert actual_client.name == "Camtasia"
        assert actual_client.platform == "Mac"
        assert actual_client.version == "2020.0.8"


class TestProjectSave:
    def test_save_writes_valid_json(self, tmp_path: Path):
        proj_dir = _create_cmproj(tmp_path)
        project = Project(proj_dir)
        project.save()
        tscproj = proj_dir / "project.tscproj"
        reloaded = json.loads(tscproj.read_text())
        assert reloaded["editRate"] == 30
        assert reloaded["authoringClientName"]["name"] == "Camtasia"

    def test_save_persists_mutations(self, tmp_path: Path):
        proj_dir = _create_cmproj(tmp_path)
        project = Project(proj_dir)
        project.timeline.add_track("new-track")
        project.save()
        reloaded = json.loads((proj_dir / "project.tscproj").read_text())
        track_names = [
            a["ident"]
            for a in reloaded["timeline"]["trackAttributes"]
        ]
        assert set(track_names) == {"", "new-track"}


class TestLoadProject:
    def test_load_project_returns_project(self, tmp_path: Path):
        proj_dir = _create_cmproj(tmp_path)
        project = load_project(proj_dir)
        assert isinstance(project, Project)
        assert project.edit_rate == 30

    def test_load_project_with_string_path(self, tmp_path: Path):
        proj_dir = _create_cmproj(tmp_path)
        project = load_project(str(proj_dir))
        assert isinstance(project, Project)


class TestUseProject:
    def test_use_project_saves_on_exit(self, tmp_path: Path):
        proj_dir = _create_cmproj(tmp_path)
        with use_project(proj_dir) as proj:
            proj.timeline.add_track("ctx-track")
        reloaded = json.loads((proj_dir / "project.tscproj").read_text())
        track_names = [
            a["ident"]
            for a in reloaded["timeline"]["trackAttributes"]
        ]
        assert set(track_names) == {"", "ctx-track"}

    def test_use_project_no_save_on_exit(self, tmp_path: Path):
        proj_dir = _create_cmproj(tmp_path)
        original = (proj_dir / "project.tscproj").read_text()
        with use_project(proj_dir, save_on_exit=False) as proj:
            proj.timeline.add_track("should-not-persist")
        after = (proj_dir / "project.tscproj").read_text()
        assert original == after


class TestNewProject:
    def test_new_project_creates_cmproj(self, tmp_path: Path):
        project_path = tmp_path / "brand_new.cmproj"
        new_project(project_path)
        assert project_path.exists()
        assert (project_path / "project.tscproj").exists()

    def test_new_project_is_loadable(self, tmp_path: Path):
        project_path = tmp_path / "brand_new.cmproj"
        new_project(project_path)
        project = load_project(project_path)
        assert isinstance(project.timeline, Timeline)
        assert isinstance(project.media_bin, MediaBin)
        assert list(project.media_bin) is not None


class TestProjectRepr:
    def test_project_repr(self, tmp_path: Path):
        proj_dir = _create_cmproj(tmp_path)
        project = Project(proj_dir)
        r = repr(project)
        assert r.startswith("Project(path='test.cmproj'")
        assert "tracks=" in r
        assert "duration=" in r
        assert r.endswith("s)")


class TestFromTemplate:
    def test_from_template_creates_project(self, tmp_path: Path):
        dest = tmp_path / "templated.cmproj"
        proj = Project.from_template(dest)
        assert dest.exists()
        assert isinstance(proj, Project)
        assert proj.width == 1920
        assert proj.height == 1080
        assert proj.frame_rate == 30

    def test_from_template_custom_settings(self, tmp_path: Path):
        dest = tmp_path / "custom.cmproj"
        proj = Project.from_template(
            dest, width=3840, height=2160, title="My Video", frame_rate=60
        )
        assert proj.width == 3840
        assert proj.height == 2160
        assert proj.title == "My Video"
        assert proj.frame_rate == 60
