"""Tests for Project-accepting wrappers in operations.speed and operations.sync."""
from __future__ import annotations

from fractions import Fraction

from camtasia.operations.speed import rescale, normalize_audio_speed
from camtasia.operations.sync import SyncSegment, apply_sync
from camtasia.timeline.clips.group import Group
from camtasia.timing import EDIT_RATE, seconds_to_ticks, ticks_to_seconds


def test_rescale_doubles_timing(project):
    """rescale(project, 2) should double all clip durations."""
    # Add a clip so there's something to scale
    track_data = project._data['timeline']['sceneTrack']['scenes'][0]['csml']['tracks'][0]
    clip = {
        '_type': 'VMFile', 'id': 99, 'src': 0,
        'start': seconds_to_ticks(1.0),
        'duration': seconds_to_ticks(5.0),
        'mediaStart': 0, 'mediaDuration': seconds_to_ticks(5.0),
        'scalar': 1, 'metadata': {}, 'parameters': {},
        'effects': [], 'attributes': {}, 'animationTracks': {},
    }
    track_data['medias'].append(clip)

    original_start = clip['start']
    original_dur = clip['duration']

    rescale(project, 2)

    assert clip['start'] == original_start * 2
    assert clip['duration'] == original_dur * 2


def test_normalize_audio_speed(project):
    """normalize_audio_speed returns the factor and adjusts the project."""
    track_data = project._data['timeline']['sceneTrack']['scenes'][0]['csml']['tracks'][0]
    # Insert a speed-changed audio clip (scalar 51/101 ≈ sped up)
    clip = {
        '_type': 'AMFile', 'id': 50, 'src': 0,
        'start': 0,
        'duration': seconds_to_ticks(10.0),
        'mediaStart': 0, 'mediaDuration': seconds_to_ticks(10.0),
        'scalar': '51/101',
        'metadata': {'clipSpeedAttribute': {'type': 'bool', 'value': True}},
        'parameters': {}, 'effects': [], 'attributes': {}, 'animationTracks': {},
    }
    track_data['medias'].append(clip)

    factor = normalize_audio_speed(project, target_speed=1.0)

    assert isinstance(factor, Fraction)
    assert factor != 0


def _make_group_data(dur_s=60.0, source_s=60.0):
    """Build a minimal Group dict with a UnifiedMedia on its internal track."""
    return {
        'id': 1, '_type': 'Group', 'src': 0,
        'start': 0,
        'duration': seconds_to_ticks(dur_s),
        'mediaStart': 0,
        'mediaDuration': seconds_to_ticks(source_s),
        'scalar': 1,
        'metadata': {}, 'parameters': {}, 'effects': [],
        'attributes': {'ident': 'rec'}, 'animationTracks': {},
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
                'effects': [], 'attributes': {'ident': 'rec'},
                'animationTracks': {},
                'video': {
                    'id': 12, '_type': 'ScreenVMFile', 'src': 1,
                    'start': 0, 'duration': seconds_to_ticks(source_s),
                    'mediaStart': 0, 'mediaDuration': seconds_to_ticks(source_s),
                    'scalar': 1, 'metadata': {}, 'parameters': {},
                    'effects': [], 'attributes': {'ident': 'rec'},
                    'animationTracks': {},
                },
                'audio': {
                    'id': 13, '_type': 'AMFile', 'src': 1,
                    'start': 0, 'duration': seconds_to_ticks(source_s),
                    'mediaStart': 0, 'mediaDuration': seconds_to_ticks(source_s),
                    'scalar': 1, 'metadata': {}, 'parameters': {},
                    'effects': [], 'attributes': {},
                    'animationTracks': {},
                },
            }]},
        ],
    }


def test_apply_sync():
    """apply_sync converts SyncSegments and calls set_internal_segment_speeds."""
    group = Group(_make_group_data(dur_s=60.0, source_s=60.0))

    segments = [
        SyncSegment(
            video_start_ticks=0,
            video_end_ticks=seconds_to_ticks(20.0),
            audio_start_seconds=0.0,
            audio_end_seconds=18.0,
            scalar=Fraction(20, 18),
        ),
        SyncSegment(
            video_start_ticks=seconds_to_ticks(20.0),
            video_end_ticks=seconds_to_ticks(60.0),
            audio_start_seconds=18.0,
            audio_end_seconds=55.0,
            scalar=Fraction(40, 37),
        ),
    ]

    apply_sync(group, segments)

    # Internal track should now have 2 ScreenVMFile clips
    internal_medias = group._data['tracks'][1]['medias']
    assert [m['_type'] for m in internal_medias] == ['ScreenVMFile', 'ScreenVMFile']

    # First clip: source 0-18s, timeline duration 20s
    first = internal_medias[0]
    assert abs(ticks_to_seconds(first['duration']) - 20.0) < 0.01
    assert abs(ticks_to_seconds(first['mediaStart'])) < 0.01
    assert abs(ticks_to_seconds(first['mediaDuration']) - 18.0) < 0.01

    # Second clip: source 18-55s, timeline duration 40s
    second = internal_medias[1]
    assert abs(ticks_to_seconds(second['duration']) - 40.0) < 0.01
    assert abs(ticks_to_seconds(second['mediaStart']) - 18.0) < 0.01
    assert abs(ticks_to_seconds(second['mediaDuration']) - 37.0) < 0.01
