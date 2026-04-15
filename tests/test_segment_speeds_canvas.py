"""Tests for canvas_width / canvas_height on set_internal_segment_speeds()."""
from __future__ import annotations

from camtasia.timeline.clips.group import Group
from camtasia.timing import seconds_to_ticks


def _group_with_unified_media() -> dict:
    return {
        'id': 1, '_type': 'Group', 'src': 0,
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
        assert clip['parameters']['width'] == 1920
        assert clip['parameters']['height'] == 1080


def test_canvas_dimensions_not_set_when_omitted():
    """Without canvas args, source parameters are preserved as-is."""
    data = _group_with_unified_media()
    group = Group(data)
    group.set_internal_segment_speeds([(0, 100, 100.0)])
    clip = data['tracks'][1]['medias'][0]
    # Original template had width=2540, which gets deep-copied into video_params
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
    assert clip['parameters']['width'] == 1920
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
    assert clip['parameters']['height'] == 1080


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
        assert clip['parameters']['width'] == 1920.0
        assert clip['parameters']['height'] == 1080.0
