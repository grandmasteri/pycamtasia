"""Tests for Track convenience methods."""
from __future__ import annotations

from fractions import Fraction
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from camtasia.project import Project, load_project
from camtasia.timeline.clips.base import EDIT_RATE
from camtasia.timeline.timeline import Timeline
from camtasia.timeline.track import Track, _PerMediaMarkers
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
    assert track.duration_seconds == track.total_duration_seconds




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
    dur_ticks = seconds_to_ticks(10.0)
    tl = _make_timeline([
        ('A', [{'id': 1, 'start': start_ticks, 'duration': dur_ticks}]),
        ('B', [{'id': 2, 'start': 0, 'duration': dur_ticks}]),
    ])
    tl.shift_all(-5.0)
    raw_tracks = tl._track_list
    # Track A: clip survives with clamped start=0 and reduced duration
    assert raw_tracks[0]['medias'][0]['start'] == 0
    assert raw_tracks[0]['medias'][0]['duration'] > 0
    # Track B: clip survives with clamped start=0 and reduced duration
    assert raw_tracks[1]['medias'][0]['start'] == 0
    assert raw_tracks[1]['medias'][0]['duration'] > 0




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
    assert 'AMFile' in desc
    assert 'VMFile' in desc
    assert 'Duration: 5.0s' in desc
    assert 'Gaps: 1' in desc


def test_track_describe_with_overlaps():
    data = {'trackIndex': 0, 'medias': [
        {'id': 1, '_type': 'AMFile', 'start': 0, 'duration': 200},
        {'id': 2, '_type': 'AMFile', 'start': 100, 'duration': 200},
    ], 'transitions': []}
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
    fixture = Path(__file__).parent / 'fixtures' / 'test_project_c.tscproj'
    proj = load_project(fixture)
    d = proj.to_dict()
    assert isinstance(d, dict)
    # Deep copy: mutating the returned dict must not affect the project
    d['__test_sentinel'] = True
    assert '__test_sentinel' not in proj._data






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
    assert next(iter(t.clips)).id == 2


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
    assert next(iter(tl.tracks)).name == 'Video'


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
    medias = [
        {'_type': 'VMFile', 'id': 1, 'start': 0, 'duration': 100},
        {'_type': 'VMFile', 'id': 2, 'start': 100, 'duration': 100},
    ]
    track = _make_track(medias=medias)
    track.set_opacity(0.5)
    for clip in track.clips:
        assert clip.opacity == 0.5
    with pytest.raises(ValueError, match=r'opacity must be 0\.0-1\.0'):
        track.set_opacity(1.5)
    with pytest.raises(ValueError, match=r'opacity must be 0\.0-1\.0'):
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
    with pytest.raises(ValueError, match=r'volume must be >= 0\.0'):
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
    clip = next(iter(track.clips))
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
    track_a = next(iter(timeline.tracks))
    track_b = list(timeline.tracks)[1]
    assert next(iter(track_a.clips)).start == 0
    assert next(iter(track_b.clips)).start == 0
    assert list(track_b.clips)[1].start == 1000


def test_normalize_timing_empty_track():
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
    tl.duplicate_track(0)
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


# ── Track.add_freeze_frame ──────────────────────────────────────────


