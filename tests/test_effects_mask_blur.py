"""Tests for Mask.animate_to and BlurRegion extended properties."""
from __future__ import annotations

import pytest

from camtasia.effects.base import effect_from_dict
from camtasia.effects.visual import BlurRegion, Mask
from camtasia.timing import EDIT_RATE
from camtasia.types import MaskShape


def _param(value, type_: str = "double", interp: str = "linr") -> dict:
    return {"type": type_, "defaultValue": value, "interp": interp}


def _make_blur() -> dict:
    return {
        "effectName": "BlurRegion",
        "bypassed": False,
        "category": "categoryVisualEffects",
        "parameters": {
            k: _param(v)
            for k, v in {
                "sigma": 5.0,
                "mask-cornerRadius": 2.0,
                "mask-invert": 0,
                "color-red": 0.1,
                "color-green": 0.2,
                "color-blue": 0.3,
                "color-alpha": 0.9,
                "mask-shape": 0,
                "mask-blend": 0.5,
                "mask-opacity": 0.8,
                "ease-in": 705_600_000,
                "ease-out": 352_800_000,
                "mask-width": 100.0,
                "mask-height": 50.0,
                "mask-positionX": 10.0,
                "mask-positionY": 20.0,
            }.items()
        },
    }


def _make_mask() -> dict:
    return {
        "effectName": "Mask",
        "bypassed": False,
        "category": "categoryVisualEffects",
        "parameters": {
            k: _param(v)
            for k, v in {
                "mask-shape": 0,
                "mask-opacity": 1.0,
                "mask-blend": 0.0,
                "mask-invert": 0,
                "mask-rotation": 0.0,
                "mask-width": 200.0,
                "mask-height": 100.0,
                "mask-positionX": 0.0,
                "mask-positionY": 0.0,
                "mask-cornerRadius": 0.0,
            }.items()
        },
    }


# ------------------------------------------------------------------
# BlurRegion registration
# ------------------------------------------------------------------


class TestBlurRegionRegistration:
    def test_effect_from_dict_dispatches(self):
        data = {"effectName": "BlurRegion", "parameters": {}}
        assert type(effect_from_dict(data)) is BlurRegion


# ------------------------------------------------------------------
# BlurRegion.color
# ------------------------------------------------------------------


class TestBlurRegionColor:
    def test_read(self):
        actual = BlurRegion(_make_blur())
        assert actual.color == (0.1, 0.2, 0.3, 0.9)

    def test_write(self):
        data = _make_blur()
        br = BlurRegion(data)
        br.color = (0.4, 0.5, 0.6, 1.0)
        assert data["parameters"]["color-red"]["defaultValue"] == 0.4
        assert data["parameters"]["color-green"]["defaultValue"] == 0.5
        assert data["parameters"]["color-blue"]["defaultValue"] == 0.6
        assert data["parameters"]["color-alpha"]["defaultValue"] == 1.0


# ------------------------------------------------------------------
# BlurRegion.shape
# ------------------------------------------------------------------


class TestBlurRegionShape:
    def test_read(self):
        assert BlurRegion(_make_blur()).shape == 0

    def test_write_int(self):
        data = _make_blur()
        br = BlurRegion(data)
        br.shape = 1
        assert data["parameters"]["mask-shape"]["defaultValue"] == 1

    def test_write_enum(self):
        data = _make_blur()
        br = BlurRegion(data)
        br.shape = MaskShape.ELLIPSE
        assert data["parameters"]["mask-shape"]["defaultValue"] == 1


# ------------------------------------------------------------------
# BlurRegion.feather
# ------------------------------------------------------------------


class TestBlurRegionFeather:
    def test_read(self):
        assert BlurRegion(_make_blur()).feather == 0.5

    def test_write(self):
        data = _make_blur()
        br = BlurRegion(data)
        br.feather = 0.75
        assert data["parameters"]["mask-blend"]["defaultValue"] == 0.75


# ------------------------------------------------------------------
# BlurRegion.opacity
# ------------------------------------------------------------------


class TestBlurRegionOpacity:
    def test_read(self):
        assert BlurRegion(_make_blur()).opacity == 0.8

    def test_write(self):
        data = _make_blur()
        br = BlurRegion(data)
        br.opacity = 0.3
        assert data["parameters"]["mask-opacity"]["defaultValue"] == 0.3


# ------------------------------------------------------------------
# BlurRegion.ease_in_seconds / ease_out_seconds
# ------------------------------------------------------------------


