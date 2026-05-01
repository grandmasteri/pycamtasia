"""Tests for misc extensions: caption anchor, Animation class, media_matte ease, gradient callouts."""
from __future__ import annotations

import pytest

from camtasia.annotations.callouts import square
from camtasia.annotations.shapes import rectangle
from camtasia.annotations.types import Color
from camtasia.effects.visual import MediaMatte
from camtasia.timeline.captions import CaptionAttributes
from camtasia.timeline.clips.base import Animation, BaseClip
from camtasia.types import MatteMode

# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _caption_data(**overrides) -> dict:
    d: dict = {}
    d.update(overrides)
    return d


def _clip_data(**overrides) -> dict:
    data = {
        "_type": "VMFile",
        "id": 1,
        "start": 0,
        "duration": 705600000,
        "mediaStart": 0,
        "mediaDuration": 705600000,
        "scalar": 1,
        "effects": [],
        "parameters": {},
        "metadata": {},
        "animationTracks": {},
    }
    data.update(overrides)
    return data


def _param(value: object, type_: str = "double", interp: str = "linr") -> dict:
    return {"type": type_, "defaultValue": value, "interp": interp}


def _make_matte(mode: int = 1) -> dict:
    return {
        "effectName": "MediaMatte",
        "bypassed": False,
        "category": "categoryVisualEffects",
        "parameters": {
            "intensity": _param(1.0),
            "matteMode": _param(mode),
            "trackDepth": _param(10002),
        },
    }


# ------------------------------------------------------------------
# (a) Caption vertical position / anchor
# ------------------------------------------------------------------


class TestCaptionPosition:
    def test_position_getter_defaults(self):
        attrs = CaptionAttributes(_caption_data())
        pos = attrs.position
        assert pos == {"x": 0.5, "y": 0.9}

    def test_position_setter(self):
        data = _caption_data()
        attrs = CaptionAttributes(data)
        attrs.position = {"x": 0.3, "y": 0.2}
        assert data["positionX"] == 0.3
        assert data["positionY"] == 0.2
        assert attrs.position == {"x": 0.3, "y": 0.2}

    def test_vertical_anchor_default_bottom(self):
        attrs = CaptionAttributes(_caption_data())
        assert attrs.vertical_anchor == "bottom"

    @pytest.mark.parametrize(("anchor", "expected_y"), [
        ("top", 0.1),
        ("middle", 0.5),
        ("bottom", 0.9),
    ])
    def test_vertical_anchor_setter(self, anchor: str, expected_y: float):
        data = _caption_data()
        attrs = CaptionAttributes(data)
        attrs.vertical_anchor = anchor
        assert data["positionY"] == expected_y
        assert attrs.vertical_anchor == anchor

    def test_vertical_anchor_invalid_raises(self):
        attrs = CaptionAttributes(_caption_data())
        with pytest.raises(ValueError, match="vertical_anchor"):
            attrs.vertical_anchor = "left"


# ------------------------------------------------------------------
# (b) Animation class + BaseClip.add_animation
# ------------------------------------------------------------------


class TestAnimationClass:
    def test_animation_defaults(self):
        anim = Animation()
        assert anim.start_seconds == 0.0
        assert anim.end_seconds == 1.0
        assert anim.scale is None
        assert anim.easing == "linr"

    def test_add_animation_scale(self):
        clip = BaseClip(_clip_data())
        anim = Animation(start_seconds=0.0, end_seconds=1.0, scale=(2.0, 2.0))
        result = clip.add_animation(anim)
        assert result is clip
        params = clip._data["parameters"]
        assert "scale0" in params
        assert params["scale0"]["keyframes"][-1]["value"] == 2.0

    def test_add_animation_position(self):
        clip = BaseClip(_clip_data())
        anim = Animation(start_seconds=0.0, end_seconds=0.5, position=(100.0, 200.0), easing="eioe")
        clip.add_animation(anim)
        params = clip._data["parameters"]
        assert params["translation0"]["keyframes"][-1]["value"] == 100.0
        assert params["translation1"]["keyframes"][-1]["value"] == 200.0

    def test_add_animation_rotation(self):
        clip = BaseClip(_clip_data())
        anim = Animation(start_seconds=0.0, end_seconds=1.0, rotation=90.0)
        clip.add_animation(anim)
        params = clip._data["parameters"]
        assert "rotation2" in params


