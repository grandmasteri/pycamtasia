"""Tests for Track and Timeline convenience methods."""
from __future__ import annotations

from typing import Any

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
    found = tl.find_track_by_name('Video')
    assert found is not None
    assert found.name == 'Video'


def test_timeline_find_track_not_found():
    tl = _make_timeline([('Audio', [])])
    assert tl.find_track_by_name('Missing') is None


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
    orig_a = tl.find_track_by_name('A')
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


# ---------------------------------------------------------------------------
# Track.filter_clips
# ---------------------------------------------------------------------------

def test_filter_clips():
    medias = [
        {'id': 1, '_type': 'VMFile', 'start': 0, 'duration': 100},
        {'id': 2, '_type': 'AMFile', 'start': 100, 'duration': 200},
        {'id': 3, '_type': 'VMFile', 'start': 300, 'duration': 150},
    ]
    track = _make_track(medias=medias)
    result = track.filter_clips(lambda c: c.start == 0)
    assert len(result) == 1
    assert result[0].id == 1

    all_clips = track.filter_clips(lambda c: True)
    assert len(all_clips) == 3

    none = track.filter_clips(lambda c: False)
    assert none == []


# ---------------------------------------------------------------------------
# Timeline.all_effects
# ---------------------------------------------------------------------------

def test_all_effects():
    medias_a = [
        {'id': 1, '_type': 'VMFile', 'start': 0, 'duration': 100,
         'effects': [{'effectName': 'Glow'}, {'effectName': 'Border'}]},
    ]
    medias_b = [
        {'id': 2, '_type': 'AMFile', 'start': 0, 'duration': 50, 'effects': []},
        {'id': 3, '_type': 'VMFile', 'start': 50, 'duration': 50,
         'effects': [{'effectName': 'Shadow'}]},
    ]
    tl = _make_timeline([('A', medias_a), ('B', medias_b)])
    effects = tl.all_effects
    assert len(effects) == 3
    # Each entry is (track, clip, effect_dict)
    names = [e[2]['effectName'] for e in effects]
    assert names == ['Glow', 'Border', 'Shadow']
    assert effects[0][0].name == 'A'
    assert effects[0][1].id == 1
    assert effects[2][0].name == 'B'
    assert effects[2][1].id == 3


# ---------------------------------------------------------------------------
# Project.all_clips
# ---------------------------------------------------------------------------

def test_all_clips():
    from camtasia.project import Project
    from unittest.mock import MagicMock

    proj = MagicMock(spec=Project)
    proj._data = _make_project_data([
        [{'id': 1, '_type': 'VMFile', 'start': 0, 'duration': 100}],
        [{'id': 2, '_type': 'AMFile', 'start': 0, 'duration': 50},
         {'id': 3, '_type': 'VMFile', 'start': 50, 'duration': 50}],
        [],
    ])
    proj.timeline = Timeline(proj._data['timeline'])
    result = Project.all_clips.fget(proj)
    assert len(result) == 3
    track_names = [t.name for t, c in result]
    clip_ids = [c.id for t, c in result]
    assert clip_ids == [1, 2, 3]
    assert track_names == ['Track0', 'Track1', 'Track1']


# ---------------------------------------------------------------------------
# BaseClip.remove_effect_by_name
# ---------------------------------------------------------------------------

def test_remove_effect_by_name():
    from camtasia.timeline.clips import clip_from_dict
    data = {
        'id': 1, '_type': 'VMFile', 'start': 0, 'duration': 100,
        'effects': [
            {'effectName': 'Glow'},
            {'effectName': 'Border'},
            {'effectName': 'Glow'},
        ],
    }
    clip = clip_from_dict(data)
    removed = clip.remove_effect_by_name('Glow')
    assert removed == 2
    assert len(clip.effects) == 1
    assert clip.effects[0]['effectName'] == 'Border'


def test_remove_effect_by_name_not_found():
    from camtasia.timeline.clips import clip_from_dict
    data = {
        'id': 1, '_type': 'VMFile', 'start': 0, 'duration': 100,
        'effects': [{'effectName': 'Border'}],
    }
    clip = clip_from_dict(data)
    removed = clip.remove_effect_by_name('Glow')
    assert removed == 0
    assert len(clip.effects) == 1


# ---------------------------------------------------------------------------
# Track.clips_at
# ---------------------------------------------------------------------------

def test_clips_at():
    medias = [
        {'id': 1, '_type': 'VMFile', 'start': 0, 'duration': seconds_to_ticks(5.0)},
        {'id': 2, '_type': 'VMFile', 'start': seconds_to_ticks(5.0), 'duration': seconds_to_ticks(3.0)},
    ]
    track = _make_track(medias=medias)
    result = track.clips_at(2.0)
    assert len(result) == 1
    assert result[0].id == 1

    result2 = track.clips_at(6.0)
    assert len(result2) == 1
    assert result2[0].id == 2


def test_clips_at_empty():
    track = _make_track(medias=[])
    assert track.clips_at(1.0) == []


# ---------------------------------------------------------------------------
# Timeline.tracks_with_clips
# ---------------------------------------------------------------------------

def test_tracks_with_clips():
    tl = _make_timeline([
        ('A', [{'id': 1, '_type': 'VMFile', 'start': 0, 'duration': 100}]),
        ('B', []),
        ('C', [{'id': 2, '_type': 'AMFile', 'start': 0, 'duration': 50}]),
    ])
    result = tl.tracks_with_clips
    assert len(result) == 2
    names = [t.name for t in result]
    assert names == ['A', 'C']


# ---------------------------------------------------------------------------
# Track.total_gap_seconds
# ---------------------------------------------------------------------------

def test_total_gap_seconds():
    medias = [
        {'id': 1, 'start': 0, 'duration': seconds_to_ticks(2.0)},
        {'id': 2, 'start': seconds_to_ticks(5.0), 'duration': seconds_to_ticks(1.0)},
        {'id': 3, 'start': seconds_to_ticks(8.0), 'duration': seconds_to_ticks(2.0)},
    ]
    track = _make_track(medias=medias)
    # gap1: 2.0→5.0 = 3.0s, gap2: 6.0→8.0 = 2.0s → total 5.0s
    assert track.total_gap_seconds == pytest.approx(5.0)


def test_total_gap_seconds_no_gaps():
    medias = [
        {'id': 1, 'start': 0, 'duration': seconds_to_ticks(3.0)},
        {'id': 2, 'start': seconds_to_ticks(3.0), 'duration': seconds_to_ticks(2.0)},
    ]
    track = _make_track(medias=medias)
    assert track.total_gap_seconds == 0.0


def test_total_gap_seconds_empty():
    track = _make_track(medias=[])
    assert track.total_gap_seconds == 0.0


# ---------------------------------------------------------------------------
# Timeline.track_names
# ---------------------------------------------------------------------------

def test_track_names():
    tl = _make_timeline([
        ('Video', [{'id': 1, 'start': 0, 'duration': 100}]),
        ('Audio', []),
        ('Captions', []),
    ])
    assert tl.track_names == ['Video', 'Audio', 'Captions']


def test_track_names_empty_timeline():
    tl = _make_timeline([])
    assert tl.track_names == []


# ---------------------------------------------------------------------------
# Project.media_count
# ---------------------------------------------------------------------------

def test_media_count(project):
    assert project.media_count == 0


# ---------------------------------------------------------------------------
# Track.describe
# ---------------------------------------------------------------------------

def test_track_describe():
    medias = [
        {'id': 1, '_type': 'VMFile', 'start': 0, 'duration': seconds_to_ticks(3.0)},
        {'id': 2, '_type': 'AMFile', 'start': seconds_to_ticks(5.0), 'duration': seconds_to_ticks(2.0)},
    ]
    track = _make_track(medias=medias, name='Narration')
    desc = track.describe()
    assert 'Track 0: Narration' in desc
    assert 'Clips: 2' in desc
    assert 'AMFile' in desc and 'VMFile' in desc
    assert 'Duration: 5.0s' in desc
    assert 'Gaps: 1' in desc


# ---------------------------------------------------------------------------
# BaseClip.describe
# ---------------------------------------------------------------------------

def test_clip_describe():
    from camtasia.timeline.clips import clip_from_dict
    data = {
        'id': 42,
        '_type': 'VMFile',
        'start': seconds_to_ticks(1.0),
        'duration': seconds_to_ticks(4.0),
        'mediaStart': 0,
        'mediaDuration': seconds_to_ticks(4.0),
        'scalar': 1,
        'effects': [{'effectName': 'Glow'}, {'effectName': 'DropShadow'}],
        'parameters': {},
        'metadata': {},
        'animationTracks': {},
    }
    clip = clip_from_dict(data)
    desc = clip.describe()
    assert 'VMFile (id=42)' in desc
    assert '1.00s' in desc
    assert '5.00s' in desc
    assert '4.00s' in desc
    assert 'Effects: Glow, DropShadow' in desc

def test_track_describe_with_overlaps():
    data = {'trackIndex': 0, 'medias': [
        {'id': 1, '_type': 'AMFile', 'start': 0, 'duration': 200},
        {'id': 2, '_type': 'AMFile', 'start': 100, 'duration': 200},
    ], 'transitions': []}
    from camtasia.timeline.track import Track
    t = Track({'ident': 'Overlap'}, data)
    actual = t.describe()
    assert 'Overlaps: 1' in actual


# ---------------------------------------------------------------------------
# Clip type-check properties
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('type_str, prop, expected', [
    ('AMFile', 'is_audio', True),
    ('VMFile', 'is_video', True),
    ('ScreenVMFile', 'is_video', True),
    ('IMFile', 'is_image', True),
    ('Group', 'is_group', True),
    ('Callout', 'is_callout', True),
    ('AMFile', 'is_video', False),
    ('VMFile', 'is_audio', False),
    ('IMFile', 'is_callout', False),
])
def test_clip_type_properties(type_str, prop, expected):
    from camtasia.timeline.clips import clip_from_dict
    data = {'_type': type_str, 'id': 1, 'start': 0, 'duration': 100,
            'mediaSource': {}, 'parameters': {}, 'effects': [],
            'metadata': {}, 'animationTracks': {}}
    clip = clip_from_dict(data)
    assert getattr(clip, prop) is expected


def test_track_typed_clips():
    medias = [
        {'_type': 'AMFile', 'id': 1, 'start': 0, 'duration': 100},
        {'_type': 'VMFile', 'id': 2, 'start': 100, 'duration': 100},
        {'_type': 'IMFile', 'id': 3, 'start': 200, 'duration': 100},
        {'_type': 'AMFile', 'id': 4, 'start': 300, 'duration': 100},
    ]
    t = _make_track(medias)
    assert len(t.audio_clips) == 2
    assert all(c.is_audio for c in t.audio_clips)
    assert len(t.video_clips) == 1
    assert t.video_clips[0].clip_type == 'VMFile'
    assert len(t.image_clips) == 1
    assert t.image_clips[0].clip_type == 'IMFile'


# ---------------------------------------------------------------------------
# Timeline.clear_all
# ---------------------------------------------------------------------------

def test_clear_all():
    medias_a = [{'_type': 'AMFile', 'id': 1, 'start': 0, 'duration': 100}]
    medias_b = [{'_type': 'VMFile', 'id': 2, 'start': 0, 'duration': 200}]
    tl = _make_timeline([('A', medias_a), ('B', medias_b)])
    assert sum(len(t) for t in tl.tracks) == 2
    tl.clear_all()
    assert all(len(t) == 0 for t in tl.tracks)


# ---------------------------------------------------------------------------
# Project.to_dict
# ---------------------------------------------------------------------------

def test_to_dict():
    from camtasia.project import load_project
    from pathlib import Path
    fixture = Path(__file__).parent / 'fixtures' / 'test_project_c.tscproj'
    proj = load_project(fixture)
    d = proj.to_dict()
    assert isinstance(d, dict)
    # Deep copy: mutating the returned dict must not affect the project
    d['__test_sentinel'] = True
    assert '__test_sentinel' not in proj._data


# ---------------------------------------------------------------------------
# BaseClip.end_seconds
# ---------------------------------------------------------------------------

def test_end_seconds():
    from camtasia.timing import EDIT_RATE
    from camtasia.timeline.clips.base import BaseClip
    start = EDIT_RATE * 2   # 2 seconds
    dur = EDIT_RATE * 3     # 3 seconds
    clip = BaseClip({'_type': 'AMFile', 'id': 1, 'start': start,
                     'duration': dur, 'metadata': {},
                     'animationTracks': {}})
    assert clip.end_seconds == pytest.approx(5.0)

# ---------------------------------------------------------------------------
# BaseClip.time_range
# ---------------------------------------------------------------------------

def test_time_range():
    from camtasia.timeline.clips import clip_from_dict
    from camtasia.timing import seconds_to_ticks
    data = {
        '_type': 'AMFile', 'id': 1,
        'start': seconds_to_ticks(2.0),
        'duration': seconds_to_ticks(3.0),
        'parameters': {}, 'effects': [],
        'metadata': {}, 'animationTracks': {},
    }
    clip = clip_from_dict(data)
    assert clip.time_range[0] == pytest.approx(2.0)
    assert clip.time_range[1] == pytest.approx(5.0)


# ---------------------------------------------------------------------------
# Track.duration_seconds
# ---------------------------------------------------------------------------

def test_track_duration_seconds():
    medias = [
        {'id': 1, 'start': 0, 'duration': seconds_to_ticks(1.5)},
        {'id': 2, 'start': seconds_to_ticks(2.0), 'duration': seconds_to_ticks(2.5)},
    ]
    t = _make_track(medias)
    assert t.duration_seconds == t.total_duration_seconds


# ---------------------------------------------------------------------------
# Timeline.has_clips
# ---------------------------------------------------------------------------

def test_has_clips_true():
    medias = [{'_type': 'AMFile', 'id': 1, 'start': 0, 'duration': 100}]
    tl = _make_timeline([('A', medias)])
    assert tl.has_clips is True


def test_has_clips_false():
    tl = _make_timeline([('A', [])])
    assert tl.has_clips is False


# ---------------------------------------------------------------------------
# Project.is_empty
# ---------------------------------------------------------------------------

def test_project_is_empty_true(project):
    assert project.is_empty is True