class TestAddFreezeFrame:
    def test_creates_imfile_clip(self, project):
        track = project.timeline.get_or_create_track('Video')
        src = track.add_clip('VMFile', 1, seconds_to_ticks(0), seconds_to_ticks(10))
        assert track.add_freeze_frame(src, at_seconds=5.0, freeze_duration_seconds=2.0).clip_type == 'IMFile'

    def test_freeze_start_position(self, project):
        track = project.timeline.get_or_create_track('Video')
        src = track.add_clip('VMFile', 1, seconds_to_ticks(0), seconds_to_ticks(10))
        freeze = track.add_freeze_frame(src, at_seconds=3.0, freeze_duration_seconds=1.0)
        assert freeze.start == seconds_to_ticks(3.0)

    def test_freeze_duration(self, project):
        track = project.timeline.get_or_create_track('Video')
        src = track.add_clip('VMFile', 1, seconds_to_ticks(0), seconds_to_ticks(10))
        freeze = track.add_freeze_frame(src, at_seconds=5.0, freeze_duration_seconds=3.0)
        assert freeze.duration == seconds_to_ticks(3.0)

    def test_freeze_uses_source_id(self, project):
        track = project.timeline.get_or_create_track('Video')
        src = track.add_clip('VMFile', 42, seconds_to_ticks(0), seconds_to_ticks(10))
        assert track.add_freeze_frame(src, at_seconds=2.0, freeze_duration_seconds=1.0).source_id == 42

    def test_freeze_media_start_offset(self, project):
        track = project.timeline.get_or_create_track('Video')
        src = track.add_clip('VMFile', 1, seconds_to_ticks(2.0), seconds_to_ticks(10))
        freeze = track.add_freeze_frame(src, at_seconds=5.0, freeze_duration_seconds=1.0)
        assert freeze._data['mediaStart'] == seconds_to_ticks(3.0)

    def test_freeze_adds_to_track_clip_count(self, project):
        track = project.timeline.get_or_create_track('Video')
        src = track.add_clip('VMFile', 1, seconds_to_ticks(0), seconds_to_ticks(10))
        initial_count = len(track)
        track.add_freeze_frame(src, at_seconds=5.0, freeze_duration_seconds=2.0)
        assert len(track) == initial_count + 1


class TestAddClipScalarValidation:
    """add_clip rejects scalar <= 0."""

    def test_zero_scalar_raises(self, project):
        track = project.timeline.tracks[0]
        with pytest.raises(ValueError, match=r"scalar must be positive"):
            track.add_clip("VMFile", 0, 0, 705600000, scalar=0)

    def test_negative_scalar_raises(self, project):
        track = project.timeline.tracks[0]
        with pytest.raises(ValueError, match=r"scalar must be positive"):
            track.add_clip("VMFile", 0, 0, 705600000, scalar=-1)


class TestShiftAllClipsClampScalarZero:
    """Track.shift_all_clips handles scalar=0 without division error when clamping."""

    def test_clamp_with_zero_scalar(self, project):
        from camtasia.timing import seconds_to_ticks
        track = project.timeline.tracks[0]
        clip = track.add_clip('VMFile', 0, seconds_to_ticks(5.0), seconds_to_ticks(10.0))
        clip._data['scalar'] = 0
        clip._data['mediaStart'] = seconds_to_ticks(2.0)
        track.shift_all_clips(-10.0)
        assert clip._data['mediaStart'] == seconds_to_ticks(2.0)


class TestAddScreenRecordingUniqueIds:
    """Bug 8: add_screen_recording must produce unique IDs for all clips."""

    def test_no_duplicate_ids(self):
        track = _make_track()
        group = track.add_screen_recording(source_id=2, start_seconds=0.0, duration_seconds=10.0)
        all_ids = []
        all_ids.append(group.id)
        for t in group._data.get('tracks', []):
            for m in t.get('medias', []):
                all_ids.append(m['id'])
                for sub_key in ('video', 'audio'):
                    sub = m.get(sub_key)
                    if sub and 'id' in sub:
                        all_ids.append(sub['id'])
        assert len(all_ids) == len(set(all_ids)), f"Duplicate IDs found: {all_ids}"

    def test_passes_validation(self):
        from camtasia.timeline.timeline import Timeline
        data = {
            'id': 0,
            'sceneTrack': {'scenes': [{'csml': {'tracks': [
                {'trackIndex': 0, 'medias': []},
            ]}}]},
            'trackAttributes': [{'ident': 'T'}],
            'parameters': {'toc': {'keyframes': []}},
        }
        tl = Timeline(data)
        t0 = tl.tracks[0]
        t0.add_screen_recording(source_id=2, start_seconds=0.0, duration_seconds=10.0)
        issues = tl.validate_structure()
        assert not issues, f"Validation issues: {issues}"


