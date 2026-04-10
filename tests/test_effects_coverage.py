"""Tests targeting uncovered lines in effects modules and callouts."""
from __future__ import annotations

import pytest

from camtasia.effects.base import Effect, effect_from_dict
from camtasia.effects.behaviors import BehaviorPhase, GenericBehaviorEffect
from camtasia.effects.cursor import CursorMotionBlur, CursorShadow
from camtasia.effects.source import SourceEffect
from camtasia.effects.visual import BlurRegion, DropShadow, Glow, Mask, MotionBlur, RoundCorners
from camtasia.annotations.callouts import text, square
from camtasia.annotations.types import Color, FillStyle, HorizontalAlignment, StrokeStyle, VerticalAlignment


def _param(value, type_="double", interp="linr"):
    return {"type": type_, "defaultValue": value, "interp": interp}


# ------------------------------------------------------------------
# effects/__init__.py — line 37: EffectSchema stub raises ImportError
# ------------------------------------------------------------------

def test_effect_schema_is_real_when_marshmallow_installed():
    from camtasia.effects import EffectSchema
    schema = EffectSchema()
    assert hasattr(schema, "type_schemas")


# ------------------------------------------------------------------
# base.py — line 78: set_parameter on scalar (non-dict) param
# ------------------------------------------------------------------

def test_set_parameter_scalar_value():
    data = {"effectName": "X", "parameters": {"enabled": 1}}
    effect = Effect(data)
    effect.set_parameter("enabled", 0)
    assert data["parameters"]["enabled"] == 0


# ------------------------------------------------------------------
# base.py — lines 87, 92: start/duration properties returning None
# ------------------------------------------------------------------

def test_effect_start_returns_none_when_absent():
    effect = Effect({"effectName": "X", "parameters": {}})
    assert effect.start is None


def test_effect_duration_returns_none_when_absent():
    effect = Effect({"effectName": "X", "parameters": {}})
    assert effect.duration is None


# ------------------------------------------------------------------
# base.py — line 110: __repr__
# ------------------------------------------------------------------

def test_effect_repr():
    effect = Effect({"effectName": "Glow", "parameters": {}})
    assert repr(effect) == "Effect(name='Glow')"


def test_effect_subclass_repr():
    data = {"effectName": "Glow", "parameters": {"radius": _param(1.0), "intensity": _param(0.5)}}
    effect = Glow(data)
    assert repr(effect) == "Glow(name='Glow')"


# ------------------------------------------------------------------
# behaviors.py — BehaviorPhase property getters/setters
# ------------------------------------------------------------------

PHASE_DATA = {
    "attributes": {
        "name": "reveal",
        "type": 0,
        "characterOrder": 1,
        "offsetBetweenCharacters": 10,
        "suggestedDurationPerCharacter": 20,
        "overlapProportion": "1/2",
        "movement": 3,
        "springDamping": 0.5,
        "springStiffness": 1.2,
        "bounceBounciness": 0.8,
    },
    "parameters": {"direction": _param(1)},
}


def _make_phase(**overrides):
    import copy
    d = copy.deepcopy(PHASE_DATA)
    d["attributes"].update(overrides)
    return d


def test_behavior_phase_name_setter():
    """Line 49: name setter."""
    phase = BehaviorPhase(_make_phase())
    phase.name = "fade"
    assert phase.name == "fade"


def test_behavior_phase_character_order_setter():
    """Line 58: character_order setter."""
    phase = BehaviorPhase(_make_phase())
    phase.character_order = 5
    assert phase.character_order == 5


def test_behavior_phase_offset_between_characters():
    """Line 67: offset_between_characters getter."""
    phase = BehaviorPhase(_make_phase())
    assert phase.offset_between_characters == 10


def test_behavior_phase_offset_between_characters_setter():
    """Line 76: offset_between_characters setter."""
    phase = BehaviorPhase(_make_phase())
    phase.offset_between_characters = 99
    assert phase.offset_between_characters == 99


def test_behavior_phase_suggested_duration_per_character():
    """Line 85: suggested_duration_per_character getter."""
    phase = BehaviorPhase(_make_phase())
    assert phase.suggested_duration_per_character == 20


def test_behavior_phase_overlap_proportion():
    """Line 101: overlap_proportion getter (string fraction)."""
    phase = BehaviorPhase(_make_phase())
    assert phase.overlap_proportion == "1/2"


def test_behavior_phase_movement():
    """Line 109: movement getter."""
    phase = BehaviorPhase(_make_phase())
    assert phase.movement == 3


def test_behavior_phase_spring_damping():
    """Line 137: spring_damping getter (via repr path covers line 23 data property too)."""
    phase = BehaviorPhase(_make_phase())
    assert phase.spring_damping == 0.5


