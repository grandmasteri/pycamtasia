"""Tests for cursor effects: general cursor effects and click effects."""
from __future__ import annotations

import pytest

from camtasia.effects.base import _EFFECT_REGISTRY, Effect, effect_from_dict
from camtasia.effects.cursor import (
    CursorColor,
    CursorGlow,
    CursorGradient,
    CursorHighlight,
    CursorIsolation,
    CursorLens,
    CursorMagnify,
    CursorMotionBlur,
    CursorNegative,
    CursorPhysics,
    CursorShadow,
    CursorSmoothing,
    CursorSpotlight,
    LeftClickBurst1,
    LeftClickBurst2,
    LeftClickBurst3,
    LeftClickBurst4,
    LeftClickRings,
    LeftClickRipple,
    LeftClickScaling,
    LeftClickScope,
    LeftClickSound,
    LeftClickTarget,
    LeftClickWarp,
    LeftClickZoom,
    RightClickBurst1,
    RightClickBurst2,
    RightClickBurst3,
    RightClickBurst4,
    RightClickRings,
    RightClickRipple,
    RightClickScaling,
    RightClickScope,
    RightClickSound,
    RightClickTarget,
    RightClickWarp,
    RightClickZoom,
)

# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _param(value, type_: str = "double", interp: str = "linr") -> dict:
    return {"type": type_, "defaultValue": value, "interp": interp}


def _color_params(prefix: str, r: float = 1.0, g: float = 0.5, b: float = 0.0, a: float = 1.0) -> dict:
    return {
        f"{prefix}-red": _param(r),
        f"{prefix}-green": _param(g),
        f"{prefix}-blue": _param(b),
        f"{prefix}-alpha": _param(a),
    }


def _effect_dict(name: str, **params) -> dict:
    return {
        "effectName": name,
        "bypassed": False,
        "category": "cursor",
        "parameters": params,
    }


# ------------------------------------------------------------------
# Existing effects (regression)
# ------------------------------------------------------------------

class TestCursorMotionBlur:

    def test_intensity_roundtrip(self):
        d = _effect_dict("CursorMotionBlur", intensity=_param(3.5))
        e = CursorMotionBlur(d)
        assert e.intensity == 3.5
        e.intensity = 7.0
        assert e.intensity == 7.0


class TestCursorShadow:

    def test_properties_roundtrip(self):
        d = _effect_dict(
            "CursorShadow",
            enabled=_param(1),
            angle=_param(1.57),
            offset=_param(10.0),
            blur=_param(5.0),
            opacity=_param(0.8),
            **_color_params("color", 0.0, 0.0, 0.0, 1.0),
        )
        e = CursorShadow(d)
        assert e.enabled == 1
        assert e.angle == pytest.approx(1.57)
        assert e.offset == 10.0
        assert e.blur == 5.0
        assert e.opacity == 0.8
        assert e.color == (0.0, 0.0, 0.0, 1.0)
        e.color = (1.0, 0.0, 0.0, 0.5)
        assert e.color == (1.0, 0.0, 0.0, 0.5)


class TestCursorPhysics:

    def test_properties_roundtrip(self):
        d = _effect_dict("CursorPhysics", intensity=_param(1.5), tilt=_param(2.5))
        e = CursorPhysics(d)
        assert e.intensity == 1.5
        assert e.tilt == 2.5
        e.intensity = 3.0
        e.tilt = 4.0
        assert e.intensity == 3.0
        assert e.tilt == 4.0


class TestLeftClickScaling:

    def test_properties_roundtrip(self):
        d = _effect_dict("LeftClickScaling", scale=_param(1.5), speed=_param(2.0))
        e = LeftClickScaling(d)
        assert e.scale == 1.5
        assert e.speed == 2.0
        e.scale = 3.0
        e.speed = 4.0
        assert e.scale == 3.0
        assert e.speed == 4.0


# ------------------------------------------------------------------
# New general cursor effects
# ------------------------------------------------------------------

class TestCursorColor:

    def test_fill_and_outline_roundtrip(self):
        d = _effect_dict(
            "CursorColor",
            **_color_params("fillColor", 1.0, 0.0, 0.0, 1.0),
            **_color_params("outlineColor", 0.0, 1.0, 0.0, 0.5),
        )
        e = CursorColor(d)
        assert e.fill_color == (1.0, 0.0, 0.0, 1.0)
        assert e.outline_color == (0.0, 1.0, 0.0, 0.5)
        e.fill_color = (0.5, 0.5, 0.5, 1.0)
        assert e.fill_color == (0.5, 0.5, 0.5, 1.0)
        e.outline_color = (0.1, 0.2, 0.3, 0.4)
        assert e.outline_color == (0.1, 0.2, 0.3, 0.4)


