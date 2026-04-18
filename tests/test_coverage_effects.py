"""Tests targeting uncovered lines in effects/source.py, effects/behaviors.py, effects/cursor.py."""
from __future__ import annotations

import pytest

from camtasia.effects.source import SourceEffect
from camtasia.effects.behaviors import BehaviorPhase, GenericBehaviorEffect
from camtasia.effects.cursor import CursorShadow, CursorPhysics, LeftClickScaling


def _param(value):
    return {'type': 'double', 'defaultValue': value, 'interp': 'linr'}


# ── source.py: mid_point setter with scalar float, XY tuple, and existing dict ──

class TestSourceEffectMidPoint:
    def test_mid_point_setter_scalar_creates_key(self):
        data = {'effectName': 'SourceEffect', 'parameters': {}}
        e = SourceEffect(data)
        e.mid_point = 0.4
        assert data['parameters']['MidPoint'] == 0.4

    def test_mid_point_setter_scalar_updates_dict(self):
        data = {'effectName': 'SourceEffect', 'parameters': {'MidPoint': _param(0.5)}}
        e = SourceEffect(data)
        e.mid_point = 0.8
        assert data['parameters']['MidPoint']['defaultValue'] == 0.8

    def test_mid_point_setter_tuple_creates_keys(self):
        data = {'effectName': 'SourceEffect', 'parameters': {}}
        e = SourceEffect(data)
        e.mid_point = (0.3, 0.7)
        assert data['parameters']['MidPointX'] == 0.3
        assert data['parameters']['MidPointY'] == 0.7

    def test_mid_point_setter_tuple_updates_dict(self):
        data = {'effectName': 'SourceEffect', 'parameters': {
            'MidPointX': _param(0.5), 'MidPointY': _param(0.5),
        }}
        e = SourceEffect(data)
        e.mid_point = (0.1, 0.9)
        assert data['parameters']['MidPointX']['defaultValue'] == 0.1
        assert data['parameters']['MidPointY']['defaultValue'] == 0.9

    def test_mid_point_default_when_no_keys(self):
        e = SourceEffect({'effectName': 'SourceEffect', 'parameters': {}})
        assert e.mid_point == (0.5, 0.5)

    def test_mid_point_scalar_removes_xy(self):
        """Setting scalar mid_point removes MidPointX/Y."""
        data = {'effectName': 'SourceEffect', 'parameters': {
            'MidPointX': 0.5, 'MidPointY': 0.5,
        }}
        e = SourceEffect(data)
        e.mid_point = 0.6
        assert 'MidPointX' not in data['parameters']
        assert 'MidPointY' not in data['parameters']

    def test_mid_point_tuple_removes_scalar(self):
        """Setting tuple mid_point removes MidPoint."""
        data = {'effectName': 'SourceEffect', 'parameters': {'MidPoint': 0.5}}
        e = SourceEffect(data)
        e.mid_point = (0.2, 0.8)
        assert 'MidPoint' not in data['parameters']


class TestSourceEffectColorSetters:
    def test_color0_setter(self):
        data = {'effectName': 'SourceEffect', 'parameters': {
            'Color0-red': _param(0), 'Color0-green': _param(0),
            'Color0-blue': _param(0), 'Color0-alpha': _param(1),
        }}
        e = SourceEffect(data)
        e.color0 = (0.5, 0.6, 0.7, 0.8)
        assert data['parameters']['Color0-red']['defaultValue'] == 0.5

    def test_color1_setter(self):
        data = {'effectName': 'SourceEffect', 'parameters': {
            'Color1-red': _param(0), 'Color1-green': _param(0),
            'Color1-blue': _param(0), 'Color1-alpha': _param(1),
        }}
        e = SourceEffect(data)
        e.color1 = (0.1, 0.2, 0.3, 0.4)
        assert data['parameters']['Color1-green']['defaultValue'] == 0.2

    def test_color2_setter(self):
        data = {'effectName': 'SourceEffect', 'parameters': {
            'Color2-red': _param(0), 'Color2-green': _param(0),
            'Color2-blue': _param(0), 'Color2-alpha': _param(1),
        }}
        e = SourceEffect(data)
        e.color2 = (0.9, 0.8, 0.7, 0.6)
        assert data['parameters']['Color2-blue']['defaultValue'] == 0.7

    def test_color3_setter(self):
        data = {'effectName': 'SourceEffect', 'parameters': {
            'Color3-red': _param(0), 'Color3-green': _param(0),
            'Color3-blue': _param(0), 'Color3-alpha': _param(1),
        }}
        e = SourceEffect(data)
        e.color3 = (0.2, 0.4, 0.6, 0.8)
        assert data['parameters']['Color3-alpha']['defaultValue'] == 0.8


class TestSourceEffectShaderColors:
    def test_set_shader_colors_2(self):
        data = {'effectName': 'SourceEffect', 'parameters': {
            'Color0-red': _param(0), 'Color0-green': _param(0),
            'Color0-blue': _param(0), 'Color0-alpha': _param(1),
            'Color1-red': _param(0), 'Color1-green': _param(0),
            'Color1-blue': _param(0), 'Color1-alpha': _param(1),
        }}
        e = SourceEffect(data)
        e.set_shader_colors((255, 0, 0), (0, 255, 0))
        assert data['parameters']['Color0-red']['defaultValue'] == 1.0
        assert data['parameters']['Color1-green']['defaultValue'] == 1.0

    def test_set_shader_colors_invalid_count(self):
        e = SourceEffect({'effectName': 'SourceEffect', 'parameters': {}})
        with pytest.raises(ValueError, match='2 or 4'):
            e.set_shader_colors((255, 0, 0), (0, 255, 0), (0, 0, 255))


