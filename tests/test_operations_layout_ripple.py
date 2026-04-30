from __future__ import annotations

import pytest

from camtasia.operations.layout import (
    ripple_delete_range,
    ripple_extend,
    ripple_move,
    ripple_move_multi,
    snap_to_clip_edge,
)
from camtasia.timeline.track import Track
from camtasia.timing import seconds_to_ticks


def _make_track(medias: list[dict] | None = None) -> Track:
    """Build a Track from raw media dicts."""
    return Track(
        attributes={'ident': 'test'},
        data={'trackIndex': 0, 'medias': medias or []},
    )


def _clip(clip_id: int, start_seconds: float, duration_seconds: float) -> dict:
    return {
        'id': clip_id,
        'start': seconds_to_ticks(start_seconds),
        'duration': seconds_to_ticks(duration_seconds),
    }


class TestRippleExtend:
    def test_extend_pushes_following_clips(self):
        track = _make_track([
            _clip(1, 0.0, 2.0),
            _clip(2, 2.0, 3.0),
            _clip(3, 5.0, 1.0),
        ])
        ripple_extend(track, clip_id=1, extend_seconds=1.0)
        medias = track._data['medias']
        assert medias[0]['duration'] == seconds_to_ticks(3.0)
        assert medias[1]['start'] == seconds_to_ticks(3.0)
        assert medias[2]['start'] == seconds_to_ticks(6.0)

    def test_extend_does_not_move_earlier_clips(self):
        track = _make_track([
            _clip(1, 0.0, 2.0),
            _clip(2, 2.0, 3.0),
            _clip(3, 5.0, 1.0),
        ])
        ripple_extend(track, clip_id=2, extend_seconds=1.0)
        assert track._data['medias'][0]['start'] == seconds_to_ticks(0.0)
        assert track._data['medias'][1]['duration'] == seconds_to_ticks(4.0)
        assert track._data['medias'][2]['start'] == seconds_to_ticks(6.0)

    def test_extend_negative_shrinks_clip(self):
        track = _make_track([
            _clip(1, 0.0, 4.0),
            _clip(2, 4.0, 2.0),
        ])
        ripple_extend(track, clip_id=1, extend_seconds=-1.0)
        assert track._data['medias'][0]['duration'] == seconds_to_ticks(3.0)
        assert track._data['medias'][1]['start'] == seconds_to_ticks(3.0)

    def test_extend_nonexistent_clip_raises(self):
        track = _make_track([_clip(1, 0.0, 2.0)])
        with pytest.raises(KeyError, match='No clip with id=999'):
            ripple_extend(track, clip_id=999, extend_seconds=1.0)

    def test_extend_negative_duration_raises(self):
        track = _make_track([_clip(1, 0.0, 1.0)])
        with pytest.raises(ValueError, match='negative'):
            ripple_extend(track, clip_id=1, extend_seconds=-2.0)

    def test_extend_clears_transitions(self):
        track = _make_track([
            _clip(1, 0.0, 2.0),
            _clip(2, 2.0, 3.0),
        ])
        track._data['transitions'] = [
            {'leftMedia': 1, 'rightMedia': 2, 'duration': 100},
        ]
        ripple_extend(track, clip_id=1, extend_seconds=1.0)
        assert track._data['transitions'] == []


