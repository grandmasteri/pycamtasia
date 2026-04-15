"""Tests for Track.insert_gap() and Track.remove_gap_at()."""
from __future__ import annotations

from typing import Any

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

    def test_shifts_transitions_after_gap(self):
        track = _make_track()
        c1 = track.add_callout("A", 0, 5)
        c2 = track.add_callout("B", 5, 5)
        track._data['transitions'] = [{'start': seconds_to_ticks(5), 'duration': 100}]

        track.insert_gap(at_seconds=5.0, gap_duration_seconds=2.0)

        assert track._data['transitions'][0]['start'] == seconds_to_ticks(7)

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

    def test_shifts_transitions_backward(self):
        track = _make_track()
        track.add_callout("A", 0, 5)
        track.add_callout("B", 10, 5)  # gap 5-10
        track._data['transitions'] = [{'start': seconds_to_ticks(10), 'duration': 100}]

        track.remove_gap_at(at_seconds=7.0)

        assert track._data['transitions'][0]['start'] == seconds_to_ticks(5)

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
