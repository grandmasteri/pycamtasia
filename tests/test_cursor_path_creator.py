"""Tests for CursorPathCreator effect and BaseClip.add_cursor_path_creator."""
from __future__ import annotations

import pytest

from camtasia.effects.base import _EFFECT_REGISTRY, effect_from_dict
from camtasia.effects.cursor import CursorPathCreator
from camtasia.timing import seconds_to_ticks


def _effect_dict(name: str, **params) -> dict:
    return {
        'effectName': name,
        'bypassed': False,
        'category': 'cursor',
        'parameters': params,
    }


def _path_param(keyframes: list[tuple[float, float, float]]) -> dict:
    """Build a cursorPath parameter from (time_seconds, x, y) tuples."""
    kfs = []
    for i, (t, x, y) in enumerate(keyframes):
        ticks = seconds_to_ticks(t)
        next_ticks = seconds_to_ticks(keyframes[i + 1][0]) if i + 1 < len(keyframes) else ticks
        kfs.append({
            'endTime': next_ticks,
            'time': ticks,
            'value': [x, y, 0],
            'duration': next_ticks - ticks,
        })
    return {
        'type': 'point',
        'defaultValue': [0, 0, 0],
        'keyframes': kfs,
    }


class TestCursorPathCreatorEffect:

    def test_registered_in_registry(self):
        assert 'CursorPathCreator' in _EFFECT_REGISTRY

    def test_effect_from_dict_dispatch(self):
        d = _effect_dict('CursorPathCreator')
        e = effect_from_dict(d)
        assert type(e) is CursorPathCreator

    def test_keyframes_empty(self):
        d = _effect_dict('CursorPathCreator', cursorPath={
            'type': 'point', 'defaultValue': [0, 0, 0], 'keyframes': [],
        })
        e = CursorPathCreator(d)
        assert e.keyframes == []

    def test_keyframes_returns_time_x_y(self):
        d = _effect_dict('CursorPathCreator', cursorPath=_path_param([
            (0.0, 100.0, 200.0),
            (1.0, 300.0, 400.0),
        ]))
        e = CursorPathCreator(d)
        kfs = e.keyframes
        assert len(kfs) == 2
        assert kfs[0] == {'time': 0.0, 'x': 100.0, 'y': 200.0}
        assert kfs[1]['x'] == 300.0
        assert kfs[1]['y'] == 400.0
        assert kfs[1]['time'] == pytest.approx(1.0)

    def test_add_point_builds_keyframes(self):
        d = _effect_dict('CursorPathCreator', cursorPath={
            'type': 'point', 'defaultValue': [0, 0, 0], 'keyframes': [],
        })
        e = CursorPathCreator(d)
        e.add_point(0.0, 10.0, 20.0)
        e.add_point(2.0, 30.0, 40.0)
        kfs = e.keyframes
        assert len(kfs) == 2
        assert kfs[0] == {'time': 0.0, 'x': 10.0, 'y': 20.0}
        assert kfs[1]['x'] == 30.0
        assert kfs[1]['y'] == 40.0

    def test_add_point_sorted_order(self):
        d = _effect_dict('CursorPathCreator')
        e = CursorPathCreator(d)
        e.add_point(2.0, 30.0, 40.0)
        e.add_point(0.0, 10.0, 20.0)
        e.add_point(1.0, 50.0, 60.0)
        kfs = e.keyframes
        assert [kf['time'] for kf in kfs] == [0.0, pytest.approx(1.0), pytest.approx(2.0)]

    def test_add_point_recomputes_durations(self):
        d = _effect_dict('CursorPathCreator')
        e = CursorPathCreator(d)
        e.add_point(0.0, 0.0, 0.0)
        e.add_point(2.0, 100.0, 100.0)
        raw_kfs = e.parameters['cursorPath']['keyframes']
        # First keyframe duration should span to second
        assert raw_kfs[0]['duration'] == seconds_to_ticks(2.0)
        # Last keyframe duration should be 0
        assert raw_kfs[1]['duration'] == 0

    def test_clear_points(self):
        d = _effect_dict('CursorPathCreator')
        e = CursorPathCreator(d)
        e.add_point(0.0, 10.0, 20.0)
        e.add_point(1.0, 30.0, 40.0)
        assert len(e.keyframes) == 2
        e.clear_points()
        assert e.keyframes == []

    def test_clear_points_no_path_is_noop(self):
        d = _effect_dict('CursorPathCreator')
        e = CursorPathCreator(d)
        e.clear_points()  # should not raise

    def test_name_property(self):
        d = _effect_dict('CursorPathCreator')
        e = CursorPathCreator(d)
        assert e.name == 'CursorPathCreator'


class TestBaseClipAddCursorPathCreator:

    def test_add_cursor_path_creator_returns_effect(self, project):
        track = project.timeline.get_or_create_track('Test')
        media = list(project.media_bin)
        clip = track.add_image(media[0].id if media else 1, start_seconds=0.0, duration_seconds=5.0)
        effect = clip.add_cursor_path_creator()
        assert isinstance(effect, CursorPathCreator)
        assert effect.name == 'CursorPathCreator'

    def test_add_cursor_path_creator_appends_to_effects(self, project):
        track = project.timeline.get_or_create_track('Test')
        media = list(project.media_bin)
        clip = track.add_image(media[0].id if media else 1, start_seconds=0.0, duration_seconds=5.0)
        clip.add_cursor_path_creator()
        assert 'CursorPathCreator' in clip.effect_names

    def test_add_cursor_path_creator_then_add_points(self, project):
        track = project.timeline.get_or_create_track('Test')
        media = list(project.media_bin)
        clip = track.add_image(media[0].id if media else 1, start_seconds=0.0, duration_seconds=5.0)
        cpc = clip.add_cursor_path_creator()
        cpc.add_point(0.0, 100.0, 200.0)
        cpc.add_point(1.0, 300.0, 400.0)
        assert len(cpc.keyframes) == 2
        # Verify effect is on the clip's effects list
        assert clip.effect_count >= 1