def test_behavior_phase_spring_stiffness():
    phase = BehaviorPhase(_make_phase())
    assert phase.spring_stiffness == 1.2


def test_behavior_phase_bounce_bounciness():
    phase = BehaviorPhase(_make_phase())
    assert phase.bounce_bounciness == 0.8


def test_behavior_phase_data_property():
    """Line 23: data property."""
    raw = _make_phase()
    phase = BehaviorPhase(raw)
    assert phase.data is raw


def test_behavior_phase_repr():
    """Line 137 (repr)."""
    phase = BehaviorPhase(_make_phase())
    assert repr(phase) == "BehaviorPhase(name='reveal', type=0)"


# ------------------------------------------------------------------
# behaviors.py — GenericBehaviorEffect (lines 158, 167)
# ------------------------------------------------------------------

BEHAVIOR_EFFECT_DATA = {
    "effectName": "TextReveal",
    "_type": "GenericBehaviorEffect",
    "bypassed": False,
    "start": 0,
    "duration": 1800000,
    "in": _make_phase(),
    "center": _make_phase(name="none", type=1),
    "out": _make_phase(name="fade", type=0),
    "metadata": {"presetName": "Reveal"},
}


def test_generic_behavior_effect_preset_name():
    """Line 158: preset_name property."""
    effect = GenericBehaviorEffect(BEHAVIOR_EFFECT_DATA)
    assert effect.preset_name == "Reveal"


def test_generic_behavior_effect_repr():
    """Line 167: __repr__."""
    effect = GenericBehaviorEffect(BEHAVIOR_EFFECT_DATA)
    assert repr(effect) == "GenericBehaviorEffect(name='TextReveal', preset='Reveal')"


def test_generic_behavior_effect_phases():
    effect = GenericBehaviorEffect(BEHAVIOR_EFFECT_DATA)
    assert effect.entrance.name == "reveal"
    assert effect.center.name == "none"
    assert effect.exit.name == "fade"


def test_generic_behavior_effect_start_duration_setters():
    import copy
    data = copy.deepcopy(BEHAVIOR_EFFECT_DATA)
    effect = GenericBehaviorEffect(data)
    effect.start = 100
    effect.duration = 200
    assert effect.start == 100
    assert effect.duration == 200


def test_generic_behavior_effect_bypassed_setter():
    import copy
    data = copy.deepcopy(BEHAVIOR_EFFECT_DATA)
    effect = GenericBehaviorEffect(data)
    effect.bypassed = True
    assert effect.bypassed is True


# ------------------------------------------------------------------
# cursor.py — CursorMotionBlur (lines 18, 22), CursorShadow (35-63),
#              CursorPhysics/LeftClickScaling setters (68, 72 already covered)
# ------------------------------------------------------------------

def test_cursor_motion_blur_intensity_getter():
    """Line 18."""
    data = {"effectName": "CursorMotionBlur", "parameters": {"intensity": _param(1.0)}}
    effect = CursorMotionBlur(data)
    assert effect.intensity == 1.0


def test_cursor_motion_blur_intensity_setter():
    """Line 22."""
    data = {"effectName": "CursorMotionBlur", "parameters": {"intensity": _param(1.0)}}
    effect = CursorMotionBlur(data)
    effect.intensity = 2.5
    assert effect.intensity == 2.5


def _cursor_shadow_data():
    return {
        "effectName": "CursorShadow",
        "parameters": {
            "angle": _param(3.93),
            "offset": _param(7.0),
            "blur": _param(10.0),
            "opacity": _param(0.5),
            "color-red": _param(0.0),
            "color-green": _param(0.0),
            "color-blue": _param(0.0),
            "color-alpha": _param(1.0),
        },
    }


def test_cursor_shadow_angle():
    """Line 35."""
    effect = CursorShadow(_cursor_shadow_data())
    assert effect.angle == 3.93


def test_cursor_shadow_angle_setter():
    """Line 39."""
    data = _cursor_shadow_data()
    effect = CursorShadow(data)
    effect.angle = 5.0
    assert effect.angle == 5.0


def test_cursor_shadow_offset():
    """Line 43."""
    effect = CursorShadow(_cursor_shadow_data())
    assert effect.offset == 7.0


def test_cursor_shadow_offset_setter():
    """Line 47."""
    data = _cursor_shadow_data()
    effect = CursorShadow(data)
    effect.offset = 14.0
    assert effect.offset == 14.0


def test_cursor_shadow_blur():
    """Line 51."""
    effect = CursorShadow(_cursor_shadow_data())
    assert effect.blur == 10.0


def test_cursor_shadow_blur_setter():
    """Line 55."""
    data = _cursor_shadow_data()
    effect = CursorShadow(data)
    effect.blur = 20.0
    assert effect.blur == 20.0


