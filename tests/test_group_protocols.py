"""Tests for GroupTrack container protocols and Group.set_internal_segment_speeds auto-id."""
from __future__ import annotations

from camtasia.timeline.clips.group import Group


def _make_group_data(media_ids=(1, 2, 3)):
    """Build minimal Group data with one track containing UnifiedMedia clips."""
    medias = [
        {
            'id': mid,
            '_type': 'UnifiedMedia',
            'start': 0,
            'duration': 100,
            'mediaStart': 0,
            'mediaDuration': 100,
            'video': {
                'src': 42,
                'attributes': {'ident': 'rec'},
                'parameters': {},
                'effects': [],
            },
        }
        for mid in media_ids
    ]
    return {
        '_type': 'IMCGroup',
        'id': 99,
        'start': 0,
        'duration': 300,
        'mediaDuration': 300.0,
        'scalar': 1,
        'src': 42,
        'trackNumber': 0,
        'attributes': {'ident': 'Group'},
        'parameters': {},
        'tracks': [{'trackIndex': 0, 'medias': medias, 'parameters': {}}],
    }


def test_set_internal_segment_speeds_auto_id():
    data = _make_group_data(media_ids=(5, 20, 15))
    group = Group(data)
    group.set_internal_segment_speeds([(0, 1, 1), (1, 2, 2)])
    medias = data['tracks'][0]['medias']
    # Auto-detected: max existing id was 20, so first new id should be 21
    assert medias[0]['id'] == 21
    assert medias[1]['id'] == 22


def test_set_internal_segment_speeds_explicit_id():
    data = _make_group_data()
    group = Group(data)
    group.set_internal_segment_speeds([(0, 1, 1)], next_id=500)
    medias = data['tracks'][0]['medias']
    assert medias[0]['id'] == 500
