from __future__ import annotations

import json
from pathlib import Path

import pytest

from camtasia.effects import (
    BlendModeEffect,
    ColorAdjustment,
    EffectSchema,
    Emphasize,
    LutEffect,
    MediaMatte,
    Spotlight,
)
from camtasia.effects.base import Effect, effect_from_dict
from camtasia.effects.behaviors import BehaviorPhase, GenericBehaviorEffect
from camtasia.effects.cursor import CursorMotionBlur, CursorPhysics, CursorShadow, LeftClickScaling
from camtasia.effects.source import SourceEffect
from camtasia.effects.visual import BlurRegion, DropShadow, Mask, MotionBlur, RoundCorners
from camtasia.timing import seconds_to_ticks

# ------------------------------------------------------------------
# Helpers: realistic effect dicts based on the Camtasia format spec
# ------------------------------------------------------------------

def _param(value, type_: str = "double", interp: str = "linr") -> dict:
    return {"type": type_, "defaultValue": value, "interp": interp}


def _round_corners_dict(**overrides) -> dict:
    d = {
        "effectName": "RoundCorners",
        "bypassed": False,
        "category": "visual",
        "parameters": {
            "radius": _param(16.0),
            "top-left": _param(True, type_="bool"),
            "top-right": _param(True, type_="bool"),
            "bottom-left": _param(False, type_="bool"),
            "bottom-right": _param(False, type_="bool"),
        },
    }
    d.update(overrides)
    return d


def _drop_shadow_dict(**overrides) -> dict:
    d = {
        "effectName": "DropShadow",
        "bypassed": False,
        "category": "visual",
        "parameters": {
            "angle": _param(4.71),
            "offset": _param(15.0),
            "blur": _param(25.0),
            "opacity": _param(0.2),
            "color-red": _param(0.0),
            "color-green": _param(0.0),
            "color-blue": _param(0.0),
            "color-alpha": _param(1.0),
        },
    }
    d.update(overrides)
    return d


def _cursor_physics_dict(**overrides) -> dict:
    d = {
        "effectName": "CursorPhysics",
        "bypassed": False,
        "category": "cursor",
        "parameters": {
            "intensity": _param(1.5),
            "tilt": _param(2.5),
        },
    }
    d.update(overrides)
    return d


def _left_click_scaling_dict(**overrides) -> dict:
    d = {
        "effectName": "LeftClickScaling",
        "bypassed": False,
        "category": "cursor",
        "parameters": {
            "scale": _param(3.5),
            "speed": _param(7.5),
        },
    }
    d.update(overrides)
    return d


# ------------------------------------------------------------------
# effect_from_dict factory dispatch
# ------------------------------------------------------------------

@pytest.mark.parametrize(
    ("effect_name", "expected_class"),
    [
        ("RoundCorners", RoundCorners),
        ("DropShadow", DropShadow),
        ("CursorPhysics", CursorPhysics),
        ("LeftClickScaling", LeftClickScaling),
    ],
    ids=["RoundCorners", "DropShadow", "CursorPhysics", "LeftClickScaling"],
)
def test_effect_from_dict_dispatches_correct_type(effect_name: str, expected_class: type) -> None:
    data = {"effectName": effect_name, "parameters": {}}
    actual_effect = effect_from_dict(data)
    assert type(actual_effect) is expected_class


def test_effect_from_dict_unknown_falls_back_to_effect() -> None:
    data = {"effectName": "UnknownEffect", "parameters": {}}
    actual_effect = effect_from_dict(data)
    assert type(actual_effect) is Effect


# ------------------------------------------------------------------
# RoundCorners
# ------------------------------------------------------------------

def test_round_corners_radius() -> None:
    effect = RoundCorners(_round_corners_dict())
    assert effect.radius == 16.0


def test_round_corners_radius_setter_mutates_dict() -> None:
    data = _round_corners_dict()
    effect = RoundCorners(data)
    effect.radius = 32.0
    assert data["parameters"]["radius"]["defaultValue"] == 32.0


def test_round_corners_corner_flags() -> None:
    effect = RoundCorners(_round_corners_dict())
    assert effect.top_left is True
    assert effect.top_right is True
    assert effect.bottom_left is False
    assert effect.bottom_right is False


# ------------------------------------------------------------------
# DropShadow
# ------------------------------------------------------------------

def test_drop_shadow_properties() -> None:
    effect = DropShadow(_drop_shadow_dict())
    assert effect.angle == 4.71
    assert effect.offset == 15.0
    assert effect.blur == 25.0
    assert effect.opacity == 0.2


def test_drop_shadow_color() -> None:
    effect = DropShadow(_drop_shadow_dict())
    assert effect.color == (0.0, 0.0, 0.0, 1.0)


def test_drop_shadow_color_setter_mutates_dict() -> None:
    data = _drop_shadow_dict()
    effect = DropShadow(data)
    effect.color = (1.0, 0.5, 0.25, 0.8)
    assert data["parameters"]["color-red"]["defaultValue"] == 1.0
    assert data["parameters"]["color-green"]["defaultValue"] == 0.5
    assert data["parameters"]["color-blue"]["defaultValue"] == 0.25
    assert data["parameters"]["color-alpha"]["defaultValue"] == 0.8


# ------------------------------------------------------------------
# CursorPhysics
# ------------------------------------------------------------------

def test_cursor_physics_intensity() -> None:
    effect = CursorPhysics(_cursor_physics_dict())
    assert effect.intensity == 1.5


def test_cursor_physics_tilt() -> None:
    effect = CursorPhysics(_cursor_physics_dict())
    assert effect.tilt == 2.5