class TestSetSegmentSpeedsMediaStartFormula:
    """Bug 10: set_segment_speeds advance formula should be dur_ticks / seg_scalar."""

    def test_media_start_correct_with_non_unity_original_scalar(self):
        """When original_scalar != 1, advance = dur_ticks / seg_scalar (not * original/seg)."""
        # Group with original_scalar = duration/mediaDuration = 100/120 = 5/6
        group_data = {
            'id': 1, '_type': 'Group',
            'start': seconds_to_ticks(10.0),
            'duration': seconds_to_ticks(100.0),
            'mediaStart': 0,
            'mediaDuration': seconds_to_ticks(120.0),
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
                    'id': 11, '_type': 'UnifiedMedia', 'src': 1,
                    'start': 0, 'duration': seconds_to_ticks(120.0),
                    'mediaStart': 0, 'mediaDuration': seconds_to_ticks(120.0),
                    'scalar': 1, 'metadata': {}, 'parameters': {},
                    'effects': [], 'attributes': {}, 'animationTracks': {},
                }]},
            ],
        }
        track = _make_track([group_data])
        pieces = track.set_segment_speeds(1, [(50, 1.0), (50, 2.0)])
        # original_scalar = 5/6
        # seg_scalar_0 = (5/6)/1 = 5/6
        # advance_0 = 50s_ticks / (5/6) = 60s_ticks
        ms1 = pieces[1]._data['mediaStart']
        assert ms1 == seconds_to_ticks(60.0)


# ==== Bug 11: _PerMediaMarkers fractional mediaDuration ====

class TestPerMediaMarkersFractionalDuration:
    """Bug 11: _PerMediaMarkers truncated fractional mediaDuration with int()."""

    def test_marker_at_fractional_boundary_not_dropped(self) -> None:
        """A marker just below a fractional mediaDuration should be included."""
        # mediaDuration is a fraction like 100/3 ≈ 33.33
        # int(Fraction('100/3')) = 33, which would wrongly exclude a marker at time 33
        media_data = {
            'start': 0,
            'mediaStart': 0,
            'mediaDuration': '100/3',  # ≈ 33.33
            'scalar': 1,
            'parameters': {
                'toc': {
                    'keyframes': [
                        {'time': 10, 'value': 'early'},
                        {'time': 33, 'value': 'near_end'},  # 33 < 33.33, should be included
                    ],
                },
            },
        }
        markers = list(_PerMediaMarkers(media_data))
        names = [m.name for m in markers]
        assert 'early' in names
        assert 'near_end' in names  # would be dropped with int() truncation

    def test_marker_past_fractional_boundary_excluded(self) -> None:
        """A marker at or past the fractional mediaDuration should be excluded."""
        media_data = {
            'start': 0,
            'mediaStart': 0,
            'mediaDuration': '100/3',  # ≈ 33.33
            'scalar': 1,
            'parameters': {
                'toc': {
                    'keyframes': [
                        {'time': 34, 'value': 'past_end'},  # 34 >= 33.33, excluded
                    ],
                },
            },
        }
        markers = list(_PerMediaMarkers(media_data))
        assert len(markers) == 0
"""Tests for duplicate_clip nested ID remapping (Bug 12)."""



def _make_track_with_group() -> Track:
    """Track with a Group clip containing nested UnifiedMedia (video+audio)."""
    dur = seconds_to_ticks(5.0)
    return Track(
        {'ident': 'T'},
        {
            'trackIndex': 0,
            'medias': [{
                '_type': 'Group',
                'id': 1,
                'start': 0,
                'duration': dur,
                'mediaStart': 0,
                'mediaDuration': dur,
                'scalar': 1,
                'parameters': {},
                'effects': [],
                'metadata': {},
                'animationTracks': {},
                'attributes': {'ident': ''},
                'tracks': [{
                    'trackIndex': 0,
                    'medias': [{
                        '_type': 'UnifiedMedia',
                        'id': 2,
                        'start': 0,
                        'duration': dur,
                        'mediaStart': 0,
                        'mediaDuration': dur,
                        'scalar': 1,
                        'effects': [],
                        'video': {
                            '_type': 'ScreenVMFile', 'id': 3, 'src': 10,
                            'start': 0, 'duration': dur, 'mediaStart': 0,
                            'mediaDuration': dur, 'scalar': 1,
                        },
                        'audio': {
                            '_type': 'AMFile', 'id': 4, 'src': 10,
                            'start': 0, 'duration': dur, 'mediaStart': 0,
                            'mediaDuration': dur, 'scalar': 1,
                        },
                    }],
                }],
            }],
            'transitions': [],
        },
    )


