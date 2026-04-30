"""Tests for BaseClip motion path, bezier handles, and line-type keyframes."""
from __future__ import annotations

from typing import Any

import pytest

from camtasia.timeline.clips import BaseClip, clip_from_dict
from camtasia.timing import seconds_to_ticks


def _clip(duration_s: float = 10.0, **kw: Any) -> BaseClip:
    d: dict[str, Any] = {
        'id': 1,
        '_type': 'VMFile',
        'src': 1,
        'start': 0,
        'duration': seconds_to_ticks(duration_s),
        'mediaStart': 0,
        'mediaDuration': seconds_to_ticks(duration_s),
        'scalar': 1,
        'parameters': {},
        'effects': [],
        'animationTracks': {},
    }
    d.update(kw)
    return clip_from_dict(d)


# ------------------------------------------------------------------
# set_position_keyframes_with_line_type
# ------------------------------------------------------------------

class TestSetPositionKeyframesWithLineType:
    def test_writes_line_type_on_each_keyframe(self) -> None:
        c = _clip()
        c.set_position_keyframes_with_line_type(
            [(0.0, 0.0, 0.0), (5.0, 100.0, 200.0)],
            ['angle', 'curve'],
        )
        x_kfs = c.parameters['translation0']['keyframes']
        assert x_kfs[0]['lineType'] == 'angle'
        assert x_kfs[1]['lineType'] == 'curve'

    def test_y_keyframes_also_tagged(self) -> None:
        c = _clip()
        c.set_position_keyframes_with_line_type(
            [(0.0, 10.0, 20.0), (3.0, 30.0, 40.0)],
            ['combination', 'angle'],
        )
        y_kfs = c.parameters['translation1']['keyframes']
        assert y_kfs[0]['lineType'] == 'combination'
        assert y_kfs[1]['lineType'] == 'angle'

    def test_default_value_is_last_point(self) -> None:
        c = _clip()
        c.set_position_keyframes_with_line_type(
            [(0.0, 1.0, 2.0), (5.0, 3.0, 4.0)],
            ['curve', 'curve'],
        )
        assert c.parameters['translation0']['defaultValue'] == 3.0
        assert c.parameters['translation1']['defaultValue'] == 4.0

    def test_creates_visual_tracks(self) -> None:
        c = _clip()
        c.set_position_keyframes_with_line_type(
            [(0.0, 0.0, 0.0), (2.0, 10.0, 10.0)],
            ['curve', 'curve'],
        )
        assert len(c.visual_animations) > 0

    def test_returns_self(self) -> None:
        c = _clip()
        assert c.set_position_keyframes_with_line_type(
            [(0.0, 0.0, 0.0)], ['curve'],
        ) is c


# ------------------------------------------------------------------
# set_position_bezier_handles
# ------------------------------------------------------------------

class TestSetPositionBezierHandles:
    def test_writes_bezier_interp(self) -> None:
        c = _clip()
        c.set_position_bezier_handles([
            {'time': 0.0, 'x': 0.0, 'y': 0.0,
             'out_tangent': {'x': 10.0, 'y': 5.0}},
            {'time': 5.0, 'x': 100.0, 'y': 50.0,
             'in_tangent': {'x': -10.0, 'y': -5.0}},
        ])
        x_kfs = c.parameters['translation0']['keyframes']
        assert x_kfs[0]['interp'] == 'bezi'
        assert x_kfs[0]['outTangent'] == 10.0
        assert x_kfs[1]['inTangent'] == -10.0

    def test_y_tangents_written(self) -> None:
        c = _clip()
        c.set_position_bezier_handles([
            {'time': 0.0, 'x': 0.0, 'y': 0.0,
             'out_tangent': {'x': 1.0, 'y': 2.0}},
            {'time': 3.0, 'x': 50.0, 'y': 60.0,
             'in_tangent': {'x': -1.0, 'y': -2.0}},
        ])
        y_kfs = c.parameters['translation1']['keyframes']
        assert y_kfs[0]['outTangent'] == 2.0
        assert y_kfs[1]['inTangent'] == -2.0

    def test_default_value_is_last_entry(self) -> None:
        c = _clip()
        c.set_position_bezier_handles([
            {'time': 0.0, 'x': 0.0, 'y': 0.0},
            {'time': 5.0, 'x': 99.0, 'y': 88.0},
        ])
        assert c.parameters['translation0']['defaultValue'] == 99.0
        assert c.parameters['translation1']['defaultValue'] == 88.0

    def test_returns_self(self) -> None:
        c = _clip()
        result = c.set_position_bezier_handles([
            {'time': 0.0, 'x': 0.0, 'y': 0.0},
        ])
        assert result is c