def test_cursor_physics_setter_mutates_dict() -> None:
    data = _cursor_physics_dict()
    effect = CursorPhysics(data)
    effect.intensity = 3.0
    effect.tilt = 5.0
    assert data["parameters"]["intensity"]["defaultValue"] == 3.0
    assert data["parameters"]["tilt"]["defaultValue"] == 5.0


# ------------------------------------------------------------------
# LeftClickScaling
# ------------------------------------------------------------------

def test_left_click_scaling_scale() -> None:
    effect = LeftClickScaling(_left_click_scaling_dict())
    assert effect.scale == 3.5


def test_left_click_scaling_speed() -> None:
    effect = LeftClickScaling(_left_click_scaling_dict())
    assert effect.speed == 7.5


def test_left_click_scaling_setter_mutates_dict() -> None:
    data = _left_click_scaling_dict()
    effect = LeftClickScaling(data)
    effect.scale = 2.0
    effect.speed = 4.0
    assert data["parameters"]["scale"]["defaultValue"] == 2.0
    assert data["parameters"]["speed"]["defaultValue"] == 4.0


# ------------------------------------------------------------------
# Effect base: bypassed read/write
# ------------------------------------------------------------------

def test_effect_bypassed_default_false() -> None:
    data = {"effectName": "SomeEffect", "parameters": {}}
    effect = Effect(data)
    assert effect.bypassed is False


def test_effect_bypassed_read() -> None:
    data = {"effectName": "SomeEffect", "bypassed": True, "parameters": {}}
    effect = Effect(data)
    assert effect.bypassed is True


def test_effect_bypassed_setter_mutates_dict() -> None:
    data = {"effectName": "SomeEffect", "bypassed": False, "parameters": {}}
    effect = Effect(data)
    effect.bypassed = True
    assert data["bypassed"] is True


# ------------------------------------------------------------------
# Effect base: name, category
# ------------------------------------------------------------------

def test_effect_name() -> None:
    effect = Effect({"effectName": "RoundCorners", "parameters": {}})
    assert effect.name == "RoundCorners"


def test_effect_category() -> None:
    effect = Effect({"effectName": "X", "category": "visual", "parameters": {}})
    assert effect.category == "visual"


def test_effect_category_default_empty() -> None:
    effect = Effect({"effectName": "X", "parameters": {}})
    assert effect.category == ""


# ------------------------------------------------------------------
# Dict mutation passthrough
# ------------------------------------------------------------------

def test_effect_set_parameter_mutates_underlying_dict() -> None:
    data = _round_corners_dict()
    effect = RoundCorners(data)
    effect.set_parameter("radius", 99.0)
    assert data["parameters"]["radius"]["defaultValue"] == 99.0


def test_effect_data_property_returns_underlying_dict() -> None:
    data = _cursor_physics_dict()
    effect = CursorPhysics(data)
    assert effect.data is data



class TestBehaviorEffectProperties:
    def test_behavior_name_category_parameters(self):
        data = {'effectName': 'TestBehavior', 'parameters': {}}
        b = GenericBehaviorEffect(data)
        assert b.name == 'TestBehavior'
        assert b.category == ''
        assert b.parameters == {}



class TestCursorEffectEnabled:
    def test_cursor_enabled_property(self):
        data = {'effectName': 'CursorShadow', 'parameters': {'enabled': 1}}
        c = CursorShadow(data)
        assert c.enabled == 1
        c.enabled = 0
        assert data['parameters']['enabled'] == 0



class TestSourceEffectProperties:
    def _make(self, **params):
        return SourceEffect({'effectName': 'TestSource', 'parameters': params})

    def test_color0_none_when_missing(self):
        assert self._make().color0 is None

    def test_color1_none_when_missing(self):
        assert self._make().color1 is None

    def test_mid_point_setter_dict(self):
        e = self._make(MidPoint={'defaultValue': 0.5})
        e.mid_point = 0.7
        assert e._data['parameters']['MidPoint']['defaultValue'] == 0.7

    def test_mid_point_setter_scalar(self):
        e = self._make(MidPoint=0.5)
        e.mid_point = 0.7
        assert e._data['parameters']['MidPoint'] == 0.7

    def test_speed_none_when_missing(self):
        assert self._make().speed is None

    def test_speed_setter(self):
        e = self._make(Speed=1.0)
        e.speed = 2.0
        assert e._data['parameters']['Speed'] == 2.0

    def test_source_file_type_none_when_missing(self):
        assert self._make().source_file_type is None



class TestVisualEffectSigma:
    def test_blur_sigma(self):
        data = {'effectName': 'blurRegion', 'parameters': {'sigma': 5.0}}
        b = BlurRegion(data)
        assert b.sigma == 5.0
        b.sigma = 10.0
        assert data['parameters']['sigma'] == 10.0



_S1 = seconds_to_ticks(1.0)
_S5 = seconds_to_ticks(5.0)




# ------------------------------------------------------------------
# SourceEffect: shader colors wrong count
# ------------------------------------------------------------------

class TestShaderColorsWrongCount:
    def test_raises(self):
        data = {'effectName': 'test', '_type': 'SourceEffect', 'parameters': {}}
        effect = SourceEffect(data)
        with pytest.raises(ValueError, match='Expected 2 or 4 colors'):
            effect.set_shader_colors((255, 0, 0), (0, 255, 0), (0, 0, 255))


# ------------------------------------------------------------------
# SourceEffect: mid_point setter
# ------------------------------------------------------------------

