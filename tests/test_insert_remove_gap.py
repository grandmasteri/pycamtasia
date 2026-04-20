"""Tests for Track.insert_gap() and Track.remove_gap_at()."""
from __future__ import annotations

from typing import Any

import pytest

from camtasia.timeline.timeline import Timeline
from camtasia.timeline.track import Track
from camtasia.timing import seconds_to_ticks


def _make_track() -> Track:
    attrs: dict[str, Any] = {"ident": "Track 1"}
    data: dict[str, Any] = {"trackIndex": 0, "medias": [], "transitions": []}
    return Track(attrs, data)


class TestInsertGap:
    def test_pushes_subsequent_clips_forward(self):
        track = _make_track()
        track.add_callout("A", 0, 5)
        track.add_callout("B", 5, 5)

        track.insert_gap(at_seconds=5.0, gap_duration_seconds=3.0)

        clips = sorted(track.clips, key=lambda c: c.start)
        assert clips[0].start == seconds_to_ticks(0)
        assert clips[1].start == seconds_to_ticks(8)

    def test_does_not_move_clips_before_gap(self):
        track = _make_track()
        track.add_callout("A", 0, 5)
        track.add_callout("B", 5, 5)

        track.insert_gap(at_seconds=5.0, gap_duration_seconds=2.0)

        first = min(track.clips, key=lambda c: c.start)
        assert first.start == seconds_to_ticks(0)

    def test_no_effect_on_empty_track(self):
        track = _make_track()
        track.insert_gap(at_seconds=0.0, gap_duration_seconds=5.0)
        assert list(track.clips) == []

    def test_gap_in_middle_of_three_clips(self):
        track = _make_track()
        track.add_callout("A", 0, 3)
        track.add_callout("B", 3, 3)
        track.add_callout("C", 6, 3)

        track.insert_gap(at_seconds=3.0, gap_duration_seconds=1.0)

        clips = sorted(track.clips, key=lambda c: c.start)
        assert clips[0].start == seconds_to_ticks(0)
        assert clips[1].start == seconds_to_ticks(4)
        assert clips[2].start == seconds_to_ticks(7)


class TestRemoveGapAt:
    def test_pulls_subsequent_clips_backward(self):
        track = _make_track()
        track.add_callout("A", 0, 5)
        track.add_callout("B", 8, 5)  # gap from 5s to 8s

        track.remove_gap_at(at_seconds=6.0)

        clips = sorted(track.clips, key=lambda c: c.start)
        assert clips[0].start == seconds_to_ticks(0)
        assert clips[1].start == seconds_to_ticks(5)

    def test_does_not_move_clips_before_gap(self):
        track = _make_track()
        track.add_callout("A", 0, 5)
        track.add_callout("B", 8, 5)

        track.remove_gap_at(at_seconds=6.0)

        first = min(track.clips, key=lambda c: c.start)
        assert first.start == seconds_to_ticks(0)

    def test_noop_when_no_gap_at_time(self):
        track = _make_track()
        track.add_callout("A", 0, 5)
        track.add_callout("B", 5, 5)  # no gap

        original_starts = sorted(c.start for c in track.clips)
        track.remove_gap_at(at_seconds=5.0)
        new_starts = sorted(c.start for c in track.clips)
        assert original_starts == new_starts

    def test_noop_on_empty_track(self):
        track = _make_track()
        track.remove_gap_at(at_seconds=3.0)
        assert list(track.clips) == []

    def test_removes_only_targeted_gap(self):
        track = _make_track()
        track.add_callout("A", 0, 3)
        track.add_callout("B", 5, 3)   # gap 3-5
        track.add_callout("C", 10, 3)  # gap 8-10

        track.remove_gap_at(at_seconds=4.0)  # remove first gap

        clips = sorted(track.clips, key=lambda c: c.start)
        assert clips[0].start == seconds_to_ticks(0)
        assert clips[1].start == seconds_to_ticks(3)
        assert clips[2].start == seconds_to_ticks(8)


class TestInsertThenRemoveGapRoundtrip:
    def test_insert_then_remove_restores_original(self):
        track = _make_track()
        track.add_callout("A", 0, 5)
        track.add_callout("B", 5, 5)

        track.insert_gap(at_seconds=5.0, gap_duration_seconds=3.0)
        track.remove_gap_at(at_seconds=6.0)

        clips = sorted(track.clips, key=lambda c: c.start)
        assert clips[0].start == seconds_to_ticks(0)
        assert clips[1].start == seconds_to_ticks(5)


# Bug 13: Timeline.remove_gap must check for clips spanning the gap


def _make_timeline(track_medias_list: list[list[dict]]) -> Timeline:
    """Build a minimal Timeline with the given tracks."""
    tracks = []
    attrs = []
    for i, medias in enumerate(track_medias_list):
        tracks.append({'trackIndex': i, 'medias': medias, 'transitions': []})
        attrs.append({'ident': f'Track {i}'})
    return Timeline({
        'id': 0,
        'sceneTrack': {'scenes': [{'csml': {'tracks': tracks}}]},
        'trackAttributes': attrs,
        'parameters': {},
    })


class TestTimelineRemoveGapSpanningClip:
    def test_rejects_clip_spanning_into_gap(self):
        """A clip that starts before the gap but extends into it should be rejected."""
        tl = _make_timeline([[
            {'id': 1, '_type': 'Callout', 'start': 0, 'duration': seconds_to_ticks(10)},
        ]])
        with pytest.raises(ValueError, match='spans into gap region'):
            tl.remove_gap(5.0, 3.0)

    def test_rejects_clip_starting_inside_gap(self):
        tl = _make_timeline([[
            {'id': 1, '_type': 'Callout', 'start': seconds_to_ticks(6), 'duration': seconds_to_ticks(2)},
        ]])
        with pytest.raises(ValueError, match='starts inside gap'):
            tl.remove_gap(5.0, 3.0)


# Bug 14: Track.remove_gap_at preserves unrelated transitions

class TestRemoveGapAtPreservesTransitions:
    def test_preserves_transitions_between_unshifted_clips(self):
        track = _make_track()
        a = track.add_callout("A", 0, 3)
        b = track.add_callout("B", 3, 3)
        # gap from 6s to 10s
        track.add_callout("C", 10, 3)

        # Add transition between A and B (both before the gap)
        track._data.setdefault('transitions', []).append({
            'name': 'FadeThroughBlack',
            'duration': seconds_to_ticks(0.5),
            'leftMedia': a.id,
            'rightMedia': b.id,
        })

        track.remove_gap_at(at_seconds=7.0)

        # Transition between A and B should be preserved
        assert len(track._data['transitions']) == 1
        assert track._data['transitions'][0]['leftMedia'] == a.id
