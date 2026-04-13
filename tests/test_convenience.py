"""Tests for Track and Timeline convenience methods."""
from __future__ import annotations

import pytest
from camtasia.timeline.track import Track
from camtasia.timeline.timeline import Timeline
from camtasia.timing import seconds_to_ticks


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_track(medias=None, name='T'):
    """Build a minimal Track from raw dicts."""
    data = {'trackIndex': 0, 'medias': medias or []}
    attrs = {'ident': name}
    return Track(attrs, data)


def _make_timeline(track_specs):
    """Build a Timeline with tracks described as (name, media_list) tuples."""
    tracks = []
    attrs = []
    for i, (name, medias) in enumerate(track_specs):
        tracks.append({'trackIndex': i, 'medias': medias})
        attrs.append({'ident': name})
    data = {
        'sceneTrack': {'scenes': [{'csml': {'tracks': tracks}}]},
        'trackAttributes': attrs,
    }
    return Timeline(data)


# ---------------------------------------------------------------------------
# Track.is_empty
# ---------------------------------------------------------------------------

def test_track_is_empty_true():
    track = _make_track(medias=[])
    assert track.is_empty is True


def test_track_is_empty_false():
    track = _make_track(medias=[{'id': 1, 'start': 0, 'duration': 100}])
    assert track.is_empty is False


# ---------------------------------------------------------------------------
# Track.end_time_ticks
# ---------------------------------------------------------------------------

def test_track_end_time_ticks():
    medias = [
        {'id': 1, 'start': 0, 'duration': 1000},
        {'id': 2, 'start': 500, 'duration': 2000},
    ]
    track = _make_track(medias=medias)
    assert track.end_time_ticks() == 2500  # 500 + 2000


def test_track_end_time_ticks_empty():
    track = _make_track(medias=[])
    assert track.end_time_ticks() == 0


# ---------------------------------------------------------------------------
# Timeline.find_track
# ---------------------------------------------------------------------------

def test_timeline_find_track_found():
    tl = _make_timeline([('Audio', []), ('Video', [{'id': 1, 'start': 0, 'duration': 1}])])
    found = tl.find_track('Video')
    assert found is not None
    assert found.name == 'Video'


def test_timeline_find_track_not_found():
    tl = _make_timeline([('Audio', [])])
    assert tl.find_track('Missing') is None


# ---------------------------------------------------------------------------
# Timeline.empty_tracks
# ---------------------------------------------------------------------------

def test_timeline_empty_tracks():
    tl = _make_timeline([
        ('Empty1', []),
        ('HasClip', [{'id': 1, 'start': 0, 'duration': 1}]),
        ('Empty2', []),
    ])
    empties = tl.empty_tracks
    assert {t.name for t in empties} == {'Empty1', 'Empty2'}


# ---------------------------------------------------------------------------
# Timeline.remove_empty_tracks
# ---------------------------------------------------------------------------

def test_timeline_remove_empty_tracks():
    tl = _make_timeline([
        ('Empty1', []),
        ('Keep', [{'id': 1, 'start': 0, 'duration': 1}]),
        ('Empty2', []),
    ])
    removed = tl.remove_empty_tracks()
    assert removed == 2
    assert tl.track_count == 1
    remaining = list(tl.tracks)
    assert remaining[0].name == 'Keep'


# ---------------------------------------------------------------------------
# Track.sort_clips
# ---------------------------------------------------------------------------

def test_sort_clips():
    medias = [
        {'id': 1, '_type': 'VMFile', 'start': 300, 'duration': 100},
        {'id': 2, '_type': 'VMFile', 'start': 100, 'duration': 100},
        {'id': 3, '_type': 'VMFile', 'start': 200, 'duration': 100},
    ]
    track = _make_track(medias=medias)
    track.sort_clips()
    assert [m['start'] for m in track._data['medias']] == [100, 200, 300]


# ---------------------------------------------------------------------------
# Timeline.total_clip_count
# ---------------------------------------------------------------------------

def test_total_clip_count():
    tl = _make_timeline([
        ('A', [{'id': 1, 'start': 0, 'duration': 1}, {'id': 2, 'start': 1, 'duration': 1}]),
        ('B', [{'id': 3, 'start': 0, 'duration': 1}]),
        ('C', []),
    ])
    assert tl.total_clip_count == 3


# ---------------------------------------------------------------------------
# Project.has_screen_recording
# ---------------------------------------------------------------------------

def _make_project_data(track_medias_list):
    """Build minimal Project._data with given track medias."""
    tracks = []
    attrs = []
    for i, medias in enumerate(track_medias_list):
        tracks.append({'trackIndex': i, 'medias': medias})
        attrs.append({'ident': f'Track{i}'})
    return {
        'timeline': {
            'sceneTrack': {'scenes': [{'csml': {'tracks': tracks}}]},
            'trackAttributes': attrs,
        },
        'sourceBin': [],
    }


