"""Tests for Track.set_segment_speeds()."""
from __future__ import annotations

import pytest

from camtasia.timeline.track import Track
from fractions import Fraction
from camtasia.timeline.clips.group import Group
from camtasia.timing import seconds_to_ticks, ticks_to_seconds


def _make_track(*medias):
    attrs = {'ident': 'test', 'audioMuted': False, 'videoHidden': False}
    data = {'trackIndex': 0, 'medias': list(medias)}
    return Track(attrs, data)


def _group_clip(clip_id=1, start_s=10.0, dur_s=100.0, source_s=120.0):
    return {
        'id': clip_id, '_type': 'Group',
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
        'id': 1, '_type': 'Group',
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
    group = Group(clip_data)
    group.set_internal_segment_speeds([(0, 50, 50.0), (50, 100, 50.0)])
    media_track = clip_data['tracks'][1]
    assert media_track.get('transitions', []) == []


# ── from test_coverage_phase4b: operations/speed.py tests ──

from fractions import Fraction
from camtasia.operations.speed import rescale_project, set_audio_speed


def _make_project_data_with_unified_audio(scalar="1/2"):
    return {
        "timeline": {
            "sceneTrack": {
                "scenes": [{
                    "csml": {
                        "tracks": [{
                            "medias": [{
                                "_type": "UnifiedMedia",
                                "start": 0,
                                "duration": 1000,
                                "mediaDuration": 1000,
                                "video": {
                                    "_type": "VMFile",
                                    "start": 0,
                                    "duration": 1000,
                                    "mediaDuration": 1000,
                                    "scalar": 1,
                                },
                                "audio": {
                                    "_type": "AMFile",
                                    "start": 0,
                                    "duration": 1000,
                                    "mediaDuration": 2000,
                                    "scalar": scalar,
                                    "metadata": {
                                        "clipSpeedAttribute": {"type": "bool", "value": True}
                                    },
                                },
                            }],
                        }],
                    }
                }]
            },
            "parameters": {"toc": {"keyframes": []}},
        }
    }


class TestSetAudioSpeedUnifiedMedia:
    def test_unified_media_audio_path(self):
        data = _make_project_data_with_unified_audio("1/2")
        factor = set_audio_speed(data, target_speed=1.0)
        assert factor == Fraction(2)
        audio = data["timeline"]["sceneTrack"]["scenes"][0]["csml"]["tracks"][0]["medias"][0]["audio"]
        assert audio["scalar"] == 1
        assert audio["metadata"]["clipSpeedAttribute"]["value"] is False

    def test_set_audio_speed_negative_raises(self):
        data = _make_project_data_with_unified_audio("1/2")
        with pytest.raises(ValueError, match="positive"):
            set_audio_speed(data, target_speed=-1.0)

    def test_set_audio_speed_non_unity_target(self):
        data = _make_project_data_with_unified_audio("1/2")
        factor = set_audio_speed(data, target_speed=0.5)
        audio = data["timeline"]["sceneTrack"]["scenes"][0]["csml"]["tracks"][0]["medias"][0]["audio"]
        assert audio["metadata"]["clipSpeedAttribute"]["value"] is True
        assert audio["scalar"] != 1


class TestProcessClipStitchedUnified:
    def test_stitched_media_with_unified_child(self):
        data = {
            "timeline": {
                "sceneTrack": {
                    "scenes": [{
                        "csml": {
                            "tracks": [{
                                "medias": [{
                                    "_type": "StitchedMedia",
                                    "start": 0,
                                    "duration": 1000,
                                    "mediaStart": 0,
                                    "mediaDuration": 1000,
                                    "medias": [{
                                        "_type": "UnifiedMedia",
                                        "start": 0,
                                        "duration": 500,
                                        "mediaStart": 0,
                                        "mediaDuration": 500,
                                        "video": {
                                            "_type": "VMFile",
                                            "start": 0,
                                            "duration": 500,
                                            "mediaDuration": 500,
                                            "scalar": 1,
                                        },
                                        "audio": {
                                            "_type": "AMFile",
                                            "start": 0,
                                            "duration": 500,
                                            "mediaDuration": 500,
                                            "scalar": 1,
                                        },
                                    }],
                                }],
                            }],
                        }
                    }]
                },
                "parameters": {"toc": {"keyframes": []}},
            }
        }
        rescale_project(data, Fraction(2))
        inner = data["timeline"]["sceneTrack"]["scenes"][0]["csml"]["tracks"][0]["medias"][0]["medias"][0]
        assert inner["video"]["duration"] == 1000
        assert inner["audio"]["duration"] == 1000


class TestOverlapFix:
    def test_overlap_fix_shrinks_duration(self):
        data = {
            "timeline": {
                "sceneTrack": {
                    "scenes": [{
                        "csml": {
                            "tracks": [{
                                "medias": [
                                    {"_type": "AMFile", "start": 0, "duration": 100, "mediaDuration": 100, "scalar": 1},
                                    {"_type": "AMFile", "start": 99, "duration": 100, "mediaDuration": 100, "scalar": 1},
                                ],
                            }],
                        }
                    }]
                },
                "parameters": {"toc": {"keyframes": []}},
            }
        }
        rescale_project(data, Fraction(3, 2))
        medias = data["timeline"]["sceneTrack"]["scenes"][0]["csml"]["tracks"][0]["medias"]
        a_end = medias[0]["start"] + medias[0]["duration"]
        b_start = medias[1]["start"]
        assert a_end <= b_start

    def test_overlap_fix_with_non_unity_scalar(self):
        data = {
            "timeline": {
                "sceneTrack": {
                    "scenes": [{
                        "csml": {
                            "tracks": [{
                                "medias": [
                                    {
                                        "_type": "AMFile",
                                        "start": 0,
                                        "duration": 100,
                                        "mediaDuration": 200,
                                        "scalar": "1/2",
                                        "metadata": {"clipSpeedAttribute": {"type": "bool", "value": True}},
                                    },
                                    {
                                        "_type": "AMFile",
                                        "start": 99,
                                        "duration": 100,
                                        "mediaDuration": 100,
                                        "scalar": 1,
                                    },
                                ],
                            }],
                        }
                    }]
                },
                "parameters": {"toc": {"keyframes": []}},
            }
        }
        rescale_project(data, Fraction(3, 2))
        medias = data["timeline"]["sceneTrack"]["scenes"][0]["csml"]["tracks"][0]["medias"]
        a_end = medias[0]["start"] + medias[0]["duration"]
        b_start = medias[1]["start"]
        assert a_end <= b_start


# ── canvas_width / canvas_height on set_internal_segment_speeds ────


def _group_with_unified_media() -> dict:
    return {
        'id': 1, '_type': 'Group',
        'start': 0,
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
                    'parameters': {'width': 2540, 'height': 1389},
                    'effects': [],
                },
                'start': 0, 'duration': seconds_to_ticks(100.0),
                'mediaStart': 0, 'mediaDuration': seconds_to_ticks(100.0),
                'scalar': 1, 'metadata': {}, 'parameters': {},
                'effects': [], 'attributes': {}, 'animationTracks': {},
            }]},
        ],
    }