# ── behaviors.py: GenericBehaviorEffect properties ──

def _behavior_data():
    return {
        '_type': 'GenericBehaviorEffect',
        'effectName': 'TextBehavior',
        'start': 0, 'duration': 100,
        'in': {'attributes': {'name': 'reveal', 'type': 1, 'characterOrder': 0,
                               'offsetBetweenCharacters': 10,
                               'suggestedDurationPerCharacter': 5,
                               'overlapProportion': '1/2',
                               'movement': 1, 'springDamping': 0.5,
                               'springStiffness': 100.0, 'bounceBounciness': 0.3},
               'parameters': {}},
        'center': {'attributes': {'name': 'none', 'type': 0}, 'parameters': {}},
        'out': {'attributes': {'name': 'none', 'type': 0}, 'parameters': {}},
        'metadata': {'presetName': 'Reveal'},
    }


class TestGenericBehaviorEffect:
    def test_category_empty(self):
        e = GenericBehaviorEffect(_behavior_data())
        assert e.category == ''

    def test_parameters_empty(self):
        e = GenericBehaviorEffect(_behavior_data())
        assert e.parameters == {}

    def test_get_parameter_raises(self):
        e = GenericBehaviorEffect(_behavior_data())
        with pytest.raises(NotImplementedError):
            e.get_parameter('foo')

    def test_set_parameter_raises(self):
        e = GenericBehaviorEffect(_behavior_data())
        with pytest.raises(NotImplementedError):
            e.set_parameter('foo', 1)

    def test_repr(self):
        e = GenericBehaviorEffect(_behavior_data())
        r = repr(e)
        assert 'TextBehavior' in r
        assert 'Reveal' in r


class TestBehaviorPhaseProperties:
    def test_character_order_setter(self):
        data = {'attributes': {'characterOrder': 0}, 'parameters': {}}
        p = BehaviorPhase(data)
        p.character_order = 2
        assert data['attributes']['characterOrder'] == 2

    def test_offset_between_characters_setter(self):
        data = {'attributes': {'offsetBetweenCharacters': 10}, 'parameters': {}}
        p = BehaviorPhase(data)
        p.offset_between_characters = 20
        assert data['attributes']['offsetBetweenCharacters'] == 20

    def test_suggested_duration_per_character_setter(self):
        data = {'attributes': {'suggestedDurationPerCharacter': 5}, 'parameters': {}}
        p = BehaviorPhase(data)
        p.suggested_duration_per_character = 15
        assert data['attributes']['suggestedDurationPerCharacter'] == 15

    def test_overlap_proportion_setter(self):
        data = {'attributes': {'overlapProportion': 0}, 'parameters': {}}
        p = BehaviorPhase(data)
        p.overlap_proportion = '1/3'
        assert data['attributes']['overlapProportion'] == '1/3'

    def test_movement_setter(self):
        data = {'attributes': {'movement': 0}, 'parameters': {}}
        p = BehaviorPhase(data)
        p.movement = 3
        assert data['attributes']['movement'] == 3

    def test_spring_stiffness_setter(self):
        data = {'attributes': {'springStiffness': 100.0}, 'parameters': {}}
        p = BehaviorPhase(data)
        p.spring_stiffness = 200.0
        assert data['attributes']['springStiffness'] == 200.0

    def test_bounce_bounciness_setter(self):
        data = {'attributes': {'bounceBounciness': 0.3}, 'parameters': {}}
        p = BehaviorPhase(data)
        p.bounce_bounciness = 0.8
        assert data['attributes']['bounceBounciness'] == 0.8

    def test_repr(self):
        data = {'attributes': {'name': 'reveal', 'type': 1}, 'parameters': {}}
        p = BehaviorPhase(data)
        assert 'reveal' in repr(p)


# ── cursor.py: CursorShadow.color setter, CursorPhysics.tilt setter ──

class TestCursorShadowColor:
    def test_color_setter(self):
        data = {
            'effectName': 'CursorShadow',
            'parameters': {
                'color-red': _param(0), 'color-green': _param(0),
                'color-blue': _param(0), 'color-alpha': _param(1),
                'enabled': _param(1), 'angle': _param(0),
                'offset': _param(5), 'blur': _param(10), 'opacity': _param(0.5),
            },
        }
        e = CursorShadow(data)
        e.color = (0.5, 0.3, 0.1, 0.9)
        assert data['parameters']['color-red']['defaultValue'] == 0.5


class TestCursorPhysicsTilt:
    def test_tilt_setter(self):
        data = {
            'effectName': 'CursorPhysics',
            'parameters': {
                'intensity': _param(0.5), 'tilt': _param(0.0),
            },
        }
        e = CursorPhysics(data)
        e.tilt = 0.7
        assert data['parameters']['tilt']['defaultValue'] == 0.7