# ------------------------------------------------------------------
# (c) add_media_matte extensions
# ------------------------------------------------------------------


class TestAddMediaMatteExtensions:
    def test_default_preset_name_alpha(self):
        clip = BaseClip(_clip_data())
        clip.add_media_matte(matte_mode=1)
        effect = clip._data["effects"][0]
        assert effect["metadata"]["presetName"] == "Media Matte Alpha"

    def test_default_preset_name_luminosity(self):
        clip = BaseClip(_clip_data())
        clip.add_media_matte(matte_mode=3)
        effect = clip._data["effects"][0]
        assert effect["metadata"]["presetName"] == "Media Matte Luminosity"

    def test_ease_in_out_seconds(self):
        clip = BaseClip(_clip_data())
        clip.add_media_matte(ease_in_seconds=0.5, ease_out_seconds=1.0)
        params = clip._data["effects"][0]["parameters"]
        assert params["ease-in"] == round(0.5 * 705600000)
        assert params["ease-out"] == round(1.0 * 705600000)

    def test_no_ease_keys_when_zero(self):
        clip = BaseClip(_clip_data())
        clip.add_media_matte()
        params = clip._data["effects"][0]["parameters"]
        assert "ease-in" not in params
        assert "ease-out" not in params

    def test_custom_preset_name_overrides(self):
        clip = BaseClip(_clip_data())
        clip.add_media_matte(matte_mode=1, preset_name="Custom")
        assert clip._data["effects"][0]["metadata"]["presetName"] == "Custom"


# ------------------------------------------------------------------
# (d) MediaMatte.mode full enum round-trip
# ------------------------------------------------------------------


class TestMediaMatteEnumRoundTrip:
    @pytest.mark.parametrize("mode", list(MatteMode))
    def test_round_trip_all_modes(self, mode: MatteMode):
        matte = MediaMatte(_make_matte(mode.value))
        assert matte.mode == mode.value
        matte.mode = mode
        assert matte.mode == mode.value


# ------------------------------------------------------------------
# (e) Gradient fill for callouts/shapes
# ------------------------------------------------------------------


class TestGradientFill:
    def test_square_gradient_stops(self):
        stops = [(0.0, Color(1.0, 0.0, 0.0)), (1.0, Color(0.0, 0.0, 1.0))]
        result = square("Hi", "Arial", "Bold", gradient_stops=stops)
        assert result["fill-style"] == "gradient"
        assert len(result["gradient-stops"]) == 2
        assert result["gradient-stops"][0]["position"] == 0.0
        assert result["gradient-stops"][0]["color-red"] == 1.0
        assert result["gradient-stops"][1]["color-blue"] == 1.0

    def test_rectangle_gradient_stops(self):
        stops = [(0.0, Color(0.0, 1.0, 0.0)), (1.0, Color(1.0, 1.0, 0.0))]
        result = rectangle(gradient_stops=stops)
        assert result["fill-style"] == "gradient"
        assert len(result["gradient-stops"]) == 2
        assert result["gradient-stops"][0]["color-green"] == 1.0

    def test_square_no_gradient_default(self):
        result = square("Hi", "Arial", "Bold")
        assert result["fill-style"] == "solid"
        assert "gradient-stops" not in result

    def test_rectangle_no_gradient_default(self):
        result = rectangle()
        assert result["fill-style"] == "solid"
        assert "gradient-stops" not in result

    def test_add_animation_opacity(self):
        """Cover base.py line 2093: animate_to with opacity."""
        clip = BaseClip(_clip_data())
        anim = Animation(start_seconds=0.0, end_seconds=1.0, opacity=0.5)
        result = clip.add_animation(anim)
        assert result is clip