class TestDuplicateClipNestedIds:
    """Bug 12: duplicate_clip id_counter should start after new_id."""

    def test_top_level_id_preserved(self) -> None:
        track = _make_track_with_group()
        dup = track.duplicate_clip(1)
        # The duplicate's top-level id should be the next available id
        assert dup.id != 1
        # Original still has id 1
        assert track._data['medias'][0]['id'] == 1

    def test_no_duplicate_ids(self) -> None:
        track = _make_track_with_group()
        track.duplicate_clip(1)
        # Collect all IDs from both clips
        all_ids: list[int] = []

        def _collect(data: dict) -> None:
            if 'id' in data:
                all_ids.append(data['id'])
            for key in ('video', 'audio'):
                if key in data and isinstance(data[key], dict):
                    _collect(data[key])
            for t in data.get('tracks', []):
                for m in t.get('medias', []):
                    _collect(m)

        for m in track._data['medias']:
            _collect(m)

        assert len(all_ids) == len(set(all_ids)), f"Duplicate IDs found: {all_ids}"

    def test_nested_ids_sequential_after_top(self) -> None:
        track = _make_track_with_group()
        track.duplicate_clip(1)
        dup_data = track._data['medias'][1]
        top_id = dup_data['id']
        nested_um = dup_data['tracks'][0]['medias'][0]
        video_id = nested_um['video']['id']
        audio_id = nested_um['audio']['id']
        # All nested IDs should be greater than the top-level ID
        assert nested_um['id'] > top_id
        assert video_id > top_id
        assert audio_id > top_id



def _make_track_bug_fix_helper(**overrides: Any) -> Track:
    attrs: dict[str, Any] = {'ident': 'Test', 'audioMuted': False, 'videoHidden': False,
                              'magnetic': False, 'matte': 0, 'solo': False}
    data: dict[str, Any] = {'trackIndex': 0, 'medias': [], 'transitions': [], 'parameters': {}}
    data.update(overrides)
    return Track(attrs, data)


def _make_group_with_asset_properties() -> dict[str, Any]:
    """Create a Group clip with assetProperties referencing internal clip IDs."""
    return {
        '_type': 'Group', 'id': 50,
        'start': 0, 'duration': EDIT_RATE * 5,
        'mediaStart': 0, 'mediaDuration': EDIT_RATE * 5, 'scalar': 1,
        'attributes': {
            'ident': '', 'widthAttr': 1920, 'heightAttr': 1080,
            'assetProperties': [
                {'objects': [51, 52], 'property': 'test'},
            ],
        },
        'tracks': [{
            'trackIndex': 0,
            'medias': [
                {'_type': 'VMFile', 'id': 51, 'src': 1,
                 'start': 0, 'duration': EDIT_RATE * 5,
                 'mediaStart': 0, 'mediaDuration': EDIT_RATE * 5, 'scalar': 1,
                 'effects': [], 'parameters': {}, 'metadata': {}, 'animationTracks': {},
                 'attributes': {'ident': ''}, 'trackNumber': 0},
                {'_type': 'VMFile', 'id': 52, 'src': 1,
                 'start': 0, 'duration': EDIT_RATE * 5,
                 'mediaStart': 0, 'mediaDuration': EDIT_RATE * 5, 'scalar': 1,
                 'effects': [], 'parameters': {}, 'metadata': {}, 'animationTracks': {},
                 'attributes': {'ident': ''}, 'trackNumber': 0},
            ],
        }],
        'effects': [], 'parameters': {}, 'metadata': {}, 'animationTracks': {},
    }


def test_duplicate_clip_asset_properties_remap() -> None:
    """Bug 8: duplicate_clip should correctly remap assetProperties."""
    track = _make_track_bug_fix_helper()
    group_data = _make_group_with_asset_properties()
    track._data['medias'].append(group_data)

    result = track.duplicate_clip(50)
    dup_data = result._data
    # assetProperties should reference the NEW internal clip IDs, not the old ones
    ap = dup_data.get('attributes', {}).get('assetProperties', [])
    assert len(ap) == 1
    # The objects should NOT contain the original IDs (51, 52)
    for obj_id in ap[0]['objects']:
        assert obj_id not in (51, 52), f'assetProperties still references old ID {obj_id}'
    # The objects should reference IDs that exist in the duplicated clip's internal tracks
    internal_ids = {m['id'] for t in dup_data.get('tracks', []) for m in t.get('medias', [])}
    for obj_id in ap[0]['objects']:
        assert obj_id in internal_ids, f'assetProperties references non-existent ID {obj_id}'


