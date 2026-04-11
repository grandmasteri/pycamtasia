"""Tests for Track.clear()."""
from __future__ import annotations

from typing import Any

from camtasia.timeline.track import Track


def _make_track(name: str = "Track 1") -> Track:
    attrs: dict[str, Any] = {"ident": name}
    data: dict[str, Any] = {"trackIndex": 0, "medias": []}
    return Track(attrs, data)


class TestTrackClearRemovesClips:
    def test_clear_removes_all_clips(self):
        track = _make_track()
        track.add_callout("A", 0, 5)
        track.add_callout("B", 5, 5)

        track.clear()

        actual_clips = list(track.clips)
        assert actual_clips == []


class TestTrackClearOnEmptyTrack:
    def test_clear_on_empty_track_is_noop(self):
        track = _make_track()

        track.clear()

        actual_clips = list(track.clips)
        assert actual_clips == []


class TestTrackClearPreservesAttributes:
    def test_clear_preserves_track_name(self):
        expected_name = "My Track"
        track = _make_track(name=expected_name)
        track.add_callout("A", 0, 5)

        track.clear()

        actual_name = track.name
        assert actual_name == expected_name

    def test_clear_preserves_track_index(self):
        track = _make_track()
        expected_index = track.index

        track.add_callout("A", 0, 5)
        track.clear()

        actual_index = track.index
        assert actual_index == expected_index
