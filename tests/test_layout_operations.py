from __future__ import annotations

import pytest

from camtasia.operations.layout import pack_track, ripple_delete, ripple_insert, snap_to_grid
from camtasia.timeline.track import Track
from camtasia.timing import EDIT_RATE, seconds_to_ticks


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


class TestPackTrack:
    def test_pack_track_removes_gaps(self):
        track = _make_track([
            _clip(1, 0.0, 2.0),
            _clip(2, 5.0, 3.0),
            _clip(3, 12.0, 1.0),
        ])
        pack_track(track)
        actual_starts = [m['start'] for m in track._data['medias']]
        expected_starts = [
            seconds_to_ticks(0.0),
            seconds_to_ticks(2.0),
            seconds_to_ticks(5.0),
        ]
        assert actual_starts == expected_starts

    def test_pack_track_with_gap(self):
        track = _make_track([
            _clip(1, 0.0, 2.0),
            _clip(2, 10.0, 3.0),
        ])
        pack_track(track, gap_seconds=0.5)
        actual_starts = [m['start'] for m in track._data['medias']]
        expected_starts = [
            seconds_to_ticks(0.0),
            seconds_to_ticks(2.5),
        ]
        assert actual_starts == expected_starts

    def test_pack_track_sorts_by_start(self):
        track = _make_track([
            _clip(2, 5.0, 1.0),
            _clip(1, 0.0, 2.0),
        ])
        pack_track(track)
        actual_ids = [m['id'] for m in track._data['medias']]
        expected_ids = [1, 2]
        assert actual_ids == expected_ids
        actual_starts = [m['start'] for m in track._data['medias']]
        expected_starts = [seconds_to_ticks(0.0), seconds_to_ticks(2.0)]
        assert actual_starts == expected_starts

    def test_pack_track_clears_transitions(self):
        track = _make_track([
            _clip(1, 0.0, 2.0),
            _clip(2, 5.0, 3.0),
        ])
        track._data['transitions'] = [
            {'leftMedia': 1, 'rightMedia': 2, 'duration': 100},
        ]
        pack_track(track)
        assert track._data['transitions'] == []

    def test_pack_track_empty(self):
        track = _make_track([])
        pack_track(track)  # should not raise
        assert track._data['medias'] == []


class TestRippleInsert:
    def test_ripple_insert_shifts_clips(self):
        track = _make_track([
            _clip(1, 0.0, 2.0),
            _clip(2, 3.0, 1.0),
            _clip(3, 5.0, 1.0),
        ])
        ripple_insert(track, position_seconds=3.0, duration_seconds=2.0)
        actual_starts = [m['start'] for m in track._data['medias']]
        expected_starts = [
            seconds_to_ticks(0.0),
            seconds_to_ticks(5.0),
            seconds_to_ticks(7.0),
        ]
        assert actual_starts == expected_starts

    def test_ripple_insert_at_start(self):
        track = _make_track([
            _clip(1, 0.0, 2.0),
            _clip(2, 3.0, 1.0),
        ])
        ripple_insert(track, position_seconds=0.0, duration_seconds=1.0)
        actual_starts = [m['start'] for m in track._data['medias']]
        expected_starts = [
            seconds_to_ticks(1.0),
            seconds_to_ticks(4.0),
        ]
        assert actual_starts == expected_starts


class TestRippleDelete:
    def test_ripple_delete_closes_gap(self):
        track = _make_track([
            _clip(1, 0.0, 2.0),
            _clip(2, 2.0, 3.0),
            _clip(3, 5.0, 1.0),
        ])
        ripple_delete(track, clip_id=2)
        assert len(track._data['medias']) == 2
        actual_starts = [m['start'] for m in track._data['medias']]
        expected_starts = [
            seconds_to_ticks(0.0),
            seconds_to_ticks(2.0),
        ]
        assert actual_starts == expected_starts

    def test_ripple_delete_nonexistent_raises(self):
        track = _make_track([_clip(1, 0.0, 1.0)])
        with pytest.raises(KeyError, match='No clip with id=999'):
            ripple_delete(track, clip_id=999)


    def test_ripple_delete_cascades_transitions(self):
        track = _make_track([
            _clip(1, 0.0, 2.0),
            _clip(2, 2.0, 3.0),
            _clip(3, 5.0, 1.0),
        ])
        track._data['transitions'] = [
            {'leftMedia': 1, 'rightMedia': 2, 'duration': 100},
            {'leftMedia': 2, 'rightMedia': 3, 'duration': 100},
        ]
        ripple_delete(track, clip_id=2)
        assert len(track._data['transitions']) == 0

    def test_ripple_delete_keeps_unrelated_transitions(self):
        track = _make_track([
            _clip(1, 0.0, 2.0),
            _clip(2, 2.0, 3.0),
            _clip(3, 5.0, 1.0),
            _clip(4, 6.0, 1.0),
        ])
        track._data['transitions'] = [
            {'leftMedia': 1, 'rightMedia': 2, 'duration': 100},
            {'leftMedia': 3, 'rightMedia': 4, 'duration': 100},
        ]
        ripple_delete(track, clip_id=2)
        assert len(track._data['transitions']) == 1
        assert track._data['transitions'][0]['leftMedia'] == 3


class TestSnapToGrid:
    @pytest.mark.parametrize(
        'actual_start, expected_start',
        [
            (0.3, 0.0),
            (0.7, 1.0),
            (1.4, 1.0),
            (2.5, 2.0 if round(2.5) == 2 else 3.0),  # Python banker's rounding
        ],
        ids=['round-down', 'round-up', 'round-down-1s', 'half'],
    )
    def test_snap_to_grid(self, actual_start: float, expected_start: float):
        track = _make_track([_clip(1, actual_start, 1.0)])
        snap_to_grid(track, grid_seconds=1.0)
        actual_result = track._data['medias'][0]['start']
        expected_result = seconds_to_ticks(expected_start)
        assert actual_result == expected_result

    def test_snap_to_grid_invalid_raises(self):
        track = _make_track([_clip(1, 0.0, 1.0)])
        with pytest.raises(ValueError, match='Grid must be positive'):
            snap_to_grid(track, grid_seconds=0)

    def test_snap_to_grid_clamps_negative(self):
        """A clip near time 0 should not snap to a negative start."""
        track = _make_track([{
            'id': 1,
            'start': -seconds_to_ticks(0.3),
            'duration': seconds_to_ticks(1.0),
        }])
        snap_to_grid(track, grid_seconds=1.0)
        assert track._data['medias'][0]['start'] == 0


class TestPackTrackNegativeGap:
    def test_negative_gap_raises(self):
        track = _make_track([_clip(1, 0.0, 2.0)])
        with pytest.raises(ValueError, match='gap_seconds must be non-negative'):
            pack_track(track, gap_seconds=-1.0)