class TestSourceEffectMidPoint:
    def test_mid_point_getter_radial(self):
        e = SourceEffect({'effectName': 'SourceEffect', 'parameters': {'MidPoint': _param(0.75)}})
        assert e.mid_point == 0.75

    def test_mid_point_getter_four_corner(self):
        e = SourceEffect({'effectName': 'SourceEffect', 'parameters': {
            'MidPointX': _param(0.3), 'MidPointY': _param(0.7),
        }})
        assert e.mid_point == (0.3, 0.7)

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
        data = {'effectName': 'SourceEffect', 'parameters': {
            'MidPointX': 0.5, 'MidPointY': 0.5,
        }}
        e = SourceEffect(data)
        e.mid_point = 0.6
        assert 'MidPointX' not in data['parameters']
        assert 'MidPointY' not in data['parameters']

    def test_mid_point_tuple_removes_scalar(self):
        data = {'effectName': 'SourceEffect', 'parameters': {'MidPoint': 0.5}}
        e = SourceEffect(data)
        e.mid_point = (0.2, 0.8)
        assert 'MidPoint' not in data['parameters']


# ------------------------------------------------------------------
# SourceEffect: color setters
# ------------------------------------------------------------------

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


# ------------------------------------------------------------------
# GenericBehaviorEffect: full property coverage
# ------------------------------------------------------------------

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


# ------------------------------------------------------------------
# CursorShadow: color setter
# ------------------------------------------------------------------

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


# ------------------------------------------------------------------
# CursorPhysics: tilt setter
# ------------------------------------------------------------------

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



def test_round_corners_properties():
    data = {
        'effectName': 'RoundCorners',
        'parameters': {
            'radius': 10.0,
            'top-left': 1.0,
            'top-right': 0.0,
            'bottom-left': 1.0,
            'bottom-right': 0.0,
        },
    }
    rc = RoundCorners(data)
    assert rc.top_left is True
    assert rc.top_right is False
    assert rc.bottom_left is True
    assert rc.bottom_right is False
    rc.top_left = False
    rc.top_right = True
    rc.bottom_left = False
    rc.bottom_right = True
    assert rc.top_right is True
    assert rc.bottom_right is True


def test_drop_shadow_flat_scalar_properties():
    data = {
        'effectName': 'DropShadow',
        'parameters': {
            'angle': 0.5,
            'enabled': 1,
            'offset': 5.0,
            'blur': 3.0,
            'opacity': 0.8,
            'color-red': 0.0,
            'color-green': 0.0,
            'color-blue': 0.0,
            'color-alpha': 1.0,
        },
    }
    ds = DropShadow(data)
    assert ds.angle == 0.5
    assert ds.offset == 5.0
    assert ds.blur == 3.0
    assert ds.opacity == 0.8
    ds.angle = 1.0
    ds.offset = 10.0
    ds.blur = 5.0
    ds.opacity = 0.5
    assert ds.angle == 1.0
    assert ds.offset == 10.0
    assert ds.blur == 5.0
    assert ds.opacity == 0.5


def test_mask_properties():
    data = {
        'effectName': 'Mask',
        'parameters': {
            'mask-shape': 1,
            'mask-opacity': 0.9,
            'mask-blend': 0.5,
            'mask-invert': 0,
            'mask-rotation': 1.57,
            'mask-width': 100.0,
            'mask-height': 200.0,
            'mask-positionX': 0.5,
            'mask-positionY': 0.5,
            'mask-cornerRadius': 10.0,
        },
    }
    m = Mask(data)
    assert m.mask_opacity == pytest.approx(0.9)
    assert m.mask_blend == pytest.approx(0.5)
    assert m.mask_invert == 0
    assert m.mask_rotation == pytest.approx(1.57)
    assert m.mask_width == pytest.approx(100.0)
    assert m.mask_height == pytest.approx(200.0)
    assert m.mask_position_x == pytest.approx(0.5)
    assert m.mask_position_y == pytest.approx(0.5)
    assert m.mask_corner_radius == pytest.approx(10.0)
    m.mask_opacity = 0.5
    m.mask_blend = 0.3
    m.mask_invert = 1
    m.mask_rotation = 3.14
    m.mask_width = 50.0
    m.mask_height = 50.0
    m.mask_position_x = 0.2
    m.mask_position_y = 0.8
    m.mask_corner_radius = 5.0
    assert m.mask_opacity == pytest.approx(0.5)


def test_blur_region_properties():
    data = {
        'effectName': 'BlurRegion',
        'parameters': {
            'sigma': 5.0,
            'mask-cornerRadius': 8.0,
            'mask-invert': 0,
            'color-alpha': 0.5,
        },
    }
    br = BlurRegion(data)
    assert br.sigma == 5.0
    assert br.mask_corner_radius == 8.0
    assert br.mask_invert == 0
    assert br.color_alpha == 0.5
    br.sigma = 10.0
    br.mask_corner_radius = 12.0
    br.mask_invert = 1
    br.color_alpha = 1.0
    assert br.sigma == 10.0


def test_cursor_shadow_properties_phase4():
    data = {
        'effectName': 'CursorShadow',
        'parameters': {
            'enabled': 1,
            'angle': 0.5,
            'offset': 3.0,
            'blur': 2.0,
            'opacity': 0.7,
            'color-red': 0.0,
            'color-green': 0.0,
            'color-blue': 0.0,
            'color-alpha': 1.0,
        },
    }
    cs = CursorShadow(data)
    assert cs.enabled == 1
    assert cs.angle == 0.5
    assert cs.offset == 3.0
    assert cs.blur == 2.0
    assert cs.opacity == 0.7
    assert cs.color == (0.0, 0.0, 0.0, 1.0)
    cs.enabled = 0
    cs.angle = 1.0
    cs.offset = 5.0
    cs.blur = 4.0
    cs.opacity = 0.5
    cs.color = (1.0, 0.0, 0.0, 0.5)
    assert cs.enabled == 0