def test_replace_clip_asset_properties_remap() -> None:
    """Bug 9: replace_clip should correctly remap assetProperties."""
    track = _make_track_bug_fix_helper()
    # Add a placeholder clip to replace
    track._data['medias'].append({
        '_type': 'VMFile', 'id': 1, 'src': 1,
        'start': 0, 'duration': EDIT_RATE,
        'mediaStart': 0, 'mediaDuration': EDIT_RATE, 'scalar': 1,
        'effects': [], 'parameters': {}, 'metadata': {}, 'animationTracks': {},
        'attributes': {'ident': ''}, 'trackNumber': 0,
    })
    replacement = _make_group_with_asset_properties()
    result = track.replace_clip(1, replacement)
    dup_data = result._data
    ap = dup_data.get('attributes', {}).get('assetProperties', [])
    assert len(ap) == 1
    internal_ids = {m['id'] for t in dup_data.get('tracks', []) for m in t.get('medias', [])}
    for obj_id in ap[0]['objects']:
        assert obj_id in internal_ids


def test_extend_clip_trims_unified_sub_effects() -> None:
    """Bug 10: extend_clip should trim effects on UnifiedMedia sub-clips when shortening."""
    dur = EDIT_RATE * 10
    eff_dur = EDIT_RATE * 8
    track = _make_track_bug_fix_helper()
    track._data['medias'].append({
        '_type': 'UnifiedMedia', 'id': 1,
        'start': 0, 'duration': dur,
        'mediaStart': 0, 'mediaDuration': dur, 'scalar': 1,
        'video': {
            '_type': 'VMFile', 'id': 2, 'src': 1,
            'start': 0, 'duration': dur,
            'mediaStart': 0, 'mediaDuration': dur, 'scalar': 1,
            'effects': [{'effectName': 'Glow', 'start': 0, 'duration': eff_dur}],
            'trackNumber': 0, 'attributes': {'ident': ''},
        },
        'audio': None,
        'effects': [{'effectName': 'Glow', 'start': 0, 'duration': eff_dur}],
    })
    # Shorten by 5 seconds
    track.extend_clip(1, extend_seconds=-5.0)
    new_dur = dur + (-EDIT_RATE * 5)
    video = track._data['medias'][0]['video']
    # Video sub-clip effects should be trimmed to new_dur
    for eff in video['effects']:
        assert eff['duration'] <= new_dur


