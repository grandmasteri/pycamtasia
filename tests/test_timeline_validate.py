"""Tests for Timeline.validate_structure."""
from __future__ import annotations

from camtasia.timeline.timeline import Timeline


def _make_timeline(tracks, track_attributes=None):
    """Build a minimal Timeline from a list of track dicts."""
    data = {
        'sceneTrack': {'scenes': [{'csml': {'tracks': tracks}}]},
        'trackAttributes': track_attributes or [{'ident': ''} for _ in tracks],
    }
    return Timeline(data)


def _track(index, medias=None, transitions=None):
    return {
        'trackIndex': index,
        'medias': medias or [],
        'transitions': transitions or [],
        'parameters': {},
    }


def _clip(clip_id, start=0, duration=100):
    return {
        'id': clip_id,
        '_type': 'IMFile',
        'start': start,
        'duration': duration,
        'mediaStart': 0,
        'mediaDuration': duration,
        'scalar': 1,
        'trackNumber': 0,
        'parameters': {},
        'effects': [],
        'animationTracks': {},
        'metadata': {},
    }


def _transition(left, right):
    return {'name': 'FadeThroughBlack', 'duration': 50, 'leftMedia': left, 'rightMedia': right}


class TestValidateStructure:
    def test_valid_timeline_returns_empty(self):
        tl = _make_timeline([
            _track(0, [_clip(1, 0, 100), _clip(2, 200, 100)]),
            _track(1, [_clip(3, 0, 100)]),
        ])
        assert tl.validate_structure() == []

    def test_duplicate_ids_detected(self):
        tl = _make_timeline([
            _track(0, [_clip(1, 0, 100)]),
            _track(1, [_clip(1, 0, 100)]),
        ])
        issues = tl.validate_structure()
        assert len(issues) == 1
        assert 'Duplicate clip ID 1' in issues[0]

    def test_stale_transition_detected(self):
        tl = _make_timeline([
            _track(0, [_clip(1, 0, 100)], [_transition(1, 999)]),
        ])
        issues = tl.validate_structure()
        assert len(issues) == 1
        assert 'rightMedia=999' in issues[0]

    def test_overlapping_clips_detected(self):
        tl = _make_timeline([
            _track(0, [_clip(1, 0, 200), _clip(2, 100, 200)]),
        ])
        issues = tl.validate_structure()
        assert len(issues) == 1
        assert 'clips 1 and 2 overlap' in issues[0]


class TestValidateStructureEdgeCases:
    def test_track_index_mismatch(self):
        tl = _make_timeline([
            _track(5),  # trackIndex=5 at array position 0
        ])
        actual_issues = tl.validate_structure()
        assert any('trackIndex=5' in i for i in actual_issues)

    def test_stale_left_media(self):
        tl = _make_timeline([
            _track(0, medias=[{'id': 1, '_type': 'AMFile', 'start': 0, 'duration': 100}],
                   transitions=[{'leftMedia': 999, 'rightMedia': 1, 'name': 'X', 'duration': 50}]),
        ])
        actual_issues = tl.validate_structure()
        assert any('leftMedia=999' in i for i in actual_issues)
