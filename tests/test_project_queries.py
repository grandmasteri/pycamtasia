"""Tests for Project.find_clips_with_effect, find_clips_by_source, replace_all_media."""
from __future__ import annotations

from typing import TYPE_CHECKING

from camtasia.types import EffectName

if TYPE_CHECKING:
    from camtasia.project import Project


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


def _add_clips(project: Project, clips: list[dict]) -> None:
    """Add clip dicts to the first track of a project."""
    track = next(iter(project.timeline.tracks))
    track._data['medias'] = clips


class TestFindClipsWithEffect:
    def test_finds_clips_with_matching_effect(self, project):
        clips = [
            _clip(1, effects=[{"effectName": "DropShadow", "parameters": {}}]),
            _clip(2),
            _clip(3, effects=[{"effectName": "DropShadow", "parameters": {}}]),
        ]
        _add_clips(project, clips)
        result = project.find_clips_with_effect("DropShadow")
        assert {c.id for _, c in result} == {1, 3}

    def test_accepts_effect_name_enum(self, project):
        clips = [_clip(1, effects=[{"effectName": "DropShadow", "parameters": {}}])]
        _add_clips(project, clips)
        result = project.find_clips_with_effect(EffectName.DROP_SHADOW)
        assert result[0][1].id == 1

    def test_returns_empty_when_no_match(self, project):
        _add_clips(project, [_clip(1)])
        assert project.find_clips_with_effect("DropShadow") == []

    def test_returns_empty_on_empty_project(self, project):
        assert project.find_clips_with_effect("DropShadow") == []

    def test_result_contains_track(self, project):
        clips = [_clip(1, effects=[{"effectName": "Glow", "parameters": {}}])]
        _add_clips(project, clips)
        result = project.find_clips_with_effect("Glow")
        _track, clip = result[0]
        assert clip.id == 1


class TestFindClipsBySource:
    def test_finds_clips_referencing_source(self, project):
        clips = [_clip(1, src=10), _clip(2, src=20), _clip(3, src=10)]
        _add_clips(project, clips)
        result = project.find_clips_by_source(10)
        assert {c.id for _, c in result} == {1, 3}

    def test_returns_empty_when_no_match(self, project):
        _add_clips(project, [_clip(1, src=5)])
        assert project.find_clips_by_source(99) == []

    def test_returns_empty_on_empty_project(self, project):
        assert project.find_clips_by_source(1) == []


class TestReplaceAllMedia:
    def test_replaces_matching_source_ids(self, project):
        clips = [_clip(1, src=10), _clip(2, src=20), _clip(3, src=10)]
        _add_clips(project, clips)
        count = project.replace_all_media(10, 99)
        assert count == 2
        assert project.find_clips_by_source(10) == []
        assert {c.id for _, c in project.find_clips_by_source(99)} == {1, 3}

    def test_returns_zero_when_no_match(self, project):
        _add_clips(project, [_clip(1, src=5)])
        assert project.replace_all_media(99, 100) == 0

    def test_returns_zero_on_empty_project(self, project):
        assert project.replace_all_media(1, 2) == 0

    def test_does_not_modify_non_matching_clips(self, project):
        clips = [_clip(1, src=10), _clip(2, src=20)]
        _add_clips(project, clips)
        project.replace_all_media(10, 99)
        # clip 2 should still reference src=20
        assert project.find_clips_by_source(20)[0][1].id == 2