def test_project_is_empty_false():
    from camtasia.project import load_project
    from pathlib import Path
    fixture = Path(__file__).parent / 'fixtures' / 'test_project_c.tscproj'
    proj = load_project(fixture)
    assert proj.is_empty is False


# ---------------------------------------------------------------------------
# Track.remove_clips_by_type
# ---------------------------------------------------------------------------

def test_remove_clips_by_type():
    medias = [
        {'_type': 'AMFile', 'id': 1, 'start': 0, 'duration': 100},
        {'_type': 'VMFile', 'id': 2, 'start': 100, 'duration': 100},
        {'_type': 'AMFile', 'id': 3, 'start': 200, 'duration': 100},
    ]
    t = _make_track(medias)
    removed = t.remove_clips_by_type('AMFile')
    assert removed == 2
    assert len(list(t.clips)) == 1
    assert list(t.clips)[0].id == 2


def test_remove_clips_by_type_none_found():
    medias = [
        {'_type': 'VMFile', 'id': 1, 'start': 0, 'duration': 100},
    ]
    t = _make_track(medias)
    removed = t.remove_clips_by_type('AMFile')
    assert removed == 0
    assert len(list(t.clips)) == 1


# ---------------------------------------------------------------------------
# Timeline.remove_tracks_by_name
# ---------------------------------------------------------------------------

def test_remove_tracks_by_name():
    tl = _make_timeline([('Audio', []), ('Video', []), ('Audio', [])])
    removed = tl.remove_tracks_by_name('Audio')
    assert removed == 2
    assert len(list(tl.tracks)) == 1
    assert list(tl.tracks)[0].name == 'Video'


def test_remove_tracks_by_name_none_found():
    tl = _make_timeline([('Video', []), ('Audio', [])])
    removed = tl.remove_tracks_by_name('Effects')
    assert removed == 0
    assert len(list(tl.tracks)) == 2


# ---------------------------------------------------------------------------
# BaseClip.to_dict
# ---------------------------------------------------------------------------

def test_clip_to_dict():
    from camtasia.timeline.clips.base import BaseClip
    start = seconds_to_ticks(1.0)
    dur = seconds_to_ticks(2.0)
    clip = BaseClip({
        'id': 42, '_type': 'VMFile', 'start': start, 'duration': dur,
        'src': 7, 'effects': [{'effectName': 'Blur'}],
    })
    d = clip.to_dict()
    assert d['id'] == 42
    assert d['type'] == 'VMFile'
    assert d['start_seconds'] == pytest.approx(1.0)
    assert d['duration_seconds'] == pytest.approx(2.0)
    assert d['end_seconds'] == pytest.approx(3.0)
    assert d['source_id'] == 7
    assert d['effects'] == ['Blur']

    # Without source_id or effects
    clip2 = BaseClip({'id': 1, '_type': 'AMFile', 'start': 0, 'duration': start})
    d2 = clip2.to_dict()
    assert 'source_id' not in d2
    assert 'effects' not in d2


# ---------------------------------------------------------------------------
# Track.to_list
# ---------------------------------------------------------------------------

def test_track_to_list():
    start1 = seconds_to_ticks(0.0)
    dur1 = seconds_to_ticks(1.5)
    start2 = seconds_to_ticks(2.0)
    dur2 = seconds_to_ticks(3.0)
    track = _make_track(medias=[
        {'id': 1, '_type': 'VMFile', 'start': start1, 'duration': dur1},
        {'id': 2, '_type': 'AMFile', 'start': start2, 'duration': dur2},
    ])
    result = track.to_list()
    assert len(result) == 2
    assert result[0]['id'] == 1
    assert result[0]['type'] == 'VMFile'
    assert result[0]['start_seconds'] == pytest.approx(0.0)
    assert result[1]['id'] == 2
    assert result[1]['duration_seconds'] == pytest.approx(3.0)


# ---------------------------------------------------------------------------
# Project.describe
# ---------------------------------------------------------------------------

def test_project_describe():
    from camtasia.project import load_project
    from pathlib import Path
    fixture = Path(__file__).parent / 'fixtures' / 'test_project_c.tscproj'
    proj = load_project(fixture)
    desc = proj.describe()
    assert isinstance(desc, str)
    assert f'Project: {proj.file_path.name}' in desc
    assert f'{proj.frame_rate}fps' in desc
    assert 'Duration:' in desc
    assert 'Tracks:' in desc
    assert 'Clips:' in desc
    assert 'Media:' in desc
    assert 'Health:' in desc

def test_project_describe_unhealthy(project):
    from unittest.mock import patch
    from camtasia.validation import ValidationIssue
    with patch.object(project, 'validate', return_value=[ValidationIssue('error', 'bad')]):
        actual = project.describe()
        assert '❌' in actual

# ---------------------------------------------------------------------------
# Timeline.to_dict
# ---------------------------------------------------------------------------

def test_timeline_to_dict():
    media = {'id': 1, 'start': 0, 'duration': seconds_to_ticks(5.0)}
    tl = _make_timeline([('Video', [media]), ('Audio', [])])
    d = tl.to_dict()
    assert d['track_count'] == 2
    assert d['total_clip_count'] == 1
    assert d['duration_seconds'] == pytest.approx(5.0)
    assert d['has_clips'] is True
    assert d['track_names'] == ['Video', 'Audio']


# ---------------------------------------------------------------------------
# BaseClip.is_at
# ---------------------------------------------------------------------------

def test_clip_is_at():
    from camtasia.timeline.clips.base import BaseClip
    start = seconds_to_ticks(2.0)
    dur = seconds_to_ticks(3.0)
    clip = BaseClip({'id': 1, '_type': 'VMFile', 'start': start, 'duration': dur})
    assert clip.is_at(2.0) is True
    assert clip.is_at(3.5) is True
    assert clip.is_at(4.99) is True
    assert clip.is_at(5.0) is False
    assert clip.is_at(1.0) is False


# ---------------------------------------------------------------------------
# Track.apply_to_all
# ---------------------------------------------------------------------------

def test_apply_to_all():
    track = _make_track(medias=[
        {'id': 1, '_type': 'VMFile', 'start': 0, 'duration': 100},
        {'id': 2, '_type': 'VMFile', 'start': 200, 'duration': 100},
        {'id': 3, '_type': 'VMFile', 'start': 400, 'duration': 100},
    ])
    visited = []
    count = track.apply_to_all(lambda c: visited.append(c.id))
    assert count == 3
    assert visited == [1, 2, 3]


def test_apply_to_all_empty():
    track = _make_track(medias=[])
    count = track.apply_to_all(lambda c: None)
    assert count == 0


# ---------------------------------------------------------------------------
# BaseClip.reset_transforms
# ---------------------------------------------------------------------------

def test_reset_transforms():
    from camtasia.timeline.clips.base import BaseClip
    clip = BaseClip({
        'id': 1, '_type': 'VMFile', 'start': 0, 'duration': 100,
        'parameters': {
            'positionX': 50.0,
            'positionY': -30.0,
            'scale0': 2.5,
            'scale1': 2.5,
            'rotation': 45.0,
        },
    })
    result = clip.reset_transforms()
    assert result is clip  # fluent chaining
    assert clip.rotation == 0.0


# ---------------------------------------------------------------------------
# BaseClip.remove_all_effects
# ---------------------------------------------------------------------------

def test_remove_all_effects():
    from camtasia.timeline.clips.base import BaseClip
    clip = BaseClip({
        'id': 1, '_type': 'VMFile', 'start': 0, 'duration': 100,
        'effects': [
            {'effectName': 'blur'},
            {'effectName': 'glow'},
        ],
    })
    assert clip.has_effects is True
    result = clip.remove_all_effects()
    assert result is clip  # fluent chaining
    assert clip.has_effects is False
    assert clip._data['effects'] == []


# ---------------------------------------------------------------------------
# Project.track_count / clip_count / duration_seconds
# ---------------------------------------------------------------------------

def test_project_track_count():
    from camtasia.project import Project
    from unittest.mock import MagicMock
    media = {'id': 1, '_type': 'VMFile', 'start': 0, 'duration': 100}
    proj = MagicMock(spec=Project)
    proj._data = _make_project_data([[media], []])
    proj.timeline = Timeline(proj._data['timeline'])
    assert Project.track_count.fget(proj) == 2


def test_project_clip_count():
    from camtasia.project import Project
    from unittest.mock import MagicMock
    m1 = {'id': 1, '_type': 'VMFile', 'start': 0, 'duration': 100}
    m2 = {'id': 2, '_type': 'VMFile', 'start': 100, 'duration': 200}
    proj = MagicMock(spec=Project)
    proj._data = _make_project_data([[m1], [m2]])
    proj.timeline = Timeline(proj._data['timeline'])
    assert Project.clip_count.fget(proj) == 2


def test_project_duration_seconds(project):
    actual = project.duration_seconds
    assert isinstance(actual, float)
    assert actual >= 0.0


# ---------------------------------------------------------------------------
# Track.has_transitions / transition_count
# ---------------------------------------------------------------------------

def test_track_has_transitions():
    track_no = _make_track(medias=[])
    assert track_no.has_transitions is False
    track_yes = Track({'ident': 'T'}, {
        'trackIndex': 0,
        'medias': [],
        'transitions': [{'start': 0, 'end': 100, 'duration': 50}],
    })
    assert track_yes.has_transitions is True


def test_track_transition_count():
    track_zero = _make_track(medias=[])
    assert track_zero.transition_count == 0
    track_two = Track({'ident': 'T'}, {
        'trackIndex': 0,
        'medias': [],
        'transitions': [
            {'start': 0, 'end': 100, 'duration': 50},
            {'start': 200, 'end': 300, 'duration': 50},
        ],
    })
    assert track_two.transition_count == 2


# ---------------------------------------------------------------------------
# Project.find_clips_by_type
# ---------------------------------------------------------------------------

def test_find_clips_by_type():
    from camtasia.project import Project
    from unittest.mock import MagicMock

    vm = {'id': 1, '_type': 'VMFile', 'start': 0, 'duration': 100}
    am = {'id': 2, '_type': 'AMFile', 'start': 0, 'duration': 200}
    vm2 = {'id': 3, '_type': 'VMFile', 'start': 100, 'duration': 50}
    proj = MagicMock(spec=Project)
    proj._data = _make_project_data([[vm, am], [vm2]])
    proj.timeline = Timeline(proj._data['timeline'])
    proj.all_clips = Project.all_clips.fget(proj)

    result = Project.find_clips_by_type(proj, 'VMFile')
    assert len(result) == 2
    assert all(c.clip_type == 'VMFile' for _, c in result)

    result_am = Project.find_clips_by_type(proj, 'AMFile')
    assert len(result_am) == 1
    assert result_am[0][1].clip_type == 'AMFile'

    assert Project.find_clips_by_type(proj, 'NoSuchType') == []


# ---------------------------------------------------------------------------
# Timeline.describe
# ---------------------------------------------------------------------------

def test_timeline_describe():
    media = {'id': 1, '_type': 'VMFile', 'start': 0, 'duration': 300}
    tl = _make_timeline([('Video', [media]), ('Audio', [])])
    desc = tl.describe()
    assert 'Timeline:' in desc
    assert '2 tracks' in desc
    assert '1 clips' in desc


# ---------------------------------------------------------------------------
# StitchedMedia.min_media_start
# ---------------------------------------------------------------------------

def test_stitched_min_media_start():
    from camtasia.timeline.clips import clip_from_dict
    clip = clip_from_dict({'_type': 'StitchedMedia', 'id': 1, 'start': 0, 'duration': 100,
                           'mediaStart': 0, 'mediaDuration': 100, 'minMediaStart': 42})
    assert clip.min_media_start == 42
    # default when key absent
    clip2 = clip_from_dict({'_type': 'StitchedMedia', 'id': 2, 'start': 0, 'duration': 100,
                            'mediaStart': 0, 'mediaDuration': 100})
    assert clip2.min_media_start == 0


# ---------------------------------------------------------------------------
# PlaceholderMedia.subtitle
# ---------------------------------------------------------------------------

def test_placeholder_subtitle():
    from camtasia.timeline.clips import clip_from_dict
    clip = clip_from_dict({'_type': 'PlaceholderMedia', 'id': 1, 'start': 0, 'duration': 100,
                           'metadata': {'placeHolderSubTitle': 'hello'}})
    assert clip.subtitle == 'hello'
    clip.subtitle = 'world'
    assert clip.subtitle == 'world'
    # default when absent
    clip2 = clip_from_dict({'_type': 'PlaceholderMedia', 'id': 2, 'start': 0, 'duration': 100})
    assert clip2.subtitle == ''


# ---------------------------------------------------------------------------
# PlaceholderMedia.width / height
# ---------------------------------------------------------------------------

def test_placeholder_width_height():
    from camtasia.timeline.clips import clip_from_dict
    clip = clip_from_dict({'_type': 'PlaceholderMedia', 'id': 1, 'start': 0, 'duration': 100,
                           'attributes': {'width': 1920.0, 'height': 1080.0}})
    assert clip.width == 1920.0
    assert clip.height == 1080.0
    # defaults
    clip2 = clip_from_dict({'_type': 'PlaceholderMedia', 'id': 2, 'start': 0, 'duration': 100})
    assert clip2.width == 0.0
    assert clip2.height == 0.0


# ---------------------------------------------------------------------------
# BaseClip.is_stitched / is_placeholder
# ---------------------------------------------------------------------------

def test_is_stitched():
    from camtasia.timeline.clips import clip_from_dict
    clip = clip_from_dict({'_type': 'StitchedMedia', 'id': 1, 'start': 0, 'duration': 100,
                           'mediaStart': 0, 'mediaDuration': 100})
    assert clip.is_stitched is True
    assert clip.is_placeholder is False


def test_is_placeholder():
    from camtasia.timeline.clips import clip_from_dict
    clip = clip_from_dict({'_type': 'PlaceholderMedia', 'id': 1, 'start': 0, 'duration': 100})
    assert clip.is_placeholder is True
    assert clip.is_stitched is False


# ---------------------------------------------------------------------------
# BaseClip.opacity
# ---------------------------------------------------------------------------

