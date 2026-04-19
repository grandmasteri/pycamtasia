"""Tests for Track.set_segment_speeds()."""
from __future__ import annotations

from camtasia.timeline.track import Track
from fractions import Fraction
from camtasia.timing import seconds_to_ticks, ticks_to_seconds


def _make_track(*medias):
    attrs = {'ident': 'test', 'audioMuted': False, 'videoHidden': False}
    data = {'trackIndex': 0, 'medias': list(medias)}
    return Track(attrs, data)


def _group_clip(clip_id=1, start_s=10.0, dur_s=100.0, source_s=120.0):
    return {
        'id': clip_id, '_type': 'Group', 'src': 0,
        'start': seconds_to_ticks(start_s),
        'duration': seconds_to_ticks(dur_s),
        'mediaStart': 0,
        'mediaDuration': seconds_to_ticks(source_s),
        'scalar': 1,
        'metadata': {}, 'parameters': {}, 'effects': [],
        'attributes': {'ident': ''}, 'animationTracks': {},
        'tracks': [
            {'medias': [{
                'id': 10, '_type': 'VMFile', 'src': 1,
                'start': 0, 'duration': seconds_to_ticks(dur_s),
                'mediaStart': 0, 'mediaDuration': seconds_to_ticks(dur_s),
                'scalar': 1, 'metadata': {}, 'parameters': {},
                'effects': [], 'attributes': {}, 'animationTracks': {},
            }]},
            {'medias': [{
                'id': 11, '_type': 'UnifiedMedia', 'src': 1,
                'start': 0, 'duration': seconds_to_ticks(source_s),
                'mediaStart': 0, 'mediaDuration': seconds_to_ticks(source_s),
                'scalar': 1, 'metadata': {}, 'parameters': {},
                'effects': [], 'attributes': {}, 'animationTracks': {},
            }]},
        ],
    }


def test_creates_correct_count():
    track = _make_track(_group_clip())
    pieces = track.set_segment_speeds(1, [(30, 1.0), (40, 2.0), (30, 0.5)])
    assert [type(p).__name__ for p in pieces] == ['Group', 'Group', 'Group']


def test_durations_match_requested():
    track = _make_track(_group_clip())
    pieces = track.set_segment_speeds(1, [(30, 1.0), (40, 2.0), (30, 0.5)])
    for piece, (dur, _) in zip(pieces, [(30, 1.0), (40, 2.0), (30, 0.5)]):
        assert abs(ticks_to_seconds(piece.duration) - dur) < 0.01


def test_clip_speed_attribute_set():
    track = _make_track(_group_clip())
    pieces = track.set_segment_speeds(1, [(50, 1.5), (50, 0.8)])
    for p in pieces:
        assert p._data['metadata']['clipSpeedAttribute']['value'] is True


def test_vmfile_scalar_compensated():
    track = _make_track(_group_clip())
    pieces = track.set_segment_speeds(1, [(50, 1.0), (50, 2.0)])
    # original_scalar = duration/mediaDuration = 100/120 = 5/6
    # vmfile_scalar = 1/original_scalar = 6/5
    expected_vmfile_scalar = Fraction(6, 5)
    for p in pieces:
        for t in p._data.get('tracks', []):
            for m in t.get('medias', []):
                if m['_type'] == 'VMFile':
                    assert Fraction(str(m['scalar'])) == expected_vmfile_scalar


def test_media_start_accumulates():
    track = _make_track(_group_clip())
    pieces = track.set_segment_speeds(1, [(30, 1.0), (40, 2.0), (30, 0.5)])
    assert pieces[0]._data['mediaStart'] == 0
    # Piece 0: 30s at 1.0x speed, original_scalar = 5/6
    # advance = 30s_ticks * (original_scalar / seg_scalar)
    # seg_scalar_0 = (5/6) / 1 = 5/6, so advance = 30s_ticks * 1 = 30s_ticks
    ms1 = pieces[1]._data['mediaStart']
    ms2 = pieces[2]._data['mediaStart']
    assert ms1 == seconds_to_ticks(30.0)
    # Piece 1: 40s at 2.0x, seg_scalar = (5/6)/2 = 5/12
    # advance = 40s_ticks * ((5/6) / (5/12)) = 40s_ticks * 2 = 80s_ticks
    assert ms2 == seconds_to_ticks(30.0) + seconds_to_ticks(80.0)


def test_set_internal_segment_speeds_clears_transitions():
    """Internal transitions must be cleared when segment speeds are applied."""
    clip_data = {
        'id': 1, '_type': 'Group', 'src': 0,
        'start': seconds_to_ticks(0.0),
        'duration': seconds_to_ticks(100.0),
        'mediaStart': 0,
        'mediaDuration': seconds_to_ticks(100.0),
        'scalar': 1,
        'metadata': {}, 'parameters': {}, 'effects': [],
        'attributes': {'ident': ''}, 'animationTracks': {},
        'tracks': [
            {'medias': [{
                'id': 10, '_type': 'VMFile', 'src': 1,
                'start': 0, 'duration': seconds_to_ticks(100.0),
                'mediaStart': 0, 'mediaDuration': seconds_to_ticks(100.0),
                'scalar': 1, 'metadata': {}, 'parameters': {},
                'effects': [], 'attributes': {}, 'animationTracks': {},
            }]},
            {'medias': [{
                'id': 11, '_type': 'UnifiedMedia',
                'video': {
                    'src': 1,
                    'attributes': {'ident': 'recording'},
                    'parameters': {},
                    'effects': [],
                },
                'start': 0, 'duration': seconds_to_ticks(100.0),
                'mediaStart': 0, 'mediaDuration': seconds_to_ticks(100.0),
                'scalar': 1, 'metadata': {}, 'parameters': {},
                'effects': [], 'attributes': {}, 'animationTracks': {},
            }], 'transitions': [
                {'leftMedia': 11, 'rightMedia': 12, 'duration': 100},
            ]},
        ],
    }
    from camtasia.timeline.clips.group import Group
    group = Group(clip_data)
    group.set_internal_segment_speeds([(0, 50, 50.0), (50, 100, 50.0)])
    media_track = clip_data['tracks'][1]
    assert media_track.get('transitions', []) == []
