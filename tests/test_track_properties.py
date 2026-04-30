"""Tests for Track-level properties: track_height, enabled, matte_mode, ripple_move."""
from __future__ import annotations

from typing import Any

import pytest

from camtasia.timeline.track import Track
from camtasia.timing import seconds_to_ticks


def _make_track(medias: list[dict[str, Any]] | None = None, name: str = 'T', **data_overrides: Any) -> Track:
    """Build a minimal Track from raw dicts."""
    data: dict[str, Any] = {'trackIndex': 0, 'medias': medias or [], 'transitions': []}
    data.update(data_overrides)
    attrs: dict[str, Any] = {'ident': name}
    return Track(attrs, data)


# ---------------------------------------------------------------------------
# track_height
# ---------------------------------------------------------------------------

class TestTrackHeight:
    def test_default_is_zero(self) -> None:
        track = _make_track()
        assert track.track_height == 0

    def test_getter_reads_metadata(self) -> None:
        attrs: dict[str, Any] = {'ident': 'T', 'metadata': {'trackHeight': '150'}}
        track = Track(attrs, {'trackIndex': 0, 'medias': []})
        assert track.track_height == 150

    def test_setter_writes_string(self) -> None:
        track = _make_track()
        track.track_height = 200
        assert track._attributes['metadata']['trackHeight'] == '200'
        assert track.track_height == 200

    def test_roundtrip(self) -> None:
        track = _make_track()
        track.track_height = 75
        assert track.track_height == 75


# ---------------------------------------------------------------------------
# enabled
# ---------------------------------------------------------------------------

class TestEnabled:
    def test_default_is_true(self) -> None:
        track = _make_track()
        assert track.enabled is True

    def test_getter_reads_metadata(self) -> None:
        attrs: dict[str, Any] = {'ident': 'T', 'metadata': {'trackEnabled': 'False'}}
        track = Track(attrs, {'trackIndex': 0, 'medias': []})
        assert track.enabled is False

    def test_setter_writes_string(self) -> None:
        track = _make_track()
        track.enabled = False
        assert track._attributes['metadata']['trackEnabled'] == 'False'
        assert track.enabled is False

    def test_roundtrip_true(self) -> None:
        track = _make_track()
        track.enabled = False
        track.enabled = True
        assert track.enabled is True

    def test_distinct_from_is_locked(self) -> None:
        track = _make_track()
        track.is_locked = True
        track.enabled = False
        assert track.is_locked is True
        assert track.enabled is False


# ---------------------------------------------------------------------------
# matte_mode
# ---------------------------------------------------------------------------

class TestMatteMode:
    def test_default_is_zero(self) -> None:
        track = _make_track()
        assert track.matte_mode == 0

    def test_getter_reads_data(self) -> None:
        track = _make_track(matte=2)
        assert track.matte_mode == 2

    def test_setter_writes_data(self) -> None:
        track = _make_track()
        track.matte_mode = 3
        assert track._data['matte'] == 3
        assert track.matte_mode == 3

    def test_roundtrip(self) -> None:
        track = _make_track()
        track.matte_mode = 1
        assert track.matte_mode == 1
        track.matte_mode = 0
        assert track.matte_mode == 0


# ---------------------------------------------------------------------------
# ripple_move
# ---------------------------------------------------------------------------

class TestRippleMove:
    def test_shifts_target_and_later_clips(self) -> None:
        one_sec = seconds_to_ticks(1.0)
        medias = [
            {'id': 1, '_type': 'VMFile', 'start': 0, 'duration': one_sec},
            {'id': 2, '_type': 'VMFile', 'start': one_sec, 'duration': one_sec},
            {'id': 3, '_type': 'VMFile', 'start': one_sec * 2, 'duration': one_sec},
        ]
        track = _make_track(medias=medias)
        track.ripple_move(2, 2.0)
        # Clip 1 is before target → unchanged
        assert track._data['medias'][0]['start'] == 0
        # Clip 2 (target) shifted forward by 2s
        assert track._data['medias'][1]['start'] == one_sec + seconds_to_ticks(2.0)
        # Clip 3 was at or after target start → also shifted
        assert track._data['medias'][2]['start'] == one_sec * 2 + seconds_to_ticks(2.0)

    def test_clamps_at_zero(self) -> None:
        one_sec = seconds_to_ticks(1.0)
        medias = [
            {'id': 1, '_type': 'VMFile', 'start': one_sec, 'duration': one_sec},
            {'id': 2, '_type': 'VMFile', 'start': one_sec * 2, 'duration': one_sec},
        ]
        track = _make_track(medias=medias)
        track.ripple_move(1, -5.0)
        assert track._data['medias'][0]['start'] == 0
        assert track._data['medias'][1]['start'] == 0

    def test_clears_transitions(self) -> None:
        one_sec = seconds_to_ticks(1.0)
        medias = [
            {'id': 1, '_type': 'VMFile', 'start': 0, 'duration': one_sec},
            {'id': 2, '_type': 'VMFile', 'start': one_sec, 'duration': one_sec},
        ]
        track = _make_track(medias=medias)
        track._data['transitions'] = [{'leftMedia': 1, 'rightMedia': 2, 'duration': 100}]
        track.ripple_move(2, 1.0)
        assert track._data['transitions'] == []

    def test_raises_on_missing_clip(self) -> None:
        track = _make_track(medias=[{'id': 1, '_type': 'VMFile', 'start': 0, 'duration': 100}])
        with pytest.raises(KeyError, match='No clip with id=99'):
            track.ripple_move(99, 1.0)

    def test_negative_shift(self) -> None:
        one_sec = seconds_to_ticks(1.0)
        medias = [
            {'id': 1, '_type': 'VMFile', 'start': 0, 'duration': one_sec},
            {'id': 2, '_type': 'VMFile', 'start': one_sec * 5, 'duration': one_sec},
            {'id': 3, '_type': 'VMFile', 'start': one_sec * 8, 'duration': one_sec},
        ]
        track = _make_track(medias=medias)
        track.ripple_move(2, -2.0)
        assert track._data['medias'][0]['start'] == 0  # before target, unchanged
        assert track._data['medias'][1]['start'] == one_sec * 3  # 5s - 2s = 3s
        assert track._data['medias'][2]['start'] == one_sec * 6  # 8s - 2s = 6s

    def test_propagates_to_unified_media(self) -> None:
        one_sec = seconds_to_ticks(1.0)
        medias: list[dict[str, Any]] = [
            {
                'id': 1, '_type': 'UnifiedMedia', 'start': one_sec,
                'duration': one_sec, 'mediaStart': 0, 'mediaDuration': one_sec,
                'scalar': 1,
                'video': {'_type': 'VMFile', 'id': 2, 'start': one_sec, 'duration': one_sec},
                'audio': {'_type': 'AMFile', 'id': 3, 'start': one_sec, 'duration': one_sec},
            },
        ]
        track = _make_track(medias=medias)
        track.ripple_move(1, 1.0)
        m = track._data['medias'][0]
        assert m['start'] == one_sec * 2
        assert m['video']['start'] == one_sec * 2
        assert m['audio']['start'] == one_sec * 2