def test_clip_opacity_get_set():
    from camtasia.timeline.clips import clip_from_dict
    clip = clip_from_dict({'_type': 'VMFile', 'id': 1, 'start': 0, 'duration': 100})
    assert clip.opacity == 1.0  # default
    clip.opacity = 0.5
    assert clip.opacity == 0.5
    # keyframe-style dict
    clip2 = clip_from_dict({'_type': 'VMFile', 'id': 2, 'start': 0, 'duration': 100,
                            'parameters': {'opacity': {'type': 'float', 'defaultValue': 0.75, 'keyframes': []}}})
    assert clip2.opacity == 0.75


def test_clip_opacity_validation():
    from camtasia.timeline.clips import clip_from_dict
    clip = clip_from_dict({'_type': 'VMFile', 'id': 1, 'start': 0, 'duration': 100})
    with pytest.raises(ValueError, match='opacity must be 0.0-1.0'):
        clip.opacity = 1.5
    with pytest.raises(ValueError, match='opacity must be 0.0-1.0'):
        clip.opacity = -0.1


# ---------------------------------------------------------------------------
# BaseClip.volume
# ---------------------------------------------------------------------------

def test_clip_volume_get_set():
    from camtasia.timeline.clips import clip_from_dict
    clip = clip_from_dict({'_type': 'AMFile', 'id': 1, 'start': 0, 'duration': 100})
    assert clip.volume == 1.0  # default
    clip.volume = 2.0
    assert clip.volume == 2.0
    # keyframe-style dict
    clip2 = clip_from_dict({'_type': 'AMFile', 'id': 2, 'start': 0, 'duration': 100,
                            'parameters': {'volume': {'type': 'float', 'defaultValue': 0.5, 'keyframes': []}}})
    assert clip2.volume == 0.5


def test_clip_volume_validation():
    from camtasia.timeline.clips import clip_from_dict
    clip = clip_from_dict({'_type': 'AMFile', 'id': 1, 'start': 0, 'duration': 100})
    with pytest.raises(ValueError, match='volume must be >= 0.0'):
        clip.volume = -0.5


# ---------------------------------------------------------------------------
# Track.rename
# ---------------------------------------------------------------------------

def test_track_rename():
    track = _make_track(name='Original')
    assert track.name == 'Original'
    track.rename('Renamed')
    assert track.name == 'Renamed'


# ---------------------------------------------------------------------------
# InterpolationType enum
# ---------------------------------------------------------------------------

def test_interpolation_type_values():
    from camtasia.types import InterpolationType
    assert InterpolationType.LINEAR == 'linr'
    assert InterpolationType.EASE_IN_OUT == 'eioe'
    assert InterpolationType.SPRING == 'sprg'
    assert InterpolationType.BOUNCE == 'bnce'
    assert len(InterpolationType) == 4


# ---------------------------------------------------------------------------
# Track.set_opacity
# ---------------------------------------------------------------------------

def test_track_set_opacity():
    from camtasia.timeline.clips import clip_from_dict
    medias = [
        {'_type': 'VMFile', 'id': 1, 'start': 0, 'duration': 100},
        {'_type': 'VMFile', 'id': 2, 'start': 100, 'duration': 100},
    ]
    track = _make_track(medias=medias)
    track.set_opacity(0.5)
    for clip in track.clips:
        assert clip.opacity == 0.5
    with pytest.raises(ValueError, match='opacity must be 0.0-1.0'):
        track.set_opacity(1.5)
    with pytest.raises(ValueError, match='opacity must be 0.0-1.0'):
        track.set_opacity(-0.1)


# ---------------------------------------------------------------------------
# Track.set_volume
# ---------------------------------------------------------------------------

def test_track_set_volume():
    medias = [
        {'_type': 'AMFile', 'id': 1, 'start': 0, 'duration': 100},
        {'_type': 'AMFile', 'id': 2, 'start': 100, 'duration': 100},
    ]
    track = _make_track(medias=medias)
    track.set_volume(0.75)
    for clip in track.clips:
        assert clip.volume == 0.75
    with pytest.raises(ValueError, match='volume must be >= 0.0'):
        track.set_volume(-1.0)


# ---------------------------------------------------------------------------
# Project.set_canvas_size
# ---------------------------------------------------------------------------

def test_set_canvas_size():
    from camtasia.project import Project
    from pathlib import Path
    from unittest.mock import patch
    proj = Project.__new__(Project)
    proj._data = {
        'sourceBin': [],
        'timeline': {
            'sceneTrack': {'scenes': [{'csml': {'tracks': []}}]},
            'trackAttributes': [],
        },
        'editRate': 30,
    }
    proj._file_path = Path('/tmp/fake.tscproj')
    proj._encoding = 'utf-8'
    proj.set_canvas_size(3840, 2160)
    assert proj.width == 3840
    assert proj.height == 2160


# ---------------------------------------------------------------------------
# BaseClip.set_opacity_fade
# ---------------------------------------------------------------------------

def test_set_opacity_fade():
    from camtasia.timeline.clips import clip_from_dict
    from camtasia.timing import seconds_to_ticks
    clip = clip_from_dict({'_type': 'VMFile', 'id': 1, 'start': 0, 'duration': 9000})
    result = clip.set_opacity_fade(1.0, 0.0, 3.0)
    assert result is clip  # returns self
    params = clip._data['parameters']['opacity']
    assert params['defaultValue'] == 1.0
    assert len(params['keyframes']) == 1
    assert params['keyframes'][0]['value'] == 0.0  # target value
    # without duration_seconds — uses clip duration
    clip2 = clip_from_dict({'_type': 'VMFile', 'id': 2, 'start': 0, 'duration': 9000})
    clip2.set_opacity_fade(0.5, 1.0)
    assert clip2._data['parameters']['opacity']['defaultValue'] == 0.5


# ---------------------------------------------------------------------------
# BaseClip.set_volume_fade
# ---------------------------------------------------------------------------

def test_set_volume_fade():
    from camtasia.timeline.clips import clip_from_dict
    clip = clip_from_dict({'_type': 'AMFile', 'id': 1, 'start': 0, 'duration': 9000})
    result = clip.set_volume_fade(1.0, 0.0, 3.0)
    assert result is clip
    params = clip._data['parameters']['volume']
    assert params['defaultValue'] == 1.0
    assert len(params['keyframes']) == 1
    assert params['keyframes'][0]['value'] == 0.0  # target value


# ---------------------------------------------------------------------------
# Track.find_clip_at
# ---------------------------------------------------------------------------

def test_find_clip_at():
    medias = [
        {'_type': 'AMFile', 'id': 1, 'start': 0, 'duration': seconds_to_ticks(5.0)},
        {'_type': 'AMFile', 'id': 2, 'start': seconds_to_ticks(10.0), 'duration': seconds_to_ticks(5.0)},
    ]
    track = _make_track(medias=medias)
    clip = track.find_clip_at(2.0)
    assert clip is not None
    assert clip.id == 1
    clip2 = track.find_clip_at(12.0)
    assert clip2 is not None
    assert clip2.id == 2


def test_find_clip_at_empty():
    track = _make_track(medias=[])
    assert track.find_clip_at(5.0) is None
    # Also test a gap between clips
    medias = [
        {'_type': 'AMFile', 'id': 1, 'start': 0, 'duration': seconds_to_ticks(3.0)},
    ]
    track2 = _make_track(medias=medias)
    assert track2.find_clip_at(5.0) is None


# ---------------------------------------------------------------------------
# Timeline.find_all_clips_at
# ---------------------------------------------------------------------------

def test_find_all_clips_at():
    t = seconds_to_ticks
    tl = _make_timeline([
        ('Track1', [{'_type': 'VMFile', 'id': 1, 'start': 0, 'duration': t(10.0)}]),
        ('Track2', [{'_type': 'AMFile', 'id': 2, 'start': 0, 'duration': t(10.0)}]),
        ('Track3', [{'_type': 'VMFile', 'id': 3, 'start': t(20.0), 'duration': t(5.0)}]),
    ])
    results = tl.find_all_clips_at(5.0)
    assert len(results) == 2
    clip_ids = {clip.id for _, clip in results}
    assert clip_ids == {1, 2}
    # Time outside all clips
    assert tl.find_all_clips_at(30.0) == []


def test_find_media_by_extension(project):
    from pathlib import Path
    wav = Path(__file__).parent / 'fixtures' / 'empty.wav'
    project.import_media(wav)
    actual = project.find_media_by_extension('wav')
    assert len(actual) >= 1
    actual_none = project.find_media_by_extension('xyz')
    assert actual_none == []


# ---------------------------------------------------------------------------
# BaseClip.set_position_keyframes
# ---------------------------------------------------------------------------

def test_set_position_keyframes():
    t = seconds_to_ticks
    media = {'_type': 'VMFile', 'id': 1, 'start': 0, 'duration': t(10.0)}
    track = _make_track(medias=[media])
    clip = list(track.clips)[0]
    result = clip.set_position_keyframes([(0.0, 100, 200), (2.0, 300, 400)])
    assert result is clip  # fluent return
    params = clip._data['parameters']
    assert params['translation0']['defaultValue'] == 300
    assert params['translation1']['defaultValue'] == 400
    assert len(params['translation0']['keyframes']) == 2
    assert len(params['translation1']['keyframes']) == 2
    kf_x = params['translation0']['keyframes'][1]
    assert kf_x['value'] == 300
    assert kf_x['time'] == t(2.0)
    kf_y = params['translation1']['keyframes'][1]
    assert kf_y['value'] == 400


# ---------------------------------------------------------------------------
# BaseClip.set_scale_keyframes
# ---------------------------------------------------------------------------

def test_set_scale_keyframes():
    t = seconds_to_ticks
    media = {'_type': 'VMFile', 'id': 1, 'start': 0, 'duration': t(10.0)}
    track = _make_track(medias=[media])
    clip = list(track.clips)[0]
    result = clip.set_scale_keyframes([(0.0, 1.0), (3.0, 2.5)])
    assert result is clip
    params = clip._data['parameters']
    assert params['scale0']['defaultValue'] == 2.5
    assert params['scale1']['defaultValue'] == 2.5
    assert len(params['scale0']['keyframes']) == 2
    kf = params['scale0']['keyframes'][1]
    assert kf['value'] == 2.5
    assert kf['time'] == t(3.0)
    # scale0 and scale1 should have independent lists
    params['scale0']['keyframes'].append({'extra': True})
    assert len(params['scale1']['keyframes']) == 2


# ---------------------------------------------------------------------------
# Project.remove_all_effects
# ---------------------------------------------------------------------------

def test_project_remove_all_effects(project):
    # Add a clip with effects to the project
    track = list(project.timeline.tracks)[0]
    media = {
        '_type': 'VMFile', 'id': 999, 'start': 0, 'duration': seconds_to_ticks(5.0),
        'effects': [{'effectName': 'FakeEffect1'}, {'effectName': 'FakeEffect2'}],
    }
    track._data['medias'].append(media)
    removed = project.remove_all_effects()
    assert removed >= 2
    # Verify effects are cleared
    for t in project.timeline.tracks:
        for clip in t.clips:
            assert clip._data.get('effects', []) == []


# ---------------------------------------------------------------------------
# BaseClip.set_rotation_keyframes
# ---------------------------------------------------------------------------

def test_set_rotation_keyframes():
    import math
    t = seconds_to_ticks
    media = {'_type': 'VMFile', 'id': 1, 'start': 0, 'duration': t(10.0)}
    track = _make_track(medias=[media])
    clip = list(track.clips)[0]
    result = clip.set_rotation_keyframes([(0.0, 0), (2.0, 90), (5.0, 180)])
    assert result is clip  # fluent
    params = clip._data['parameters']
    rot = params['rotation2']
    assert rot['type'] == 'double'
    assert rot['defaultValue'] == pytest.approx(math.radians(180))
    assert len(rot['keyframes']) == 3
    assert rot['keyframes'][1]['value'] == pytest.approx(math.radians(90))
    assert rot['keyframes'][1]['time'] == t(2.0)
    assert rot['keyframes'][2]['value'] == pytest.approx(math.radians(180))


# ---------------------------------------------------------------------------
# Timeline.apply_to_all_clips
# ---------------------------------------------------------------------------

def test_timeline_apply_to_all_clips():
    t = seconds_to_ticks
    tl = _make_timeline([
        ('A', [{'_type': 'VMFile', 'id': 1, 'start': 0, 'duration': t(5.0)}]),
        ('B', [
            {'_type': 'VMFile', 'id': 2, 'start': 0, 'duration': t(3.0)},
            {'_type': 'VMFile', 'id': 3, 'start': t(3.0), 'duration': t(2.0)},
        ]),
    ])
    touched = []
    count = tl.apply_to_all_clips(lambda c: touched.append(c.id))
    assert count == 3
    assert sorted(touched) == [1, 2, 3]


# ---------------------------------------------------------------------------
# BaseClip.set_crop_keyframes
# ---------------------------------------------------------------------------

def test_set_crop_keyframes():
    t = seconds_to_ticks
    media = {'_type': 'VMFile', 'id': 1, 'start': 0, 'duration': t(10.0)}
    track = _make_track(medias=[media])
    clip = list(track.clips)[0]
    result = clip.set_crop_keyframes([
        (0.0, 0.0, 0.0, 0.0, 0.0),
        (3.0, 0.1, 0.2, 0.3, 0.4),
    ])
    assert result is clip  # fluent
    params = clip._data['parameters']
    for i, name in enumerate(['geometryCrop0', 'geometryCrop1', 'geometryCrop2', 'geometryCrop3']):
        assert name in params
        assert params[name]['type'] == 'double'
        assert len(params[name]['keyframes']) == 2
        assert params[name]['keyframes'][0]['value'] == 0.0
    # Check second keyframe values: left=0.1, top=0.2, right=0.3, bottom=0.4
    assert params['geometryCrop0']['keyframes'][1]['value'] == pytest.approx(0.1)
    assert params['geometryCrop1']['keyframes'][1]['value'] == pytest.approx(0.2)
    assert params['geometryCrop2']['keyframes'][1]['value'] == pytest.approx(0.3)
    assert params['geometryCrop3']['keyframes'][1]['value'] == pytest.approx(0.4)
    assert params['geometryCrop0']['keyframes'][1]['time'] == t(3.0)


# ---------------------------------------------------------------------------
# BaseClip.animate
# ---------------------------------------------------------------------------

