"""Tests for null transition refs, overlapping clips, and behavior phases checks."""
from __future__ import annotations

from camtasia.validation import (
    _check_behavior_effect_structure,
    _check_clip_overlap_on_track,
    _check_transition_null_endpoints,
)


def _make_data(tracks):
    return {
        'timeline': {
            'sceneTrack': {
                'scenes': [{
                    'csml': {'tracks': tracks}
                }]
            }
        }
    }


# --- Null transition refs ---

class TestNullTransitionRefs:
    def test_explicit_null_left_media_flagged(self):
        data = _make_data([{
            'medias': [{'id': 1}],
            'transitions': [{'leftMedia': None, 'rightMedia': 1, 'name': 'Fade', 'duration': 100}],
        }])
        issues = _check_transition_null_endpoints(data)
        assert len(issues) == 1
        assert issues[0].level == 'warning'
        assert 'leftMedia=null' in issues[0].message

    def test_explicit_null_right_media_flagged(self):
        data = _make_data([{
            'medias': [{'id': 1}],
            'transitions': [{'leftMedia': 1, 'rightMedia': None, 'name': 'Fade', 'duration': 100}],
        }])
        issues = _check_transition_null_endpoints(data)
        assert len(issues) == 1
        assert 'rightMedia=null' in issues[0].message

    def test_both_null_flags_two_issues(self):
        data = _make_data([{
            'medias': [{'id': 1}],
            'transitions': [{'leftMedia': None, 'rightMedia': None, 'name': 'Fade', 'duration': 100}],
        }])
        issues = _check_transition_null_endpoints(data)
        assert len(issues) == 2

    def test_omitted_fields_pass(self):
        data = _make_data([{
            'medias': [{'id': 1}],
            'transitions': [{'name': 'Fade', 'duration': 100}],
        }])
        issues = _check_transition_null_endpoints(data)
        assert issues == []

    def test_valid_integer_refs_pass(self):
        data = _make_data([{
            'medias': [{'id': 1}, {'id': 2}],
            'transitions': [{'leftMedia': 1, 'rightMedia': 2, 'name': 'Fade', 'duration': 100}],
        }])
        issues = _check_transition_null_endpoints(data)
        assert issues == []


# --- Overlapping clips ---

class TestOverlappingClips:
    def test_overlapping_clips_flagged(self):
        data = _make_data([{
            'medias': [
                {'id': 1, 'start': 0, 'duration': 100},
                {'id': 2, 'start': 50, 'duration': 100},
            ],
        }])
        issues = _check_clip_overlap_on_track(data)
        assert len(issues) == 1
        assert issues[0].level == 'warning'
        assert 'clip id=1' in issues[0].message
        assert 'clip id=2' in issues[0].message

    def test_adjacent_clips_pass(self):
        data = _make_data([{
            'medias': [
                {'id': 1, 'start': 0, 'duration': 100},
                {'id': 2, 'start': 100, 'duration': 100},
            ],
        }])
        issues = _check_clip_overlap_on_track(data)
        assert issues == []

    def test_gap_between_clips_passes(self):
        data = _make_data([{
            'medias': [
                {'id': 1, 'start': 0, 'duration': 50},
                {'id': 2, 'start': 100, 'duration': 50},
            ],
        }])
        issues = _check_clip_overlap_on_track(data)
        assert issues == []

    def test_single_clip_passes(self):
        data = _make_data([{
            'medias': [{'id': 1, 'start': 0, 'duration': 100}],
        }])
        issues = _check_clip_overlap_on_track(data)
        assert issues == []

    def test_different_tracks_dont_conflict(self):
        data = _make_data([
            {'medias': [{'id': 1, 'start': 0, 'duration': 100}]},
            {'medias': [{'id': 2, 'start': 0, 'duration': 100}]},
        ])
        issues = _check_clip_overlap_on_track(data)
        assert issues == []


# --- Behavior phases ---

class TestBehaviorPhases:
    def test_missing_in_phase_flagged(self):
        data = _make_data([{
            'medias': [{'id': 1, 'effects': [{
                '_type': 'GenericBehaviorEffect',
                'center': {}, 'out': {},
            }]}],
        }])
        issues = _check_behavior_effect_structure(data)
        assert len(issues) == 1
        assert issues[0].level == 'error'
        assert "'in'" in issues[0].message

    def test_missing_all_phases_flags_three(self):
        data = _make_data([{
            'medias': [{'id': 1, 'effects': [{
                '_type': 'GenericBehaviorEffect',
            }]}],
        }])
        issues = _check_behavior_effect_structure(data)
        assert len(issues) == 3

    def test_complete_phases_pass(self):
        data = _make_data([{
            'medias': [{'id': 1, 'effects': [{
                '_type': 'GenericBehaviorEffect',
                'in': {}, 'center': {}, 'out': {},
            }]}],
        }])
        issues = _check_behavior_effect_structure(data)
        assert issues == []

    def test_other_effect_types_ignored(self):
        data = _make_data([{
            'medias': [{'id': 1, 'effects': [{
                '_type': 'SomeOtherEffect',
            }]}],
        }])
        issues = _check_behavior_effect_structure(data)
        assert issues == []

    def test_no_effects_passes(self):
        data = _make_data([{
            'medias': [{'id': 1}],
        }])
        issues = _check_behavior_effect_structure(data)
        assert issues == []
