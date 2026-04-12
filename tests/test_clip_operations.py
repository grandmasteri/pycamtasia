"""Tests for Track.duplicate_clip() and Track.move_clip()."""
from __future__ import annotations

from typing import Any

import pytest

from camtasia.timeline.track import Track
from camtasia.timing import seconds_to_ticks, ticks_to_seconds


def _make_track() -> Track:
    attrs: dict[str, Any] = {"ident": "Track 1"}
    data: dict[str, Any] = {"trackIndex": 0, "medias": []}
    return Track(attrs, data)


class TestDuplicateClip:
    def test_duplicate_clip_creates_copy(self):
        track = _make_track()
        orig = track.add_callout("Hello", 0, 5)

        dup = track.duplicate_clip(orig.id)

        assert len(list(track.clips)) == 2
        assert dup._data['_type'] == orig._data['_type']

    def test_duplicate_clip_new_id(self):
        track = _make_track()
        orig = track.add_callout("Hello", 0, 5)

        dup = track.duplicate_clip(orig.id)

        assert dup.id != orig.id

    def test_duplicate_clip_positioned_after_original(self):
        track = _make_track()
        orig = track.add_callout("Hello", 1, 5)

        dup = track.duplicate_clip(orig.id)

        expected_start = seconds_to_ticks(1) + seconds_to_ticks(5)
        assert dup.start == expected_start

    def test_duplicate_clip_with_offset(self):
        track = _make_track()
        orig = track.add_callout("Hello", 0, 5)

        dup = track.duplicate_clip(orig.id, offset_seconds=2.0)

        expected_start = seconds_to_ticks(5) + seconds_to_ticks(2)
        assert dup.start == expected_start

    def test_duplicate_clip_nonexistent_raises(self):
        track = _make_track()

        with pytest.raises(KeyError, match="No clip with id=999"):
            track.duplicate_clip(999)


class TestMoveClip:
    def test_move_clip_changes_start(self):
        track = _make_track()
        clip = track.add_callout("Hello", 0, 5)

        track.move_clip(clip.id, 10.0)

        moved = list(track.clips)[0]
        assert moved.start == seconds_to_ticks(10.0)

    def test_move_clip_nonexistent_raises(self):
        track = _make_track()

        with pytest.raises(KeyError, match="No clip with id=999"):
            track.move_clip(999, 5.0)


    def test_move_clip_removes_transitions(self):
        track = _make_track()
        c1 = track.add_callout("A", 0, 5)
        c2 = track.add_callout("B", 5, 5)
        track._data['transitions'] = [
            {'leftMedia': c1.id, 'rightMedia': c2.id, 'duration': 100},
        ]
        track.move_clip(c1.id, 20.0)
        assert track._data['transitions'] == []


class TestDuplicateGroupClip:
    def test_duplicate_group_remaps_nested_ids(self):
        data = {
            'trackIndex': 0,
            'medias': [{
                'id': 1, '_type': 'Group', 'start': 0, 'duration': 100,
                'tracks': [{'medias': [{'id': 2, '_type': 'VMFile', 'start': 0, 'duration': 100}]}],
            }],
        }
        from camtasia.timeline.track import Track
        t = Track({'ident': 'test'}, data)
        actual_clip = t.duplicate_clip(1)
        # The nested clip should have a different ID than the original
        inner_id = data['medias'][1]['tracks'][0]['medias'][0]['id']
        assert inner_id != 2