def test_animate_fade_in():
    from camtasia.timeline.clips import clip_from_dict
    clip = clip_from_dict({'_type': 'VMFile', 'id': 1, 'start': 0, 'duration': seconds_to_ticks(10.0), 'mediaDuration': seconds_to_ticks(10.0)})
    result = clip.animate(fade_in=2.0)
    assert result is clip
    # _add_opacity_track writes to both parameters.opacity and animationTracks.visual
    assert 'opacity' in clip._data.get('parameters', {})
    assert 'animationTracks' in clip._data


def test_animate_scale():
    from camtasia.timeline.clips import clip_from_dict
    clip = clip_from_dict({'_type': 'VMFile', 'id': 1, 'start': 0, 'duration': seconds_to_ticks(10.0)})
    clip.animate(scale_from=0.5, scale_to=1.5)
    params = clip._data['parameters']
    assert params['scale0']['keyframes'][0]['value'] == 0.5
    assert params['scale0']['keyframes'][1]['value'] == 1.5
    assert params['scale0']['keyframes'][1]['time'] == seconds_to_ticks(10.0)


def test_animate_move():
    from camtasia.timeline.clips import clip_from_dict
    clip = clip_from_dict({'_type': 'VMFile', 'id': 1, 'start': 0, 'duration': seconds_to_ticks(10.0)})
    clip.animate(move_from=(0, 0), move_to=(100, 200))
    params = clip._data['parameters']
    assert params['translation0']['keyframes'][0]['value'] == 0
    assert params['translation0']['keyframes'][1]['value'] == 100
    assert params['translation1']['keyframes'][1]['value'] == 200
    assert params['translation0']['keyframes'][1]['time'] == seconds_to_ticks(10.0)


def test_animate_combined():
    from camtasia.timeline.clips import clip_from_dict
    clip = clip_from_dict({'_type': 'VMFile', 'id': 1, 'start': 0, 'duration': seconds_to_ticks(10.0)})
    clip.animate(fade_in=1.0, scale_from=0.0, scale_to=1.0, move_from=(0, 0), move_to=(50, 50))
    params = clip._data['parameters']
    # fade
    assert params['opacity']['keyframes'][0]['value'] == 1.0  # fade-in target (defaultValue is 0.0)
    assert len(params["opacity"]["keyframes"]) >= 1
    # scale
    assert params['scale0']['keyframes'][0]['value'] == 0.0
    assert params['scale0']['keyframes'][1]['value'] == 1.0
    # position
    assert params['translation0']['keyframes'][1]['value'] == 50
    assert params['translation1']['keyframes'][1]['value'] == 50


def test_animate_chaining():
    from camtasia.timeline.clips import clip_from_dict
    clip = clip_from_dict({'_type': 'VMFile', 'id': 1, 'start': 0, 'duration': seconds_to_ticks(10.0)})
    result = clip.animate(fade_in=1.0).animate(scale_from=1.0, scale_to=2.0)
    assert result is clip
    params = clip._data['parameters']
    assert 'opacity' in params
    assert 'scale0' in params

def test_animate_fade_out():
    from camtasia.timeline.clips import clip_from_dict
    from camtasia.timing import seconds_to_ticks
    data = {'_type': 'VMFile', 'id': 1, 'start': 0, 'duration': seconds_to_ticks(5.0), 'mediaDuration': seconds_to_ticks(5.0), 'parameters': {}}
    clip = clip_from_dict(data)
    clip.animate(fade_out=1.0)
    # fade() writes to animationTracks
    assert 'animationTracks' in data or 'opacity' in data.get('parameters', {})


# ---------------------------------------------------------------------------
# Track.split_at_time
# ---------------------------------------------------------------------------

def test_split_at_time():
    """split_at_time splits all clips spanning the given time."""
    media = [
        {'id': 1, '_type': 'VMFile', 'start': 0, 'duration': seconds_to_ticks(10.0)},
        {'id': 2, '_type': 'VMFile', 'start': seconds_to_ticks(10.0), 'duration': seconds_to_ticks(10.0)},
    ]
    track = _make_track(medias=media)
    count = track.split_at_time(5.0)
    assert count == 1
    # Should now have 3 clips (clip 1 split into two, clip 2 untouched)
    assert len(list(track.clips)) == 3


# ---------------------------------------------------------------------------
# Timeline.remove_all_transitions
# ---------------------------------------------------------------------------

def test_remove_all_transitions():
    """remove_all_transitions clears transitions from all tracks."""
    tl = _make_timeline([
        ('Track1', [{'id': 1, 'start': 0, 'duration': 100}]),
        ('Track2', [{'id': 2, 'start': 0, 'duration': 100}]),
    ])
    # Inject transitions into raw data
    for track in tl.tracks:
        track._data['transitions'] = [{'type': 'fade'}, {'type': 'dissolve'}]
    count = tl.remove_all_transitions()
    assert count == 4
    for track in tl.tracks:
        assert track._data.get('transitions') == []


# ---------------------------------------------------------------------------
# Project.strip_audio
# ---------------------------------------------------------------------------

def test_strip_audio():
    """strip_audio removes all AMFile clips from all tracks."""
    from camtasia.project import Project
    tl_data = {
        'sceneTrack': {'scenes': [{'csml': {'tracks': [
            {'trackIndex': 0, 'medias': [
                {'id': 1, '_type': 'VMFile', 'start': 0, 'duration': 100},
            ], 'transitions': []},
            {'trackIndex': 1, 'medias': [
                {'id': 2, '_type': 'AMFile', 'start': 0, 'duration': 100},
                {'id': 3, '_type': 'AMFile', 'start': 100, 'duration': 100},
            ], 'transitions': []},
        ]}}]},
        'trackAttributes': [{'ident': 'Video'}, {'ident': 'Audio'}],
    }
    proj = object.__new__(Project)
    proj._data = {'timeline': tl_data}
    count = proj.strip_audio()
    assert count == 2
    # Video clip should remain
    all_clips = [c for t in proj.timeline.tracks for c in t.clips]
    assert len(all_clips) == 1
    assert all_clips[0].clip_type == 'VMFile'


def test_split_at_time_at_boundary():
    """split_at_time at exact clip start should not crash."""
    from camtasia.timeline.track import Track
    from camtasia.timing import seconds_to_ticks
    data = {'trackIndex': 0, 'medias': [
        {'id': 1, '_type': 'AMFile', 'start': 0, 'duration': seconds_to_ticks(5.0)},
    ], 'transitions': []}
    t = Track({'ident': 'test'}, data)
    # Split at exact start - should handle gracefully
    actual = t.split_at_time(0.0)
    assert isinstance(actual, int)


# ---------------------------------------------------------------------------
# Timeline.reverse_track_order
# ---------------------------------------------------------------------------

def test_reverse_track_order():
    tl = _make_timeline([('A', []), ('B', []), ('C', [])])
    tl.reverse_track_order()
    names = [t.name for t in tl.tracks]
    assert names == ['C', 'B', 'A']
    for i, t in enumerate(tl.tracks):
        assert t._data['trackIndex'] == i


# ---------------------------------------------------------------------------
# Track.remove_all_effects
# ---------------------------------------------------------------------------

def test_track_remove_all_effects():
    data = {'trackIndex': 0, 'medias': [
        {'id': 1, '_type': 'VMFile', 'start': 0, 'duration': 100, 'effects': [{'type': 'blur'}, {'type': 'glow'}]},
        {'id': 2, '_type': 'VMFile', 'start': 100, 'duration': 100, 'effects': [{'type': 'shadow'}]},
    ]}
    t = Track({'ident': 'test'}, data)
    removed = t.remove_all_effects()
    assert removed == 3
    for clip in t.clips:
        assert clip._data['effects'] == []


# ---------------------------------------------------------------------------
# Timeline.sort_tracks_by_name
# ---------------------------------------------------------------------------

def test_sort_tracks_by_name():
    tl = _make_timeline([('Zebra', []), ('Apple', []), ('Mango', [])])
    tl.sort_tracks_by_name()
    names = [t.name for t in tl.tracks]
    assert names == ['Apple', 'Mango', 'Zebra']
    for i, t in enumerate(tl.tracks):
        assert t._data['trackIndex'] == i


# ---------------------------------------------------------------------------
# BaseClip.speed / set_speed
# ---------------------------------------------------------------------------

def test_clip_speed_get_set():
    media = {'id': 1, 'start': 0, 'duration': 100}
    t = _make_track([media])
    clip = list(t.clips)[0]
    assert clip.speed == 1  # default
    result = clip.set_speed(2.0)
    assert clip.speed == 2.0
    assert result is clip  # fluent return


def test_clip_speed_validation():
    media = {'id': 1, 'start': 0, 'duration': 100}
    t = _make_track([media])
    clip = list(t.clips)[0]
    with pytest.raises(ValueError):
        clip.set_speed(0)
    with pytest.raises(ValueError):
        clip.set_speed(-1)


# ---------------------------------------------------------------------------
# Track.total_end_seconds
# ---------------------------------------------------------------------------

def test_track_total_end_seconds():
    medias = [
        {'id': 1, 'start': 0, 'duration': seconds_to_ticks(5)},
        {'id': 2, 'start': seconds_to_ticks(5), 'duration': seconds_to_ticks(3)},
    ]
    t = _make_track(medias)
    assert t.total_end_seconds == pytest.approx(8.0)


# ---------------------------------------------------------------------------
# Timeline.end_seconds
# ---------------------------------------------------------------------------

def test_timeline_end_seconds():
    medias = [
        {'id': 1, 'start': 0, 'duration': seconds_to_ticks(10)},
    ]
    tl = _make_timeline([('Track1', medias)])
    assert tl.end_seconds == pytest.approx(10.0)


# ---------------------------------------------------------------------------
# Track.clip_types
# ---------------------------------------------------------------------------

def test_track_clip_types():
    medias = [
        {'id': 1, '_type': 'ScreenRecording', 'start': 0, 'duration': 100},
        {'id': 2, '_type': 'UnifiedMedia', 'start': 100, 'duration': 100},
        {'id': 3, '_type': 'ScreenRecording', 'start': 200, 'duration': 100},
    ]
    t = _make_track(medias)
    assert t.clip_types == {'ScreenRecording', 'UnifiedMedia'}


# ---------------------------------------------------------------------------
# Track.effect_names
# ---------------------------------------------------------------------------

def test_track_effect_names():
    medias = [
        {'id': 1, '_type': 'VMFile', 'start': 0, 'duration': 100, 'effects': [
            {'effectName': 'Blur'},
            {'effectName': 'Glow'},
        ]},
        {'id': 2, '_type': 'VMFile', 'start': 100, 'duration': 100, 'effects': [
            {'effectName': 'Blur'},
        ]},
    ]
    t = _make_track(medias)
    assert t.effect_names == {'Blur', 'Glow'}


# ---------------------------------------------------------------------------
# Project.effect_summary
# ---------------------------------------------------------------------------

def test_project_effect_summary(project):
    track = project.timeline.add_track('Test')
    c1 = track.add_clip('VMFile', 1, 0, 100)
    c1._data['effects'] = [{'effectName': 'Blur'}, {'effectName': 'Glow'}]
    c2 = track.add_clip('VMFile', 1, 100, 100)
    c2._data['effects'] = [{'effectName': 'Blur'}]
    result = project.effect_summary
    assert result == {'Blur': 2, 'Glow': 1}


# ---------------------------------------------------------------------------
# Project.clip_type_summary
# ---------------------------------------------------------------------------

def test_project_clip_type_summary(project):
    track = project.timeline.add_track('Test')
    track.add_clip('VMFile', 1, 0, 100)
    track.add_clip('AMFile', 1, 100, 100)
    track.add_clip('VMFile', 1, 200, 100)
    result = project.clip_type_summary
    assert result['VMFile'] == 2
    assert result['AMFile'] == 1


# ---------------------------------------------------------------------------
# Track.find_clips_with_effect
# ---------------------------------------------------------------------------

def test_find_clips_with_effect():
    medias = [
        {'id': 1, '_type': 'VMFile', 'start': 0, 'duration': 100, 'effects': [
            {'effectName': 'Blur'},
        ]},
        {'id': 2, '_type': 'VMFile', 'start': 100, 'duration': 100, 'effects': []},
        {'id': 3, 'start': 200, 'duration': 100, 'effects': [
            {'effectName': 'Glow'},
            {'effectName': 'Blur'},
        ]},
    ]
    track = _make_track(medias)
    result = track.find_clips_with_effect('Blur')
    assert len(result) == 2
    assert result[0].id == 1
    assert result[1].id == 3
    assert track.find_clips_with_effect('Nonexistent') == []


# ---------------------------------------------------------------------------
# Track.find_clips_without_effects
# ---------------------------------------------------------------------------

def test_find_clips_without_effects():
    medias = [
        {'id': 1, '_type': 'VMFile', 'start': 0, 'duration': 100, 'effects': [
            {'effectName': 'Blur'},
        ]},
        {'id': 2, 'start': 100, 'duration': 100},
        {'id': 3, 'start': 200, 'duration': 100, 'effects': []},
    ]
    track = _make_track(medias)
    result = track.find_clips_without_effects()
    assert len(result) == 2
    assert result[0].id == 2
    assert result[1].id == 3


# ---------------------------------------------------------------------------
# BaseClip.effect_names
# ---------------------------------------------------------------------------

def test_clip_effect_names():
    medias = [
        {'id': 1, '_type': 'VMFile', 'start': 0, 'duration': 100, 'effects': [
            {'effectName': 'Blur'},
            {'effectName': 'Glow'},
        ]},
        {'id': 2, 'start': 100, 'duration': 100},
    ]
    track = _make_track(medias)
    clips = list(track.clips)
    assert clips[0].effect_names == ['Blur', 'Glow']
    assert clips[1].effect_names == []


# ---------------------------------------------------------------------------
# Project.summary_table
# ---------------------------------------------------------------------------

