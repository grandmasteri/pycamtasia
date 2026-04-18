"""Tests for Project.find_clips_with_effect, find_clips_by_source, replace_all_media."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from camtasia.project import Project
from camtasia.types import EffectName


def _make_project(tmp_path: Path, clips: list[dict]) -> Project:
    """Create a minimal project with the given clip dicts on track 0."""
    data = {
        "editRate": 30,
        "authoringClientName": {"name": "Camtasia", "platform": "Mac", "version": "2020.0.8"},
        "sourceBin": [],
        "timeline": {
            "id": 1,
            "sceneTrack": {
                "scenes": [{"csml": {"tracks": [{"trackIndex": 0, "medias": clips}]}}]
            },
            "trackAttributes": [
                {"ident": "Track 1", "audioMuted": False, "videoHidden": False,
                 "magnetic": False, "metadata": {"IsLocked": "False"}},
            ],
        },
    }
    proj_dir = tmp_path / "test.cmproj"
    proj_dir.mkdir()
    (proj_dir / "project.tscproj").write_text(json.dumps(data))
    return Project(proj_dir)


def _clip(clip_id: int, src: int = 1, effects: list[dict] | None = None) -> dict:
    return {
        "id": clip_id,
        "src": src,
        "trackNumber": 0,
        "start": 0,
        "duration": 300,
        "mediaStart": 0,
        "mediaDuration": 300,
        "_type": "VMFile",
        "effects": effects or [],
        "parameters": {},
    }


class TestFindClipsWithEffect:
    def test_finds_clips_with_matching_effect(self, tmp_path: Path):
        clips = [
            _clip(1, effects=[{"effectName": "DropShadow", "parameters": {}}]),
            _clip(2),
            _clip(3, effects=[{"effectName": "DropShadow", "parameters": {}}]),
        ]
        proj = _make_project(tmp_path, clips)
        result = proj.find_clips_with_effect("DropShadow")
        assert len(result) == 2
        assert {c.id for _, c in result} == {1, 3}

    def test_accepts_effect_name_enum(self, tmp_path: Path):
        clips = [_clip(1, effects=[{"effectName": "DropShadow", "parameters": {}}])]
        proj = _make_project(tmp_path, clips)
        result = proj.find_clips_with_effect(EffectName.DROP_SHADOW)
        assert len(result) == 1

    def test_returns_empty_when_no_match(self, tmp_path: Path):
        proj = _make_project(tmp_path, [_clip(1)])
        assert proj.find_clips_with_effect("DropShadow") == []

    def test_returns_empty_on_empty_project(self, tmp_path: Path):
        proj = _make_project(tmp_path, [])
        assert proj.find_clips_with_effect("DropShadow") == []

    def test_result_contains_track(self, tmp_path: Path):
        clips = [_clip(1, effects=[{"effectName": "Glow", "parameters": {}}])]
        proj = _make_project(tmp_path, clips)
        result = proj.find_clips_with_effect("Glow")
        track, clip = result[0]
        assert track.name == "Track 1"
        assert clip.id == 1


class TestFindClipsBySource:
    def test_finds_clips_referencing_source(self, tmp_path: Path):
        clips = [_clip(1, src=10), _clip(2, src=20), _clip(3, src=10)]
        proj = _make_project(tmp_path, clips)
        result = proj.find_clips_by_source(10)
        assert len(result) == 2
        assert {c.id for _, c in result} == {1, 3}

    def test_returns_empty_when_no_match(self, tmp_path: Path):
        proj = _make_project(tmp_path, [_clip(1, src=5)])
        assert proj.find_clips_by_source(99) == []

    def test_returns_empty_on_empty_project(self, tmp_path: Path):
        proj = _make_project(tmp_path, [])
        assert proj.find_clips_by_source(1) == []


class TestReplaceAllMedia:
    def test_replaces_matching_source_ids(self, tmp_path: Path):
        clips = [_clip(1, src=10), _clip(2, src=20), _clip(3, src=10)]
        proj = _make_project(tmp_path, clips)
        count = proj.replace_all_media(10, 99)
        assert count == 2
        assert len(proj.find_clips_by_source(10)) == 0
        assert len(proj.find_clips_by_source(99)) == 2

    def test_returns_zero_when_no_match(self, tmp_path: Path):
        proj = _make_project(tmp_path, [_clip(1, src=5)])
        assert proj.replace_all_media(99, 100) == 0

    def test_returns_zero_on_empty_project(self, tmp_path: Path):
        proj = _make_project(tmp_path, [])
        assert proj.replace_all_media(1, 2) == 0

    def test_does_not_modify_non_matching_clips(self, tmp_path: Path):
        clips = [_clip(1, src=10), _clip(2, src=20)]
        proj = _make_project(tmp_path, clips)
        proj.replace_all_media(10, 99)
        # clip 2 should still reference src=20
        assert len(proj.find_clips_by_source(20)) == 1
