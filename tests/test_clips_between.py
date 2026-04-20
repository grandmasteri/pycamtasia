"""Tests for is_between, intersects, Track.clips_between, and Project.clips_between."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from camtasia.project import Project

EDIT_RATE = 705600000


class TestBaseClipIsBetween:
    def test_clip_entirely_within_range(self, project: Project) -> None:
        track = project.timeline.add_track('T')
        clip = track.add_clip('VMFile', 1, EDIT_RATE * 2, EDIT_RATE * 3)
        assert clip.is_between(1.0, 6.0) is True

    def test_clip_exactly_matching_range(self, project: Project) -> None:
        track = project.timeline.add_track('T')
        clip = track.add_clip('VMFile', 1, EDIT_RATE * 2, EDIT_RATE * 3)
        assert clip.is_between(2.0, 5.0) is True

    def test_clip_starts_before_range(self, project: Project) -> None:
        track = project.timeline.add_track('T')
        clip = track.add_clip('VMFile', 1, 0, EDIT_RATE * 3)
        assert clip.is_between(1.0, 5.0) is False

    def test_clip_ends_after_range(self, project: Project) -> None:
        track = project.timeline.add_track('T')
        clip = track.add_clip('VMFile', 1, EDIT_RATE * 2, EDIT_RATE * 5)
        # is_between checks full containment: start AND end must be within range
        assert clip.is_between(2.0, 5.0) is False


class TestBaseClipIntersects:
    def test_clip_fully_inside_range(self, project: Project) -> None:
        track = project.timeline.add_track('T')
        clip = track.add_clip('VMFile', 1, EDIT_RATE * 2, EDIT_RATE * 2)
        assert clip.intersects(1.0, 6.0) is True

    def test_clip_overlaps_range_start(self, project: Project) -> None:
        track = project.timeline.add_track('T')
        clip = track.add_clip('VMFile', 1, 0, EDIT_RATE * 3)
        assert clip.intersects(2.0, 6.0) is True

    def test_clip_overlaps_range_end(self, project: Project) -> None:
        track = project.timeline.add_track('T')
        clip = track.add_clip('VMFile', 1, EDIT_RATE * 4, EDIT_RATE * 3)
        assert clip.intersects(1.0, 5.0) is True

    def test_clip_completely_before_range(self, project: Project) -> None:
        track = project.timeline.add_track('T')
        clip = track.add_clip('VMFile', 1, 0, EDIT_RATE * 1)
        assert clip.intersects(2.0, 5.0) is False

    def test_clip_completely_after_range(self, project: Project) -> None:
        track = project.timeline.add_track('T')
        clip = track.add_clip('VMFile', 1, EDIT_RATE * 6, EDIT_RATE * 1)
        assert clip.intersects(2.0, 5.0) is False

    def test_adjacent_clip_does_not_intersect(self, project: Project) -> None:
        track = project.timeline.add_track('T')
        clip = track.add_clip('VMFile', 1, EDIT_RATE * 5, EDIT_RATE * 2)
        assert clip.intersects(0.0, 5.0) is False


class TestTrackClipsBetween:
    def test_returns_only_clips_within_range(self, project: Project) -> None:
        track = project.timeline.add_track('T')
        track.add_clip('VMFile', 1, 0, EDIT_RATE * 1)              # 0-1s
        track.add_clip('VMFile', 1, EDIT_RATE * 2, EDIT_RATE * 1)  # 2-3s
        track.add_clip('VMFile', 1, EDIT_RATE * 5, EDIT_RATE * 1)  # 5-6s
        result = track.clips_between(1.5, 4.0)
        assert len(result) == 1
        assert result[0].start_seconds == 2.0

    def test_returns_empty_when_no_clips_in_range(self, project: Project) -> None:
        track = project.timeline.add_track('T')
        track.add_clip('VMFile', 1, 0, EDIT_RATE * 1)
        assert track.clips_between(5.0, 10.0) == []


class TestProjectClipsBetween:
    def test_returns_clips_across_tracks(self, project: Project) -> None:
        track_a = project.timeline.add_track('A')
        track_b = project.timeline.add_track('B')
        track_a.add_clip('VMFile', 1, EDIT_RATE * 1, EDIT_RATE * 1)  # 1-2s
        track_b.add_clip('AMFile', 1, EDIT_RATE * 1, EDIT_RATE * 1)  # 1-2s
        track_a.add_clip('VMFile', 1, EDIT_RATE * 5, EDIT_RATE * 1)  # 5-6s outside
        result = project.clips_between(0.0, 3.0)
        assert len(result) == 2

    def test_returns_empty_when_no_clips_in_range(self, project: Project) -> None:
        track = project.timeline.add_track('T')
        track.add_clip('VMFile', 1, EDIT_RATE * 10, EDIT_RATE * 1)
        assert project.clips_between(0.0, 5.0) == []

    def test_result_contains_track_clip_tuples(self, project: Project) -> None:
        track = project.timeline.add_track('T')
        track.add_clip('VMFile', 1, EDIT_RATE * 1, EDIT_RATE * 1)
        result = project.clips_between(0.0, 5.0)
        returned_track, returned_clip = result[0]
        assert returned_track.name == 'T'
        assert returned_clip.start_seconds == 1.0


# ---------------------------------------------------------------------------
# Bug 1: is_between / intersects must use tick-space comparison
# ---------------------------------------------------------------------------

class TestIsBetweenTickSpace:
    """is_between must convert seconds to ticks before comparing."""

    def test_clip_at_exact_tick_boundary(self, project: Project) -> None:
        track = project.timeline.add_track('T')
        clip = track.add_clip('VMFile', 1, EDIT_RATE * 2, EDIT_RATE * 3)
        # Clip: 2s-5s. Range: 2s-5s. start_ticks <= clip.start < end_ticks
        assert clip.is_between(2.0, 5.0) is True

    def test_clip_start_equals_range_start_ticks(self, project: Project) -> None:
        track = project.timeline.add_track('T')
        clip = track.add_clip('VMFile', 1, EDIT_RATE * 3, EDIT_RATE * 1)
        assert clip.is_between(3.0, 10.0) is True

    def test_clip_start_before_range_start_ticks(self, project: Project) -> None:
        track = project.timeline.add_track('T')
        clip = track.add_clip('VMFile', 1, EDIT_RATE * 1, EDIT_RATE * 2)
        assert clip.is_between(2.0, 10.0) is False


class TestIntersectsTickSpace:
    """intersects must use tick-space comparison."""

    def test_overlapping_clip_detected(self, project: Project) -> None:
        track = project.timeline.add_track('T')
        clip = track.add_clip('VMFile', 1, EDIT_RATE * 1, EDIT_RATE * 4)
        assert clip.intersects(3.0, 6.0) is True

    def test_non_overlapping_clip_rejected(self, project: Project) -> None:
        track = project.timeline.add_track('T')
        clip = track.add_clip('VMFile', 1, EDIT_RATE * 6, EDIT_RATE * 2)
        assert clip.intersects(1.0, 5.0) is False

    def test_adjacent_clip_does_not_intersect_ticks(self, project: Project) -> None:
        track = project.timeline.add_track('T')
        clip = track.add_clip('VMFile', 1, EDIT_RATE * 5, EDIT_RATE * 2)
        assert clip.intersects(1.0, 5.0) is False


class TestIsBetweenFullContainment:
    """Bug 1: is_between must check full containment, not just start."""

    def test_clip_end_exceeds_range_is_not_between(self, project: Project) -> None:
        track = project.timeline.add_track('T')
        # Clip: 2s-7s, Range: 2s-5s → end exceeds range
        clip = track.add_clip('VMFile', 1, EDIT_RATE * 2, EDIT_RATE * 5)
        assert clip.is_between(2.0, 5.0) is False

    def test_clip_fully_contained(self, project: Project) -> None:
        track = project.timeline.add_track('T')
        # Clip: 2s-4s, Range: 1s-5s → fully contained
        clip = track.add_clip('VMFile', 1, EDIT_RATE * 2, EDIT_RATE * 2)
        assert clip.is_between(1.0, 5.0) is True

    def test_clip_end_exactly_at_range_end(self, project: Project) -> None:
        track = project.timeline.add_track('T')
        # Clip: 2s-5s, Range: 2s-5s → exactly contained
        clip = track.add_clip('VMFile', 1, EDIT_RATE * 2, EDIT_RATE * 3)
        assert clip.is_between(2.0, 5.0) is True
