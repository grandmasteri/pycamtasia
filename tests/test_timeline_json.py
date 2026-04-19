from __future__ import annotations

import json
from pathlib import Path

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
    assert actual_data['version'] == '1.0'


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