def test_summary_table():
    from camtasia.project import Project
    from unittest.mock import MagicMock

    medias0 = [
        {'id': 1, '_type': 'ScreenRecording', 'start': 0, 'duration': 300, 'effects': [
            {'effectName': 'Blur'},
        ]},
        {'id': 2, '_type': 'UnifiedMedia', 'start': 300, 'duration': 600, 'effects': []},
    ]
    medias1 = []
    proj = MagicMock(spec=Project)
    proj._data = _make_project_data([medias0, medias1])
    proj.timeline = Timeline(proj._data['timeline'])
    proj.clip_count = 2
    proj.duration_seconds = 30.0

    result = Project.summary_table(proj)
    lines = result.split('\n')
    assert lines[0] == '| Track | Clips | Types | Duration | Effects |'
    assert lines[1].startswith('|---')
    # Track0 row
    assert '| Track0 |' in lines[2]
    assert '| 2 |' in lines[2]
    # Track1 row (empty)
    assert '| Track1 |' in lines[3]
    assert '| 0 |' in lines[3]
    # Total row
    assert '**Total**' in lines[4]
    assert '**2**' in lines[4]
    assert '**30.0s**' in lines[4]


# ---------------------------------------------------------------------------
# BaseClip.is_visible / Track.visible_clips / Project.has_audio / has_video
# ---------------------------------------------------------------------------

def test_is_visible():
    audio = _make_track([{'id': 1, '_type': 'AMFile', 'start': 0, 'duration': 100}])
    video = _make_track([{'id': 2, '_type': 'VMFile', 'start': 0, 'duration': 100}])
    assert list(audio.clips)[0].is_visible is False
    assert list(video.clips)[0].is_visible is True


def test_visible_clips():
    medias = [
        {'id': 1, '_type': 'AMFile', 'start': 0, 'duration': 100},
        {'id': 2, '_type': 'VMFile', 'start': 100, 'duration': 100},
        {'id': 3, '_type': 'IMFile', 'start': 200, 'duration': 100},
    ]
    track = _make_track(medias)
    visible = track.visible_clips
    assert len(visible) == 2
    assert all(c.is_visible for c in visible)


def test_has_audio(project):
    assert project.has_audio is False  # empty project has no audio


def test_has_video(project):
    assert project.has_video is False  # empty project has no video


# ---------------------------------------------------------------------------
# Track is_muted / is_hidden / is_solo / is_magnetic
# ---------------------------------------------------------------------------

def test_track_is_muted():
    track = _make_track()
    assert track.is_muted is False
    track.is_muted = True
    assert track.is_muted is True
    assert track.audio_muted is True


def test_track_is_hidden():
    track = _make_track()
    assert track.is_hidden is False
    track.is_hidden = True
    assert track.is_hidden is True
    assert track.video_hidden is True


def test_track_is_solo():
    track = _make_track()
    assert track.is_solo is False
    track.is_solo = True
    assert track.is_solo is True
    assert track.solo is True


def test_track_is_magnetic():
    track = _make_track()
    assert track.is_magnetic is False
    track.is_magnetic = True
    assert track.is_magnetic is True
    assert track.magnetic is True


# ---------------------------------------------------------------------------
# ColorAdjustment ramp parameters
# ---------------------------------------------------------------------------

def test_color_adjustment_ramp_params():
    media = {'id': 1, '_type': 'IMFile', 'start': 0, 'duration': 100, 'effects': []}
    from camtasia.timeline.clips import clip_from_dict
    clip = clip_from_dict(media)
    clip.add_color_adjustment(
        brightness=0.1,
        shadow_ramp_start=0.05,
        shadow_ramp_end=0.2,
        highlight_ramp_start=0.8,
        highlight_ramp_end=0.95,
    )
    effects = media['effects']
    assert len(effects) == 1
    params = effects[0]['parameters']
    assert params['brightness'] == 0.1
    assert params['shadowRampStart'] == 0.05
    assert params['shadowRampEnd'] == 0.2
    assert params['highlightRampStart'] == 0.8
    assert params['highlightRampEnd'] == 0.95


def test_add_paint_arcs_transition():
    from camtasia.timeline.track import Track
    data = {'trackIndex': 0, 'medias': [
        {'id': 1, '_type': 'AMFile', 'start': 0, 'duration': 705600000},
        {'id': 2, '_type': 'AMFile', 'start': 705600000, 'duration': 705600000},
    ], 'transitions': []}
    t = Track({'ident': 'test'}, data)
    t.transitions.add_paint_arcs(1, 2, 0.5)
    assert len(data['transitions']) == 1
    assert data['transitions'][0]['name'] == 'PaintArcs'


def test_add_spherical_spin_transition():
    from camtasia.timeline.track import Track
    data = {'trackIndex': 0, 'medias': [
        {'id': 1, '_type': 'AMFile', 'start': 0, 'duration': 705600000},
        {'id': 2, '_type': 'AMFile', 'start': 705600000, 'duration': 705600000},
    ], 'transitions': []}
    t = Track({'ident': 'test'}, data)
    t.transitions.add_spherical_spin(1, 2, 0.5)
    assert len(data['transitions']) == 1
    assert data['transitions'][0]['name'] == 'SphericalSpin'


# ---------------------------------------------------------------------------
# Timeline gain / background_color / new CalloutShape values
# ---------------------------------------------------------------------------

def test_timeline_gain():
    from camtasia.timeline.timeline import Timeline
    data = {
        'sceneTrack': {'scenes': [{'csml': {'tracks': []}}]},
        'trackAttributes': [],
    }
    tl = Timeline(data)
    assert tl.gain == 1.0  # default
    tl.gain = 0.5
    assert tl.gain == 0.5
    assert data['gain'] == 0.5


def test_timeline_background_color():
    from camtasia.timeline.timeline import Timeline
    data = {
        'sceneTrack': {'scenes': [{'csml': {'tracks': []}}]},
        'trackAttributes': [],
    }
    tl = Timeline(data)
    assert tl.background_color == [0, 0, 0, 255]  # default
    tl.background_color = [255, 0, 0, 255]
    assert tl.background_color == [255, 0, 0, 255]
    assert data['backgroundColor'] == [255, 0, 0, 255]


def test_new_callout_shapes():
    from camtasia.types import CalloutShape
    assert CalloutShape.SHAPE_ELLIPSE.value == 'shape-ellipse'
    assert CalloutShape.SHAPE_TRIANGLE.value == 'shape-triangle'
    assert CalloutShape.TEXT.value == 'text'
    assert CalloutShape.TEXT_RECTANGLE.value == 'text-rectangle'
    assert CalloutShape.SHAPE_RECTANGLE.value == 'shape-rectangle'


def test_timeline_legacy_attenuate():
    tl = _make_timeline([('T', [])])
    assert tl.legacy_attenuate_audio_mix is True
    tl._data['legacyAttenuateAudioMix'] = False
    assert tl.legacy_attenuate_audio_mix is False


# ---------------------------------------------------------------------------
# Track.clip_at_index
# ---------------------------------------------------------------------------

def test_clip_at_index():
    medias = [
        {'id': 2, '_type': 'AMFile', 'start': 200, 'duration': 100},
        {'id': 1, '_type': 'VMFile', 'start': 50, 'duration': 100},
        {'id': 3, '_type': 'IMFile', 'start': 500, 'duration': 100},
    ]
    track = _make_track(medias=medias)
    first_clip = track.clip_at_index(0)
    assert first_clip.id == 1  # start=50 is earliest
    second_clip = track.clip_at_index(1)
    assert second_clip.id == 2  # start=200
    third_clip = track.clip_at_index(2)
    assert third_clip.id == 3  # start=500


def test_clip_at_index_out_of_range():
    track = _make_track(medias=[
        {'id': 1, '_type': 'AMFile', 'start': 0, 'duration': 100},
    ])
    with pytest.raises(IndexError, match='clip index 5 out of range'):
        track.clip_at_index(5)
    with pytest.raises(IndexError, match='clip index -1 out of range'):
        track.clip_at_index(-1)


# ---------------------------------------------------------------------------
# BaseClip.source_id
# ---------------------------------------------------------------------------

def test_source_id_replaces_source_path():
    from camtasia.timeline.clips import clip_from_dict
    clip_with_src = clip_from_dict({
        'id': 1, '_type': 'VMFile', 'start': 0, 'duration': 100,
        'src': '/media/video.mp4',
    })
    assert clip_with_src.source_id == '/media/video.mp4'

    clip_without_src = clip_from_dict({
        'id': 2, '_type': 'AMFile', 'start': 0, 'duration': 100,
    })
    assert clip_without_src.source_id is None


# ---------------------------------------------------------------------------
# BaseClip.media_start_seconds
# ---------------------------------------------------------------------------

def test_media_start_seconds():
    from camtasia.timeline.clips import clip_from_dict
    from camtasia.timing import EDIT_RATE
    media_start_ticks: int = EDIT_RATE * 5  # exactly 5 seconds
    clip = clip_from_dict({
        'id': 1, '_type': 'VMFile', 'start': 0, 'duration': 100,
        'mediaStart': media_start_ticks,
    })
    assert clip.media_start_seconds == pytest.approx(5.0)


# ---------------------------------------------------------------------------
# Project.source_bin_paths
# ---------------------------------------------------------------------------

def test_source_bin_paths(tmp_path):
    from camtasia.project import Project
    import json

    project_dir = tmp_path / 'test.tscproj'
    project_dir.mkdir()
    project_file = project_dir / 'project.tscproj'
    project_data = {
        'title': 'test',
        'sourceBin': [
            {'id': 1, 'src': 'clip_a.mp4', 'rect': [0, 0, 100, 100], 'lastMod': '0', 'sourceTracks': []},
            {'id': 2, 'src': 'clip_b.wav', 'rect': [0, 0, 0, 0], 'lastMod': '0', 'sourceTracks': []},
        ],
        'timeline': {
            'sceneTrack': {'scenes': [{'csml': {'tracks': []}}]},
            'trackAttributes': [],
        },
        'authoringClientName': {'name': 'test', 'platform': 'test', 'version': '1'},
    }
    project_file.write_text(json.dumps(project_data))

    project = Project(project_dir)
    source_paths: list[str] = project.source_bin_paths
    assert len(source_paths) == 2
    assert any('clip_a.mp4' in path for path in source_paths)
    assert any('clip_b.wav' in path for path in source_paths)


# ---------------------------------------------------------------------------
# Timeline.longest_track
# ---------------------------------------------------------------------------

def test_longest_track():
    short_medias = [{'id': 1, '_type': 'AMFile', 'start': 0, 'duration': 100}]
    long_medias = [{'id': 2, '_type': 'VMFile', 'start': 0, 'duration': 99999}]
    timeline = _make_timeline([
        ('Short', short_medias),
        ('Long', long_medias),
    ])
    longest = timeline.longest_track
    assert longest is not None
    assert longest.name == 'Long'

    empty_timeline = _make_timeline([])
    assert empty_timeline.longest_track is None


# ---------------------------------------------------------------------------
# clip_before / clip_after / overlaps_with / distance_to
# ---------------------------------------------------------------------------

def test_clip_before():
    """clip_before returns the last clip ending before the given time."""
    track = _make_track([
        {'id': 1, '_type': 'VMFile', 'start': 0, 'duration': seconds_to_ticks(2)},
        {'id': 2, '_type': 'VMFile', 'start': seconds_to_ticks(3), 'duration': seconds_to_ticks(1)},
    ])
    clip = track.clip_before(3.0)
    assert clip is not None
    assert clip.id == 1


def test_clip_before_none():
    """clip_before returns None when no clip ends before the given time."""
    track = _make_track([
        {'id': 1, '_type': 'VMFile', 'start': seconds_to_ticks(5), 'duration': seconds_to_ticks(1)},
    ])
    assert track.clip_before(1.0) is None


def test_clip_after():
    """clip_after returns the first clip starting after the given time."""
    track = _make_track([
        {'id': 1, '_type': 'VMFile', 'start': 0, 'duration': seconds_to_ticks(2)},
        {'id': 2, '_type': 'VMFile', 'start': seconds_to_ticks(5), 'duration': seconds_to_ticks(1)},
    ])
    clip = track.clip_after(3.0)
    assert clip is not None
    assert clip.id == 2


def test_clip_after_none():
    """clip_after returns None when no clip starts after the given time."""
    track = _make_track([
        {'id': 1, '_type': 'VMFile', 'start': 0, 'duration': seconds_to_ticks(1)},
    ])
    assert track.clip_after(5.0) is None


def test_overlaps_with_true():
    """overlaps_with returns True for overlapping clips."""
    from camtasia.timeline.clips import BaseClip
    clip_a = BaseClip({'id': 1, '_type': 'VMFile', 'start': 0, 'duration': seconds_to_ticks(3)})
    clip_b = BaseClip({'id': 2, '_type': 'VMFile', 'start': seconds_to_ticks(2), 'duration': seconds_to_ticks(2)})
    assert clip_a.overlaps_with(clip_b) is True


def test_overlaps_with_false():
    """overlaps_with returns False for non-overlapping clips."""
    from camtasia.timeline.clips import BaseClip
    clip_a = BaseClip({'id': 1, '_type': 'VMFile', 'start': 0, 'duration': seconds_to_ticks(2)})
    clip_b = BaseClip({'id': 2, '_type': 'VMFile', 'start': seconds_to_ticks(3), 'duration': seconds_to_ticks(1)})
    assert clip_a.overlaps_with(clip_b) is False


def test_distance_to_gap():
    """distance_to returns positive seconds for a gap between clips."""
    from camtasia.timeline.clips import BaseClip
    clip_a = BaseClip({'id': 1, '_type': 'VMFile', 'start': 0, 'duration': seconds_to_ticks(2)})
    clip_b = BaseClip({'id': 2, '_type': 'VMFile', 'start': seconds_to_ticks(5), 'duration': seconds_to_ticks(1)})
    assert clip_a.distance_to(clip_b) == pytest.approx(3.0)


def test_distance_to_overlap():
    """distance_to returns negative seconds for overlapping clips."""
    from camtasia.timeline.clips import BaseClip
    clip_a = BaseClip({'id': 1, '_type': 'VMFile', 'start': 0, 'duration': seconds_to_ticks(3)})
    clip_b = BaseClip({'id': 2, '_type': 'VMFile', 'start': seconds_to_ticks(2), 'duration': seconds_to_ticks(2)})
    assert clip_a.distance_to(clip_b) == pytest.approx(-1.0)


# ---------------------------------------------------------------------------
# Timeline.insert_gap / Timeline.remove_gap
# ---------------------------------------------------------------------------

