"""Tests for Track.freeze_at_clip_start, freeze_at_clip_end, and extend_clip_to."""
from __future__ import annotations

import pytest

from camtasia.timing import seconds_to_ticks


class TestFreezeAtClipStart:
    def test_creates_freeze_at_start(self, project):
        track = project.timeline.get_or_create_track('Video')
        src = track.add_clip('VMFile', 1, seconds_to_ticks(2.0), seconds_to_ticks(10.0))
        initial = len(track)
        track.freeze_at_clip_start(src.id, freeze_duration_seconds=1.0)
        assert len(track) == initial + 1

    def test_freeze_position_matches_clip_start(self, project):
        track = project.timeline.get_or_create_track('Video')
        src = track.add_clip('VMFile', 1, seconds_to_ticks(3.0), seconds_to_ticks(10.0))
        track.freeze_at_clip_start(src.id, freeze_duration_seconds=2.0)
        # The freeze frame should be at the clip's start
        freeze = [c for c in track.clips if c.id != src.id][-1]
        assert freeze.start == seconds_to_ticks(3.0)
        assert freeze.duration == seconds_to_ticks(2.0)

    def test_missing_clip_raises(self, project):
        track = project.timeline.get_or_create_track('Video')
        with pytest.raises(KeyError):
            track.freeze_at_clip_start(99999, freeze_duration_seconds=1.0)


class TestFreezeAtClipEnd:
    def test_creates_freeze_near_end(self, project):
        track = project.timeline.get_or_create_track('Video')
        src = track.add_clip('VMFile', 1, seconds_to_ticks(0.0), seconds_to_ticks(10.0))
        initial = len(track)
        track.freeze_at_clip_end(src.id, freeze_duration_seconds=1.0)
        assert len(track) == initial + 1

    def test_freeze_position_near_clip_end(self, project):
        track = project.timeline.get_or_create_track('Video')
        src = track.add_clip('VMFile', 1, seconds_to_ticks(0.0), seconds_to_ticks(10.0))
        track.freeze_at_clip_end(src.id, freeze_duration_seconds=2.0)
        freeze = [c for c in track.clips if c.id != src.id][-1]
        # Should be placed very close to the end (10s - epsilon)
        expected_end = seconds_to_ticks(10.0)
        assert freeze.start >= expected_end - 2  # within 1 tick of end
        assert freeze.duration == seconds_to_ticks(2.0)

    def test_missing_clip_raises(self, project):
        track = project.timeline.get_or_create_track('Video')
        with pytest.raises(KeyError):
            track.freeze_at_clip_end(99999, freeze_duration_seconds=1.0)


class TestExtendClipTo:
    def test_extend_to_longer(self, project):
        track = project.timeline.get_or_create_track('Video')
        clip = track.add_clip('VMFile', 1, seconds_to_ticks(0.0), seconds_to_ticks(5.0))
        track.extend_clip_to(clip.id, target_duration_seconds=10.0)
        updated = track.find_clip(clip.id)
        assert updated.duration == seconds_to_ticks(10.0)

    def test_shrink_to_shorter(self, project):
        track = project.timeline.get_or_create_track('Video')
        clip = track.add_clip('VMFile', 1, seconds_to_ticks(0.0), seconds_to_ticks(10.0))
        track.extend_clip_to(clip.id, target_duration_seconds=3.0)
        updated = track.find_clip(clip.id)
        assert updated.duration == seconds_to_ticks(3.0)

    def test_same_duration_noop(self, project):
        track = project.timeline.get_or_create_track('Video')
        clip = track.add_clip('VMFile', 1, seconds_to_ticks(0.0), seconds_to_ticks(5.0))
        track.extend_clip_to(clip.id, target_duration_seconds=5.0)
        updated = track.find_clip(clip.id)
        assert updated.duration == seconds_to_ticks(5.0)

    def test_zero_target_raises(self, project):
        track = project.timeline.get_or_create_track('Video')
        clip = track.add_clip('VMFile', 1, seconds_to_ticks(0.0), seconds_to_ticks(5.0))
        with pytest.raises(ValueError):
            track.extend_clip_to(clip.id, target_duration_seconds=0.0)

    def test_missing_clip_raises(self, project):
        track = project.timeline.get_or_create_track('Video')
        with pytest.raises(KeyError):
            track.extend_clip_to(99999, target_duration_seconds=10.0)
