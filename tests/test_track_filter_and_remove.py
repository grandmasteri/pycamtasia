"""Tests for Track.filter_and_remove() and Track.keep_only()."""
from __future__ import annotations

from typing import Any

from camtasia.timeline.track import Track


def _make_track() -> Track:
    attrs: dict[str, Any] = {"ident": "Track 1"}
    data: dict[str, Any] = {"trackIndex": 0, "medias": [], "transitions": []}
    return Track(attrs, data)


class TestFilterAndRemove:
    def test_removes_matching_clips(self):
        track = _make_track()
        track.add_callout("A", 0, 5)
        track.add_callout("B", 5, 5)
        track.add_video(1, 10, 5)

        removed = track.filter_and_remove(lambda c: c.clip_type == "Callout")

        assert removed == 2
        assert len(track) == 1
        assert next(iter(track.clips)).clip_type == "VMFile"

    def test_returns_zero_when_none_match(self):
        track = _make_track()
        track.add_callout("A", 0, 5)

        removed = track.filter_and_remove(lambda c: c.clip_type == "VMFile")

        assert removed == 0
        assert len(track) == 1

    def test_removes_all_when_all_match(self):
        track = _make_track()
        track.add_callout("A", 0, 5)
        track.add_callout("B", 5, 5)

        removed = track.filter_and_remove(lambda _: True)

        assert removed == 2
        assert len(track) == 0

    def test_on_empty_track(self):
        track = _make_track()

        removed = track.filter_and_remove(lambda _: True)

        assert removed == 0

    def test_also_cleans_transitions(self):
        track = _make_track()
        c1 = track.add_callout("A", 0, 5)
        c2 = track.add_callout("B", 5, 5)
        track.add_fade_through_black(c1, c2, 0.5)

        track.filter_and_remove(lambda c: c.id == c2.id)

        assert len(track._data.get("transitions", [])) == 0


class TestKeepOnly:
    def test_keeps_matching_removes_rest(self):
        track = _make_track()
        track.add_callout("A", 0, 5)
        track.add_video(1, 5, 5)
        track.add_callout("B", 10, 5)

        removed = track.keep_only(lambda c: c.clip_type == "Callout")

        assert removed == 1
        assert len(track) == 2
        assert all(c.clip_type == "Callout" for c in track.clips)

    def test_returns_zero_when_all_kept(self):
        track = _make_track()
        track.add_callout("A", 0, 5)

        removed = track.keep_only(lambda _: True)

        assert removed == 0
        assert len(track) == 1

    def test_removes_all_when_none_match(self):
        track = _make_track()
        track.add_callout("A", 0, 5)
        track.add_callout("B", 5, 5)

        removed = track.keep_only(lambda _: False)

        assert removed == 2
        assert len(track) == 0

    def test_on_empty_track(self):
        track = _make_track()

        removed = track.keep_only(lambda _: True)

        assert removed == 0