def test_cursor_motion_blur_phase4():
    data = {'effectName': 'CursorMotionBlur', 'parameters': {'intensity': 0.5}}
    cmb = CursorMotionBlur(data)
    assert cmb.intensity == 0.5
    cmb.intensity = 1.0
    assert cmb.intensity == 1.0


def test_effect_schema_raises():
    with pytest.raises(RuntimeError, match='marshmallow'):
        EffectSchema()


def test_behavior_phase_data_phase4():
    phase_data = {'attributes': {'name': 'test'}}
    bp = BehaviorPhase(phase_data)
    assert bp.data is phase_data


def test_generic_behavior_start_duration_setters_phase4():
    data = {
        'effectName': 'TestBehavior',
        'parameters': {},
        'in': {'attributes': {}},
        'center': {'attributes': {}},
        'out': {'attributes': {}},
    }
    gbe = GenericBehaviorEffect(data)
    gbe.start = 100
    assert gbe.start == 100
    gbe.duration = 200
    assert gbe.duration == 200


def test_effect_edge_mods():
    data = {
        'effectName': 'Test',
        'parameters': {},
        'start': 100,
        'duration': 500,
        'leftEdgeMods': [{'type': 'fadeIn'}],
        'rightEdgeMods': [{'type': 'fadeOut'}],
    }
    e = Effect(data)
    assert e.left_edge_mods == [{'type': 'fadeIn'}]
    assert e.right_edge_mods == [{'type': 'fadeOut'}]
    assert e.start == 100
    assert e.duration == 500



class TestCursorMotionBlurSetter:
    def test_set_intensity(self):
        data = {"effectName": "CursorMotionBlur", "parameters": {"intensity": {"type": "double", "defaultValue": 0.5}}}
        e = CursorMotionBlur(data)
        e.intensity = 0.8
        assert e.intensity == 0.8


class TestCursorShadowSetters:
    def _make(self):
        data = {
            "effectName": "CursorShadow",
            "parameters": {
                "enabled": {"type": "int", "defaultValue": 1},
                "angle": {"type": "double", "defaultValue": 0.5},
                "offset": {"type": "double", "defaultValue": 3.0},
                "blur": {"type": "double", "defaultValue": 2.0},
                "opacity": {"type": "double", "defaultValue": 0.7},
                "color-red": {"type": "double", "defaultValue": 0.0},
                "color-green": {"type": "double", "defaultValue": 0.0},
                "color-blue": {"type": "double", "defaultValue": 0.0},
                "color-alpha": {"type": "double", "defaultValue": 1.0},
            },
        }
        return CursorShadow(data)

    @pytest.mark.parametrize(("attr", "new_value"), [
        ("enabled", 0),
        ("angle", 1.5),
        ("offset", 5.0),
        ("blur", 4.0),
        ("opacity", 0.3),
    ])
    def test_scalar_setter(self, attr, new_value):
        e = self._make()
        setattr(e, attr, new_value)
        assert getattr(e, attr) == new_value

    def test_set_color(self):
        e = self._make()
        e.color = (1.0, 0.5, 0.25, 0.8)
        assert e.color == (1.0, 0.5, 0.25, 0.8)


class TestCursorPhysicsSetters:
    def _make(self):
        return CursorPhysics({
            "effectName": "CursorPhysics",
            "parameters": {
                "intensity": {"type": "double", "defaultValue": 0.5},
                "tilt": {"type": "double", "defaultValue": 0.3},
            },
        })

    @pytest.mark.parametrize(("attr", "new_value"), [
        ("intensity", 0.9),
        ("tilt", 0.7),
    ])
    def test_setter(self, attr, new_value):
        e = self._make()
        setattr(e, attr, new_value)
        assert getattr(e, attr) == new_value


class TestLeftClickScalingSetters:
    def _make(self):
        return LeftClickScaling({
            "effectName": "LeftClickScaling",
            "parameters": {
                "scale": {"type": "double", "defaultValue": 1.5},
                "speed": {"type": "double", "defaultValue": 1.0},
            },
        })

    @pytest.mark.parametrize(("attr", "new_value"), [
        ("scale", 2.0),
        ("speed", 0.5),
    ])
    def test_setter(self, attr, new_value):
        e = self._make()
        setattr(e, attr, new_value)
        assert getattr(e, attr) == new_value


FIXTURES = Path(__file__).parent / "fixtures"


# ------------------------------------------------------------------
# Helpers (from test_new_features)
# ------------------------------------------------------------------

def _nf_param(value, type_: str = "double", interp: str = "linr") -> dict:
    """Build a standard Camtasia parameter dict."""
    return {"type": type_, "defaultValue": value, "interp": interp}


def _keyframed_param(default: float, keyframes: list[dict]) -> dict:
    """Build a keyframed parameter dict."""
    return {
        "type": "double",
        "defaultValue": default,
        "keyframes": keyframes,
    }


# ------------------------------------------------------------------
# MotionBlur
# ------------------------------------------------------------------

MOTION_BLUR_DICT = {
    "effectName": "MotionBlur",
    "bypassed": False,
    "category": "categoryVisualEffects",
    "parameters": {
        "intensity": _nf_param(0.75),
    },
}