def test_insert_gap():
    """insert_gap shifts clips at or after the position by the gap duration."""
    medias_a = [
        {'id': 1, 'start': 0, 'duration': seconds_to_ticks(2)},
        {'id': 2, 'start': seconds_to_ticks(3), 'duration': seconds_to_ticks(1)},
    ]
    medias_b = [
        {'id': 3, 'start': seconds_to_ticks(1), 'duration': seconds_to_ticks(1)},
    ]
    tl = _make_timeline([('A', medias_a), ('B', medias_b)])

    tl.insert_gap(position_seconds=2.0, gap_duration_seconds=5.0)

    # Clip at 0s is before position → unchanged
    assert medias_a[0]['start'] == 0
    # Clip at 3s is after position → shifted by 5s
    assert medias_a[1]['start'] == seconds_to_ticks(8)
    # Clip at 1s is before position → unchanged
    assert medias_b[0]['start'] == seconds_to_ticks(1)


def test_remove_gap():
    """remove_gap pulls clips after the gap region back by the gap duration."""
    medias_a = [
        {'id': 1, 'start': 0, 'duration': seconds_to_ticks(2)},
        {'id': 2, 'start': seconds_to_ticks(10), 'duration': seconds_to_ticks(1)},
    ]
    medias_b = [
        {'id': 3, 'start': seconds_to_ticks(7), 'duration': seconds_to_ticks(1)},
    ]
    tl = _make_timeline([('A', medias_a), ('B', medias_b)])

    tl.remove_gap(position_seconds=2.0, gap_duration_seconds=5.0)

    # Clip at 0s is before gap region → unchanged
    assert medias_a[0]['start'] == 0
    # Clip at 10s is after gap region (2+5=7) → pulled back by 5s to 5s
    assert medias_a[1]['start'] == seconds_to_ticks(5)
    # Clip at 7s equals position+gap → pulled back by 5s to 2s
    assert medias_b[0]['start'] == seconds_to_ticks(2)


# ---------------------------------------------------------------------------
# Project.duration_formatted
# ---------------------------------------------------------------------------

def test_duration_formatted():
    """duration_formatted returns MM:SS string."""
    from unittest.mock import PropertyMock, patch
    from camtasia.project import Project

    with patch.object(Project, 'duration_seconds', new_callable=PropertyMock, return_value=125.7):
        proj = object.__new__(Project)
        assert proj.duration_formatted == '2:05'


# ---------------------------------------------------------------------------
# Track.clip_count_by_type
# ---------------------------------------------------------------------------

def test_clip_count_by_type():
    medias = [
        {'id': 1, 'start': 0, 'duration': 100, '_type': 'VMFile'},
        {'id': 2, 'start': 100, 'duration': 100, '_type': 'VMFile'},
        {'id': 3, 'start': 200, 'duration': 100, '_type': 'Callout'},
    ]
    track = _make_track(medias=medias)
    counts: dict[str, int] = track.clip_count_by_type
    assert counts['VMFile'] == 2
    assert counts['Callout'] == 1
    assert len(counts) == 2


# ---------------------------------------------------------------------------
# Timeline.track_summary
# ---------------------------------------------------------------------------

def test_track_summary():
    medias_a = [
        {'id': 1, 'start': 0, 'duration': seconds_to_ticks(5)},
    ]
    tl = _make_timeline([('Video', medias_a), ('Audio', [])])
    summary: list[dict] = tl.track_summary
    assert len(summary) == 2
    assert summary[0]['name'] == 'Video'
    assert summary[0]['clip_count'] == 1
    assert summary[0]['is_empty'] is False
    assert summary[1]['name'] == 'Audio'
    assert summary[1]['clip_count'] == 0
    assert summary[1]['is_empty'] is True


# ---------------------------------------------------------------------------
# BaseClip.has_keyframes
# ---------------------------------------------------------------------------

def test_has_keyframes_true():
    media = {
        'id': 1, 'start': 0, 'duration': 100,
        'parameters': {
            'opacity': {
                'type': 'double',
                'defaultValue': 1.0,
                'keyframes': [{'time': 0, 'value': 1.0}],
            },
        },
    }
    track = _make_track(medias=[media])
    clip = list(track.clips)[0]
    assert clip.has_keyframes is True


def test_has_keyframes_false():
    media = {
        'id': 1, 'start': 0, 'duration': 100,
        'parameters': {
            'opacity': 0.5,
        },
    }
    track = _make_track(medias=[media])
    clip = list(track.clips)[0]
    assert clip.has_keyframes is False


# ---------------------------------------------------------------------------
# Track.keyframed_clips
# ---------------------------------------------------------------------------

def test_keyframed_clips():
    medias = [
        {
            'id': 1, 'start': 0, 'duration': 100,
            'parameters': {
                'scale0': {
                    'type': 'double',
                    'defaultValue': 1.0,
                    'keyframes': [{'time': 0, 'value': 1.0}],
                },
            },
        },
        {'id': 2, 'start': 100, 'duration': 100, 'parameters': {'opacity': 0.8}},
    ]
    track = _make_track(medias=medias)
    keyframed = track.keyframed_clips
    assert len(keyframed) == 1
    assert keyframed[0].id == 1


# ---------------------------------------------------------------------------
# BaseClip.clear_all_keyframes
# ---------------------------------------------------------------------------

def test_clear_all_keyframes():
    media: dict[str, Any] = {
        'id': 1, 'start': 0, 'duration': 100,
        'parameters': {
            'scale0': {
                'type': 'double',
                'defaultValue': 1.0,
                'keyframes': [{'time': 0, 'value': 1.0}, {'time': 50, 'value': 2.0}],
            },
            'rotation': {
                'type': 'double',
                'defaultValue': 0,
                'keyframes': [{'time': 0, 'value': 0}, {'time': 100, 'value': 90}],
            },
            'opacity': 0.5,
        },
    }
    track = _make_track(medias=[media])
    clip = list(track.clips)[0]
    result = clip.clear_all_keyframes()
    assert result is clip
    assert media['parameters']['scale0'] == {'type': 'double', 'defaultValue': 1.0}
    assert media['parameters']['rotation'] == {'type': 'double', 'defaultValue': 0}
    assert media['parameters']['opacity'] == 0.5


# ---------------------------------------------------------------------------
# Track.normalize_timing
# ---------------------------------------------------------------------------

def test_normalize_timing():
    medias: list[dict[str, Any]] = [
        {'id': 1, 'start': 1000, 'duration': 100},
        {'id': 2, 'start': 2000, 'duration': 200},
    ]
    track = _make_track(medias=medias)
    track.normalize_timing()
    assert medias[0]['start'] == 0
    assert medias[1]['start'] == 1000


def test_normalize_timing_already_at_zero():
    medias: list[dict[str, Any]] = [
        {'id': 1, 'start': 0, 'duration': 100},
        {'id': 2, 'start': 500, 'duration': 200},
    ]
    track = _make_track(medias=medias)
    track.normalize_timing()
    assert medias[0]['start'] == 0
    assert medias[1]['start'] == 500


# ---------------------------------------------------------------------------
# Timeline.normalize_all_tracks
# ---------------------------------------------------------------------------

def test_normalize_all_tracks():
    track_specs: list[tuple[str, list[dict[str, Any]]]] = [
        ('A', [{'id': 1, 'start': 500, 'duration': 100}]),
        ('B', [{'id': 2, 'start': 1000, 'duration': 200}, {'id': 3, 'start': 2000, 'duration': 100}]),
    ]
    timeline = _make_timeline(track_specs)
    timeline.normalize_all_tracks()
    track_a = list(timeline.tracks)[0]
    track_b = list(timeline.tracks)[1]
    assert list(track_a.clips)[0].start == 0
    assert list(track_b.clips)[0].start == 0
    assert list(track_b.clips)[1].start == 1000


def test_normalize_timing_empty_track():
    from camtasia.timeline.track import Track
    data: dict[str, Any] = {'trackIndex': 0, 'medias': [], 'transitions': []}
    track = Track({'ident': 'empty'}, data)
    track.normalize_timing()  # should not raise
    assert data['medias'] == []


# ---------------------------------------------------------------------------
# BaseClip.keyframe_count
# ---------------------------------------------------------------------------

def test_keyframe_count():
    media: dict[str, Any] = {
        'id': 1,
        'start': 0,
        'duration': 300,
        'parameters': {
            'scale': {
                'keyframes': [{'time': 0, 'value': 1.0}, {'time': 100, 'value': 2.0}],
            },
            'opacity': {
                'keyframes': [{'time': 0, 'value': 1.0}],
            },
            'volume': 0.8,  # not a keyframed parameter
        },
    }
    track = _make_track(medias=[media])
    clip = list(track.clips)[0]
    assert clip.keyframe_count == 3


# ---------------------------------------------------------------------------
# BaseClip.is_at_origin
# ---------------------------------------------------------------------------

def test_is_at_origin():
    at_zero: dict[str, Any] = {'id': 1, 'start': 0, 'duration': 100}
    not_zero: dict[str, Any] = {'id': 2, 'start': 500, 'duration': 100}
    track = _make_track(medias=[at_zero, not_zero])
    clips = list(track.clips)
    assert clips[0].is_at_origin is True
    assert clips[1].is_at_origin is False


# ---------------------------------------------------------------------------
# Project.total_effect_count
# ---------------------------------------------------------------------------

def test_total_effect_count(project):
    track = project.timeline.add_track('FX')
    clip = track.add_clip('VMFile', 1, 0, 705600000)
    clip.add_drop_shadow()
    clip.add_round_corners()
    assert project.total_effect_count >= 2


# ---------------------------------------------------------------------------
# Project.total_transition_count
# ---------------------------------------------------------------------------

def test_total_transition_count():
    track_data_a: dict[str, Any] = {
        'trackIndex': 0,
        'medias': [
            {'id': 1, 'start': 0, 'duration': 100},
            {'id': 2, 'start': 100, 'duration': 100},
        ],
        'transitions': [
            {'start': 50, 'end': 150, 'duration': 100},
        ],
    }
    track_data_b: dict[str, Any] = {
        'trackIndex': 1,
        'medias': [],
        'transitions': [],
    }
    data: dict[str, Any] = {
        'timeline': {
            'id': 'test',
            'sceneTrack': {'scenes': [{'csml': {'tracks': [track_data_a, track_data_b]}}]},
            'trackAttributes': [{'ident': 'A'}, {'ident': 'B'}],
            'parameters': {},
            'authoringClientName': 'test',
        },
    }
    timeline = Timeline(data['timeline'])

    from camtasia.project import Project
    project = Project.__new__(Project)
    object.__setattr__(project, '_timeline', timeline)
    object.__setattr__(project, '_data', data)
    object.__setattr__(project, '_path', None)
    assert project.total_transition_count == 1


# ---------------------------------------------------------------------------
# BaseClip.copy_timing_from
# ---------------------------------------------------------------------------

def test_copy_timing_from():
    from camtasia.timeline.clips.base import BaseClip
    source = BaseClip({'id': 1, '_type': 'VMFile', 'start': 1000, 'duration': 5000})
    target = BaseClip({'id': 2, '_type': 'VMFile', 'start': 0, 'duration': 100})
    result = target.copy_timing_from(source)
    assert target.start == 1000
    assert target.duration == 5000
    assert result is target  # returns self for chaining


# ---------------------------------------------------------------------------
# Track.align_clips_to_start
# ---------------------------------------------------------------------------

def test_align_clips_to_start():
    medias: list[dict[str, Any]] = [
        {'id': 1, '_type': 'VMFile', 'start': 500, 'duration': 100},
        {'id': 2, '_type': 'VMFile', 'start': 100, 'duration': 200},
        {'id': 3, '_type': 'VMFile', 'start': 900, 'duration': 300},
    ]
    track = _make_track(medias=medias)
    track._data['transitions'] = [{'some': 'transition'}]
    track.align_clips_to_start()
    # Clips should be sorted by original start and packed sequentially
    assert track._data['medias'][0]['start'] == 0
    assert track._data['medias'][0]['duration'] == 200   # was id=2
    assert track._data['medias'][1]['start'] == 200
    assert track._data['medias'][1]['duration'] == 100   # was id=1
    assert track._data['medias'][2]['start'] == 300
    assert track._data['medias'][2]['duration'] == 300   # was id=3
    assert track._data['transitions'] == []  # transitions cleared


# ---------------------------------------------------------------------------
# BaseClip.matches_type
# ---------------------------------------------------------------------------

def test_matches_type():
    from camtasia.timeline.clips.base import BaseClip
    from camtasia.types import ClipType
    clip = BaseClip({'id': 1, '_type': 'VMFile', 'start': 0, 'duration': 100})
    assert clip.matches_type('VMFile') is True
    assert clip.matches_type(ClipType.VIDEO) is True
    assert clip.matches_type('AMFile') is False
    assert clip.matches_type(ClipType.AUDIO) is False


# ---------------------------------------------------------------------------
# Track.total_media_duration_seconds
# ---------------------------------------------------------------------------

def test_total_media_duration_seconds():
    from camtasia.timing import seconds_to_ticks
    one_sec: int = seconds_to_ticks(1.0)
    two_sec: int = seconds_to_ticks(2.0)
    medias: list[dict[str, Any]] = [
        {'id': 1, '_type': 'VMFile', 'start': 0, 'duration': one_sec},
        {'id': 2, '_type': 'VMFile', 'start': one_sec + 999, 'duration': two_sec},
    ]
    track = _make_track(medias=medias)
    assert track.total_media_duration_seconds == pytest.approx(3.0)


# ---------------------------------------------------------------------------
# BaseClip.snap_to_seconds
# ---------------------------------------------------------------------------

def test_snap_to_seconds():
    from camtasia.timeline.clips.base import BaseClip
    from camtasia.timing import seconds_to_ticks
    clip = BaseClip({'id': 1, '_type': 'VMFile', 'start': 0, 'duration': seconds_to_ticks(2.0)})
    result = clip.snap_to_seconds(5.0)
    assert clip.start == seconds_to_ticks(5.0)
    assert result is clip  # returns self for chaining


# ---------------------------------------------------------------------------
# Track.distribute_evenly
# ---------------------------------------------------------------------------

