"""Tests for remove_clip() cascading transition deletion."""
from __future__ import annotations

from typing import Any

from camtasia.timeline.track import Track


def _make_track() -> Track:
    attrs: dict[str, Any] = {"ident": "Track 1"}
    data: dict[str, Any] = {"trackIndex": 0, "medias": []}
    return Track(attrs, data)


class TestRemoveClipCascadesTransitions:
    def test_remove_clip_cascades_transitions(self):
        track = _make_track()
        c1 = track.add_callout("A", 0, 5)
        c2 = track.add_callout("B", 5, 5)
        track.add_fade_through_black(c1, c2, 0.5)

        track.remove_clip(c1.id)

        assert track._data.get('transitions', []) == []

    def test_remove_clip_preserves_unrelated_transitions(self):
        track = _make_track()
        c1 = track.add_callout("A", 0, 5)
        c2 = track.add_callout("B", 5, 5)
        c3 = track.add_callout("C", 10, 5)
        track.add_fade_through_black(c1, c2, 0.5)
        track.add_fade_through_black(c2, c3, 0.5)

        track.remove_clip(c2.id)

        transitions = track._data.get('transitions', [])
        assert len(transitions) == 0

    def test_remove_middle_clip_keeps_outer_transition(self):
        track = _make_track()
        c1 = track.add_callout("A", 0, 5)
        c2 = track.add_callout("B", 5, 5)
        c3 = track.add_callout("C", 10, 5)
        track.add_fade_through_black(c1, c2, 0.5)
        track.add_fade_through_black(c1, c3, 0.5)

        track.remove_clip(c2.id)

        transitions = track._data.get('transitions', [])
        assert len(transitions) == 1
        assert transitions[0]['leftMedia'] == c1.id
        assert transitions[0]['rightMedia'] == c3.id