class TestRippleDeleteRange:
    def test_delete_range_removes_fully_contained_clips(self):
        track = _make_track([
            _clip(1, 0.0, 2.0),
            _clip(2, 2.0, 2.0),
            _clip(3, 4.0, 2.0),
            _clip(4, 6.0, 2.0),
        ])
        ripple_delete_range(track, start_seconds=2.0, end_seconds=6.0)
        medias = track._data['medias']
        actual_ids = [m['id'] for m in medias]
        assert actual_ids == [1, 4]
        assert medias[0]['start'] == seconds_to_ticks(0.0)
        assert medias[1]['start'] == seconds_to_ticks(2.0)

    def test_delete_range_trims_clip_starting_before(self):
        track = _make_track([
            _clip(1, 0.0, 3.0),
            _clip(2, 3.0, 2.0),
        ])
        ripple_delete_range(track, start_seconds=2.0, end_seconds=3.0)
        medias = track._data['medias']
        assert medias[0]['duration'] == seconds_to_ticks(2.0)
        assert medias[1]['start'] == seconds_to_ticks(2.0)

    def test_delete_range_trims_clip_ending_after(self):
        track = _make_track([
            _clip(1, 0.0, 1.0),
            _clip(2, 1.0, 4.0),
        ])
        # Range [1.0, 3.0) — clip 2 starts at 1.0, ends at 5.0
        ripple_delete_range(track, start_seconds=1.0, end_seconds=3.0)
        medias = track._data['medias']
        assert len(medias) == 2
        # Clip 2 was trimmed: lost 2s from start, now starts at range_start=1.0
        assert medias[1]['start'] == seconds_to_ticks(1.0)
        assert medias[1]['duration'] == seconds_to_ticks(2.0)

    def test_delete_range_clip_spanning_entire_range(self):
        track = _make_track([_clip(1, 0.0, 10.0)])
        ripple_delete_range(track, start_seconds=2.0, end_seconds=5.0)
        medias = track._data['medias']
        assert len(medias) == 1
        assert medias[0]['duration'] == seconds_to_ticks(7.0)

    def test_delete_range_invalid_raises(self):
        track = _make_track([_clip(1, 0.0, 2.0)])
        with pytest.raises(ValueError, match='start_seconds must be non-negative'):
            ripple_delete_range(track, start_seconds=-1.0, end_seconds=1.0)
        with pytest.raises(ValueError, match='end_seconds must be greater'):
            ripple_delete_range(track, start_seconds=3.0, end_seconds=2.0)
        with pytest.raises(ValueError, match='end_seconds must be greater'):
            ripple_delete_range(track, start_seconds=2.0, end_seconds=2.0)

    def test_delete_range_removes_transitions_for_deleted_clips(self):
        track = _make_track([
            _clip(1, 0.0, 2.0),
            _clip(2, 2.0, 2.0),
            _clip(3, 4.0, 2.0),
        ])
        track._data['transitions'] = [
            {'leftMedia': 1, 'rightMedia': 2, 'duration': 100},
            {'leftMedia': 2, 'rightMedia': 3, 'duration': 100},
        ]
        ripple_delete_range(track, start_seconds=2.0, end_seconds=4.0)
        assert track._data['transitions'] == []


class TestRippleMove:
    def test_move_shifts_clip_and_following(self):
        track = _make_track([
            _clip(1, 0.0, 2.0),
            _clip(2, 2.0, 2.0),
            _clip(3, 4.0, 2.0),
        ])
        ripple_move(track, clip_id=2, delta_seconds=1.0)
        medias = track._data['medias']
        assert medias[0]['start'] == seconds_to_ticks(0.0)
        assert medias[1]['start'] == seconds_to_ticks(3.0)
        assert medias[2]['start'] == seconds_to_ticks(5.0)

    def test_move_negative_shifts_left(self):
        track = _make_track([
            _clip(1, 2.0, 2.0),
            _clip(2, 4.0, 2.0),
        ])
        ripple_move(track, clip_id=1, delta_seconds=-1.0)
        medias = track._data['medias']
        assert medias[0]['start'] == seconds_to_ticks(1.0)
        assert medias[1]['start'] == seconds_to_ticks(3.0)

    def test_move_nonexistent_clip_raises(self):
        track = _make_track([_clip(1, 0.0, 2.0)])
        with pytest.raises(KeyError, match='No clip with id=999'):
            ripple_move(track, clip_id=999, delta_seconds=1.0)

    def test_move_negative_start_raises(self):
        track = _make_track([_clip(1, 0.0, 2.0)])
        with pytest.raises(ValueError, match='negative start time'):
            ripple_move(track, clip_id=1, delta_seconds=-1.0)

    def test_move_clears_transitions(self):
        track = _make_track([
            _clip(1, 0.0, 2.0),
            _clip(2, 2.0, 2.0),
        ])
        track._data['transitions'] = [
            {'leftMedia': 1, 'rightMedia': 2, 'duration': 100},
        ]
        ripple_move(track, clip_id=2, delta_seconds=1.0)
        assert track._data['transitions'] == []


