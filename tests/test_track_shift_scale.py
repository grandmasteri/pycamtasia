"""Tests for Track.shift_all_clips() and Track.scale_all_durations()."""
from __future__ import annotations

from typing import Any

import pytest

from camtasia.timeline.track import Track
from camtasia.timing import seconds_to_ticks


def _make_track() -> Track:
    attrs: dict[str, Any] = {"ident": "Track 1"}
    data: dict[str, Any] = {"trackIndex": 0, "medias": [], "transitions": []}
    return Track(attrs, data)


class TestShiftAllClipsForward:
    def test_shifts_clips_forward(self):
        track = _make_track()
        track.add_callout("A", 0, 5)
        track.add_callout("B", 5, 5)

        track.shift_all_clips(2.0)

        starts = [m['start'] for m in track._data['medias']]
        assert starts == [seconds_to_ticks(2.0), seconds_to_ticks(7.0)]




class TestShiftAllClipsBackward:
    def test_shifts_clips_backward(self):
        track = _make_track()
        track.add_callout("A", 5, 5)

        track.shift_all_clips(-2.0)

        assert track._data['medias'][0]['start'] == seconds_to_ticks(3.0)

    def test_clamps_to_zero(self):
        track = _make_track()
        track.add_callout("A", 1, 5)

        track.shift_all_clips(-5.0)

        assert track._data['medias'][0]['start'] == 0


class TestShiftAllClipsEmpty:
    def test_empty_track_is_noop(self):
        track = _make_track()
        track.shift_all_clips(10.0)
        assert track._data['medias'] == []


class TestScaleAllDurations:
    def test_doubles_durations(self):
        track = _make_track()
        track.add_callout("A", 0, 5)
        orig_dur = track._data['medias'][0]['duration']
        orig_mdur = track._data['medias'][0]['mediaDuration']

        track.scale_all_durations(2.0)

        assert track._data['medias'][0]['duration'] == int(orig_dur * 2)
        assert track._data['medias'][0]['mediaDuration'] == int(orig_mdur * 2)

    def test_halves_durations(self):
        track = _make_track()
        track.add_callout("A", 0, 10)
        orig_dur = track._data['medias'][0]['duration']

        track.scale_all_durations(0.5)

        assert track._data['medias'][0]['duration'] == int(orig_dur * 0.5)

    def test_scales_start_times_proportionally(self):
        track = _make_track()
        track.add_callout("A", 3, 5)
        orig_start = track._data['medias'][0]['start']

        track.scale_all_durations(2.0)

        assert track._data["medias"][0]["start"] == int(orig_start * 2.0)  # scaled proportionally


class TestScaleAllDurationsValidation:
    def test_zero_factor_raises(self):
        track = _make_track()
        with pytest.raises(ValueError, match="factor must be > 0"):
            track.scale_all_durations(0)

    def test_negative_factor_raises(self):
        track = _make_track()
        with pytest.raises(ValueError, match="factor must be > 0"):
            track.scale_all_durations(-1.0)


class TestScaleAllDurationsEmpty:
    def test_empty_track_is_noop(self):
        track = _make_track()
        track.scale_all_durations(2.0)
        assert track._data['medias'] == []
