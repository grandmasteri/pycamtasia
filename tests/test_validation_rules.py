"""Tests for duplicate clip ID and track index consistency validation rules."""
from __future__ import annotations

from camtasia.validation import _check_duplicate_clip_ids, _check_track_indices


def _make_data(tracks):
    """Wrap track list into the expected nested project data structure."""
    return {
        'timeline': {
            'sceneTrack': {
                'scenes': [{
                    'csml': {'tracks': tracks}
                }]
            }
        }
    }


# --- Duplicate clip IDs ---

def test_duplicate_clip_ids_detected():
    data = _make_data([
        {'medias': [{'id': 1}, {'id': 1}]},
    ])
    issues = _check_duplicate_clip_ids(data)
    assert len(issues) == 1
    assert issues[0].level == 'error'
    assert 'Duplicate clip ID 1' in issues[0].message


def test_no_duplicate_ids_passes():
    data = _make_data([
        {'medias': [{'id': 1}, {'id': 2}]},
        {'medias': [{'id': 3}]},
    ])
    issues = _check_duplicate_clip_ids(data)
    assert issues == []


# --- Track index consistency ---

def test_track_index_mismatch_detected():
    data = _make_data([
        {'trackIndex': 0, 'medias': []},
        {'trackIndex': 5, 'medias': []},
    ])
    issues = _check_track_indices(data)
    assert len(issues) == 1
    assert issues[0].level == 'warning'
    assert 'array[1]' in issues[0].message
    assert 'trackIndex=5' in issues[0].message


def test_track_index_consistent_passes():
    data = _make_data([
        {'trackIndex': 0, 'medias': []},
        {'trackIndex': 1, 'medias': []},
    ])
    issues = _check_track_indices(data)
    assert issues == []


class TestDuplicateIdsWithNestedMedia:
    def test_video_audio_ids_checked(self):
        data = _make_data(tracks=[
            {'trackIndex': 0, 'medias': [
                {'id': 1, '_type': 'UnifiedMedia',
                 'video': {'id': 2, '_type': 'ScreenVMFile'},
                 'audio': {'id': 2, '_type': 'AMFile'}},
            ]},
        ])
        actual_issues = _check_duplicate_clip_ids(data)
        assert any('Duplicate clip ID 2' in i.message for i in actual_issues)

    def test_nested_group_ids_checked(self):
        data = _make_data(tracks=[
            {'trackIndex': 0, 'medias': [
                {'id': 1, '_type': 'Group', 'tracks': [
                    {'medias': [{'id': 1, '_type': 'VMFile'}]}
                ]},
            ]},
        ])
        actual_issues = _check_duplicate_clip_ids(data)
        assert any('Duplicate clip ID 1' in i.message for i in actual_issues)
