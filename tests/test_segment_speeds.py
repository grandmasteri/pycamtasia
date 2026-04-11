"""Tests for Track.set_segment_speeds()."""
from __future__ import annotations

from camtasia.timeline.track import Track
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
    for p in pieces:
        for t in p._data.get('tracks', []):
            for m in t.get('medias', []):
                if m['_type'] == 'VMFile':
                    assert m['scalar'] != 1  # should be 1/original_scalar


def test_media_start_accumulates():
    track = _make_track(_group_clip())
    pieces = track.set_segment_speeds(1, [(30, 1.0), (40, 2.0), (30, 0.5)])
    assert pieces[0]._data['mediaStart'] == 0
    assert pieces[1]._data['mediaStart'] > 0
    assert pieces[2]._data['mediaStart'] > pieces[1]._data['mediaStart']
