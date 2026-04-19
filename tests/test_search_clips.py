"""Tests for Project.search_clips."""
from __future__ import annotations

from typing import TYPE_CHECKING

from camtasia.types import ClipType

if TYPE_CHECKING:
    from camtasia.project import Project


class TestSearchClips:
    def test_by_type(self, project: Project) -> None:
        track = project.timeline.add_track('Test')
        track.add_clip('VMFile', 1, 0, 705600000)
        track.add_clip('AMFile', 1, 705600000, 705600000)
        results = project.search_clips(clip_type=ClipType.VIDEO)
        assert results[0][1].clip_type == 'VMFile'
        assert results[0][1].start == 0

    def test_by_duration(self, project: Project) -> None:
        track = project.timeline.add_track('Test')
        track.add_clip('VMFile', 1, 0, 705600000)      # 1s
        track.add_clip('VMFile', 1, 705600000, 705600000 * 5)  # 5s
        results = project.search_clips(min_duration_seconds=3.0)
        assert results[0][1].duration == 705600000 * 5

    def test_by_effects(self, project: Project) -> None:
        track = project.timeline.add_track('Test')
        clip_with = track.add_clip('VMFile', 1, 0, 705600000)
        clip_with.add_drop_shadow()
        track.add_clip('VMFile', 1, 705600000, 705600000)
        results = project.search_clips(has_effects=True)
        assert results[0][1].start == 0

    def test_combined(self, project: Project) -> None:
        track = project.timeline.add_track('Audio')
        track.add_clip('AMFile', 1, 0, 705600000 * 10)
        track2 = project.timeline.add_track('Video')
        track2.add_clip('VMFile', 1, 0, 705600000)
        results = project.search_clips(clip_type='AMFile', on_track='Audio')
        assert results[0][1].clip_type == 'AMFile'

    def test_no_match(self, project: Project) -> None:
        track = project.timeline.add_track('Test')
        track.add_clip('VMFile', 1, 0, 705600000)
        results = project.search_clips(clip_type='AMFile')
        assert results == []

    def test_max_duration_filter(self, project: Project) -> None:
        track = project.timeline.add_track('Test')
        track.add_clip('VMFile', 1, 0, 705600000)      # 1s
        track.add_clip('VMFile', 1, 705600000, 705600000 * 5)  # 5s
        results = project.search_clips(max_duration_seconds=2.0)
        assert results[0][1].duration == 705600000

    def test_has_keyframes_filter(self, project: Project) -> None:
        track = project.timeline.add_track('Test')
        clip = track.add_clip('VMFile', 1, 0, 705600000 * 5)
        clip.set_opacity_fade(1.0, 0.0)
        track.add_clip('VMFile', 1, 705600000 * 5, 705600000)
        results = project.search_clips(has_keyframes=True)
        assert results[0][1].start == 0

    def test_on_track_mismatch(self, project: Project) -> None:
        project.timeline.add_track('Audio')
        track = project.timeline.add_track('Video')
        track.add_clip('VMFile', 1, 0, 705600000)
        results = project.search_clips(on_track='Audio')
        assert results == []
