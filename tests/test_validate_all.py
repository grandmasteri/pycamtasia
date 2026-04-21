"""Tests for validate_all() and the supporting private checks."""
from __future__ import annotations

from camtasia import validate_all as va
from camtasia.validation import (
    ValidationIssue,
    _check_track_attributes_count,
    _check_transition_completeness,
    validate_all,
)


def _make_data(tracks, track_attributes=None):
    """Wrap tracks into the nested project data structure."""
    return {
        'editRate': 705600000,
        'timeline': {
            'id': 9999,
            'sceneTrack': {
                'scenes': [{'csml': {'tracks': tracks}}],
            },
            'trackAttributes': track_attributes if track_attributes is not None else [{'ident': ''} for _ in tracks],
        },
    }


# --- _check_transition_completeness ---

class TestTransitionCompleteness:
    def test_complete_transition_passes(self):
        data = _make_data([{
            'medias': [{'id': 1}, {'id': 2}],
            'transitions': [{'name': 'Fade', 'duration': 50, 'leftMedia': 1, 'rightMedia': 2}],
        }])
        assert _check_transition_completeness(data) == []

    def test_missing_name_detected(self):
        data = _make_data([{
            'medias': [],
            'transitions': [{'duration': 50, 'leftMedia': 1}],
        }])
        issues = _check_transition_completeness(data)
        assert len(issues) == 1
        assert issues[0].level == 'error'
        assert "'name'" in issues[0].message

    def test_missing_duration_detected(self):
        data = _make_data([{
            'medias': [],
            'transitions': [{'name': 'Fade', 'leftMedia': 1}],
        }])
        issues = _check_transition_completeness(data)
        assert len(issues) == 1
        assert "'duration'" in issues[0].message

    def test_missing_both_keys(self):
        data = _make_data([{
            'medias': [],
            'transitions': [{'leftMedia': 1}],
        }])
        issues = _check_transition_completeness(data)
        assert len(issues) == 2


# --- _check_track_attributes_count ---

class TestTrackAttributesCount:
    def test_matching_count_passes(self):
        data = _make_data(
            [{'medias': []}, {'medias': []}],
            track_attributes=[{'ident': 'A'}, {'ident': 'B'}],
        )
        assert _check_track_attributes_count(data) == []

    def test_mismatch_detected(self):
        data = _make_data(
            [{'medias': []}, {'medias': []}],
            track_attributes=[{'ident': 'A'}],
        )
        issues = _check_track_attributes_count(data)
        assert len(issues) == 1
        assert issues[0].level == 'warning'
        assert '1' in issues[0].message
        assert '2' in issues[0].message


# --- validate_all ---

class TestValidateAll:
    def test_clean_data_returns_empty(self):
        data = _make_data([
            {'trackIndex': 0, 'medias': [{'id': 1}], 'transitions': []},
        ])
        assert validate_all(data) == []

    def test_aggregates_multiple_checks(self):
        data = _make_data(
            [
                {
                    'trackIndex': 5,                       # bad trackIndex
                    'medias': [{'id': 1}, {'id': 1}],      # duplicate IDs
                    'transitions': [{'leftMedia': 999}],   # stale ref + missing name + missing duration
                },
            ],
            track_attributes=[],                           # count mismatch
        )
        issues = validate_all(data)
        messages = ' '.join(i.message for i in issues)
        assert 'Duplicate clip ID 1' in messages
        assert 'trackIndex=5' in messages
        assert 'leftMedia=999' in messages
        assert "'name'" in messages
        assert 'trackAttributes length' in messages

    def test_returns_list_of_validation_issues(self):
        data = _make_data([{'medias': [{'id': 1}, {'id': 1}]}])
        issues = validate_all(data)
        assert all(isinstance(i, ValidationIssue) for i in issues)

    def test_importable_from_package(self):
        assert callable(va)


class TestCheckTimelineIdUnique:
    def test_missing_timeline_id_warns(self):
        from camtasia.validation import _check_timeline_id_unique
        data = {'timeline': {}}
        issues = _check_timeline_id_unique(data)
        assert len(issues) == 1
        assert 'missing' in issues[0].message

    def test_timeline_id_collides_with_clip_id(self):
        from camtasia.validation import _check_timeline_id_unique
        data = _make_data([{'trackIndex': 0, 'medias': [{'id': 42}], 'transitions': []}])
        data['timeline']['id'] = 42
        issues = _check_timeline_id_unique(data)
        assert len(issues) == 1
        assert 'collides' in issues[0].message

    def test_timeline_id_unique_ok(self):
        from camtasia.validation import _check_timeline_id_unique
        data = _make_data([{'trackIndex': 0, 'medias': [{'id': 1}], 'transitions': []}])
        assert _check_timeline_id_unique(data) == []


class TestCheckBehaviorEffectStructure:
    def test_missing_phase_flagged(self):
        from camtasia.validation import _check_behavior_effect_structure
        data = _make_data([{'trackIndex': 0, 'medias': [
            {'id': 1, 'effects': [{'_type': 'GenericBehaviorEffect', 'in': {}, 'center': {}}]},
        ], 'transitions': []}])
        issues = _check_behavior_effect_structure(data)
        assert len(issues) == 1
        assert "'out'" in issues[0].message

    def test_complete_behavior_ok(self):
        from camtasia.validation import _check_behavior_effect_structure
        data = _make_data([{'trackIndex': 0, 'medias': [
            {'id': 1, 'effects': [{'_type': 'GenericBehaviorEffect',
                                   'in': {}, 'center': {}, 'out': {}}]},
        ], 'transitions': []}])
        assert _check_behavior_effect_structure(data) == []


class TestCheckClipOverlapOnTrack:
    def test_overlapping_clips_flagged(self):
        from camtasia.validation import _check_clip_overlap_on_track
        data = _make_data([{'trackIndex': 0, 'medias': [
            {'id': 1, 'start': 0, 'duration': 100},
            {'id': 2, 'start': 50, 'duration': 100},
        ], 'transitions': []}])
        issues = _check_clip_overlap_on_track(data)
        assert len(issues) == 1
        assert 'overlapping' in issues[0].message

    def test_adjacent_clips_ok(self):
        from camtasia.validation import _check_clip_overlap_on_track
        data = _make_data([{'trackIndex': 0, 'medias': [
            {'id': 1, 'start': 0, 'duration': 100},
            {'id': 2, 'start': 100, 'duration': 100},
        ], 'transitions': []}])
        assert _check_clip_overlap_on_track(data) == []


class TestCheckTransitionNullEndpoints:
    def test_null_left_media_flagged(self):
        from camtasia.validation import _check_transition_null_endpoints
        data = _make_data([{'trackIndex': 0, 'medias': [], 'transitions': [
            {'leftMedia': None, 'rightMedia': 5},
        ]}])
        issues = _check_transition_null_endpoints(data)
        assert len(issues) == 1
        assert 'leftMedia=null' in issues[0].message

    def test_omitted_left_media_ok(self):
        from camtasia.validation import _check_transition_null_endpoints
        data = _make_data([{'trackIndex': 0, 'medias': [], 'transitions': [
            {'rightMedia': 5},
        ]}])
        assert _check_transition_null_endpoints(data) == []