class TestBlurRegionEase:
    def test_ease_in_read(self):
        assert BlurRegion(_make_blur()).ease_in_seconds == pytest.approx(1.0)

    def test_ease_out_read(self):
        assert BlurRegion(_make_blur()).ease_out_seconds == pytest.approx(0.5)

    def test_ease_in_write(self):
        data = _make_blur()
        br = BlurRegion(data)
        br.ease_in_seconds = 2.0
        assert data["parameters"]["ease-in"]["defaultValue"] == 2 * EDIT_RATE

    def test_ease_out_write(self):
        data = _make_blur()
        br = BlurRegion(data)
        br.ease_out_seconds = 1.5
        assert data["parameters"]["ease-out"]["defaultValue"] == round(1.5 * EDIT_RATE)


# ------------------------------------------------------------------
# BlurRegion position/dimension properties
# ------------------------------------------------------------------


class TestBlurRegionPositionDimension:
    def test_mask_width(self):
        data = _make_blur()
        br = BlurRegion(data)
        assert br.mask_width == 100.0
        br.mask_width = 200.0
        assert data["parameters"]["mask-width"]["defaultValue"] == 200.0

    def test_mask_height(self):
        data = _make_blur()
        br = BlurRegion(data)
        assert br.mask_height == 50.0
        br.mask_height = 75.0
        assert data["parameters"]["mask-height"]["defaultValue"] == 75.0

    def test_mask_position_x(self):
        data = _make_blur()
        br = BlurRegion(data)
        assert br.mask_position_x == 10.0
        br.mask_position_x = 30.0
        assert data["parameters"]["mask-positionX"]["defaultValue"] == 30.0

    def test_mask_position_y(self):
        data = _make_blur()
        br = BlurRegion(data)
        assert br.mask_position_y == 20.0
        br.mask_position_y = 40.0
        assert data["parameters"]["mask-positionY"]["defaultValue"] == 40.0


# ------------------------------------------------------------------
# Mask.animate_to
# ------------------------------------------------------------------


class TestMaskAnimateTo:
    def test_appends_keyframes(self):
        data = _make_mask()
        mask = Mask(data)
        mask.animate_to(1.0, 50.0, 60.0, 300.0, 150.0)

        expected_ticks = round(1.0 * EDIT_RATE)
        params = data["parameters"]
        for key, expected_val in (
            ("mask-positionX", 50.0),
            ("mask-positionY", 60.0),
            ("mask-width", 300.0),
            ("mask-height", 150.0),
        ):
            kf = params[key]["keyframes"]
            assert len(kf) == 1
            assert kf[0] == {"time": expected_ticks, "value": expected_val, "interp": "linr"}

    def test_multiple_keyframes(self):
        data = _make_mask()
        mask = Mask(data)
        mask.animate_to(0.0, 0.0, 0.0, 100.0, 100.0)
        mask.animate_to(2.0, 50.0, 50.0, 200.0, 200.0)

        kf = data["parameters"]["mask-width"]["keyframes"]
        assert len(kf) == 2
        assert kf[0]["value"] == 100.0
        assert kf[1]["value"] == 200.0
        assert kf[1]["time"] == round(2.0 * EDIT_RATE)

    def test_converts_scalar_to_keyframed(self):
        """animate_to on a param that was a plain scalar promotes it to a dict."""
        data = {
            "effectName": "Mask",
            "parameters": {
                "mask-positionX": 5.0,
                "mask-positionY": 10.0,
                "mask-width": 100.0,
                "mask-height": 50.0,
            },
        }
        mask = Mask(data)
        mask.animate_to(0.5, 20.0, 30.0, 150.0, 80.0)

        entry = data["parameters"]["mask-positionX"]
        assert isinstance(entry, dict)
        assert entry["defaultValue"] == 5.0
        assert len(entry["keyframes"]) == 1
        assert entry["keyframes"][0]["value"] == 20.0

    def test_creates_missing_params(self):
        """animate_to creates parameter entries when they don't exist."""
        data = {"effectName": "Mask", "parameters": {}}
        mask = Mask(data)
        mask.animate_to(1.0, 10.0, 20.0, 30.0, 40.0)

        for key in ("mask-positionX", "mask-positionY", "mask-width", "mask-height"):
            assert key in data["parameters"]
            assert len(data["parameters"][key]["keyframes"]) == 1