def test_cursor_shadow_opacity():
    """Line 59."""
    effect = CursorShadow(_cursor_shadow_data())
    assert effect.opacity == 0.5


def test_cursor_shadow_opacity_setter():
    """Line 63."""
    data = _cursor_shadow_data()
    effect = CursorShadow(data)
    effect.opacity = 0.8
    assert effect.opacity == 0.8


def test_cursor_shadow_color():
    """Line 68."""
    effect = CursorShadow(_cursor_shadow_data())
    assert effect.color == (0.0, 0.0, 0.0, 1.0)


def test_cursor_shadow_color_setter():
    """Line 72."""
    data = _cursor_shadow_data()
    effect = CursorShadow(data)
    effect.color = (1.0, 0.5, 0.25, 0.9)
    assert effect.color == (1.0, 0.5, 0.25, 0.9)


# ------------------------------------------------------------------
# source.py — SourceEffect (lines 19-90)
# ------------------------------------------------------------------

def _source_effect_data():
    return {
        "effectName": "SourceEffect",
        "parameters": {
            "Color0-red": _param(0.137), "Color0-green": _param(0.184),
            "Color0-blue": _param(0.243), "Color0-alpha": _param(1.0),
            "Color1-red": _param(0.020), "Color1-green": _param(0.627),
            "Color1-blue": _param(0.820), "Color1-alpha": _param(1.0),
            "Color2-red": _param(0.137), "Color2-green": _param(0.184),
            "Color2-blue": _param(0.243), "Color2-alpha": _param(1.0),
            "Color3-red": _param(0.020), "Color3-green": _param(0.627),
            "Color3-blue": _param(0.820), "Color3-alpha": _param(1.0),
            "MidPointX": _param(0.5), "MidPointY": _param(0.5),
            "Speed": _param(5.0),
            "sourceFileType": "tscshadervid",
        },
    }


@pytest.mark.parametrize("color_idx,expected_rgba", [
    (0, (0.137, 0.184, 0.243, 1.0)),
    (1, (0.020, 0.627, 0.820, 1.0)),
    (2, (0.137, 0.184, 0.243, 1.0)),
    (3, (0.020, 0.627, 0.820, 1.0)),
], ids=["color0", "color1", "color2", "color3"])
def test_source_effect_color_getter(color_idx, expected_rgba):
    """Lines 19-20 (_get_color), 37, 45, 53, 61."""
    effect = SourceEffect(_source_effect_data())
    actual_color = getattr(effect, f"color{color_idx}")
    assert actual_color == expected_rgba


@pytest.mark.parametrize("color_idx", [0, 1, 2, 3], ids=["color0", "color1", "color2", "color3"])
def test_source_effect_color_setter(color_idx):
    """Lines 29-33 (_set_color), 41, 49, 57, 65."""
    data = _source_effect_data()
    effect = SourceEffect(data)
    new_rgba = (0.9, 0.8, 0.7, 0.6)
    setattr(effect, f"color{color_idx}", new_rgba)
    assert getattr(effect, f"color{color_idx}") == new_rgba


def test_source_effect_mid_point():
    """Line 70."""
    effect = SourceEffect(_source_effect_data())
    assert effect.mid_point == (0.5, 0.5)


def test_source_effect_mid_point_setter():
    """Lines 77-78."""
    data = _source_effect_data()
    effect = SourceEffect(data)
    effect.mid_point = (0.3, 0.7)
    assert effect.mid_point == (0.3, 0.7)


def test_source_effect_speed():
    """Line 82."""
    effect = SourceEffect(_source_effect_data())
    assert effect.speed == 5.0


def test_source_effect_speed_setter():
    """Line 86."""
    data = _source_effect_data()
    effect = SourceEffect(data)
    effect.speed = 10.0
    assert effect.speed == 10.0


def test_source_effect_source_file_type():
    """Line 90."""
    effect = SourceEffect(_source_effect_data())
    assert effect.source_file_type == "tscshadervid"


# ------------------------------------------------------------------
# visual.py — RoundCorners setters (lines 31, 39, 47, 55)
# ------------------------------------------------------------------

def _round_corners_data():
    return {
        "effectName": "RoundCorners",
        "parameters": {
            "radius": _param(16.0),
            "topLeft": _param(True, "bool"),
            "topRight": _param(True, "bool"),
            "bottomLeft": _param(False, "bool"),
            "bottomRight": _param(False, "bool"),
        },
    }