class TestCursorGlow:

    def test_properties_roundtrip(self):
        d = _effect_dict(
            "CursorGlow",
            **_color_params("color", 1.0, 1.0, 0.0, 1.0),
            opacity=_param(0.7),
            radius=_param(20.0),
        )
        e = CursorGlow(d)
        assert e.color == (1.0, 1.0, 0.0, 1.0)
        assert e.opacity == 0.7
        assert e.radius == 20.0
        e.opacity = 0.3
        e.radius = 40.0
        assert e.opacity == 0.3
        assert e.radius == 40.0


class TestCursorHighlight:

    def test_properties_roundtrip(self):
        d = _effect_dict(
            "CursorHighlight",
            size=_param(50.0),
            **_color_params("color", 1.0, 1.0, 0.0, 0.5),
            opacity=_param(0.6),
        )
        e = CursorHighlight(d)
        assert e.size == 50.0
        assert e.color == (1.0, 1.0, 0.0, 0.5)
        assert e.opacity == 0.6
        e.size = 100.0
        assert e.size == 100.0


class TestCursorIsolation:

    def test_properties_roundtrip(self):
        d = _effect_dict("CursorIsolation", size=_param(80.0), feather=_param(10.0))
        e = CursorIsolation(d)
        assert e.size == 80.0
        assert e.feather == 10.0
        e.size = 120.0
        e.feather = 20.0
        assert e.size == 120.0
        assert e.feather == 20.0


class TestCursorMagnify:

    def test_properties_roundtrip(self):
        d = _effect_dict("CursorMagnify", scale=_param(2.0), size=_param(100.0))
        e = CursorMagnify(d)
        assert e.scale == 2.0
        assert e.size == 100.0
        e.scale = 3.0
        e.size = 150.0
        assert e.scale == 3.0
        assert e.size == 150.0


class TestCursorSpotlight:

    def test_properties_roundtrip(self):
        d = _effect_dict(
            "CursorSpotlight",
            size=_param(60.0),
            opacity=_param(0.5),
            blur=_param(15.0),
            **_color_params("color", 0.0, 0.0, 0.0, 0.8),
        )
        e = CursorSpotlight(d)
        assert e.size == 60.0
        assert e.opacity == 0.5
        assert e.blur == 15.0
        assert e.color == (0.0, 0.0, 0.0, 0.8)
        e.blur = 25.0
        assert e.blur == 25.0


class TestCursorGradient:

    def test_properties_roundtrip(self):
        d = _effect_dict(
            "CursorGradient",
            **_color_params("color", 0.2, 0.4, 0.6, 1.0),
            size=_param(40.0),
            opacity=_param(0.9),
        )
        e = CursorGradient(d)
        assert e.color == (0.2, 0.4, 0.6, 1.0)
        assert e.size == 40.0
        assert e.opacity == 0.9
        e.size = 80.0
        assert e.size == 80.0


class TestCursorLens:

    def test_properties_roundtrip(self):
        d = _effect_dict("CursorLens", scale=_param(1.5), size=_param(75.0))
        e = CursorLens(d)
        assert e.scale == 1.5
        assert e.size == 75.0
        e.scale = 2.5
        e.size = 90.0
        assert e.scale == 2.5
        assert e.size == 90.0


class TestCursorNegative:

    def test_properties_roundtrip(self):
        d = _effect_dict("CursorNegative", size=_param(60.0), feather=_param(8.0))
        e = CursorNegative(d)
        assert e.size == 60.0
        assert e.feather == 8.0
        e.size = 90.0
        e.feather = 12.0
        assert e.size == 90.0
        assert e.feather == 12.0


class TestCursorSmoothing:

    def test_level_roundtrip(self):
        d = _effect_dict("CursorSmoothing", level=_param(5.0))
        e = CursorSmoothing(d)
        assert e.level == 5.0
        e.level = 10.0
        assert e.level == 10.0


# ------------------------------------------------------------------
# Click effects — burst variants
# ------------------------------------------------------------------