def test_remove_gap_at_preserves_both_shifted_transitions() -> None:
    """Bug 11: remove_gap_at should preserve transitions where both endpoints shifted."""
    dur = EDIT_RATE * 5
    gap = EDIT_RATE * 2
    track = _make_track_bug_fix_helper()
    # Clip A at 0, Clip B after gap, Clip C after B
    track._data['medias'] = [
        {'_type': 'VMFile', 'id': 1, 'start': 0, 'duration': dur,
         'mediaStart': 0, 'mediaDuration': dur, 'scalar': 1},
        {'_type': 'VMFile', 'id': 2, 'start': dur + gap, 'duration': dur,
         'mediaStart': 0, 'mediaDuration': dur, 'scalar': 1},
        {'_type': 'VMFile', 'id': 3, 'start': dur + gap + dur, 'duration': dur,
         'mediaStart': 0, 'mediaDuration': dur, 'scalar': 1},
    ]
    # Transition between clips 2 and 3 (both will be shifted)
    track._data['transitions'] = [
        {'leftMedia': 2, 'rightMedia': 3, 'duration': EDIT_RATE},
    ]
    from camtasia.timing import ticks_to_seconds
    gap_time = ticks_to_seconds(dur + gap // 2)  # middle of the gap
    track.remove_gap_at(gap_time)
    # Transition between 2 and 3 should be PRESERVED (both shifted equally)
    assert len(track._data['transitions']) == 1
    assert track._data['transitions'][0]['leftMedia'] == 2
    assert track._data['transitions'][0]['rightMedia'] == 3


def test_remove_gap_at_removes_split_transitions() -> None:
    """Bug 11: remove_gap_at should remove transitions where only one endpoint shifted."""
    dur = EDIT_RATE * 5
    gap = EDIT_RATE * 2
    track = _make_track_bug_fix_helper()
    track._data['medias'] = [
        {'_type': 'VMFile', 'id': 1, 'start': 0, 'duration': dur,
         'mediaStart': 0, 'mediaDuration': dur, 'scalar': 1},
        {'_type': 'VMFile', 'id': 2, 'start': dur + gap, 'duration': dur,
         'mediaStart': 0, 'mediaDuration': dur, 'scalar': 1},
    ]
    # Transition between clip 1 (not shifted) and clip 2 (shifted)
    track._data['transitions'] = [
        {'leftMedia': 1, 'rightMedia': 2, 'duration': EDIT_RATE},
    ]
    from camtasia.timing import ticks_to_seconds
    gap_time = ticks_to_seconds(dur + gap // 2)
    track.remove_gap_at(gap_time)
    # Transition should be REMOVED (only one endpoint shifted)
    assert len(track._data['transitions']) == 0


def test_shift_all_preserves_fractional_duration() -> None:
    """Bug 12: shift_all should not truncate non-integer durations."""
    track = _make_track_bug_fix_helper()
    track._data['medias'].append({
        '_type': 'VMFile', 'id': 1,
        'start': EDIT_RATE * 3, 'duration': '7056000001/2',
        'mediaStart': 0, 'mediaDuration': '7056000001/2', 'scalar': 1,
        'effects': [], 'parameters': {}, 'metadata': {}, 'animationTracks': {},
        'attributes': {'ident': ''}, 'trackNumber': 0,
    })
    track.shift_all_clips(-1.0)
    m = track._data['medias'][0]
    # Duration should still be a Fraction-compatible value, not truncated
    dur = Fraction(str(m['duration']))
    assert dur > 0
    # The original duration was 7056000001/2 = 3528000000.5
    # After shifting back 1s (705600000 ticks), start goes from 3*ER to 2*ER
    # No clamping needed, so duration should be unchanged
    assert dur == Fraction('7056000001/2')


def test_timeline_shift_all_preserves_fractional_duration() -> None:
    """Bug 12: Timeline.shift_all should not truncate non-integer durations."""
    from camtasia.timeline.timeline import Timeline
    tl_data = {
        'id': 0,
        'sceneTrack': {'scenes': [{'csml': {'tracks': [{
            'trackIndex': 0,
            'medias': [{
                '_type': 'VMFile', 'id': 1,
                'start': EDIT_RATE, 'duration': '7056000001/3',
                'mediaStart': 0, 'mediaDuration': '7056000001/3', 'scalar': 1,
                'effects': [],
            }],
            'transitions': [],
            'parameters': {},
        }]}}]},
        'trackAttributes': [{'ident': 'T', 'audioMuted': False, 'videoHidden': False,
                             'magnetic': False, 'matte': 0, 'solo': False}],
        'parameters': {},
    }
    tl = Timeline(tl_data)
    tl.shift_all(-0.5)
    m = tl_data['sceneTrack']['scenes'][0]['csml']['tracks'][0]['medias'][0]
    dur = Fraction(str(m['duration']))
    assert dur > 0
    # No clamping needed (start was 1s, shift is -0.5s), so duration unchanged
    assert dur == Fraction('7056000001/3')


def _make_track_cycle10(medias: list[dict] | None = None) -> Track:
    attrs: dict[str, Any] = {"ident": "Track 1"}
    data: dict[str, Any] = {
        "trackIndex": 0,
        "medias": medias or [],
        "transitions": [],
    }
    return Track(attrs, data)


def _vmfile(uid: int, start: int, duration: int) -> dict[str, Any]:
    return {
        "id": uid, "_type": "VMFile", "src": 1,
        "start": start, "duration": duration,
        "mediaStart": 0, "mediaDuration": duration, "scalar": 1,
    }


# -- Bug 8: shift_all_clips stores duration as int, not string --

class TestShiftAllClipsStoresIntDuration:
    def test_duration_is_int_after_negative_shift(self):
        start_ticks = seconds_to_ticks(1.0)
        dur_ticks = seconds_to_ticks(5.0)
        clip = _vmfile(1, start=start_ticks, duration=dur_ticks)
        track = _make_track_cycle10([clip])
        track.shift_all_clips(-3.0)  # shift back 3s, clamps at 0
        m = track._data["medias"][0]
        assert isinstance(m["duration"], int)

    def test_duration_is_int_after_fractional_clamp(self):
        start_ticks = seconds_to_ticks(0.5)
        dur_ticks = seconds_to_ticks(5.0)
        clip = _vmfile(1, start=start_ticks, duration=dur_ticks)
        track = _make_track_cycle10([clip])
        track.shift_all_clips(-2.0)
        m = track._data["medias"][0]
        assert isinstance(m["duration"], int)


# -- Bug 9: remove_gap_at detects leading gap --

class TestRemoveGapAtHandlesLeadingGap:
    def test_leading_gap_removed(self):
        start_ticks = seconds_to_ticks(5.0)
        dur_ticks = seconds_to_ticks(3.0)
        clip = _vmfile(1, start=start_ticks, duration=dur_ticks)
        track = _make_track_cycle10([clip])
        track.remove_gap_at(0.0)
        m = track._data["medias"][0]
        assert m["start"] == 0

    def test_leading_gap_at_midpoint(self):
        start_ticks = seconds_to_ticks(10.0)
        dur_ticks = seconds_to_ticks(3.0)
        clip = _vmfile(1, start=start_ticks, duration=dur_ticks)
        track = _make_track_cycle10([clip])
        track.remove_gap_at(5.0)  # 5s is within leading gap [0, 10s)
        m = track._data["medias"][0]
        assert m["start"] == 0

    def test_no_leading_gap_no_change(self):
        clip = _vmfile(1, start=0, duration=seconds_to_ticks(3.0))
        track = _make_track_cycle10([clip])
        track.remove_gap_at(0.0)
        m = track._data["medias"][0]
        assert m["start"] == 0


# -- Bug 10: replace_clip no double-remap --

class TestReplaceClipNoDoubleRemapAssetProperties:
    def test_replace_clip_id_is_new_id(self):
        track = _make_track_cycle10()
        original = track.add_callout("A", 0, 5)
        old_id = original.id
        new_data: dict[str, Any] = {
            "_type": "Callout", "id": 999,
            "duration": 10, "start": 0,
            "mediaStart": 0, "mediaDuration": 10,
        }
        result = track.replace_clip(old_id, new_data)
        assert result.id != old_id
        assert result.id != 999  # should be remapped

    def test_replace_compound_clip_nested_ids_remapped(self):
        track = _make_track_cycle10()
        original = track.add_callout("A", 0, 5)
        old_id = original.id
        new_data: dict[str, Any] = {
            "_type": "UnifiedMedia", "id": 100,
            "duration": 10, "start": 0,
            "mediaStart": 0, "mediaDuration": 10, "scalar": 1,
            "video": {"id": 101, "_type": "VMFile", "duration": 10,
                      "start": 0, "mediaDuration": 10, "scalar": 1, "src": 1},
            "audio": {"id": 102, "_type": "AMFile", "duration": 10,
                      "start": 0, "mediaDuration": 10, "scalar": 1, "src": 1},
        }
        result = track.replace_clip(old_id, new_data)
        top_id = result._data["id"]
        vid_id = result._data["video"]["id"]
        aud_id = result._data["audio"]["id"]
        assert len({top_id, vid_id, aud_id}) == 3
        assert top_id not in (100, 101, 102)


# -- Bug: add_clip must force scalar=1 for IMFile/ScreenIMFile --

def test_add_clip_imfile_scalar_always_one() -> None:
    """IMFile clips created via add_clip should always have scalar=1."""
    track = _make_track()
    clip = track.add_clip('IMFile', 1, 0, 300)
    assert clip._data['scalar'] == 1
    assert clip._data['mediaDuration'] == 1


def test_add_clip_screen_imfile_scalar_always_one() -> None:
    """ScreenIMFile clips created via add_clip should always have scalar=1."""
    track = _make_track()
    clip = track.add_clip('ScreenIMFile', 1, 0, 300)
    assert clip._data['scalar'] == 1
    assert clip._data['mediaDuration'] == 1