class TestMotionBlur:
    def test_intensity_read(self):
        actual_effect = MotionBlur(MOTION_BLUR_DICT)
        assert actual_effect.intensity == 0.75

    def test_intensity_write(self):
        data = json.loads(json.dumps(MOTION_BLUR_DICT))
        actual_effect = MotionBlur(data)
        actual_effect.intensity = 1.5
        assert actual_effect.intensity == 1.5
        assert data["parameters"]["intensity"]["defaultValue"] == 1.5

    def test_name_and_category(self):
        actual_effect = MotionBlur(MOTION_BLUR_DICT)
        assert actual_effect.name == "MotionBlur"
        assert actual_effect.category == "categoryVisualEffects"

    def test_effect_from_dict_dispatches_motion_blur(self):
        actual_effect = effect_from_dict(MOTION_BLUR_DICT)
        assert isinstance(actual_effect, MotionBlur)
        assert actual_effect.intensity == 0.75


# ------------------------------------------------------------------
# Mask
# ------------------------------------------------------------------

MASK_KEYFRAMES = [
    {"endTime": 705600000, "time": 0, "value": 346.97, "duration": 705600000},
    {"endTime": 9760800000, "time": 9055200000, "value": 346.97, "duration": 705600000},
]

MASK_DICT = {
    "effectName": "Mask",
    "bypassed": False,
    "category": "categoryVisualEffects",
    "parameters": {
        "mask-shape": _nf_param(0, type_="int"),
        "mask-opacity": _nf_param(0.0),
        "mask-blend": _nf_param(-0.02),
        "mask-invert": _nf_param(0, type_="int"),
        "mask-rotation": _nf_param(0.0),
        "mask-width": _keyframed_param(346.97, MASK_KEYFRAMES),
        "mask-height": _keyframed_param(347.68, MASK_KEYFRAMES),
        "mask-positionX": _keyframed_param(9.07, MASK_KEYFRAMES),
        "mask-positionY": _keyframed_param(1.96, MASK_KEYFRAMES),
    },
}


class TestMaskEffect:
    def test_all_scalar_parameters(self):
        actual_effect = Mask(MASK_DICT)
        assert actual_effect.mask_shape == 0
        assert actual_effect.mask_opacity == 0.0
        assert actual_effect.mask_blend == -0.02
        assert actual_effect.mask_invert == 0
        assert actual_effect.mask_rotation == 0.0

    def test_keyframed_width_returns_default_value(self):
        actual_effect = Mask(MASK_DICT)
        assert actual_effect.mask_width == 346.97

    def test_keyframed_height_returns_default_value(self):
        actual_effect = Mask(MASK_DICT)
        assert actual_effect.mask_height == 347.68

    def test_keyframed_position(self):
        actual_effect = Mask(MASK_DICT)
        assert actual_effect.mask_position_x == 9.07
        assert actual_effect.mask_position_y == 1.96

    def test_mask_shape_write(self):
        data = json.loads(json.dumps(MASK_DICT))
        actual_effect = Mask(data)
        actual_effect.mask_shape = 2
        assert actual_effect.mask_shape == 2

    def test_effect_from_dict_dispatches_mask(self):
        actual_effect = effect_from_dict(MASK_DICT)
        assert isinstance(actual_effect, Mask)
        assert actual_effect.mask_blend == -0.02


# ------------------------------------------------------------------
# BlurRegion
# ------------------------------------------------------------------

BLUR_REGION_DICT = {
    "effectName": "BlurRegion",
    "bypassed": False,
    "category": "",
    "parameters": {
        "sigma": _nf_param(10.0),
        "mask-cornerRadius": _nf_param(5.0),
        "mask-invert": _nf_param(0, type_="int"),
        "color-alpha": _nf_param(0.8),
    },
    "metadata": {"presetName": "Blur Region"},
}


class TestEffectFromDictDispatchNewFeatures:
    @pytest.mark.parametrize(
        ("effect_dict", "expected_type"),
        [
            (MOTION_BLUR_DICT, MotionBlur),
            (MASK_DICT, Mask),
        ],
        ids=["MotionBlur", "Mask"],
    )
    def test_dispatches_to_correct_class(self, effect_dict, expected_type):
        actual_effect = effect_from_dict(effect_dict)
        assert type(actual_effect) is expected_type

    def test_unknown_effect_returns_base(self):
        actual_effect = effect_from_dict({"effectName": "UnknownEffect", "parameters": {}})
        assert type(actual_effect) is Effect


# ------------------------------------------------------------------
# GenericBehaviorEffect (from test_new_features)
# ------------------------------------------------------------------

BEHAVIOR_DICT = {
    "_type": "GenericBehaviorEffect",
    "effectName": "reveal",
    "bypassed": False,
    "start": 1411200000,
    "duration": 12277440000,
    "in": {
        "attributes": {
            "name": "reveal",
            "type": 0,
            "characterOrder": 7,
            "offsetBetweenCharacters": 35280000,
            "suggestedDurationPerCharacter": 517440000,
            "overlapProportion": 0,
            "movement": 16,
            "springDamping": 5.0,
            "springStiffness": 50.0,
            "bounceBounciness": 0.45,
        },
        "parameters": {
            "direction": {
                "type": "int",
                "valueBounds": {"minValue": 0, "maxValue": 20, "defaultValue": 0},
                "keyframes": [
                    {"endTime": 0, "time": 0, "value": 0, "duration": 0}
                ],
            }
        },
    },
    "center": {
        "attributes": {
            "name": "none",
            "type": 1,
            "characterOrder": 6,
            "secondsPerLoop": 1,
            "numberOfLoops": -1,
        },
        "parameters": {},
    },
    "out": {
        "attributes": {
            "name": "reveal",
            "type": 0,
            "characterOrder": 7,
            "offsetBetweenCharacters": 35280000,
            "suggestedDurationPerCharacter": 517440000,
            "overlapProportion": "1/2",
            "movement": 6,
            "springDamping": 5.0,
            "springStiffness": 50.0,
            "bounceBounciness": 0.45,
        },
        "parameters": {},
    },
    "metadata": {"presetName": "Reveal"},
}