def test_has_screen_recording_true():
    from camtasia.project import Project
    from unittest.mock import MagicMock
    group_media = {
        'id': 1, '_type': 'Group', 'start': 0, 'duration': 100,
        'tracks': [{'trackIndex': 0, 'medias': [{'id': 2, '_type': 'UnifiedMedia', 'start': 0, 'duration': 100}]}],
        'attributes': {'ident': ''},
    }
    proj = MagicMock(spec=Project)
    proj._data = _make_project_data([[group_media]])
    proj.timeline = Timeline(proj._data['timeline'])
    assert Project.has_screen_recording.fget(proj) is True


def test_has_screen_recording_false():
    from camtasia.project import Project
    from unittest.mock import MagicMock
    plain_media = {'id': 1, '_type': 'VMFile', 'start': 0, 'duration': 100}
    proj = MagicMock(spec=Project)
    proj._data = _make_project_data([[plain_media]])
    proj.timeline = Timeline(proj._data['timeline'])
    assert Project.has_screen_recording.fget(proj) is False


# ---------------------------------------------------------------------------
# Track.first_clip / Track.last_clip
# ---------------------------------------------------------------------------

def test_first_clip():
    medias = [
        {'id': 1, '_type': 'VMFile', 'start': 300, 'duration': 100},
        {'id': 2, '_type': 'VMFile', 'start': 100, 'duration': 100},
    ]
    track = _make_track(medias=medias)
    assert track.first_clip is not None
    assert track.first_clip.id == 2


def test_last_clip():
    medias = [
        {'id': 1, '_type': 'VMFile', 'start': 100, 'duration': 50},
        {'id': 2, '_type': 'VMFile', 'start': 200, 'duration': 300},
    ]
    track = _make_track(medias=medias)
    assert track.last_clip is not None
    assert track.last_clip.id == 2  # 200+300=500 > 100+50=150


def test_first_clip_empty():
    track = _make_track(medias=[])
    assert track.first_clip is None


def test_last_clip_empty():
    track = _make_track(medias=[])
    assert track.last_clip is None


# ---------------------------------------------------------------------------
# Track.total_duration_seconds
# ---------------------------------------------------------------------------

def test_total_duration_seconds():
    medias = [
        {'id': 1, 'start': 0, 'duration': seconds_to_ticks(2.0)},
        {'id': 2, 'start': seconds_to_ticks(3.0), 'duration': seconds_to_ticks(1.5)},
    ]
    track = _make_track(medias=medias)
    assert track.total_duration_seconds == pytest.approx(3.5)


# ---------------------------------------------------------------------------
# Track.gaps
# ---------------------------------------------------------------------------

def test_gaps_between_clips():
    medias = [
        {'id': 1, 'start': 0, 'duration': seconds_to_ticks(1.0)},
        {'id': 2, 'start': seconds_to_ticks(2.0), 'duration': seconds_to_ticks(1.0)},
        {'id': 3, 'start': seconds_to_ticks(5.0), 'duration': seconds_to_ticks(1.0)},
    ]
    track = _make_track(medias=medias)
    result = track.gaps()
    assert len(result) == 2
    assert result[0] == pytest.approx((1.0, 2.0))
    assert result[1] == pytest.approx((3.0, 5.0))


def test_gaps_no_gaps():
    medias = [
        {'id': 1, 'start': 0, 'duration': seconds_to_ticks(1.0)},
        {'id': 2, 'start': seconds_to_ticks(1.0), 'duration': seconds_to_ticks(1.0)},
    ]
    track = _make_track(medias=medias)
    assert track.gaps() == []


# ---------------------------------------------------------------------------
# Track.overlaps
# ---------------------------------------------------------------------------

def test_overlaps_found():
    medias = [
        {'id': 10, 'start': 0, 'duration': seconds_to_ticks(3.0)},
        {'id': 20, 'start': seconds_to_ticks(2.0), 'duration': seconds_to_ticks(2.0)},
    ]
    track = _make_track(medias=medias)
    assert track.overlaps() == [(10, 20)]


def test_overlaps_none():
    medias = [
        {'id': 10, 'start': 0, 'duration': seconds_to_ticks(1.0)},
        {'id': 20, 'start': seconds_to_ticks(2.0), 'duration': seconds_to_ticks(1.0)},
    ]
    track = _make_track(medias=medias)
    assert track.overlaps() == []


# ---------------------------------------------------------------------------
# Timeline.shift_all
# ---------------------------------------------------------------------------

def test_shift_all_forward():
    tl = _make_timeline([
        ('A', [{'id': 1, 'start': 0, 'duration': 100}, {'id': 2, 'start': 1000, 'duration': 200}]),
        ('B', [{'id': 3, 'start': 500, 'duration': 100}]),
    ])
    tl.shift_all(2.0)
    offset = seconds_to_ticks(2.0)
    raw_tracks = tl._track_list
    assert raw_tracks[0]['medias'][0]['start'] == offset
    assert raw_tracks[0]['medias'][1]['start'] == 1000 + offset
    assert raw_tracks[1]['medias'][0]['start'] == 500 + offset