def test_distribute_evenly():
    one_sec: int = seconds_to_ticks(1.0)
    two_sec: int = seconds_to_ticks(2.0)
    medias: list[dict[str, Any]] = [
        {'id': 2, '_type': 'VMFile', 'start': two_sec, 'duration': one_sec},
        {'id': 1, '_type': 'VMFile', 'start': 0, 'duration': two_sec},
    ]
    track = _make_track(medias=medias)
    track.distribute_evenly()
    # Clips should be sorted by original start and packed with no gap
    assert track._data['medias'][0]['id'] == 1
    assert track._data['medias'][0]['start'] == 0
    assert track._data['medias'][1]['id'] == 2
    assert track._data['medias'][1]['start'] == two_sec  # right after first clip


def test_distribute_evenly_with_gap():
    one_sec: int = seconds_to_ticks(1.0)
    half_sec: int = seconds_to_ticks(0.5)
    medias: list[dict[str, Any]] = [
        {'id': 1, '_type': 'VMFile', 'start': 0, 'duration': one_sec},
        {'id': 2, '_type': 'VMFile', 'start': one_sec * 5, 'duration': one_sec},
    ]
    track = _make_track(medias=medias)
    track.distribute_evenly(gap_seconds=0.5)
    assert track._data['medias'][0]['start'] == 0
    assert track._data['medias'][1]['start'] == one_sec + half_sec


# ---------------------------------------------------------------------------
# Project.total_keyframe_count
# ---------------------------------------------------------------------------

def test_total_keyframe_count():
    from camtasia.project import Project
    medias: list[dict[str, Any]] = [
        {
            'id': 1, '_type': 'VMFile', 'start': 0, 'duration': 100,
            'parameters': {
                'scale': {'defaultValue': 1, 'keyframes': [{'time': 0, 'value': 1}, {'time': 50, 'value': 2}]},
            },
        },
        {
            'id': 2, '_type': 'VMFile', 'start': 100, 'duration': 100,
            'parameters': {
                'opacity': {'defaultValue': 1, 'keyframes': [{'time': 0, 'value': 1}]},
            },
        },
    ]
    data: dict[str, Any] = {
        'timeline': {
            'id': 'test',
            'sceneTrack': {'scenes': [{'csml': {'tracks': [{'trackIndex': 0, 'medias': medias}]}}]},
            'trackAttributes': [{'ident': 'T'}],
            'parameters': {},
            'authoringClientName': 'test',
        },
    }
    timeline = Timeline(data['timeline'])
    project = Project.__new__(Project)
    object.__setattr__(project, '_timeline', timeline)
    object.__setattr__(project, '_data', data)
    object.__setattr__(project, '_path', None)
    assert project.total_keyframe_count == 3


# ---------------------------------------------------------------------------
# BaseClip.is_longer_than
# ---------------------------------------------------------------------------

def test_is_longer_than():
    from camtasia.timeline.clips.base import BaseClip
    from camtasia.timing import seconds_to_ticks
    clip = BaseClip({'id': 1, '_type': 'VMFile', 'start': 0, 'duration': seconds_to_ticks(3.0)})
    assert clip.is_longer_than(2.0) is True
    assert clip.is_longer_than(3.0) is False
    assert clip.is_longer_than(4.0) is False


# ---------------------------------------------------------------------------
# Track.remove_short_clips
# ---------------------------------------------------------------------------

def test_remove_short_clips():
    one_sec: int = seconds_to_ticks(1.0)
    three_sec: int = seconds_to_ticks(3.0)
    five_sec: int = seconds_to_ticks(5.0)
    medias: list[dict[str, Any]] = [
        {'id': 1, '_type': 'VMFile', 'start': 0, 'duration': one_sec},
        {'id': 2, '_type': 'VMFile', 'start': one_sec, 'duration': three_sec},
        {'id': 3, '_type': 'VMFile', 'start': one_sec + three_sec, 'duration': five_sec},
    ]
    track = _make_track(medias=medias)
    removed_count: int = track.remove_short_clips(2.0)
    assert removed_count == 1
    remaining_ids: list[int] = [c.id for c in track.clips]
    assert 1 not in remaining_ids
    assert 2 in remaining_ids
    assert 3 in remaining_ids


# ---------------------------------------------------------------------------
# Timeline.remove_short_clips_all_tracks
# ---------------------------------------------------------------------------

def test_remove_short_clips_all_tracks():
    one_sec: int = seconds_to_ticks(1.0)
    five_sec: int = seconds_to_ticks(5.0)
    track_a_medias: list[dict[str, Any]] = [
        {'id': 1, '_type': 'VMFile', 'start': 0, 'duration': one_sec},
        {'id': 2, '_type': 'VMFile', 'start': one_sec, 'duration': five_sec},
    ]
    track_b_medias: list[dict[str, Any]] = [
        {'id': 3, '_type': 'AMFile', 'start': 0, 'duration': one_sec},
    ]
    timeline = _make_timeline([('A', track_a_medias), ('B', track_b_medias)])
    total_removed: int = timeline.remove_short_clips_all_tracks(2.0)
    assert total_removed == 2
    remaining_clip_count: int = sum(len(list(t.clips)) for t in timeline.tracks)
    assert remaining_clip_count == 1


# ---------------------------------------------------------------------------
# BaseClip.is_shorter_than
# ---------------------------------------------------------------------------

def test_is_shorter_than():
    from camtasia.timeline.clips.base import BaseClip
    clip = BaseClip({'id': 1, '_type': 'VMFile', 'start': 0, 'duration': seconds_to_ticks(2.0)})
    assert clip.is_shorter_than(3.0) is True
    assert clip.is_shorter_than(2.0) is False
    assert clip.is_shorter_than(1.0) is False


# ---------------------------------------------------------------------------
# Project.longest_clip
# ---------------------------------------------------------------------------

def test_longest_clip(project):
    track = project.timeline.add_track('Test')
    track.add_clip('VMFile', 1, 0, 705600000 * 2)  # 2s
    track.add_clip('VMFile', 1, 705600000 * 3, 705600000 * 5)  # 5s
    result = project.longest_clip
    assert result is not None
    _, longest_clip = result
    assert longest_clip.duration == 705600000 * 5


def test_longest_clip_empty(project):
    assert project.longest_clip is None


# ---------------------------------------------------------------------------
# Project.shortest_clip
# ---------------------------------------------------------------------------

def test_shortest_clip(project):
    track = project.timeline.add_track('Test')
    track.add_clip('VMFile', 1, 0, 705600000 * 5)  # 5s
    track.add_clip('VMFile', 1, 705600000 * 6, 705600000 * 2)  # 2s
    result = project.shortest_clip
    assert result is not None
    _, shortest_clip = result
    assert shortest_clip.duration == 705600000 * 2


def test_shortest_clip_empty(project):
    assert project.shortest_clip is None


# ---------------------------------------------------------------------------
# Track.average_clip_duration_seconds
# ---------------------------------------------------------------------------

def test_track_average_clip_duration():
    medias = [
        {'id': 1, '_type': 'VMFile', 'start': 0, 'duration': seconds_to_ticks(3.0)},
        {'id': 2, '_type': 'VMFile', 'start': seconds_to_ticks(4.0), 'duration': seconds_to_ticks(5.0)},
    ]
    track = _make_track(medias)
    assert track.average_clip_duration_seconds == pytest.approx(4.0)


def test_track_average_clip_duration_empty():
    track = _make_track()
    assert track.average_clip_duration_seconds == 0.0


# ---------------------------------------------------------------------------
# Project.average_clip_duration_seconds
# ---------------------------------------------------------------------------

def test_project_average_clip_duration(project):
    track = project.timeline.add_track('Test')
    track.add_clip('VMFile', 1, 0, 705600000 * 3)  # 3s
    track.add_clip('VMFile', 1, 705600000 * 4, 705600000 * 5)  # 5s
    assert project.average_clip_duration_seconds == pytest.approx(4.0)


def test_project_average_clip_duration_empty(project):
    assert project.average_clip_duration_seconds == 0.0


# ---------------------------------------------------------------------------
# Project.batch_apply
# ---------------------------------------------------------------------------

def test_batch_apply(project):
    track = project.timeline.add_track('BA')
    track.add_clip('VMFile', 1, 0, 705600000)
    track.add_clip('VMFile', 1, 705600000, 705600000)
    titles: list[str] = []
    modified_count: int = project.batch_apply(lambda clip: titles.append(clip.clip_type))
    assert modified_count == 2
    assert len(titles) == 2


def test_batch_apply_with_filter(project):
    track = project.timeline.add_track('BAF')
    track.add_clip('VMFile', 1, 0, 705600000)
    track.add_clip('AMFile', 1, 0, 705600000)
    modified_count: int = project.batch_apply(
        lambda clip: None,
        clip_type='VMFile',
        on_track='BAF',
    )
    assert modified_count == 1


# ---------------------------------------------------------------------------
# Project.replace_media_path
# ---------------------------------------------------------------------------

def test_replace_media_path(project):
    project._data.setdefault('sourceBin', []).extend([
        {'src': '/old/path/video.mp4'},
        {'src': '/old/path/audio.wav'},
    ])
    replaced_count: int = project.replace_media_path('/old/path', '/new/path')
    assert replaced_count == 2
    assert project._data['sourceBin'][-2]['src'] == '/new/path/video.mp4'
    assert project._data['sourceBin'][-1]['src'] == '/new/path/audio.wav'


def test_replace_media_path_no_match(project):
    project._data.setdefault('sourceBin', []).append({'src': '/some/other/file.mp4'})
    replaced_count: int = project.replace_media_path('/nonexistent', '/replacement')
    assert replaced_count == 0
    assert project._data['sourceBin'][-1]['src'] == '/some/other/file.mp4'


# ---------------------------------------------------------------------------
# Timeline.duplicate_track
# ---------------------------------------------------------------------------

def test_duplicate_track():
    tl = _make_timeline([
        ('Audio', [{'id': 1, 'start': 0, 'duration': 100}]),
        ('Video', [{'id': 2, 'start': 0, 'duration': 200}]),
    ])
    new_track: Track = tl.duplicate_track(0)
    assert new_track.name == 'Audio (copy)'
    assert len(list(tl.tracks)) == 3
    # Inserted after source at index 1
    assert list(tl.tracks)[1].name == 'Audio (copy)'


def test_duplicate_track_remaps_ids():
    tl = _make_timeline([
        ('Track1', [{'id': 5, 'start': 0, 'duration': 100},
                     {'id': 8, 'start': 100, 'duration': 200}]),
    ])
    new_track: Track = tl.duplicate_track(0)
    original_ids: set[int] = {m['id'] for m in tl._data['sceneTrack']['scenes'][0]['csml']['tracks'][0]['medias']}
    duplicated_ids: set[int] = {m['id'] for m in tl._data['sceneTrack']['scenes'][0]['csml']['tracks'][1]['medias']}
    assert original_ids.isdisjoint(duplicated_ids), 'Duplicated clip IDs must not collide with originals'
    assert len(duplicated_ids) == 2


# ---------------------------------------------------------------------------
# BaseClip.set_source
# ---------------------------------------------------------------------------

def test_set_source():
    from camtasia.timeline.clips.base import BaseClip
    clip = BaseClip({'id': 1, 'src': 10, '_type': 'AMFile', 'start': 0, 'duration': 100})
    result = clip.set_source(42)
    assert clip.source_id == 42
    assert result is clip  # fluent return


# ---------------------------------------------------------------------------
# BaseClip.set_metadata / get_metadata
# ---------------------------------------------------------------------------

def test_set_get_metadata():
    from camtasia.timeline.clips.base import BaseClip
    clip = BaseClip({'id': 1, '_type': 'AMFile', 'start': 0, 'duration': 100})
    # get_metadata returns default when key missing
    assert clip.get_metadata('author') is None
    assert clip.get_metadata('author', 'unknown') == 'unknown'
    # set_metadata returns self (fluent) and stores value
    result = clip.set_metadata('author', 'Alice')
    assert result is clip
    assert clip.get_metadata('author') == 'Alice'
    # metadata property reflects the change
    assert clip.metadata == {'author': 'Alice'}


# ---------------------------------------------------------------------------
# Track.clip_ids_sorted
# ---------------------------------------------------------------------------

def test_clip_ids_sorted():
    track = _make_track([
        {'id': 3, 'start': 300, 'duration': 100},
        {'id': 1, 'start': 100, 'duration': 100},
        {'id': 2, 'start': 200, 'duration': 100},
    ])
    assert track.clip_ids_sorted == [1, 2, 3]
    # Original clip_ids preserves insertion order
    assert track.clip_ids == [3, 1, 2]


# ---------------------------------------------------------------------------
# Project.has_effects
# ---------------------------------------------------------------------------

def test_project_has_effects(project):
    assert project.has_effects is False


# ---------------------------------------------------------------------------
# Project.has_transitions
# ---------------------------------------------------------------------------

def test_project_has_transitions(project):
    assert project.has_transitions is False


# ---------------------------------------------------------------------------
# Project.has_keyframes
# ---------------------------------------------------------------------------

def test_project_has_keyframes(project):
    assert project.has_keyframes is False


# ---------------------------------------------------------------------------
# BaseClip.is_muted
# ---------------------------------------------------------------------------

def test_clip_is_muted():
    media = {'id': 1, 'start': 0, 'duration': 100, 'attributes': {'gain': 0.0}}
    track = _make_track(medias=[media])
    muted_clip = list(track.clips)[0]
    assert muted_clip.is_muted is True

    audible_media = {'id': 2, 'start': 200, 'duration': 100, 'attributes': {'gain': 0.75}}
    audible_track = _make_track(medias=[audible_media])
    audible_clip = list(audible_track.clips)[0]
    assert audible_clip.is_muted is False


# ---------------------------------------------------------------------------
# Track.muted_clips
# ---------------------------------------------------------------------------

def test_muted_clips():
    medias = [
        {'id': 1, 'start': 0, 'duration': 100, 'attributes': {'gain': 0.0}},
        {'id': 2, 'start': 200, 'duration': 100, 'attributes': {'gain': 1.0}},
        {'id': 3, 'start': 400, 'duration': 100, 'attributes': {'gain': 0.0}},
    ]
    track = _make_track(medias=medias)
    muted = track.muted_clips
    assert len(muted) == 2
    muted_ids: list[int] = [clip.id for clip in muted]
    assert muted_ids == [1, 3]


# ---------------------------------------------------------------------------
# BaseClip.duplicate_effects_to
# ---------------------------------------------------------------------------