class TestRippleMoveMulti:
    def test_multi_track_move(self):
        track_a = _make_track([
            _clip(1, 0.0, 2.0),
            _clip(2, 2.0, 2.0),
        ])
        track_b = _make_track([
            _clip(3, 0.0, 3.0),
            _clip(4, 3.0, 1.0),
        ])
        ripple_move_multi(
            tracks=[track_a, track_b],
            clip_ids_per_track=[[2], [4]],
            delta_seconds=1.0,
        )
        assert track_a._data['medias'][0]['start'] == seconds_to_ticks(0.0)
        assert track_a._data['medias'][1]['start'] == seconds_to_ticks(3.0)
        assert track_b._data['medias'][0]['start'] == seconds_to_ticks(0.0)
        assert track_b._data['medias'][1]['start'] == seconds_to_ticks(4.0)

    def test_mismatched_lengths_raises(self):
        track = _make_track([_clip(1, 0.0, 2.0)])
        with pytest.raises(ValueError, match='same length'):
            ripple_move_multi(
                tracks=[track],
                clip_ids_per_track=[[1], [2]],
                delta_seconds=1.0,
            )

    def test_multi_track_nonexistent_clip_raises(self):
        track = _make_track([_clip(1, 0.0, 2.0)])
        with pytest.raises(KeyError, match='No clip with id=999'):
            ripple_move_multi(
                tracks=[track],
                clip_ids_per_track=[[999]],
                delta_seconds=1.0,
            )


class TestSnapToClipEdge:
    def test_snap_start_to_previous_end(self):
        # Clip 2 starts at 2.02s, clip 1 ends at 2.0s — within 0.05s tolerance
        track = _make_track([
            _clip(1, 0.0, 2.0),
            _clip(2, 2.02, 3.0),
        ])
        snap_to_clip_edge(track, tolerance_seconds=0.05)
        medias = track._data['medias']
        assert medias[1]['start'] == seconds_to_ticks(2.0)

    def test_snap_end_to_next_start(self):
        # Clip 1 ends at 1.98s (start=0, dur=1.98), clip 2 starts at 2.0s
        track = _make_track([
            _clip(1, 0.0, 1.98),
            _clip(2, 2.0, 3.0),
        ])
        snap_to_clip_edge(track, tolerance_seconds=0.05)
        medias = track._data['medias']
        # Clip 1's end (1.98) should snap to clip 2's start (2.0)
        assert medias[0]['duration'] == seconds_to_ticks(2.0)

    def test_no_snap_outside_tolerance(self):
        track = _make_track([
            _clip(1, 0.0, 2.0),
            _clip(2, 2.1, 3.0),
        ])
        original_start = track._data['medias'][1]['start']
        snap_to_clip_edge(track, tolerance_seconds=0.05)
        assert track._data['medias'][1]['start'] == original_start

    def test_single_clip_no_op(self):
        track = _make_track([_clip(1, 0.0, 2.0)])
        snap_to_clip_edge(track)  # should not raise
        assert track._data['medias'][0]['start'] == seconds_to_ticks(0.0)

    def test_negative_tolerance_raises(self):
        track = _make_track([_clip(1, 0.0, 2.0)])
        with pytest.raises(ValueError, match='tolerance_seconds must be non-negative'):
            snap_to_clip_edge(track, tolerance_seconds=-0.01)

    def test_snap_clears_transitions_when_shifted(self):
        track = _make_track([
            _clip(1, 0.0, 2.0),
            _clip(2, 2.02, 3.0),
        ])
        track._data['transitions'] = [
            {'leftMedia': 1, 'rightMedia': 2, 'duration': 100},
        ]
        snap_to_clip_edge(track, tolerance_seconds=0.05)
        assert track._data['transitions'] == []

    def test_snap_preserves_transitions_when_no_shift(self):
        track = _make_track([
            _clip(1, 0.0, 2.0),
            _clip(2, 2.0, 3.0),
        ])
        track._data['transitions'] = [
            {'leftMedia': 1, 'rightMedia': 2, 'duration': 100},
        ]
        snap_to_clip_edge(track, tolerance_seconds=0.05)
        assert len(track._data['transitions']) == 1
