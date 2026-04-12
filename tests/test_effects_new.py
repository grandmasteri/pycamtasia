from __future__ import annotations

import pytest

from camtasia.effects.base import Effect, effect_from_dict
from camtasia.effects.cursor import CursorPhysics, LeftClickScaling
from camtasia.effects.visual import DropShadow, RoundCorners


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
    "effect_name, expected_class",
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
