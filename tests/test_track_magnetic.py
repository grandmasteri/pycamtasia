"""Tests for magnetic track behavior — auto-pack, ripple-insert, re-pack on move."""
from __future__ import annotations

from camtasia.operations.layout import pack_track
from camtasia.timeline.track import Track
from camtasia.timing import seconds_to_ticks


def _make_track(
    medias: list[dict] | None = None,
    *,
    magnetic: bool = False,
) -> Track:
    attrs: dict = {'ident': 'test', 'magnetic': magnetic}
    data: dict = {
        'trackIndex': 0,
        'medias': medias or [],
        'transitions': [],
        'magnetic': magnetic,
    }
    return Track(attributes=attrs, data=data)


def _clip(clip_id: int, start_seconds: float, duration_seconds: float, **kw) -> dict:
    d = {
        'id': clip_id,
        '_type': kw.get('_type', 'AMFile'),
        'src': kw.get('src', 1),
        'start': seconds_to_ticks(start_seconds),
        'duration': seconds_to_ticks(duration_seconds),
        'mediaStart': 0,
        'mediaDuration': seconds_to_ticks(duration_seconds),
        'scalar': 1,
        'metadata': {},
        'animationTracks': {},
        'parameters': {},
        'effects': [],
    }
    d.update(kw)
    return d


class TestMagneticSetterAutopack:
    """Setting magnetic=True should close existing gaps."""

    def test_setting_magnetic_true_packs_track(self):
        track = _make_track([
            _clip(1, 0.0, 2.0),
            _clip(2, 5.0, 3.0),  # gap of 3s
        ])
        track.magnetic = True
        medias = track._data['medias']
        assert medias[0]['start'] == 0
        assert medias[1]['start'] == seconds_to_ticks(2.0)

    def test_setting_magnetic_false_does_not_pack(self):
        track = _make_track([
            _clip(1, 0.0, 2.0),
            _clip(2, 5.0, 3.0),
        ], magnetic=True)
        # Reset to non-magnetic — should not re-pack
        track._data['medias'][1]['start'] = seconds_to_ticks(5.0)
        track.magnetic = False
        assert track._data['medias'][1]['start'] == seconds_to_ticks(5.0)

    def test_magnetic_setter_on_empty_track(self):
        track = _make_track([])
        track.magnetic = True  # should not raise
        assert track.magnetic is True


class TestMagneticAddClip:
    """add_clip on a magnetic track should ripple-insert."""

    def test_add_clip_between_existing_clips_ripples(self):
        track = _make_track([
            _clip(1, 0.0, 2.0),
            _clip(2, 2.0, 3.0),
        ], magnetic=True)
        # Insert a 1s clip at t=1s — should push clip 2 forward by 1s
        track.add_clip('AMFile', 1, seconds_to_ticks(1.0), seconds_to_ticks(1.0))
        medias = sorted(track._data['medias'], key=lambda m: m['start'])
        # Clip 1 at 0, new clip at 1s, clip 2 pushed to 3s
        assert medias[0]['start'] == 0
        assert medias[0]['id'] == 1
        assert medias[1]['start'] == seconds_to_ticks(1.0)
        assert medias[2]['start'] == seconds_to_ticks(3.0)
        assert medias[2]['id'] == 2

    def test_add_clip_at_end_no_ripple_needed(self):
        track = _make_track([
            _clip(1, 0.0, 2.0),
        ], magnetic=True)
        track.add_clip('AMFile', 1, seconds_to_ticks(2.0), seconds_to_ticks(1.0))
        medias = sorted(track._data['medias'], key=lambda m: m['start'])
        assert medias[0]['start'] == 0
        assert medias[1]['start'] == seconds_to_ticks(2.0)

    def test_add_clip_non_magnetic_no_ripple(self):
        track = _make_track([
            _clip(1, 0.0, 2.0),
            _clip(2, 2.0, 3.0),
        ])
        track.add_clip('AMFile', 1, seconds_to_ticks(1.0), seconds_to_ticks(1.0))
        # Clip 2 should NOT have moved
        clip2 = next(m for m in track._data['medias'] if m['id'] == 2)
        assert clip2['start'] == seconds_to_ticks(2.0)


class TestMagneticMoveClip:
    """move_clip on a magnetic track should re-pack."""

    def test_move_clip_repacks_on_magnetic(self):
        track = _make_track([
            _clip(1, 0.0, 2.0),
            _clip(2, 2.0, 3.0),
            _clip(3, 5.0, 1.0),
        ], magnetic=True)
        # Move clip 2 to t=10s — magnetic should re-pack
        track.move_clip(2, 10.0)
        medias = sorted(track._data['medias'], key=lambda m: m['start'])
        # After re-pack: clips packed end-to-end starting at 0
        assert medias[0]['start'] == 0
        assert medias[1]['start'] == medias[0]['duration']
        assert medias[2]['start'] == medias[0]['duration'] + medias[1]['duration']

    def test_move_clip_non_magnetic_leaves_gaps(self):
        track = _make_track([
            _clip(1, 0.0, 2.0),
            _clip(2, 2.0, 3.0),
        ])
        track.move_clip(2, 10.0)
        assert track._data['medias'][1]['start'] == seconds_to_ticks(10.0)


class TestPackTrackPreserveGroups:
    """pack_track with preserve_groups=True keeps Group positions."""

    def test_groups_keep_position(self):
        track = _make_track([
            _clip(1, 0.0, 2.0),
            _clip(2, 5.0, 1.0, _type='Group'),
            _clip(3, 10.0, 2.0),
        ])
        pack_track(track, preserve_groups=True)
        medias = track._data['medias']
        # Clip 1 packed to 0
        assert medias[0]['start'] == 0
        # Group stays at 5s
        assert medias[1]['start'] == seconds_to_ticks(5.0)
        # Clip 3 packed after group ends (5+1=6s)
        assert medias[2]['start'] == seconds_to_ticks(6.0)

    def test_no_groups_packs_normally(self):
        track = _make_track([
            _clip(1, 0.0, 2.0),
            _clip(2, 5.0, 3.0),
        ])
        pack_track(track, preserve_groups=True)
        assert track._data['medias'][1]['start'] == seconds_to_ticks(2.0)

    def test_preserve_groups_false_moves_groups(self):
        track = _make_track([
            _clip(1, 0.0, 2.0),
            _clip(2, 5.0, 1.0, _type='Group'),
        ])
        pack_track(track, preserve_groups=False)
        assert track._data['medias'][1]['start'] == seconds_to_ticks(2.0)