class TestGenericBehaviorEffectNewFeatures:
    def test_create_from_dict(self):
        actual_effect = GenericBehaviorEffect(BEHAVIOR_DICT)
        assert actual_effect.effect_name == "reveal"
        assert actual_effect.bypassed is False
        assert actual_effect.start == 1411200000
        assert actual_effect.duration == 12277440000
        assert actual_effect.preset_name == "Reveal"

    def test_entrance_phase(self):
        actual_phase = GenericBehaviorEffect(BEHAVIOR_DICT).entrance
        assert actual_phase.name == "reveal"
        assert actual_phase.phase_type == 0
        assert actual_phase.character_order == 7
        assert actual_phase.offset_between_characters == 35280000
        assert actual_phase.suggested_duration_per_character == 517440000
        assert actual_phase.movement == 16
        assert actual_phase.spring_damping == 5.0
        assert actual_phase.spring_stiffness == 50.0
        assert actual_phase.bounce_bounciness == 0.45

    def test_center_phase(self):
        actual_phase = GenericBehaviorEffect(BEHAVIOR_DICT).center
        assert actual_phase.name == "none"
        assert actual_phase.phase_type == 1
        assert actual_phase.character_order == 6

    def test_exit_phase(self):
        actual_phase = GenericBehaviorEffect(BEHAVIOR_DICT).exit
        assert actual_phase.name == "reveal"
        assert actual_phase.phase_type == 0
        assert actual_phase.movement == 6

    def test_overlap_proportion_string_fraction(self):
        actual_phase = GenericBehaviorEffect(BEHAVIOR_DICT).exit
        assert actual_phase.overlap_proportion == "1/2"

    def test_overlap_proportion_integer(self):
        actual_phase = GenericBehaviorEffect(BEHAVIOR_DICT).entrance
        assert actual_phase.overlap_proportion == 0

    def test_entrance_parameters_contain_direction(self):
        actual_params = GenericBehaviorEffect(BEHAVIOR_DICT).entrance.parameters
        assert "direction" in actual_params
        assert actual_params["direction"]["type"] == "int"

    def test_bypassed_write(self):
        data = json.loads(json.dumps(BEHAVIOR_DICT))
        actual_effect = GenericBehaviorEffect(data)
        actual_effect.bypassed = True
        assert actual_effect.bypassed is True
        assert data["bypassed"] is True

    def test_preset_name_missing_metadata(self):
        data = json.loads(json.dumps(BEHAVIOR_DICT))
        del data["metadata"]
        actual_effect = GenericBehaviorEffect(data)
        assert actual_effect.preset_name == ""

    def test_repr(self):
        actual_repr = repr(GenericBehaviorEffect(BEHAVIOR_DICT))
        assert actual_repr == "GenericBehaviorEffect(name='reveal', preset='Reveal')"


class TestBehaviorPhaseNewFeatures:
    def test_repr(self):
        actual_phase = GenericBehaviorEffect(BEHAVIOR_DICT).entrance
        assert repr(actual_phase) == "BehaviorPhase(name='reveal', type=0)"

    def test_name_write(self):
        data = json.loads(json.dumps(BEHAVIOR_DICT))
        actual_phase = GenericBehaviorEffect(data).entrance
        actual_phase.name = "typewriter"
        assert actual_phase.name == "typewriter"
        assert data["in"]["attributes"]["name"] == "typewriter"

    def test_spring_damping_write(self):
        data = json.loads(json.dumps(BEHAVIOR_DICT))
        actual_phase = GenericBehaviorEffect(data).entrance
        actual_phase.spring_damping = 10.0
        assert actual_phase.spring_damping == 10.0

    def test_defaults_for_missing_optional_attrs(self):
        actual_phase = GenericBehaviorEffect(BEHAVIOR_DICT).center
        assert actual_phase.movement == 0
        assert actual_phase.spring_damping == 0.0
        assert actual_phase.spring_stiffness == 0.0
        assert actual_phase.bounce_bounciness == 0.0
        assert actual_phase.offset_between_characters == 0
        assert actual_phase.suggested_duration_per_character == 0


# ------------------------------------------------------------------
# Integration tests with test project B fixture (effect-related)
# ------------------------------------------------------------------

@pytest.fixture
def test_project_b_data():
    fixture_path = FIXTURES / "test_project_b.tscproj"
    if not fixture_path.exists():
        pytest.skip("test_project_b.tscproj fixture not available")
    with open(fixture_path) as f:
        return json.load(f)


def _collect_all(obj, predicate):
    """Recursively collect all dicts matching predicate."""
    results = []
    if isinstance(obj, dict):
        if predicate(obj):
            results.append(obj)
        for v in obj.values():
            results.extend(_collect_all(v, predicate))
    elif isinstance(obj, list):
        for v in obj:
            results.extend(_collect_all(v, predicate))
    return results


