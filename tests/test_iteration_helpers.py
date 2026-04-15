"""Tests for Project.apply_to_all_clips() and Project.for_each_track()."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from camtasia.project import Project


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
                            {"trackIndex": 1, "medias": []},
                        ]
                    }
                }
            ]
        },
        "trackAttributes": [
            {"ident": "Track-0", "audioMuted": False, "videoHidden": False,
             "magnetic": False, "metadata": {"IsLocked": "False"}},
            {"ident": "Track-1", "audioMuted": False, "videoHidden": False,
             "magnetic": False, "metadata": {"IsLocked": "False"}},
        ],
    },
}


def _make_project(tmp_path: Path, data: dict | None = None) -> Project:
    proj_dir = tmp_path / "test.cmproj"
    proj_dir.mkdir()
    tscproj = proj_dir / "test.tscproj"
    tscproj.write_text(json.dumps(data or MINIMAL_PROJECT_DATA))
    return Project(proj_dir)


# ── apply_to_all_clips ──────────────────────────────────────────────


class TestApplyToAllClips:
    def test_returns_zero_on_empty_project(self, tmp_path):
        proj = _make_project(tmp_path)
        assert proj.apply_to_all_clips(lambda c: None) == 0

    def test_applies_to_every_clip(self, project):
        visited: list[int] = []
        count = project.apply_to_all_clips(lambda c: visited.append(c.id))
        assert count == len(visited)
        assert count == project.clip_count

    def test_filter_narrows_scope(self, project):
        if project.clip_count == 0:
            pytest.skip("fixture has no clips")
        visited: list[int] = []
        # filter that rejects everything
        count = project.apply_to_all_clips(
            lambda c: visited.append(c.id),
            clip_filter=lambda c: False,
        )
        assert count == 0
        assert visited == []

    def test_filter_accepts_all(self, project):
        visited: list[int] = []
        count = project.apply_to_all_clips(
            lambda c: visited.append(c.id),
            clip_filter=lambda c: True,
        )
        assert count == project.clip_count

    def test_filter_by_clip_type(self, project):
        if project.clip_count == 0:
            pytest.skip("fixture has no clips")
        first_type = project.all_clips[0][1].clip_type
        visited: list[int] = []
        count = project.apply_to_all_clips(
            lambda c: visited.append(c.id),
            clip_filter=lambda c: c.clip_type == first_type,
        )
        expected = sum(1 for _, c in project.all_clips if c.clip_type == first_type)
        assert count == expected

    def test_operation_mutates_clips(self, project):
        """Verify the operation callback can actually modify clip data."""
        if project.clip_count == 0:
            pytest.skip("fixture has no clips")
        project.apply_to_all_clips(lambda c: c._data.update({"_touched": True}))
        for _, clip in project.all_clips:
            assert clip._data.get("_touched") is True


# ── for_each_track ───────────────────────────────────────────────────


class TestForEachTrack:
    def test_returns_track_count(self, project):
        count = project.for_each_track(lambda t: None)
        assert count == project.track_count

    def test_visits_every_track(self, project):
        names: list[str] = []
        project.for_each_track(lambda t: names.append(t.name))
        assert len(names) == project.track_count

    def test_operation_can_mutate(self, tmp_path):
        proj = _make_project(tmp_path)
        proj.for_each_track(lambda t: setattr(t, 'audio_muted', True))
        for track in proj.timeline.tracks:
            assert track.audio_muted is True

    def test_returns_zero_on_single_track_project(self, tmp_path):
        data = json.loads(json.dumps(MINIMAL_PROJECT_DATA))
        data["timeline"]["sceneTrack"]["scenes"][0]["csml"]["tracks"] = [
            {"trackIndex": 0, "medias": []},
        ]
        data["timeline"]["trackAttributes"] = [
            {"ident": "Solo", "audioMuted": False, "videoHidden": False,
             "magnetic": False, "metadata": {"IsLocked": "False"}},
        ]
        proj = _make_project(tmp_path, data)
        assert proj.for_each_track(lambda t: None) == 1

    def test_no_filter_applies_to_all(self, project):
        track = project.timeline.add_track('Test')
        track.add_clip('VMFile', 1, 0, 705600000)
        track.add_clip('AMFile', 1, 705600000, 705600000)
        gains = []
        count = project.apply_to_all_clips(lambda c: gains.append(c.gain))
        assert count == 2
        assert len(gains) == 2
