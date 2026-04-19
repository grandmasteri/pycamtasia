"""Tests for Project.apply_to_all_clips() and Project.for_each_track()."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from camtasia.project import Project


# ── apply_to_all_clips ──────────────────────────────────────────────


class TestApplyToAllClips:
    def test_returns_zero_on_empty_project(self, project):
        assert project.apply_to_all_clips(lambda c: None) == 0

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

    def test_operation_can_mutate(self, project):
        project.for_each_track(lambda t: setattr(t, 'audio_muted', True))
        for track in project.timeline.tracks:
            assert track.audio_muted is True

    def test_returns_one_on_single_track_project(self, project):
        # The conftest project has 2 default tracks
        count = project.for_each_track(lambda t: None)
        assert count == 2

    def test_no_filter_applies_to_all(self, project):
        track = project.timeline.add_track('Test')
        track.add_clip('VMFile', 1, 0, 705600000)
        track.add_clip('AMFile', 1, 705600000, 705600000)
        gains = []
        count = project.apply_to_all_clips(lambda c: gains.append(c.gain))
        assert count == 2