@pytest.mark.parametrize("prop,param_key", [
    ("top_left", "topLeft"),
    ("top_right", "topRight"),
    ("bottom_left", "bottomLeft"),
    ("bottom_right", "bottomRight"),
], ids=["top_left", "top_right", "bottom_left", "bottom_right"])
def test_round_corners_corner_setters(prop, param_key):
    """Lines 31, 39, 47, 55."""
    data = _round_corners_data()
    effect = RoundCorners(data)
    setattr(effect, prop, not getattr(effect, prop))
    assert data["parameters"][param_key]["defaultValue"] == (not _round_corners_data()["parameters"][param_key]["defaultValue"])


# ------------------------------------------------------------------
# visual.py — DropShadow setters (lines 92, 100, 108, 116)
# ------------------------------------------------------------------

def _drop_shadow_data():
    return {
        "effectName": "DropShadow",
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


@pytest.mark.parametrize("prop,new_val", [
    ("angle", 3.14),
    ("offset", 20.0),
    ("blur", 50.0),
    ("opacity", 0.9),
], ids=["angle", "offset", "blur", "opacity"])
def test_drop_shadow_setters(prop, new_val):
    """Lines 92, 100, 108, 116."""
    data = _drop_shadow_data()
    effect = DropShadow(data)
    setattr(effect, prop, new_val)
    assert getattr(effect, prop) == new_val


# ------------------------------------------------------------------
# visual.py — Mask setters (lines 171, 179, 187, 195, 203, 211, 219, 227)
# ------------------------------------------------------------------

def _mask_data():
    return {
        "effectName": "Mask",
        "parameters": {
            "mask_shape": _param(0),
            "mask_opacity": _param(1.0),
            "mask_blend": _param(0.0),
            "mask_invert": _param(0),
            "mask_rotation": _param(0.0),
            "mask_width": _param(0.5),
            "mask_height": _param(0.5),
            "mask_positionX": _param(0.0),
            "mask_positionY": _param(0.0),
        },
    }


@pytest.mark.parametrize("prop,param_key,new_val", [
    ("mask_opacity", "mask_opacity", 0.7),
    ("mask_blend", "mask_blend", 0.3),
    ("mask_invert", "mask_invert", 1),
    ("mask_rotation", "mask_rotation", 45.0),
    ("mask_width", "mask_width", 0.8),
    ("mask_height", "mask_height", 0.6),
    ("mask_position_x", "mask_positionX", 0.25),
    ("mask_position_y", "mask_positionY", 0.75),
], ids=["opacity", "blend", "invert", "rotation", "width", "height", "posX", "posY"])
def test_mask_setters(prop, param_key, new_val):
    """Lines 171, 179, 187, 195, 203, 211, 219, 227."""
    data = _mask_data()
    effect = Mask(data)
    setattr(effect, prop, new_val)
    assert getattr(effect, prop) == new_val


# ------------------------------------------------------------------
# visual.py — BlurRegion setters (lines 277, 285, 293)
# ------------------------------------------------------------------

def _blur_region_data():
    return {
        "effectName": "BlurRegion",
        "parameters": {
            "sigma": _param(10.0),
            "mask_corner_radius": _param(0.0),
            "mask_invert": _param(0),
            "color_alpha": _param(1.0),
        },
    }


@pytest.mark.parametrize("prop,new_val", [
    ("mask_corner_radius", 5.0),
    ("mask_invert", 1),
    ("color_alpha", 0.5),
], ids=["corner_radius", "invert", "color_alpha"])
def test_blur_region_setters(prop, new_val):
    """Lines 277, 285, 293."""
    data = _blur_region_data()
    effect = BlurRegion(data)
    setattr(effect, prop, new_val)
    assert getattr(effect, prop) == new_val


# ------------------------------------------------------------------
# callouts.py — text() line 18, square() line 68
# ------------------------------------------------------------------

def test_callout_text_returns_expected_structure():
    """Line 18: text() return."""
    actual_result = text("Hello", "Arial", "bold")
    assert actual_result["kind"] == "remix"
    assert actual_result["shape"] == "text"
    assert actual_result["text"] == "Hello"
    assert actual_result["font"]["name"] == "Arial"
    assert actual_result["font"]["weight"] == "bold"
    assert actual_result["font"]["size"] == 96.0
    assert actual_result["horizontal-alignment"] == "center"
    assert actual_result["vertical-alignment"] == "center"


def test_callout_square_returns_expected_structure():
    """Line 68: square() return."""
    actual_result = square("World", "Helvetica", "normal")
    assert actual_result["kind"] == "remix"
    assert actual_result["shape"] == "text-rectangle"
    assert actual_result["text"] == "World"
    assert actual_result["font"]["name"] == "Helvetica"
    assert actual_result["font"]["weight"] == "normal"
    assert actual_result["fill-color-red"] == 1.0
    assert actual_result["stroke-width"] == 2.0
