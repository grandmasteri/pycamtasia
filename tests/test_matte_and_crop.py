"""Tests for MediaMatte.mode setter with enum, Crop effect, crop_to_aspect, fit_to_canvas."""
from __future__ import annotations

import pytest

from camtasia.effects.base import effect_from_dict
from camtasia.effects.visual import Crop, MediaMatte
from camtasia.types import MatteMode


def _param(value, type_: str = "double", interp: str = "linr") -> dict:
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


def _make_crop(left: float = 0.0, right: float = 0.0, top: float = 0.0, bottom: float = 0.0) -> dict:
    return {
        "effectName": "Crop",
        "bypassed": False,
        "category": "categoryVisualEffects",
        "parameters": {
            "left": _param(left),
            "right": _param(right),
            "top": _param(top),
            "bottom": _param(bottom),
        },
    }


# ------------------------------------------------------------------
# MediaMatte mode setter
# ------------------------------------------------------------------


class TestMediaMatteModeSetter:
    def test_set_mode_with_int(self):
        matte = MediaMatte(_make_matte(1))
        matte.mode = 3
        assert matte.mode == 3

    def test_set_mode_with_matte_mode_enum(self):
        matte = MediaMatte(_make_matte(1))
        matte.mode = MatteMode.LUMINOSITY_INVERT
        assert matte.mode == 4

    @pytest.mark.parametrize(
        ("enum_val", "expected_int"),
        [
            (MatteMode.ALPHA, 1),
            (MatteMode.ALPHA_INVERT, 2),
            (MatteMode.LUMINOSITY, 3),
            (MatteMode.LUMINOSITY_INVERT, 4),
        ],
    )
    def test_set_mode_all_enum_values(self, enum_val: MatteMode, expected_int: int):
        matte = MediaMatte(_make_matte(1))
        matte.mode = enum_val
        assert matte.mode == expected_int

    def test_mode_round_trip_preserves_int(self):
        data = _make_matte(2)
        matte = MediaMatte(data)
        assert matte.mode == 2
        matte.mode = MatteMode.ALPHA
        assert data["parameters"]["matteMode"]["defaultValue"] == 1


# ------------------------------------------------------------------
# Crop effect
# ------------------------------------------------------------------


class TestCropEffect:
    def test_read_properties(self):
        crop = Crop(_make_crop(0.1, 0.2, 0.3, 0.4))
        assert crop.left == pytest.approx(0.1)
        assert crop.right == pytest.approx(0.2)
        assert crop.top == pytest.approx(0.3)
        assert crop.bottom == pytest.approx(0.4)

    def test_write_properties(self):
        data = _make_crop()
        crop = Crop(data)
        crop.left = 0.15
        crop.right = 0.25
        crop.top = 0.35
        crop.bottom = 0.45
        assert data["parameters"]["left"]["defaultValue"] == 0.15
        assert data["parameters"]["right"]["defaultValue"] == 0.25
        assert data["parameters"]["top"]["defaultValue"] == 0.35
        assert data["parameters"]["bottom"]["defaultValue"] == 0.45

    def test_effect_from_dict_dispatches_crop(self):
        data = {"effectName": "Crop", "parameters": {}}
        assert type(effect_from_dict(data)) is Crop

    def test_name(self):
        crop = Crop(_make_crop())
        assert crop.name == "Crop"


# ------------------------------------------------------------------
# BaseClip.crop_to_aspect
# ------------------------------------------------------------------


def _make_clip_data(**overrides) -> dict:
    """Minimal clip data dict for BaseClip."""
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


class TestCropToAspect:
    def test_wide_aspect_crops_top_bottom(self):
        from camtasia.timeline.clips.base import BaseClip
        clip = BaseClip(_make_clip_data())
        clip.crop_to_aspect(16 / 9)
        effects = clip._data["effects"]
        assert len(effects) == 1
        assert effects[0]["effectName"] == "Crop"
        crop = Crop(effects[0])
        assert crop.left == pytest.approx(0.0)
        assert crop.right == pytest.approx(0.0)
        assert crop.top == pytest.approx((1.0 - 9 / 16) / 2)
        assert crop.bottom == pytest.approx((1.0 - 9 / 16) / 2)

    def test_tall_aspect_crops_left_right(self):
        from camtasia.timeline.clips.base import BaseClip
        clip = BaseClip(_make_clip_data())
        clip.crop_to_aspect(9 / 16)
        effects = clip._data["effects"]
        crop = Crop(effects[0])
        assert crop.top == pytest.approx(0.0)
        assert crop.bottom == pytest.approx(0.0)
        assert crop.left == pytest.approx((1.0 - 9 / 16) / 2)
        assert crop.right == pytest.approx((1.0 - 9 / 16) / 2)

    def test_square_aspect_no_crop(self):
        from camtasia.timeline.clips.base import BaseClip
        clip = BaseClip(_make_clip_data())
        clip.crop_to_aspect(1.0)
        crop = Crop(clip._data["effects"][0])
        assert crop.left == pytest.approx(0.0)
        assert crop.right == pytest.approx(0.0)
        assert crop.top == pytest.approx(0.0)
        assert crop.bottom == pytest.approx(0.0)

    def test_invalid_aspect_raises(self):
        from camtasia.timeline.clips.base import BaseClip
        clip = BaseClip(_make_clip_data())
        with pytest.raises(ValueError, match="aspect_ratio must be > 0"):
            clip.crop_to_aspect(0)


# ------------------------------------------------------------------
# BaseClip.fit_to_canvas
# ------------------------------------------------------------------


class TestFitToCanvas:
    def test_center_resets_scale_and_translation(self):
        from camtasia.timeline.clips.base import BaseClip
        clip = BaseClip(_make_clip_data(parameters={"scale0": 2.0, "scale1": 2.0, "translation0": 100.0, "translation1": 50.0}))
        clip.fit_to_canvas("center")
        assert clip.scale == (1.0, 1.0)
        assert clip.translation == (0.0, 0.0)

    def test_cover_uses_max_scale(self):
        from camtasia.timeline.clips.base import BaseClip
        clip = BaseClip(_make_clip_data(parameters={"scale0": 0.5, "scale1": 0.8}))
        clip.fit_to_canvas("cover")
        assert clip.scale == (0.8, 0.8)
        assert clip.translation == (0.0, 0.0)

    def test_contain_uses_min_scale(self):
        from camtasia.timeline.clips.base import BaseClip
        clip = BaseClip(_make_clip_data(parameters={"scale0": 0.5, "scale1": 0.8}))
        clip.fit_to_canvas("contain")
        assert clip.scale == (0.5, 0.5)
        assert clip.translation == (0.0, 0.0)

    def test_invalid_mode_raises(self):
        from camtasia.timeline.clips.base import BaseClip
        clip = BaseClip(_make_clip_data())
        with pytest.raises(ValueError, match="mode must be one of"):
            clip.fit_to_canvas("stretch")

    def test_chaining(self):
        from camtasia.timeline.clips.base import BaseClip
        clip = BaseClip(_make_clip_data())
        result = clip.fit_to_canvas("center")
        assert result is clip