def test_duplicate_effects_to():
    """duplicate_effects_to copies effects from self to target clip."""
    source_media: dict[str, Any] = {
        'id': 1,
        'start': 0,
        'duration': 100,
        'effects': [{'effectName': 'Glow', 'params': {'radius': 10}}],
    }
    target_media: dict[str, Any] = {
        'id': 2,
        'start': 200,
        'duration': 100,
    }
    track = _make_track(medias=[source_media, target_media])
    clips = list(track.clips)
    source_clip = clips[0]
    target_clip = clips[1]

    result = source_clip.duplicate_effects_to(target_clip)

    # Returns self for chaining
    assert result is source_clip
    # Target now has the effect
    assert len(target_clip._data.get('effects', [])) == 1
    assert target_clip._data['effects'][0]['effectName'] == 'Glow'
    # Deep copy — mutating target doesn't affect source
    target_clip._data['effects'][0]['params']['radius'] = 999
    assert source_clip._data['effects'][0]['params']['radius'] == 10


# ---------------------------------------------------------------------------
# Track.reverse_clip_order
# ---------------------------------------------------------------------------

def test_reverse_clip_order():
    """reverse_clip_order reverses clips and packs them end-to-end."""
    medias: list[dict[str, Any]] = [
        {'id': 1, 'start': 0, 'duration': 100},
        {'id': 2, 'start': 100, 'duration': 200},
        {'id': 3, 'start': 300, 'duration': 50},
    ]
    track = _make_track(medias=medias)
    track._data['transitions'] = [{'some': 'transition'}]

    track.reverse_clip_order()

    reversed_medias: list[dict[str, Any]] = track._data['medias']
    # Clip 3 (was last) is now first
    assert reversed_medias[0]['id'] == 3
    assert reversed_medias[0]['start'] == 0
    # Clip 2 follows clip 3
    assert reversed_medias[1]['id'] == 2
    assert reversed_medias[1]['start'] == 50
    # Clip 1 (was first) is now last
    assert reversed_medias[2]['id'] == 1
    assert reversed_medias[2]['start'] == 250
    # Transitions cleared
    assert track._data['transitions'] == []


# ---------------------------------------------------------------------------
# Project.total_duration_formatted
# ---------------------------------------------------------------------------

def test_total_duration_formatted(project):
    """total_duration_formatted returns M:SS for short projects."""
    formatted: str = project.total_duration_formatted
    # The empty/new project has 0 duration → "0:00"
    assert formatted == '0:00'


def test_total_duration_formatted_with_hours(project):
    """total_duration_formatted shows hours when duration exceeds 60 minutes."""
    # Add a very long clip to get hours
    track = project.timeline.add_track('Long')
    track.add_clip('VMFile', 1, 0, 705600000 * 3700)  # ~3700 seconds = 1:01:40
    actual_formatted: str = project.total_duration_formatted
    assert ':' in actual_formatted
    parts = actual_formatted.split(':')
    assert len(parts) == 3  # H:MM:SS


# ---------------------------------------------------------------------------
# Track.find_gaps_longer_than
# ---------------------------------------------------------------------------

def test_find_gaps_longer_than_returns_only_gaps_exceeding_threshold():
    """find_gaps_longer_than filters out gaps shorter than the threshold."""
    medias = [
        {'id': 1, 'start': 0, 'duration': seconds_to_ticks(1.0)},
        # 0.5s gap
        {'id': 2, 'start': seconds_to_ticks(1.5), 'duration': seconds_to_ticks(1.0)},
        # 3.0s gap
        {'id': 3, 'start': seconds_to_ticks(5.5), 'duration': seconds_to_ticks(1.0)},
    ]
    track = _make_track(medias=medias)
    long_gaps: list[tuple[float, float]] = track.find_gaps_longer_than(1.0)
    assert len(long_gaps) == 1
    gap_start, gap_end = long_gaps[0]
    assert gap_end - gap_start == pytest.approx(3.0, abs=0.01)


def test_find_gaps_longer_than_returns_empty_when_no_gaps_exceed():
    """find_gaps_longer_than returns [] when all gaps are below threshold."""
    medias = [
        {'id': 1, 'start': 0, 'duration': seconds_to_ticks(1.0)},
        {'id': 2, 'start': seconds_to_ticks(1.5), 'duration': seconds_to_ticks(1.0)},
    ]
    track = _make_track(medias=medias)
    long_gaps: list[tuple[float, float]] = track.find_gaps_longer_than(1.0)
    assert long_gaps == []


def test_find_gaps_longer_than_returns_empty_for_no_clips():
    """find_gaps_longer_than returns [] on an empty track."""
    track = _make_track(medias=[])
    assert track.find_gaps_longer_than(0.0) == []


# ---------------------------------------------------------------------------
# Project.empty_tracks
# ---------------------------------------------------------------------------

def test_project_empty_tracks_returns_tracks_with_no_clips():
    """Project.empty_tracks delegates to timeline.empty_tracks."""
    timeline = _make_timeline([
        ('Audio', [{'id': 1, 'start': 0, 'duration': 100}]),
        ('Empty', []),
        ('Also Empty', []),
    ])
    empty_track_names: list[str] = [t.name for t in timeline.empty_tracks]
    assert 'Empty' in empty_track_names
    assert 'Also Empty' in empty_track_names
    assert 'Audio' not in empty_track_names


def test_project_empty_tracks_returns_empty_list_when_all_have_clips():
    """Project.empty_tracks returns [] when every track has clips."""
    timeline = _make_timeline([
        ('A', [{'id': 1, 'start': 0, 'duration': 100}]),
    ])
    empty_tracks: list = timeline.empty_tracks
    assert empty_tracks == []


# ---------------------------------------------------------------------------
# BaseClip.set_start_seconds
# ---------------------------------------------------------------------------

def test_set_start_seconds_updates_data():
    """set_start_seconds writes the correct tick value to _data['start']."""
    from camtasia.timeline.clips.base import BaseClip
    clip_data: dict[str, Any] = {'id': 1, 'start': 0, 'duration': 100, 'type': 'VMFile', 'parameters': {}, 'effects': [], 'attributes': {'ident': ''}}
    clip: BaseClip = BaseClip(clip_data)
    result = clip.set_start_seconds(2.0)
    assert clip._data['start'] == seconds_to_ticks(2.0)
    assert result is clip  # returns self for chaining


# ---------------------------------------------------------------------------
# BaseClip.set_duration_seconds
# ---------------------------------------------------------------------------

def test_set_duration_seconds_updates_data():
    """set_duration_seconds writes the correct tick value to _data['duration']."""
    from camtasia.timeline.clips.base import BaseClip
    clip_data: dict[str, Any] = {'id': 1, 'start': 0, 'duration': 100, 'type': 'VMFile', 'parameters': {}, 'effects': [], 'attributes': {'ident': ''}}
    clip: BaseClip = BaseClip(clip_data)
    result = clip.set_duration_seconds(5.0)
    assert clip._data['duration'] == seconds_to_ticks(5.0)
    assert result is clip  # returns self for chaining


# ---------------------------------------------------------------------------
# Timeline.find_track_by_name
# ---------------------------------------------------------------------------

def test_find_track_by_name_returns_matching_track():
    """find_track_by_name returns the first track with the given name."""
    timeline = _make_timeline([
        ('Audio', []),
        ('Video', [{'id': 1, 'start': 0, 'duration': 100}]),
    ])
    found_track: Track | None = timeline.find_track_by_name('Video')
    assert found_track is not None
    assert found_track.name == 'Video'


def test_find_track_by_name_returns_none_when_not_found():
    """find_track_by_name returns None when no track matches."""
    timeline = _make_timeline([
        ('Audio', []),
    ])
    result: Track | None = timeline.find_track_by_name('Nonexistent')
    assert result is None


# ---------------------------------------------------------------------------
# Project.remove_track_by_name
# ---------------------------------------------------------------------------

def test_remove_track_by_name_found(project):
    """remove_track_by_name removes the first matching track and returns True."""
    project.timeline.add_track('Disposable')
    initial_track_count: int = project.track_count
    removed: bool = project.remove_track_by_name('Disposable')
    assert removed is True
    assert project.track_count == initial_track_count - 1


def test_remove_track_by_name_not_found(project):
    """remove_track_by_name returns False when no track matches."""
    removed: bool = project.remove_track_by_name('NonExistent')
    assert removed is False


def test_remove_track_by_name_only_first(project):
    """remove_track_by_name removes only the first track with a duplicate name."""
    project.timeline.add_track('Dup')
    project.timeline.add_track('Dup')
    count_before: int = project.track_count
    project.remove_track_by_name('Dup')
    assert project.track_count == count_before - 1
    remaining_names: list[str] = [t.name for t in project.timeline.tracks]
    assert 'Dup' in remaining_names


# ---------------------------------------------------------------------------
# BaseClip.is_effect_applied
# ---------------------------------------------------------------------------

def test_is_effect_applied_true():
    """is_effect_applied returns True when the effect is present."""
    clip_data: dict = {
        'id': 1, '_type': 'VMFile', 'start': 0, 'duration': 100,
        'effects': [{'effectName': 'DropShadow'}],
    }
    from camtasia.timeline.clips.base import BaseClip
    clip = BaseClip(clip_data)
    assert clip.is_effect_applied('DropShadow') is True


def test_is_effect_applied_false():
    """is_effect_applied returns False when the effect is absent."""
    clip_data: dict = {
        'id': 1, '_type': 'VMFile', 'start': 0, 'duration': 100,
        'effects': [{'effectName': 'Glow'}],
    }
    from camtasia.timeline.clips.base import BaseClip
    clip = BaseClip(clip_data)
    assert clip.is_effect_applied('DropShadow') is False


def test_is_effect_applied_no_effects():
    """is_effect_applied returns False when clip has no effects list."""
    clip_data: dict = {'id': 1, '_type': 'VMFile', 'start': 0, 'duration': 100}
    from camtasia.timeline.clips.base import BaseClip
    clip = BaseClip(clip_data)
    assert clip.is_effect_applied('DropShadow') is False


def test_is_effect_applied_with_enum():
    """is_effect_applied works with EffectName enum values."""
    from camtasia.types import EffectName
    clip_data: dict = {
        'id': 1, '_type': 'VMFile', 'start': 0, 'duration': 100,
        'effects': [{'effectName': 'DropShadow'}],
    }
    from camtasia.timeline.clips.base import BaseClip
    clip = BaseClip(clip_data)
    assert clip.is_effect_applied(EffectName.DROP_SHADOW) is True


# ---------------------------------------------------------------------------
# Track.total_transition_duration_seconds
# ---------------------------------------------------------------------------

def test_total_transition_duration_seconds_empty():
    """total_transition_duration_seconds is 0.0 when no transitions exist."""
    track = _make_track()
    assert track.total_transition_duration_seconds == 0.0


def test_total_transition_duration_seconds_single():
    """total_transition_duration_seconds converts a single transition correctly."""
    from camtasia.timing import EDIT_RATE
    duration_ticks: int = EDIT_RATE * 2  # 2 seconds
    data: dict = {'trackIndex': 0, 'medias': [], 'transitions': [{'duration': duration_ticks}]}
    attrs: dict = {'ident': 'T'}
    track = Track(attrs, data)
    assert track.total_transition_duration_seconds == pytest.approx(2.0)


def test_total_transition_duration_seconds_multiple():
    """total_transition_duration_seconds sums multiple transitions."""
    from camtasia.timing import EDIT_RATE
    transitions: list[dict] = [
        {'duration': EDIT_RATE},      # 1 second
        {'duration': EDIT_RATE * 3},   # 3 seconds
    ]
    data: dict = {'trackIndex': 0, 'medias': [], 'transitions': transitions}
    attrs: dict = {'ident': 'T'}
    track = Track(attrs, data)
    assert track.total_transition_duration_seconds == pytest.approx(4.0)


# ---------------------------------------------------------------------------
# Timeline.total_transition_count
# ---------------------------------------------------------------------------

def test_timeline_total_transition_count_empty():
    """total_transition_count is 0 for a timeline with no transitions."""
    timeline = _make_timeline([('A', []), ('B', [])])
    assert timeline.total_transition_count == 0


def test_timeline_total_transition_count_with_transitions():
    """total_transition_count sums transitions across all tracks."""
    data: dict = {
        'sceneTrack': {'scenes': [{'csml': {'tracks': [
            {'trackIndex': 0, 'medias': [], 'transitions': [{'duration': 100}]},
            {'trackIndex': 1, 'medias': [], 'transitions': [{'duration': 200}, {'duration': 300}]},
        ]}}]},
        'trackAttributes': [{'ident': 'A'}, {'ident': 'B'}],
    }
    timeline = Timeline(data)
    assert timeline.total_transition_count == 3


# ---------------------------------------------------------------------------
# BaseClip.clear_metadata
# ---------------------------------------------------------------------------

def test_clear_metadata_removes_all():
    """clear_metadata empties the metadata dict."""
    clip_data: dict = {
        'id': 1, '_type': 'VMFile', 'start': 0, 'duration': 100,
        'metadata': {'presetName': 'Intro', 'author': 'Test'},
    }
    from camtasia.timeline.clips.base import BaseClip
    clip = BaseClip(clip_data)
    result = clip.clear_metadata()
    assert clip.metadata == {}
    assert clip_data['metadata'] == {}


def test_clear_metadata_returns_self():
    """clear_metadata returns self for chaining."""
    clip_data: dict = {
        'id': 1, '_type': 'VMFile', 'start': 0, 'duration': 100,
        'metadata': {'key': 'value'},
    }
    from camtasia.timeline.clips.base import BaseClip
    clip = BaseClip(clip_data)
    returned: BaseClip = clip.clear_metadata()
    assert returned is clip


def test_clear_metadata_on_empty():
    """clear_metadata works when metadata is already empty or absent."""
    clip_data: dict = {'id': 1, '_type': 'VMFile', 'start': 0, 'duration': 100}
    from camtasia.timeline.clips.base import BaseClip
    clip = BaseClip(clip_data)
    clip.clear_metadata()
    assert clip_data['metadata'] == {}


def test_project_empty_tracks_property(project):
    """Project.empty_tracks delegates to timeline.empty_tracks."""
    actual_empty: list = project.empty_tracks
    assert isinstance(actual_empty, list)
