"""Tests for Project.timeline_to_dict()."""

from __future__ import annotations

from pathlib import Path

from camtasia.timing import seconds_to_ticks

RESOURCES = Path(__file__).parent.parent / 'src' / 'camtasia' / 'resources'


def test_timeline_to_dict_empty_project(project):
    actual_result = project.timeline_to_dict()
    assert actual_result['title'] == project.title
    assert actual_result['duration_seconds'] == project.duration_seconds
    assert actual_result['resolution'] == f'{project.width}x{project.height}'
    assert isinstance(actual_result['tracks'], list)


def test_timeline_to_dict_top_level_keys(project):
    actual_result = project.timeline_to_dict()
    assert set(actual_result.keys()) == {'title', 'duration_seconds', 'resolution', 'tracks'}


def test_timeline_to_dict_with_clip(project):
    track = project.timeline.add_track('TestTrack')
    clip = track.add_clip('VMFile', 1, 0, seconds_to_ticks(5.0))

    actual_result = project.timeline_to_dict()
    track_data = [t for t in actual_result['tracks'] if t['name'] == 'TestTrack']
    assert len(track_data) == 1
    assert track_data[0]['clip_count'] == 1
    clip_data = track_data[0]['clips'][0]
    assert clip_data['type'] == 'VMFile'
    assert clip_data['duration_seconds'] > 0
    assert 'id' in clip_data
    assert 'speed' in clip_data
    assert isinstance(clip_data['effects'], list)


def test_timeline_to_dict_clip_effects(project):
    track = project.timeline.add_track('FX')
    clip = track.add_clip('VMFile', 1, 0, seconds_to_ticks(3.0))
    clip._data.setdefault('effects', []).append({'effectName': 'DropShadow'})

    actual_result = project.timeline_to_dict()
    fx_track = [t for t in actual_result['tracks'] if t['name'] == 'FX'][0]
    assert fx_track['clips'][0]['effects'] == ['DropShadow']


def test_timeline_to_dict_multiple_tracks(project):
    project.timeline.add_track('A')
    t2 = project.timeline.add_track('B')
    t2.add_clip('IMFile', 2, 0, seconds_to_ticks(2.0))
    t2.add_clip('AMFile', 3, seconds_to_ticks(2.0), seconds_to_ticks(1.0))

    actual_result = project.timeline_to_dict()
    b_track = [t for t in actual_result['tracks'] if t['name'] == 'B'][0]
    assert b_track['clip_count'] == 2
    assert len(b_track['clips']) == 2


def test_timeline_to_dict_resolution_format(project):
    project.width = 3840
    project.height = 2160
    actual_result = project.timeline_to_dict()
    assert actual_result['resolution'] == '3840x2160'


def test_timeline_to_dict_effect_missing_name(project):
    track = project.timeline.add_track('T')
    clip = track.add_clip('VMFile', 1, 0, seconds_to_ticks(1.0))
    clip._data.setdefault('effects', []).append({'bypassed': False})

    actual_result = project.timeline_to_dict()
    assert actual_result['tracks'][-1]['clips'][0]['effects'] == ['?']
