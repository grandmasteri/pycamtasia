"""Tests for uncovered lines in operations/speed.py."""
from __future__ import annotations

import copy
from fractions import Fraction

import pytest

from camtasia.operations.speed import _adjust_scalar, rescale_project


def _minimal_project(*clips):
    """Build a minimal project dict with given clips on one track."""
    return {
        'timeline': {
            'sceneTrack': {
                'scenes': [{
                    'csml': {
                        'tracks': [{'trackIndex': 0, 'medias': list(clips), 'transitions': []}],
                    },
                }],
            },
            'parameters': {'toc': {'keyframes': []}},
        },
    }


# ── _adjust_scalar ──

class TestAdjustScalar:
    def test_adjusts_existing_scalar(self):
        clip = {'scalar': '51/101'}
        _adjust_scalar(clip, Fraction(2))
        assert clip['scalar'] == '102/101'

    def test_adjusts_default_scalar(self):
        clip = {}
        _adjust_scalar(clip, Fraction(3))
        assert clip['scalar'] == '3/1'


# ── overlap fix in rescale_project ──

class TestOverlapFix:
    def test_overlap_trimmed_after_rescale(self):
        """Two clips that overlap by 1 tick after rescaling get fixed."""
        clip_a = {
            '_type': 'AMFile', 'id': 1, 'start': 0, 'duration': 100,
            'mediaStart': 0, 'mediaDuration': 100, 'scalar': 1,
            'parameters': {}, 'effects': [], 'metadata': {},
        }
        clip_b = {
            '_type': 'AMFile', 'id': 2, 'start': 99, 'duration': 100,
            'mediaStart': 0, 'mediaDuration': 100, 'scalar': 1,
            'parameters': {}, 'effects': [], 'metadata': {},
        }
        data = _minimal_project(clip_a, clip_b)
        rescale_project(data, Fraction(1))
        medias = data['timeline']['sceneTrack']['scenes'][0]['csml']['tracks'][0]['medias']
        a_end = medias[0]['start'] + medias[0]['duration']
        b_start = medias[1]['start']
        assert a_end <= b_start


# ── _mark_speed_changed (nested in rescale_project, tested via rescale) ──

class TestMarkSpeedChanged:
    def test_marks_amfile_via_rescale(self):
        clip = {
            '_type': 'AMFile', 'id': 1, 'start': 0, 'duration': 100,
            'mediaStart': 0, 'mediaDuration': 100, 'scalar': 1,
            'parameters': {}, 'effects': [], 'metadata': {},
        }
        data = _minimal_project(clip)
        rescale_project(data, Fraction(2))
        media = data['timeline']['sceneTrack']['scenes'][0]['csml']['tracks'][0]['medias'][0]
        assert media['metadata']['clipSpeedAttribute']['value'] is True

    def test_skips_excluded_types(self):
        clip = {
            '_type': 'IMFile', 'id': 1, 'start': 0, 'duration': 100,
            'mediaStart': 0, 'mediaDuration': 1, 'scalar': 1,
            'parameters': {}, 'effects': [], 'metadata': {},
        }
        data = _minimal_project(clip)
        rescale_project(data, Fraction(2))
        media = data['timeline']['sceneTrack']['scenes'][0]['csml']['tracks'][0]['medias'][0]
        assert 'clipSpeedAttribute' not in media.get('metadata', {})

    def test_recurses_into_unified_children(self):
        clip = {
            '_type': 'UnifiedMedia', 'id': 1, 'start': 0, 'duration': 100,
            'mediaStart': 0, 'mediaDuration': 100, 'scalar': 1,
            'parameters': {}, 'effects': [], 'metadata': {},
            'video': {
                '_type': 'VMFile', 'id': 2, 'start': 0, 'duration': 100,
                'mediaStart': 0, 'mediaDuration': 100, 'scalar': 1,
                'parameters': {}, 'effects': [], 'metadata': {},
            },
            'audio': {
                '_type': 'AMFile', 'id': 3, 'start': 0, 'duration': 100,
                'mediaStart': 0, 'mediaDuration': 100, 'scalar': 1,
                'parameters': {}, 'effects': [], 'metadata': {},
            },
        }
        data = _minimal_project(clip)
        rescale_project(data, Fraction(2))
        um = data['timeline']['sceneTrack']['scenes'][0]['csml']['tracks'][0]['medias'][0]
        assert um['video']['metadata']['clipSpeedAttribute']['value'] is True
        assert um['audio']['metadata']['clipSpeedAttribute']['value'] is True

    def test_recurses_into_group_tracks(self):
        clip = {
            '_type': 'Group', 'id': 1, 'start': 0, 'duration': 100,
            'mediaStart': 0, 'mediaDuration': 100, 'scalar': 1,
            'parameters': {}, 'effects': [], 'metadata': {},
            'tracks': [{'medias': [{
                '_type': 'VMFile', 'id': 2, 'start': 0, 'duration': 100,
                'mediaStart': 0, 'mediaDuration': 100, 'scalar': 1,
                'parameters': {}, 'effects': [], 'metadata': {},
            }]}],
        }
        data = _minimal_project(clip)
        rescale_project(data, Fraction(2))
        inner = data['timeline']['sceneTrack']['scenes'][0]['csml']['tracks'][0]['medias'][0]['tracks'][0]['medias'][0]
        assert inner['metadata']['clipSpeedAttribute']['value'] is True

    def test_recurses_into_stitched_medias(self):
        clip = {
            '_type': 'StitchedMedia', 'id': 1, 'start': 0, 'duration': 100,
            'mediaStart': 0, 'mediaDuration': 100, 'scalar': 1,
            'parameters': {}, 'effects': [], 'metadata': {},
            'medias': [{
                '_type': 'AMFile', 'id': 2, 'start': 0, 'duration': 100,
                'mediaStart': 0, 'mediaDuration': 100, 'scalar': 1,
                'parameters': {}, 'effects': [], 'metadata': {},
            }],
        }
        data = _minimal_project(clip)
        rescale_project(data, Fraction(2))
        inner = data['timeline']['sceneTrack']['scenes'][0]['csml']['tracks'][0]['medias'][0]['medias'][0]
        assert inner['metadata']['clipSpeedAttribute']['value'] is True
