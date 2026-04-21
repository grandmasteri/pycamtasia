from __future__ import annotations

import json

import pytest

from camtasia.export.timeline_json import export_timeline_json, load_timeline_json


@pytest.fixture
def timeline_json_path(tmp_path):
    return tmp_path / 'timeline.json'


@pytest.fixture
def populated_project(project):
    """Project with a track containing a clip and a timeline marker."""
    track = project.timeline.add_track('TestTrack')
    track.add_clip('AMFile', 1, 0, 705600000)  # 1 second
    project.timeline.add_marker('Intro', 0.5)
    return project


def test_export_creates_file(populated_project, timeline_json_path):
    actual_result = export_timeline_json(populated_project, timeline_json_path)
    assert actual_result.exists()
    assert actual_result == timeline_json_path


def test_export_has_version(populated_project, timeline_json_path):
    export_timeline_json(populated_project, timeline_json_path)
    actual_data = json.loads(timeline_json_path.read_text())
    assert actual_data['version'] == '1.1'


def test_export_has_canvas(populated_project, timeline_json_path):
    export_timeline_json(populated_project, timeline_json_path)
    actual_data = json.loads(timeline_json_path.read_text())
    assert actual_data['canvas'] == {
        'width': populated_project.width,
        'height': populated_project.height,
    }


def test_export_has_tracks_with_clips(populated_project, timeline_json_path):
    export_timeline_json(populated_project, timeline_json_path)
    actual_data = json.loads(timeline_json_path.read_text())
    test_tracks = [t for t in actual_data['tracks'] if t['name'] == 'TestTrack']
    assert len(test_tracks) == 1
    assert len(test_tracks[0]['clips']) == 1
    actual_clip = test_tracks[0]['clips'][0]
    assert actual_clip['type'] == 'AMFile'
    assert actual_clip['duration_seconds'] == 1.0


def test_export_has_markers(populated_project, timeline_json_path):
    export_timeline_json(populated_project, timeline_json_path)
    actual_data = json.loads(timeline_json_path.read_text())
    assert any(m['name'] == 'Intro' for m in actual_data['markers'])


def test_load_reads_back(populated_project, timeline_json_path):
    export_timeline_json(populated_project, timeline_json_path)
    actual_data = load_timeline_json(timeline_json_path)
    assert isinstance(actual_data, dict)
    assert 'version' in actual_data
    assert 'tracks' in actual_data


def test_round_trip_export_load(populated_project, timeline_json_path):
    export_timeline_json(populated_project, timeline_json_path)
    actual_data = load_timeline_json(timeline_json_path)
    raw = json.loads(timeline_json_path.read_text())
    assert actual_data == raw


def test_export_includes_transitions_when_enabled(populated_project, timeline_json_path):
    """With include_transitions=True (default), transitions appear in track entries."""
    # Inject a transition on track 0
    track = populated_project.timeline.tracks[0]
    track._data['transitions'] = [
        {'name': 'fade', 'leftMedia': 1, 'rightMedia': 2, 'duration': 10},
    ]
    export_timeline_json(populated_project, timeline_json_path)
    data = json.loads(timeline_json_path.read_text())
    t0 = next(t for t in data['tracks'] if t['index'] == 0)
    assert 'transitions' in t0
    assert t0['transitions'][0]['name'] == 'fade'


def test_export_excludes_transitions_when_disabled(populated_project, timeline_json_path):
    track = populated_project.timeline.tracks[0]
    track._data['transitions'] = [
        {'name': 'fade', 'leftMedia': 1, 'rightMedia': 2, 'duration': 10},
    ]
    export_timeline_json(populated_project, timeline_json_path, include_transitions=False)
    data = json.loads(timeline_json_path.read_text())
    for t in data['tracks']:
        assert 'transitions' not in t


def test_export_includes_effects_when_enabled(populated_project, timeline_json_path):
    """Clips with effects have their effect names listed."""
    track = populated_project.timeline.find_track_by_name('TestTrack')
    clip = next(iter(track.clips))
    clip._data['effects'] = [{'effectName': 'DropShadow'}]
    export_timeline_json(populated_project, timeline_json_path)
    data = json.loads(timeline_json_path.read_text())
    all_clips = [c for t in data['tracks'] for c in t['clips']]
    with_effects = [c for c in all_clips if 'effects' in c]
    assert any('DropShadow' in c['effects'] for c in with_effects)


def test_export_includes_metadata_when_enabled(populated_project, timeline_json_path):
    """Clip metadata (mediaDuration, scalar) appears."""
    export_timeline_json(populated_project, timeline_json_path)
    data = json.loads(timeline_json_path.read_text())
    all_clips = [c for t in data['tracks'] for c in t['clips']]
    # At least one clip should expose mediaDuration
    assert any('mediaDuration' in c for c in all_clips)


def test_export_includes_scalar_when_non_unity(populated_project, timeline_json_path):
    """When a clip has a speed change (scalar != 1), it's included."""
    track = populated_project.timeline.find_track_by_name('TestTrack')
    clip = next(iter(track.clips))
    clip._data['scalar'] = '1/2'
    export_timeline_json(populated_project, timeline_json_path)
    data = json.loads(timeline_json_path.read_text())
    all_clips = [c for t in data['tracks'] for c in t['clips']]
    assert any(c.get('scalar') == '1/2' for c in all_clips)
