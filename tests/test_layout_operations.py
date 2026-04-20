from __future__ import annotations

import pytest

from camtasia.operations.layout import pack_track, ripple_delete, ripple_insert, snap_to_grid
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

    def test_ripple_insert_clears_transitions(self):
        track = _make_track([
            _clip(1, 0.0, 2.0),
            _clip(2, 3.0, 1.0),
            _clip(3, 5.0, 1.0),
        ])
        track._data['transitions'] = [
            {'leftMedia': 2, 'rightMedia': 3, 'duration': 100},
        ]
        ripple_insert(track, position_seconds=3.0, duration_seconds=2.0)
        assert track._data['transitions'] == []

    def test_ripple_insert_no_shift_keeps_transitions(self):
        track = _make_track([
            _clip(1, 0.0, 2.0),
            _clip(2, 3.0, 1.0),
        ])
        track._data['transitions'] = [
            {'leftMedia': 1, 'rightMedia': 2, 'duration': 100},
        ]
        # Insert after all clips — nothing shifts
        ripple_insert(track, position_seconds=10.0, duration_seconds=2.0)
        assert len(track._data['transitions']) == 1


class TestRippleDelete:
    def test_ripple_delete_closes_gap(self):
        track = _make_track([
            _clip(1, 0.0, 2.0),
            _clip(2, 2.0, 3.0),
            _clip(3, 5.0, 1.0),
        ])
        ripple_delete(track, clip_id=2)
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
        assert track._data['transitions'] == []

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
        assert track._data['transitions'][0]['leftMedia'] == 3


class TestSnapToGrid:
    @pytest.mark.parametrize(
        ('actual_start', 'expected_start'),
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


class TestStringFractionTicks:
    """Verify layout operations handle string-fraction start/duration values."""

    @staticmethod
    def _frac_clip(clip_id: int, start: str, duration: str) -> dict:
        return {'id': clip_id, 'start': start, 'duration': duration}

    def test_pack_track_with_fraction_duration(self):
        track = _make_track([
            self._frac_clip(1, 0, '705600000/2'),
            self._frac_clip(2, '705600000', '705600000/2'),
        ])
        pack_track(track)
        assert track._data['medias'][0]['start'] == 0
        assert track._data['medias'][1]['start'] == 352800000

    def test_ripple_insert_with_fraction_start(self):
        track = _make_track([
            self._frac_clip(1, '705600000/2', '705600000'),
        ])
        ripple_insert(track, position_seconds=0.0, duration_seconds=1.0)
        assert track._data['medias'][0]['start'] == 352800000 + seconds_to_ticks(1.0)

    def test_ripple_delete_with_fraction_values(self):
        track = _make_track([
            self._frac_clip(1, 0, '705600000/2'),
            self._frac_clip(2, '705600000/2', '705600000'),
            self._frac_clip(3, '705600000/2', '705600000'),
        ])
        # Clip 3 starts at 352800000 which is >= 0 + 352800000, so it shifts
        ripple_delete(track, clip_id=1)
        assert len(track._data['medias']) == 2

    def test_snap_to_grid_with_fraction_start(self):
        track = _make_track([
            self._frac_clip(1, '705600000/2', '705600000'),
        ])
        snap_to_grid(track, grid_seconds=1.0)
        # 352800000 ticks = 0.5s; banker's rounding snaps to 0
        assert track._data['medias'][0]['start'] == 0


class TestRippleDeleteDoesNotPropagateUnshiftedClips:
    """Bug 6: ripple_delete must only call _propagate_start_to_unified for shifted clips."""

    def test_unshifted_clip_not_propagated(self):
        """A clip before the deleted clip should not have its start modified."""
        track = _make_track([
            _clip(1, 0.0, 2.0),
            _clip(2, 2.0, 3.0),
            _clip(3, 5.0, 1.0),
        ])
        # Add UnifiedMedia-style nested data to clip 1 to detect unwanted propagation
        track._data['medias'][0]['_type'] = 'UnifiedMedia'
        track._data['medias'][0]['video'] = {
            '_type': 'VMFile', 'start': 999, 'duration': seconds_to_ticks(2.0),
        }
        original_video_start = track._data['medias'][0]['video']['start']

        ripple_delete(track, clip_id=2)

        # Clip 1 was NOT shifted, so its video.start should be untouched
        assert track._data['medias'][0]['video']['start'] == original_video_start


class TestRippleInsertNegativeDuration:
    """Bug 7: ripple_insert must reject negative duration_seconds."""

    def test_negative_duration_raises(self):
        track = _make_track([_clip(1, 0.0, 2.0)])
        with pytest.raises(ValueError, match='duration_seconds must be non-negative'):
            ripple_insert(track, position_seconds=0.0, duration_seconds=-1.0)


    def test_negative_position_raises(self):
        """Bug 7: ripple_insert must reject negative position_seconds."""
        track = _make_track([_clip(1, 0.0, 2.0)])
        with pytest.raises(ValueError, match='position_seconds must be non-negative'):
            ripple_insert(track, position_seconds=-1.0, duration_seconds=1.0)


class TestSnapToGridTransitions:
    """Bug 8: snap_to_grid should only clear transitions if clips actually moved."""

    def test_snap_preserves_transitions_when_already_aligned(self):
        track = _make_track([
            _clip(1, 0.0, 2.0),
            _clip(2, 2.0, 3.0),
        ])
        track._data['transitions'] = [
            {'leftMedia': 1, 'rightMedia': 2, 'duration': 100},
        ]
        snap_to_grid(track, grid_seconds=1.0)
        assert len(track._data['transitions']) == 1

    def test_snap_clears_transitions_when_clips_moved(self):
        track = _make_track([
            _clip(1, 0.0, 2.0),
            _clip(2, 2.3, 3.0),  # not on grid
        ])
        track._data['transitions'] = [
            {'leftMedia': 1, 'rightMedia': 2, 'duration': 100},
        ]
        snap_to_grid(track, grid_seconds=1.0)
        assert track._data['transitions'] == []