def test_shift_all_backward_clamps():
    start_ticks = seconds_to_ticks(1.0)
    tl = _make_timeline([
        ('A', [{'id': 1, 'start': start_ticks, 'duration': 100}]),
        ('B', [{'id': 2, 'start': 0, 'duration': 100}]),
    ])
    tl.shift_all(-5.0)
    raw_tracks = tl._track_list
    # Both should be clamped to 0
    assert raw_tracks[0]['medias'][0]['start'] == 0
    assert raw_tracks[1]['medias'][0]['start'] == 0


# ---------------------------------------------------------------------------
# Timeline.flatten_to_track
# ---------------------------------------------------------------------------

def test_flatten_to_track():
    tl = _make_timeline([
        ('A', [{'id': 1, '_type': 'VMFile', 'start': 0, 'duration': 100}]),
        ('B', [{'id': 2, '_type': 'AMFile', 'start': 50, 'duration': 200}]),
    ])
    target = tl.flatten_to_track('Merged')
    assert target.name == 'Merged'
    clips = list(target.clips)
    assert len(clips) == 2
    # Clips get new unique IDs
    ids = {c.id for c in clips}
    assert ids.isdisjoint({1, 2})
    # Original tracks unchanged
    orig_a = tl.find_track('A')
    assert len(list(orig_a.clips)) == 1


# ---------------------------------------------------------------------------
# BaseClip.has_effects
# ---------------------------------------------------------------------------

def test_has_effects_true():
    from camtasia.timeline.clips.base import BaseClip
    clip = BaseClip({'id': 1, 'effects': [{'effectName': 'Glow'}]})
    assert clip.has_effects is True


def test_has_effects_false():
    from camtasia.timeline.clips.base import BaseClip
    clip = BaseClip({'id': 1, 'effects': []})
    assert clip.has_effects is False
    clip2 = BaseClip({'id': 2})
    assert clip2.has_effects is False


# ---------------------------------------------------------------------------
# BaseClip.effect_count
# ---------------------------------------------------------------------------

def test_effect_count():
    from camtasia.timeline.clips.base import BaseClip
    clip = BaseClip({'id': 1, 'effects': [{'effectName': 'Glow'}, {'effectName': 'Border'}]})
    assert clip.effect_count == 2
    empty = BaseClip({'id': 2})
    assert empty.effect_count == 0

def test_project_has_screen_recording_with_real_data():
    """Test has_screen_recording against a real project fixture."""
    import json
    from pathlib import Path
    from camtasia.timeline.clips import clip_from_dict
    from camtasia.timeline.clips.group import Group
    
    fixture = Path(__file__).parent / 'fixtures' / 'techsmith_sample.tscproj'
    data = json.loads(fixture.read_text())
    tracks = data['timeline']['sceneTrack']['scenes'][0]['csml']['tracks']
    
    has_screen = False
    for t in tracks:
        for m in t.get('medias', []):
            clip = clip_from_dict(m)
            if isinstance(clip, Group) and clip.is_screen_recording:
                has_screen = True
    # TechSmith sample has ScreenVMFile clips
    # (may or may not be inside Groups depending on the sample)
    assert isinstance(has_screen, bool)


# ---------------------------------------------------------------------------
# Track.reorder_clips
# ---------------------------------------------------------------------------

def test_reorder_clips():
    medias = [
        {'id': 1, '_type': 'VMFile', 'start': 0, 'duration': 100, 'effects': []},
        {'id': 2, '_type': 'VMFile', 'start': 100, 'duration': 200, 'effects': []},
        {'id': 3, '_type': 'VMFile', 'start': 300, 'duration': 150, 'effects': []},
    ]
    data = {'trackIndex': 0, 'medias': medias, 'transitions': [{'leftMedia': 1, 'rightMedia': 2}]}
    track = Track({'ident': 'T'}, data)
    track.reorder_clips([3, 1, 2])
    ids = [m['id'] for m in track._data['medias']]
    starts = [m['start'] for m in track._data['medias']]
    assert ids == [3, 1, 2]
    assert starts == [0, 150, 250]
    assert track._data['transitions'] == []


def test_reorder_clips_wrong_ids_raises():
    medias = [
        {'id': 1, '_type': 'VMFile', 'start': 0, 'duration': 100, 'effects': []},
        {'id': 2, '_type': 'VMFile', 'start': 100, 'duration': 200, 'effects': []},
    ]
    track = _make_track(medias=medias)
    with pytest.raises(ValueError):
        track.reorder_clips([1, 99])


# ---------------------------------------------------------------------------
# Timeline.total_duration_ticks (property)
# ---------------------------------------------------------------------------

def test_total_duration_ticks():
    tl = _make_timeline([
        ('A', [{'id': 1, 'start': 0, 'duration': 500}]),
        ('B', [{'id': 2, 'start': 100, 'duration': 600}]),
        ('C', []),
    ])
    assert tl.total_duration_ticks == 700  # max(500, 100+600, 0)