_BURST_CLASSES = [
    ("LeftClickBurst1", LeftClickBurst1),
    ("LeftClickBurst2", LeftClickBurst2),
    ("LeftClickBurst3", LeftClickBurst3),
    ("LeftClickBurst4", LeftClickBurst4),
    ("RightClickBurst1", RightClickBurst1),
    ("RightClickBurst2", RightClickBurst2),
    ("RightClickBurst3", RightClickBurst3),
    ("RightClickBurst4", RightClickBurst4),
]


@pytest.mark.parametrize(("name", "cls"), _BURST_CLASSES, ids=[n for n, _ in _BURST_CLASSES])
class TestClickBurst:

    def test_properties_roundtrip(self, name, cls):
        d = _effect_dict(
            name,
            **_color_params("color", 1.0, 0.0, 0.0, 1.0),
            size=_param(30.0),
            opacity=_param(0.8),
            duration=_param(0.5),
        )
        e = cls(d)
        assert e.color == (1.0, 0.0, 0.0, 1.0)
        assert e.size == 30.0
        assert e.opacity == 0.8
        assert e.duration == 0.5
        e.size = 60.0
        e.duration = 1.0
        assert e.size == 60.0
        assert e.duration == 1.0

    def test_effect_from_dict_dispatch(self, name, cls):
        d = _effect_dict(name, size=_param(10.0))
        e = effect_from_dict(d)
        assert type(e) is cls


# ------------------------------------------------------------------
# Click effects — zoom, rings, ripple, scope, target, warp, sound
# ------------------------------------------------------------------

_ZOOM_CLASSES = [("LeftClickZoom", LeftClickZoom), ("RightClickZoom", RightClickZoom)]


@pytest.mark.parametrize(("name", "cls"), _ZOOM_CLASSES, ids=[n for n, _ in _ZOOM_CLASSES])
class TestClickZoom:

    def test_properties_roundtrip(self, name, cls):
        d = _effect_dict(name, scale=_param(2.0), size=_param(50.0), duration=_param(0.3))
        e = cls(d)
        assert e.scale == 2.0
        assert e.size == 50.0
        assert e.duration == 0.3
        e.scale = 4.0
        assert e.scale == 4.0


_RINGS_CLASSES = [("LeftClickRings", LeftClickRings), ("RightClickRings", RightClickRings)]


@pytest.mark.parametrize(("name", "cls"), _RINGS_CLASSES, ids=[n for n, _ in _RINGS_CLASSES])
class TestClickRings:

    def test_properties_roundtrip(self, name, cls):
        d = _effect_dict(
            name,
            **_color_params("color", 0.0, 1.0, 0.0, 1.0),
            size=_param(40.0),
            opacity=_param(0.7),
            duration=_param(0.6),
        )
        e = cls(d)
        assert e.color == (0.0, 1.0, 0.0, 1.0)
        assert e.size == 40.0
        assert e.opacity == 0.7
        assert e.duration == 0.6


_RIPPLE_CLASSES = [("LeftClickRipple", LeftClickRipple), ("RightClickRipple", RightClickRipple)]


@pytest.mark.parametrize(("name", "cls"), _RIPPLE_CLASSES, ids=[n for n, _ in _RIPPLE_CLASSES])
class TestClickRipple:

    def test_properties_roundtrip(self, name, cls):
        d = _effect_dict(name, size=_param(35.0), opacity=_param(0.6), duration=_param(0.4))
        e = cls(d)
        assert e.size == 35.0
        assert e.opacity == 0.6
        assert e.duration == 0.4
        e.opacity = 0.9
        assert e.opacity == 0.9


_SCOPE_CLASSES = [("LeftClickScope", LeftClickScope), ("RightClickScope", RightClickScope)]


@pytest.mark.parametrize(("name", "cls"), _SCOPE_CLASSES, ids=[n for n, _ in _SCOPE_CLASSES])
class TestClickScope:

    def test_properties_roundtrip(self, name, cls):
        d = _effect_dict(
            name,
            **_color_params("color", 0.0, 0.0, 1.0, 1.0),
            size=_param(45.0),
            opacity=_param(0.5),
        )
        e = cls(d)
        assert e.color == (0.0, 0.0, 1.0, 1.0)
        assert e.size == 45.0
        assert e.opacity == 0.5


_TARGET_CLASSES = [("LeftClickTarget", LeftClickTarget), ("RightClickTarget", RightClickTarget)]