class TestProjectBEffectsIntegration:
    def test_generic_behavior_effects(self, test_project_b_data):
        actual_behaviors = _collect_all(
            test_project_b_data,
            lambda d: d.get("_type") == "GenericBehaviorEffect",
        )
        assert len(actual_behaviors) == 16
        actual_effect = GenericBehaviorEffect(actual_behaviors[0])
        assert actual_effect.effect_name == "reveal"
        assert actual_effect.preset_name == "Reveal"
        assert actual_effect.entrance.name == "reveal"
        assert actual_effect.center.name == "none"
        assert actual_effect.exit.name == "reveal"

    def test_mask_effects(self, test_project_b_data):
        actual_masks = _collect_all(
            test_project_b_data,
            lambda d: d.get("effectName") == "Mask",
        )
        assert len(actual_masks) == 1
        actual_params = actual_masks[0]["parameters"]
        assert "mask-shape" in actual_params

    def test_motion_blur_effects(self, test_project_b_data):
        actual_effects = _collect_all(
            test_project_b_data,
            lambda d: d.get("effectName") == "MotionBlur",
        )
        assert len(actual_effects) == 8
        actual_first = actual_effects[0]
        assert actual_first["category"] == "categoryVisualEffects"


# ------------------------------------------------------------------
# EffectMetadata (from test_new_effect_types)
# ------------------------------------------------------------------

class TestEffectMetadataProperty:
    def test_effect_metadata_property(self):
        e = Effect({"effectName": "X", "parameters": {}, "metadata": {"presetName": "foo"}})
        assert e.metadata == {"presetName": "foo"}

    def test_effect_without_metadata(self):
        e2 = Effect({"effectName": "Y", "parameters": {}})
        assert e2.metadata == {}


# ── SourceEffect.set_shader_colors (variable color counts) ─────────


def _radial_effect():
    """SourceEffect with only 2 colors (radial gradient)."""
    return {
        "effectName": "SourceEffect",
        "parameters": {
            "Color0-red": 0.0, "Color0-green": 0.0,
            "Color0-blue": 0.0, "Color0-alpha": 1.0,
            "Color1-red": 1.0, "Color1-green": 1.0,
            "Color1-blue": 1.0, "Color1-alpha": 1.0,
            "MidPoint": 0.5,
            "Speed": 5.0,
            "sourceFileType": "tscshadervid",
        },
    }


def _four_corner_effect():
    """SourceEffect with 4 colors (four-corner gradient)."""
    return {
        "effectName": "SourceEffect",
        "parameters": {
            "Color0-red": 0.0, "Color0-green": 0.0,
            "Color0-blue": 0.0, "Color0-alpha": 1.0,
            "Color1-red": 1.0, "Color1-green": 0.0,
            "Color1-blue": 0.0, "Color1-alpha": 1.0,
            "Color2-red": 0.0, "Color2-green": 1.0,
            "Color2-blue": 0.0, "Color2-alpha": 1.0,
            "Color3-red": 0.0, "Color3-green": 0.0,
            "Color3-blue": 1.0, "Color3-alpha": 1.0,
            "MidPointX": 0.5, "MidPointY": 0.5,
            "Speed": 5.0,
            "sourceFileType": "tscshadervid",
        },
    }


def test_set_shader_colors_two_colors():
    effect = SourceEffect(_radial_effect())
    effect.set_shader_colors((255, 0, 0), (0, 255, 0))
    assert effect.color0 == (1.0, 0.0, 0.0, 1.0)
    assert effect.color1 == (0.0, 1.0, 0.0, 1.0)


def test_set_shader_colors_four_colors():
    effect = SourceEffect(_four_corner_effect())
    effect.set_shader_colors((255, 0, 0), (0, 255, 0), (0, 0, 255), (128, 128, 128))
    assert effect.color0 == (1.0, 0.0, 0.0, 1.0)
    assert effect.color1 == (0.0, 1.0, 0.0, 1.0)
    assert effect.color2 == (0.0, 0.0, 1.0, 1.0)
    r, _g, _b, a = effect.color3
    assert abs(r - 128 / 255) < 1e-9
    assert a == 1.0



# ---------------------------------------------------------------------------
# Typed effect wrappers: ColorAdjustment, LutEffect, BlendModeEffect,
# Emphasize, Spotlight, MediaMatte
# ---------------------------------------------------------------------------


def _make_effect_dict(name: str, params: dict) -> dict:
    return {
        "effectName": name,
        "bypassed": False,
        "category": "visual",
        "parameters": {k: _param(v) for k, v in params.items()},
    }


def test_color_adjustment_read_write():
    data = _make_effect_dict("ColorAdjustment",
                             {"brightness": 1.2, "contrast": 1.5, "saturation": 0.3})
    eff = ColorAdjustment(data)
    assert eff.brightness == 1.2
    assert eff.contrast == 1.5
    assert eff.saturation == 0.3
    eff.brightness = 0.8
    assert data["parameters"]["brightness"]["defaultValue"] == 0.8


def test_lut_effect_read_write():
    data = _make_effect_dict("LutEffect", {"lutSource": "Tasteful.cube", "lut_intensity": 0.7})
    eff = LutEffect(data)
    assert eff.lut_source == "Tasteful.cube"
    assert eff.intensity == 0.7
    eff.intensity = 1.0
    assert data["parameters"]["lut_intensity"]["defaultValue"] == 1.0


def test_blend_mode_effect_read_write():
    data = _make_effect_dict("BlendModeEffect", {"mode": 16, "intensity": 1.0, "invert": 0})
    eff = BlendModeEffect(data)
    assert eff.mode == 16
    assert eff.intensity == 1.0
    assert eff.invert == 0
    eff.mode = 5
    assert data["parameters"]["mode"]["defaultValue"] == 5


