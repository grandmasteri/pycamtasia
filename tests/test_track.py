"""Tests for Track convenience methods."""
from __future__ import annotations

from typing import Any

import pytest
from camtasia.timeline.track import Track
from camtasia.timeline.timeline import Timeline
from camtasia.timing import seconds_to_ticks

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


def test_has_screen_recording_true():
    from camtasia.project import Project
    from unittest.mock import MagicMock
    group_media = {
        'id': 1, '_type': 'Group', 'start': 0, 'duration': 100,
        'tracks': [{'trackIndex': 0, 'medias': [{'id': 2, '_type': 'UnifiedMedia', 'start': 0, 'duration': 100, 'video': {'_type': 'ScreenVMFile'}}]}],
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


def test_track_describe_with_overlaps():
    data = {'trackIndex': 0, 'medias': [
        {'id': 1, '_type': 'AMFile', 'start': 0, 'duration': 200},
        {'id': 2, '_type': 'AMFile', 'start': 100, 'duration': 200},
    ], 'transitions': []}
    from camtasia.timeline.track import Track
    t = Track({'ident': 'Overlap'}, data)
    actual = t.describe()
    assert 'Overlaps: 1' in actual


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
# Track.has_transitions / transition_count
# ---------------------------------------------------------------------------

def test_track_has_transitions():
    track_no = _make_track(medias=[])
    assert track_no.has_transitions is False
    track_yes = Track({'ident': 'T'}, {
        'trackIndex': 0,
        'medias': [],
        'transitions': [{'name': 'Fade', 'duration': 50, 'leftMedia': 1, 'rightMedia': 2, 'attributes': {}}],
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
# Track.rename
# ---------------------------------------------------------------------------

def test_track_rename():
    track = _make_track(name='Original')
    assert track.name == 'Original'
    track.rename('Renamed')
    assert track.name == 'Renamed'




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



# ── total_clip_duration_ticks ────────────────────────────────────────


def test_total_clip_duration_ticks():
    track = _make_track(medias=[
        {'id': 1, 'start': 0, 'duration': 300},
        {'id': 2, 'start': 400, 'duration': 200},
    ])
    assert track.total_clip_duration_ticks == 500


# ── first_gap / largest_gap ─────────────────────────────────────────


def test_first_gap_returns_first():
    track = _make_track(medias=[
        {'id': 1, 'start': 0, 'duration': 100},
        {'id': 2, 'start': 200, 'duration': 100},
        {'id': 3, 'start': 400, 'duration': 100},
    ])
    gap = track.first_gap
    assert gap is not None


def test_first_gap_none_when_no_gaps():
    track = _make_track(medias=[
        {'id': 1, 'start': 0, 'duration': 100},
        {'id': 2, 'start': 100, 'duration': 100},
    ])
    assert track.first_gap is None


def test_largest_gap():
    track = _make_track(medias=[
        {'id': 1, 'start': 0, 'duration': 100},
        {'id': 2, 'start': 200, 'duration': 100},
        {'id': 3, 'start': 500, 'duration': 100},
    ])
    gap = track.largest_gap
    assert gap is not None
    # The gap from 300..500 is larger than 100..200
    assert gap[1] > gap[0]


def test_largest_gap_none_when_no_gaps():
    track = _make_track(medias=[{'id': 1, 'start': 0, 'duration': 100}])
    assert track.largest_gap is None


# ── partition_by_type ────────────────────────────────────────────────


def test_partition_by_type():
    track = _make_track(medias=[
        {'id': 1, '_type': 'VMFile', 'start': 0, 'duration': 100},
        {'id': 2, '_type': 'AMFile', 'start': 100, 'duration': 100},
        {'id': 3, '_type': 'VMFile', 'start': 200, 'duration': 100},
    ])
    result = track.partition_by_type()
    assert 'VMFile' in result
    assert 'AMFile' in result
    assert len(result['VMFile']) == 2
    assert len(result['AMFile']) == 1