@pytest.mark.parametrize(("name", "cls"), _TARGET_CLASSES, ids=[n for n, _ in _TARGET_CLASSES])
class TestClickTarget:

    def test_properties_roundtrip(self, name, cls):
        d = _effect_dict(
            name,
            **_color_params("color", 1.0, 0.0, 0.0, 1.0),
            size=_param(25.0),
            opacity=_param(0.9),
        )
        e = cls(d)
        assert e.color == (1.0, 0.0, 0.0, 1.0)
        assert e.size == 25.0
        assert e.opacity == 0.9
        e.color = (0.0, 1.0, 0.0, 1.0)
        assert e.color == (0.0, 1.0, 0.0, 1.0)


_WARP_CLASSES = [("LeftClickWarp", LeftClickWarp), ("RightClickWarp", RightClickWarp)]


@pytest.mark.parametrize(("name", "cls"), _WARP_CLASSES, ids=[n for n, _ in _WARP_CLASSES])
class TestClickWarp:

    def test_properties_roundtrip(self, name, cls):
        d = _effect_dict(name, intensity=_param(5.0), size=_param(50.0), duration=_param(0.3))
        e = cls(d)
        assert e.intensity == 5.0
        assert e.size == 50.0
        assert e.duration == 0.3
        e.intensity = 10.0
        assert e.intensity == 10.0


_SOUND_CLASSES = [("LeftClickSound", LeftClickSound), ("RightClickSound", RightClickSound)]


@pytest.mark.parametrize(("name", "cls"), _SOUND_CLASSES, ids=[n for n, _ in _SOUND_CLASSES])
class TestClickSound:

    def test_properties_roundtrip(self, name, cls):
        d = _effect_dict(name, volume=_param(0.8), soundId="click_01")
        e = cls(d)
        assert e.volume == 0.8
        assert e.sound_id == "click_01"
        e.volume = 0.5
        e.sound_id = "click_02"
        assert e.volume == 0.5
        assert e.sound_id == "click_02"


class TestRightClickScaling:

    def test_properties_roundtrip(self):
        d = _effect_dict("RightClickScaling", scale=_param(1.5), speed=_param(2.0))
        e = RightClickScaling(d)
        assert e.scale == 1.5
        assert e.speed == 2.0
        e.scale = 3.0
        e.speed = 4.0
        assert e.scale == 3.0
        assert e.speed == 4.0

    def test_mirrors_left_click_scaling(self):
        """RightClickScaling has the same interface as LeftClickScaling."""
        left = _effect_dict("LeftClickScaling", scale=_param(2.0), speed=_param(1.0))
        right = _effect_dict("RightClickScaling", scale=_param(2.0), speed=_param(1.0))
        el = LeftClickScaling(left)
        er = RightClickScaling(right)
        assert el.scale == er.scale
        assert el.speed == er.speed


# ------------------------------------------------------------------
# Registry / effect_from_dict dispatch
# ------------------------------------------------------------------

_ALL_EFFECT_NAMES = [
    "CursorMotionBlur", "CursorShadow", "CursorPhysics", "LeftClickScaling",
    "CursorColor", "CursorGlow", "CursorHighlight", "CursorIsolation",
    "CursorMagnify", "CursorSpotlight", "CursorGradient", "CursorLens",
    "CursorNegative", "CursorSmoothing",
    "LeftClickBurst1", "LeftClickBurst2", "LeftClickBurst3", "LeftClickBurst4",
    "RightClickBurst1", "RightClickBurst2", "RightClickBurst3", "RightClickBurst4",
    "LeftClickZoom", "RightClickZoom",
    "LeftClickRings", "RightClickRings",
    "LeftClickRipple", "RightClickRipple",
    "LeftClickScope", "RightClickScope",
    "LeftClickTarget", "RightClickTarget",
    "LeftClickWarp", "RightClickWarp",
    "LeftClickSound", "RightClickSound",
    "RightClickScaling",
]


class TestCursorEffectRegistration:

    @pytest.mark.parametrize("name", _ALL_EFFECT_NAMES)
    def test_registered_in_registry(self, name):
        assert name in _EFFECT_REGISTRY

    @pytest.mark.parametrize("name", _ALL_EFFECT_NAMES)
    def test_effect_from_dict_returns_subclass(self, name):
        d = _effect_dict(name)
        e = effect_from_dict(d)
        assert type(e) is not Effect
        assert isinstance(e, Effect)
        assert e.name == name