def test_emphasize_read_write():
    data = _make_effect_dict("Emphasize", {
        "emphasizeAmount": 0.8, "emphasizeRampPosition": 0,
        "emphasizeRampInTime": 705600000, "emphasizeRampOutTime": 705600000,
    })
    eff = Emphasize(data)
    assert eff.amount == 0.8
    assert eff.ramp_in_ticks == 705600000
    eff.amount = 0.5
    assert data["parameters"]["emphasizeAmount"]["defaultValue"] == 0.5


def test_spotlight_position_read_write():
    data = _make_effect_dict("Spotlight", {
        "brightness": 1.2, "concentration": 0.5, "opacity": 0.8,
        "positionX": 0.25, "positionY": 0.5,
    })
    eff = Spotlight(data)
    assert eff.brightness == 1.2
    assert eff.opacity == 0.8
    assert eff.position == (0.25, 0.5)
    eff.position = (0.5, 0.75)
    assert data["parameters"]["positionX"]["defaultValue"] == 0.5
    assert data["parameters"]["positionY"]["defaultValue"] == 0.75


def test_media_matte_read_write():
    data = _make_effect_dict("MediaMatte", {"intensity": 1.0, "matteMode": 3, "trackDepth": 10002})
    eff = MediaMatte(data)
    assert eff.intensity == 1.0
    assert eff.mode == 3
    assert eff.track_depth == 10002
    eff.mode = 2
    assert data["parameters"]["matteMode"]["defaultValue"] == 2


def test_effect_from_dict_dispatches_to_new_classes():
    """effect_from_dict should return the typed subclass for each new effect name."""
    from camtasia.effects import effect_from_dict
    assert isinstance(effect_from_dict(_make_effect_dict("ColorAdjustment", {"brightness": 1.0})), ColorAdjustment)
    assert isinstance(effect_from_dict(_make_effect_dict("LutEffect", {"lutSource": "x.cube"})), LutEffect)
    assert isinstance(effect_from_dict(_make_effect_dict("BlendModeEffect", {"mode": 0})), BlendModeEffect)
    assert isinstance(effect_from_dict(_make_effect_dict("Emphasize", {"emphasizeAmount": 1.0})), Emphasize)
    assert isinstance(effect_from_dict(_make_effect_dict("Spotlight", {"brightness": 1.0})), Spotlight)
    assert isinstance(effect_from_dict(_make_effect_dict("MediaMatte", {"intensity": 1.0})), MediaMatte)


def test_color_adjustment_setters():
    data = _make_effect_dict("ColorAdjustment", {"brightness": 1.0, "contrast": 1.0, "saturation": 0.0})
    eff = ColorAdjustment(data)
    eff.contrast = 2.0
    eff.saturation = -0.5
    assert data["parameters"]["contrast"]["defaultValue"] == 2.0
    assert data["parameters"]["saturation"]["defaultValue"] == -0.5


def test_lut_effect_source_setter():
    data = _make_effect_dict("LutEffect", {"lutSource": "a.cube", "lut_intensity": 1.0})
    eff = LutEffect(data)
    eff.lut_source = "b.cube"
    assert data["parameters"]["lutSource"]["defaultValue"] == "b.cube"


def test_blend_mode_setters():
    data = _make_effect_dict("BlendModeEffect", {"mode": 0, "intensity": 1.0, "invert": 0})
    eff = BlendModeEffect(data)
    eff.intensity = 0.5
    eff.invert = 1
    assert data["parameters"]["intensity"]["defaultValue"] == 0.5
    assert data["parameters"]["invert"]["defaultValue"] == 1


def test_emphasize_setters():
    data = _make_effect_dict("Emphasize", {
        "emphasizeAmount": 0.5, "emphasizeRampPosition": 0,
        "emphasizeRampInTime": 0, "emphasizeRampOutTime": 0,
    })
    eff = Emphasize(data)
    # Read getters first for coverage
    assert eff.ramp_position == 0.0
    assert eff.ramp_out_ticks == 0
    eff.ramp_position = 0.25
    eff.ramp_in_ticks = 1000
    eff.ramp_out_ticks = 2000
    assert data["parameters"]["emphasizeRampPosition"]["defaultValue"] == 0.25
    assert data["parameters"]["emphasizeRampInTime"]["defaultValue"] == 1000
    assert data["parameters"]["emphasizeRampOutTime"]["defaultValue"] == 2000


def test_spotlight_setters():
    data = _make_effect_dict("Spotlight", {
        "brightness": 1.0, "concentration": 0.5, "opacity": 1.0,
        "positionX": 0.5, "positionY": 0.5,
    })
    eff = Spotlight(data)
    assert eff.concentration == 0.5
    eff.brightness = 2.0
    eff.concentration = 0.25
    eff.opacity = 0.75
    assert data["parameters"]["brightness"]["defaultValue"] == 2.0
    assert data["parameters"]["concentration"]["defaultValue"] == 0.25
    assert data["parameters"]["opacity"]["defaultValue"] == 0.75


def test_media_matte_setters():
    data = _make_effect_dict("MediaMatte", {"intensity": 1.0, "matteMode": 3, "trackDepth": 10002})
    eff = MediaMatte(data)
    eff.intensity = 0.5
    eff.track_depth = 20000
    assert data["parameters"]["intensity"]["defaultValue"] == 0.5
    assert data["parameters"]["trackDepth"]["defaultValue"] == 20000
