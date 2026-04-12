"""Tests for Track.trim_clip()."""
from __future__ import annotations

from typing import Any

import pytest

from camtasia.timeline.track import Track
from camtasia.timing import seconds_to_ticks


def _make_track() -> Track:
    attrs: dict[str, Any] = {"ident": "Track 1"}
    data: dict[str, Any] = {"trackIndex": 0, "medias": []}
    return Track(attrs, data)


class TestTrimClip:
    def test_trim_start(self):
        track = _make_track()
        clip = track.add_callout("Hello", 1.0, 10.0)
        orig_start = seconds_to_ticks(1.0)
        orig_dur = seconds_to_ticks(10.0)

        track.trim_clip(clip.id, trim_start_seconds=2.0)

        m = track._data['medias'][0]
        assert m['start'] == orig_start + seconds_to_ticks(2.0)
        assert m['duration'] == orig_dur - seconds_to_ticks(2.0)
        assert m['mediaStart'] == seconds_to_ticks(2.0)

    def test_trim_end(self):
        track = _make_track()
        clip = track.add_callout("Hello", 1.0, 10.0)
        orig_start = seconds_to_ticks(1.0)
        orig_dur = seconds_to_ticks(10.0)

        track.trim_clip(clip.id, trim_end_seconds=3.0)

        m = track._data['medias'][0]
        assert m['start'] == orig_start
        assert m['duration'] == orig_dur - seconds_to_ticks(3.0)

    def test_trim_both(self):
        track = _make_track()
        clip = track.add_callout("Hello", 0.0, 10.0)

        track.trim_clip(clip.id, trim_start_seconds=2.0, trim_end_seconds=3.0)

        m = track._data['medias'][0]
        assert m['start'] == seconds_to_ticks(2.0)
        assert m['duration'] == seconds_to_ticks(10.0) - seconds_to_ticks(2.0) - seconds_to_ticks(3.0)
        assert m['mediaStart'] == seconds_to_ticks(2.0)

    def test_trim_too_much_raises(self):
        track = _make_track()
        clip = track.add_callout("Hello", 0.0, 5.0)

        with pytest.raises(ValueError, match="zero or negative duration"):
            track.trim_clip(clip.id, trim_start_seconds=3.0, trim_end_seconds=3.0)

    def test_trim_nonexistent_raises(self):
        track = _make_track()

        with pytest.raises(KeyError, match="No clip with id=999"):
            track.trim_clip(999, trim_start_seconds=1.0)