# ------------------------------------------------------------------
# add_motion_point
# ------------------------------------------------------------------

class TestAddMotionPoint:
    def test_creates_keyframes_from_scratch(self) -> None:
        c = _clip()
        c.add_motion_point(0.0, 10.0, 20.0)
        assert c.parameters['translation0']['keyframes'][0]['value'] == 10.0
        assert c.parameters['translation1']['keyframes'][0]['value'] == 20.0

    def test_appends_to_existing_keyframes(self) -> None:
        c = _clip()
        c.add_motion_point(0.0, 0.0, 0.0)
        c.add_motion_point(5.0, 100.0, 200.0)
        x_kfs = c.parameters['translation0']['keyframes']
        assert len(x_kfs) == 2
        assert x_kfs[1]['value'] == 100.0

    def test_patches_previous_keyframe_timing(self) -> None:
        c = _clip()
        c.add_motion_point(0.0, 0.0, 0.0)
        c.add_motion_point(3.0, 50.0, 50.0)
        prev = c.parameters['translation0']['keyframes'][0]
        assert prev['endTime'] == seconds_to_ticks(3.0)
        assert prev['duration'] == seconds_to_ticks(3.0)

    def test_line_type_stored(self) -> None:
        c = _clip()
        c.add_motion_point(0.0, 0.0, 0.0, line_type='angle')
        assert c.parameters['translation0']['keyframes'][0]['lineType'] == 'angle'

    def test_returns_self(self) -> None:
        c = _clip()
        assert c.add_motion_point(0.0, 0.0, 0.0) is c


# ------------------------------------------------------------------
# apply_motion_path
# ------------------------------------------------------------------

class TestApplyMotionPath:
    def test_adds_motion_path_effect(self) -> None:
        c = _clip()
        c.apply_motion_path([(0.0, 0.0, 0.0), (5.0, 100.0, 100.0)])
        assert c.is_effect_applied('MotionPath')

    def test_does_not_duplicate_effect(self) -> None:
        c = _clip()
        c.apply_motion_path([(0.0, 0.0, 0.0), (5.0, 100.0, 100.0)])
        c.apply_motion_path([(0.0, 0.0, 0.0), (5.0, 200.0, 200.0)])
        count = sum(1 for e in c.effects if e.get('effectName') == 'MotionPath')
        assert count == 1

    def test_sets_position_keyframes(self) -> None:
        c = _clip()
        c.apply_motion_path([(0.0, 0.0, 0.0), (5.0, 50.0, 60.0)])
        assert c.parameters['translation0']['defaultValue'] == 50.0
        assert c.parameters['translation1']['defaultValue'] == 60.0

    def test_easing_stored_in_effect(self) -> None:
        c = _clip()
        c.apply_motion_path(
            [(0.0, 0.0, 0.0), (5.0, 10.0, 10.0)],
            easing='ease-in-out',
        )
        effect = next(e for e in c.effects if e['effectName'] == 'MotionPath')
        assert effect['parameters']['easing'] == 'ease-in-out'

    def test_auto_orient_stored(self) -> None:
        c = _clip()
        c.apply_motion_path(
            [(0.0, 0.0, 0.0), (5.0, 10.0, 10.0)],
            auto_orient=True,
        )
        effect = next(e for e in c.effects if e['effectName'] == 'MotionPath')
        assert effect['parameters']['autoOrient'] is True

    def test_line_type_applied_to_all_keyframes(self) -> None:
        c = _clip()
        c.apply_motion_path(
            [(0.0, 0.0, 0.0), (3.0, 10.0, 20.0), (6.0, 30.0, 40.0)],
            line_type='angle',
        )
        for kf in c.parameters['translation0']['keyframes']:
            assert kf['lineType'] == 'angle'

    def test_returns_self(self) -> None:
        c = _clip()
        assert c.apply_motion_path([(0.0, 0.0, 0.0)]) is c


# ------------------------------------------------------------------
# apply_to_all_animations
# ------------------------------------------------------------------

class TestApplyToAllAnimations:
    def test_calls_func_on_each_visual_animation(self) -> None:
        c = _clip()
        c.fade(fade_in_seconds=1.0, fade_out_seconds=1.0)
        visited: list[dict] = []
        c.apply_to_all_animations(lambda a: visited.append(a))
        assert len(visited) == len(c.visual_animations)

    def test_noop_when_no_animations(self) -> None:
        c = _clip()
        visited: list[dict] = []
        c.apply_to_all_animations(lambda a: visited.append(a))
        assert visited == []

    def test_returns_self(self) -> None:
        c = _clip()
        assert c.apply_to_all_animations(lambda a: None) is c