def test_canvas_dimensions_set_on_all_segments():
    """When canvas_width/height are given, every ScreenVMFile clip gets them."""
    data = _group_with_unified_media()
    group = Group(data)
    group.set_internal_segment_speeds(
        [(0, 50, 50.0), (50, 100, 50.0)],
        canvas_width=1920,
        canvas_height=1080,
    )
    media_track = data['tracks'][1]
    for clip in media_track['medias']:
        assert clip['_type'] == 'ScreenVMFile'
        assert 'scale0' in clip['parameters']
        assert 'scale1' in clip['parameters']


def test_canvas_dimensions_not_set_when_omitted():
    """Without canvas args, source parameters are preserved as-is."""
    data = _group_with_unified_media()
    group = Group(data)
    group.set_internal_segment_speeds([(0, 100, 100.0)])
    clip = data['tracks'][1]['medias'][0]
    assert clip['parameters']['width'] == 2540
    assert clip['parameters']['height'] == 1389


def test_canvas_width_only():
    """Only canvas_width provided; height stays from source."""
    data = _group_with_unified_media()
    group = Group(data)
    group.set_internal_segment_speeds(
        [(0, 100, 100.0)],
        canvas_width=1920,
    )
    clip = data['tracks'][1]['medias'][0]
    assert 'scale0' in clip['parameters']
    assert clip['parameters']['height'] == 1389


def test_canvas_height_only():
    """Only canvas_height provided; width stays from source."""
    data = _group_with_unified_media()
    group = Group(data)
    group.set_internal_segment_speeds(
        [(0, 100, 100.0)],
        canvas_height=1080,
    )
    clip = data['tracks'][1]['medias'][0]
    assert clip['parameters']['width'] == 2540
    assert 'scale1' in clip['parameters']


def test_retina_to_1080p_normalisation():
    """End-to-end: Retina 2540x1389 recording normalised to 1920x1080 canvas."""
    data = _group_with_unified_media()
    group = Group(data)
    group.set_internal_segment_speeds(
        [(0, 30, 30.0), (30, 70, 20.0), (70, 100, 50.0)],
        canvas_width=1920.0,
        canvas_height=1080.0,
    )
    for clip in data['tracks'][1]['medias']:
        assert 'scale0' in clip['parameters']
        assert 'scale1' in clip['parameters']
