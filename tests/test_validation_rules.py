"""Tests for duplicate clip ID and track index consistency validation rules."""
from __future__ import annotations

from camtasia.validation import (
    _check_duplicate_clip_ids,
    _check_track_attributes_count,
    _check_track_indices,
    _check_transition_completeness,
    _check_transition_references,
)


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


# --- Transition references ---

def test_stale_transition_detected():
    data = _make_data([
        {'medias': [{'id': 1}, {'id': 2}],
         'transitions': [{'leftMedia': 1, 'rightMedia': 999}]},
    ])
    issues = _check_transition_references(data)
    assert len(issues) == 1
    assert issues[0].level == 'error'
    assert 'rightMedia=999' in issues[0].message


def test_valid_transitions_pass():
    data = _make_data([
        {'medias': [{'id': 1}, {'id': 2}],
         'transitions': [{'leftMedia': 1, 'rightMedia': 2}]},
    ])
    issues = _check_transition_references(data)
    assert issues == []


class TestStaleLeftMediaTransition:
    def test_stale_left_media_detected(self):
        data = _make_data(tracks=[{
            'trackIndex': 0,
            'medias': [{'id': 1, '_type': 'AMFile'}],
            'transitions': [{'leftMedia': 999, 'rightMedia': 1, 'name': 'FadeThroughBlack', 'duration': 100}],
        }])
        actual_issues = _check_transition_references(data)
        assert any('leftMedia=999' in i.message for i in actual_issues)


# --- Transition completeness ---

def test_transition_missing_both_media_detected():
    data = _make_data([
        {'medias': [{'id': 1}],
         'transitions': [{'leftMedia': None, 'rightMedia': None, 'name': 'Fade', 'duration': 100}]},
    ])
    issues = _check_transition_completeness(data)
    assert len(issues) == 1
    assert issues[0].level == 'error'
    assert 'neither leftMedia nor rightMedia' in issues[0].message


def test_transition_with_left_media_passes():
    data = _make_data([
        {'medias': [{'id': 1}],
         'transitions': [{'leftMedia': 1, 'rightMedia': None, 'name': 'Fade', 'duration': 100}]},
    ])
    issues = _check_transition_completeness(data)
    assert issues == []


def test_transition_with_right_media_passes():
    data = _make_data([
        {'medias': [{'id': 1}],
         'transitions': [{'leftMedia': None, 'rightMedia': 1, 'name': 'Fade', 'duration': 100}]},
    ])
    issues = _check_transition_completeness(data)
    assert issues == []


def test_transition_with_both_media_passes():
    data = _make_data([
        {'medias': [{'id': 1}, {'id': 2}],
         'transitions': [{'leftMedia': 1, 'rightMedia': 2, 'name': 'Fade', 'duration': 100}]},
    ])
    issues = _check_transition_completeness(data)
    assert issues == []


# --- Track attributes count ---

def _make_data_with_attrs(tracks, attrs):
    """Wrap tracks and trackAttributes into project data."""
    return {
        'timeline': {
            'sceneTrack': {
                'scenes': [{
                    'csml': {'tracks': tracks}
                }]
            },
            'trackAttributes': attrs,
        }
    }


def test_track_attributes_count_mismatch_detected():
    data = _make_data_with_attrs(
        [{'medias': []}, {'medias': []}],
        [{}],
    )
    issues = _check_track_attributes_count(data)
    assert len(issues) == 1
    assert issues[0].level == 'warning'
    assert 'trackAttributes length (1) != tracks length (2)' in issues[0].message


def test_track_attributes_count_matches_passes():
    data = _make_data_with_attrs(
        [{'medias': []}, {'medias': []}],
        [{}, {}],
    )
    issues = _check_track_attributes_count(data)
    assert issues == []


# --- Callout excluded from timing consistency ---

def test_callout_excluded_from_timing_consistency():
    """Bug 2: Callout clips should be excluded from mediaDuration consistency check."""
    from camtasia.validation import _check_timing_consistency
    data = _make_data([{
        'medias': [{
            'id': 1,
            '_type': 'Callout',
            'start': 0,
            'duration': 1000,
            'mediaDuration': 500,
            'scalar': '1/2',
        }],
    }])
    issues = _check_timing_consistency(data)
    assert issues == []


def test_collect_ids_recurses_into_unified_media():
    """Bug 4: _collect_ids_grouped should recurse into UnifiedMedia video/audio sub-dicts."""
    from camtasia.validation import _collect_ids_grouped
    media = {
        'id': 1, '_type': 'UnifiedMedia',
        'video': {'id': 2, '_type': 'VMFile'},
        'audio': {'id': 3, '_type': 'AMFile'},
    }
    ids_to_locs: dict = {}
    _collect_ids_grouped(media, ids_to_locs, 'test')
    collected_ids = list(ids_to_locs.keys())
    assert 1 in collected_ids
    assert 2 in collected_ids
    assert 3 in collected_ids


def test_check_group_required_fields_recurses_into_stitched_media():
    """Bug 5: _check_group_required_fields should recurse into StitchedMedia/UnifiedMedia."""
    from camtasia.validation import _check_group_required_fields
    data = {
        'version': '10.0',
        'timeline': {'sceneTrack': {'scenes': [{'csml': {'tracks': [
            {'medias': [{
                '_type': 'StitchedMedia', 'id': 1,
                'medias': [{
                    '_type': 'Group', 'id': 2,
                    'parameters': {},  # missing required params
                    'metadata': {},
                    'tracks': [],
                }],
            }]},
        ]}}]}},
    }
    issues = _check_group_required_fields(data)
    # Should find the nested Group with missing parameters
    assert any('group id=2' in i.message for i in issues)


def test_check_group_required_fields_recurses_into_unified_media():
    """Bug 5: _check_group_required_fields should recurse into UnifiedMedia children."""
    from camtasia.validation import _check_group_required_fields
    data = {
        'version': '10.0',
        'timeline': {'sceneTrack': {'scenes': [{'csml': {'tracks': [
            {'medias': [{
                '_type': 'UnifiedMedia', 'id': 1,
                'video': {
                    '_type': 'Group', 'id': 3,
                    'parameters': {},
                    'metadata': {},
                    'tracks': [],
                },
            }]},
        ]}}]}},
    }
    issues = _check_group_required_fields(data)
    assert any('group id=3' in i.message for i in issues)


# -- visual track order validator --

def test_unsorted_visual_segments_detected() -> None:
    """_check_visual_track_order catches out-of-order visual animation segments
    (regression for src/camtasia/validation.py:519).

    Visual parameters share animation tracks that require monotonically
    increasing segment times; unsorted segments would produce a file
    Camtasia rejects.
    """
    from camtasia.validation import _check_visual_track_order
    data = _make_data([
        {
            'medias': [
                {
                    'id': 1,
                    'animationTracks': {
                        'visual': [
                            {'range': [100]},
                            {'range': [50]},  # out of order
                            {'range': [200]},
                        ],
                    },
                }
            ],
        },
    ])
    issues = _check_visual_track_order(data)
    assert any('unsorted animationTracks.visual segments' in i.message for i in issues)
