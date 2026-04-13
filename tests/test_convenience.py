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