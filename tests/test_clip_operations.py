"""Tests for Track.duplicate_clip() and Track.move_clip()."""
from __future__ import annotations

from typing import Any

import pytest

from camtasia.timeline.track import Track
from camtasia.timing import seconds_to_ticks


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

        moved = next(iter(track.clips))
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
        t = Track({'ident': 'test'}, data)
        t.duplicate_clip(1)
        # The nested clip should have a different ID than the original
        inner_id = data['medias'][1]['tracks'][0]['medias'][0]['id']
        assert inner_id != 2


class TestExtendClip:
    def test_extend_clip_positive(self):
        track = _make_track()
        clip = track.add_callout("Hello", 0, 5)
        original_dur = clip.duration

        track.extend_clip(clip.id, extend_seconds=3.0)

        updated = next(iter(track.clips))
        assert updated.duration == original_dur + seconds_to_ticks(3.0)

    def test_extend_clip_negative(self):
        track = _make_track()
        clip = track.add_callout("Hello", 0, 5)
        original_dur = clip.duration

        track.extend_clip(clip.id, extend_seconds=-2.0)

        updated = next(iter(track.clips))
        assert updated.duration == original_dur + seconds_to_ticks(-2.0)

    def test_extend_clip_too_much_raises(self):
        track = _make_track()
        clip = track.add_callout("Hello", 0, 5)

        with pytest.raises(ValueError, match="non-positive duration"):
            track.extend_clip(clip.id, extend_seconds=-10.0)

    def test_extend_clip_nonexistent_raises(self):
        track = _make_track()

        with pytest.raises(KeyError, match="No clip with id=999"):
            track.extend_clip(999, extend_seconds=1.0)


class TestSwapClips:
    def test_swap_clips(self):
        track = _make_track()
        c1 = track.add_callout("A", 1, 5)
        c2 = track.add_callout("B", 10, 5)
        orig_start_a = c1.start
        orig_start_b = c2.start

        track.swap_clips(c1.id, c2.id)

        swapped_a = track.clips[c1.id]
        swapped_b = track.clips[c2.id]
        assert swapped_a.start == orig_start_b
        assert swapped_b.start == orig_start_a

    def test_swap_clips_nonexistent_raises(self):
        track = _make_track()
        c1 = track.add_callout("A", 0, 5)

        with pytest.raises(KeyError, match="No clip with id=999"):
            track.swap_clips(c1.id, 999)

    def test_swap_clips_second_nonexistent_raises(self):
        data = {'trackIndex': 0, 'medias': [
            {'id': 1, '_type': 'AMFile', 'start': 0, 'duration': 100},
        ]}
        t = Track({'ident': 'test'}, data)
        with pytest.raises(KeyError, match='999'):
            t.swap_clips(1, 999)


class TestInsertClipAt:
    def test_insert_clip_at_shifts_subsequent(self):
        track = _make_track()
        # Place a clip at 5s with duration 3s
        existing = track.add_clip('AMFile', 1, seconds_to_ticks(5), seconds_to_ticks(3))

        # Insert a 2s clip at 4s — should push the existing clip forward by 2s
        inserted = track.insert_clip_at('AMFile', 2, position_seconds=4.0, duration_seconds=2.0)

        assert inserted.start == seconds_to_ticks(4.0)
        assert inserted.duration == seconds_to_ticks(2.0)
        # The existing clip that was at 5s should now be at 7s (shifted by 2s)
        updated = track.clips[existing.id]
        assert updated.start == seconds_to_ticks(7.0)


class TestMergeAdjacentClips:
    def test_merge_adjacent_clips(self):
        track = _make_track()
        c1 = track.add_callout("A", 0, 5)
        c2 = track.add_callout("B", 5, 3)

        merged = track.merge_adjacent_clips(c1.id, c2.id)

        assert merged.duration == seconds_to_ticks(8)
        assert len(list(track.clips)) == 1

    def test_merge_adjacent_clips_nonexistent_raises(self):
        track = _make_track()
        c1 = track.add_callout("A", 0, 5)

        with pytest.raises(KeyError, match="No clip with id=999"):
            track.merge_adjacent_clips(c1.id, 999)
