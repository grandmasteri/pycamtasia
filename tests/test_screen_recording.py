"""Tests for camtasia.timeline.clips.screen_recording — ScreenVMFile, ScreenIMFile."""
from __future__ import annotations

import pytest

from camtasia.timeline.clips import ScreenIMFile, ScreenVMFile
from camtasia.timing import EDIT_RATE


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _base_clip_dict(**overrides) -> dict:
    base = {
        "id": 14,
        "_type": "AMFile",
        "src": 3,
        "start": 0,
        "duration": 106051680000,
        "mediaStart": 0,
        "mediaDuration": 113484000000,
        "scalar": 1,
    }
    base.update(overrides)
    return base


def _screen_vmfile_dict(**overrides) -> dict:
    d = _base_clip_dict(
        _type="ScreenVMFile",
        id=50,
        src=2,
        scalar="51/101",
        parameters={
            "cursorScale": {"type": "double", "defaultValue": 5.0, "interp": "linr"},
            "cursorOpacity": {"type": "double", "defaultValue": 0.8, "interp": "linr"},
        },
    )
    d.update(overrides)
    return d


def _base(**kw) -> dict:
    d = {
        "id": 1, "_type": "AMFile", "src": 1,
        "start": 0, "duration": EDIT_RATE * 10,
        "mediaStart": 0, "mediaDuration": EDIT_RATE * 10, "scalar": 1,
    }
    d.update(kw)
    return d


# ------------------------------------------------------------------
# ScreenVMFile basic properties
# ------------------------------------------------------------------

def test_screen_vmfile_cursor_scale() -> None:
    clip = ScreenVMFile(_screen_vmfile_dict())
    assert clip.cursor_scale == 5.0


def test_screen_vmfile_cursor_opacity() -> None:
    clip = ScreenVMFile(_screen_vmfile_dict())
    assert clip.cursor_opacity == 0.8


def test_screen_vmfile_cursor_scale_setter_mutates_dict() -> None:
    data = _screen_vmfile_dict()
    clip = ScreenVMFile(data)
    clip.cursor_scale = 3.0
    assert data["parameters"]["cursorScale"]["defaultValue"] == 3.0


def test_screen_vmfile_cursor_scale_default() -> None:
    data = _base_clip_dict(_type="ScreenVMFile")
    clip = ScreenVMFile(data)
    assert clip.cursor_scale == 5.0


def test_screen_vmfile_cursor_opacity_default() -> None:
    data = _base_clip_dict(_type="ScreenVMFile")
    clip = ScreenVMFile(data)
    assert clip.cursor_opacity == 1.0


# ------------------------------------------------------------------
# ScreenVMFile: translation, scale, cursor setters, cursor effects
# ------------------------------------------------------------------

class TestScreenVMFileCoverage:
    def _make(self, **kw):
        params = {
            "translation0": {"type": "double", "defaultValue": 2.0, "interp": "eioe"},
            "translation1": {"type": "double", "defaultValue": -4.0, "interp": "eioe"},
            "scale0": {"type": "double", "defaultValue": 0.75, "interp": "eioe"},
            "scale1": {"type": "double", "defaultValue": 0.75, "interp": "eioe"},
            "cursorScale": {"type": "double", "defaultValue": 5.0, "interp": "linr"},
            "cursorOpacity": {"type": "double", "defaultValue": 1.0, "interp": "linr"},
            "cursorTrackLevel": {"type": "double", "defaultValue": 0.5, "interp": "linr"},
            "smoothCursorAcrossEditDuration": 0,
        }
        params.update(kw)
        return ScreenVMFile(_base(_type="ScreenVMFile", parameters=params))

    def test_translation(self):
        clip = self._make()
        assert clip.translation == (2.0, -4.0)

    def test_translation_setter(self):
        data = _base(_type="ScreenVMFile", parameters={})
        clip = ScreenVMFile(data)
        clip.translation = (10.0, 20.0)
        assert data["parameters"]["translation0"] == 10.0
        assert data["parameters"]["translation1"] == 20.0

    def test_scale(self):
        clip = self._make()
        assert clip.scale == (0.75, 0.75)

    def test_scale_setter(self):
        data = _base(_type="ScreenVMFile", parameters={
            "scale0": {"type": "double", "defaultValue": 1.0, "interp": "eioe"},
            "scale1": {"type": "double", "defaultValue": 1.0, "interp": "eioe"},
        })
        clip = ScreenVMFile(data)
        clip.scale = (0.5, 0.5)
        assert data["parameters"]["scale0"]["defaultValue"] == 0.5

    def test_cursor_opacity_setter(self):
        data = _base(_type="ScreenVMFile", parameters={
            "cursorOpacity": {"type": "double", "defaultValue": 1.0, "interp": "linr"},
        })
        clip = ScreenVMFile(data)
        clip.cursor_opacity = 0.5
        assert data["parameters"]["cursorOpacity"]["defaultValue"] == 0.5

    def test_cursor_track_level(self):
        clip = self._make()
        assert clip.cursor_track_level == 0.5

    def test_smooth_cursor_across_edit_duration(self):
        clip = self._make()
        assert clip.smooth_cursor_across_edit_duration == 0

    def test_cursor_motion_blur_intensity_with_effect(self):
        data = _base(_type="ScreenVMFile", parameters={}, effects=[
            {"effectName": "CursorMotionBlur", "parameters": {
                "intensity": {"type": "double", "defaultValue": 1.0, "interp": "linr"},
            }},
        ])
        clip = ScreenVMFile(data)
        assert clip.cursor_motion_blur_intensity == 1.0

    @pytest.mark.parametrize("attr,expected", [
        ("cursor_motion_blur_intensity", 0.0),
        ("cursor_shadow", {}),
        ("cursor_physics", {}),
        ("left_click_scaling", {}),
    ])
    def test_cursor_effect_no_effect_defaults(self, attr, expected):
        clip = ScreenVMFile(_base(_type="ScreenVMFile"))
        assert getattr(clip, attr) == expected

    def test_cursor_shadow_with_effect(self):
        data = _base(_type="ScreenVMFile", parameters={}, effects=[
            {"effectName": "CursorShadow", "parameters": {
                "angle": {"type": "double", "defaultValue": 3.9, "interp": "linr"},
                "offset": 7.0,
            }},
        ])
        clip = ScreenVMFile(data)
        actual_shadow = clip.cursor_shadow
        assert actual_shadow["angle"] == 3.9
        assert actual_shadow["offset"] == 7.0


    def test_cursor_physics_with_effect(self):
        data = _base(_type="ScreenVMFile", parameters={}, effects=[
            {"effectName": "CursorPhysics", "parameters": {
                "intensity": {"type": "double", "defaultValue": 1.5, "interp": "linr"},
                "tilt": {"type": "double", "defaultValue": 2.5, "interp": "linr"},
            }},
        ])
        clip = ScreenVMFile(data)
        actual_physics = clip.cursor_physics
        assert actual_physics["intensity"] == 1.5
        assert actual_physics["tilt"] == 2.5


    def test_left_click_scaling_with_effect(self):
        data = _base(_type="ScreenVMFile", parameters={}, effects=[
            {"effectName": "LeftClickScaling", "parameters": {
                "scale": {"type": "double", "defaultValue": 3.5, "interp": "linr"},
                "speed": 7.5,
            }},
        ])
        clip = ScreenVMFile(data)
        actual_click = clip.left_click_scaling
        assert actual_click["scale"] == 3.5
        assert actual_click["speed"] == 7.5


    def test_get_param_value_raw_numeric(self):
        data = _base(_type="ScreenVMFile", parameters={"cursorScale": 3.0})
        clip = ScreenVMFile(data)
        assert clip.cursor_scale == 3.0

    def test_set_param_value_creates_new(self):
        data = _base(_type="ScreenVMFile", parameters={})
        clip = ScreenVMFile(data)
        clip.cursor_scale = 4.0
        assert data["parameters"]["cursorScale"]["defaultValue"] == 4.0
        assert data["parameters"]["cursorScale"]["interp"] == "linr"


class TestScreenVMFileEffectParamRawValue:
    def test_get_effect_param_raw_numeric(self):
        data = _base(_type="ScreenVMFile", parameters={}, effects=[
            {"effectName": "CursorMotionBlur", "parameters": {"intensity": 0.75}},
        ])
        clip = ScreenVMFile(data)
        assert clip.cursor_motion_blur_intensity == 0.75


# ------------------------------------------------------------------
# ScreenIMFile
# ------------------------------------------------------------------

class TestScreenIMFileCoverage:
    def test_cursor_image_path(self):
        data = _base(_type="ScreenIMFile", parameters={
            "cursorImagePath": "2b7b6af1/2",
        })
        clip = ScreenIMFile(data)
        assert clip.cursor_image_path == "2b7b6af1/2"

    def test_cursor_image_path_none(self):
        clip = ScreenIMFile(_base(_type="ScreenIMFile"))
        assert clip.cursor_image_path is None

    def test_cursor_location_keyframes(self):
        data = _base(_type="ScreenIMFile", parameters={
            "cursorLocation": {
                "type": "point",
                "keyframes": [
                    {"time": 0, "endTime": 100, "value": [10, 20, 0], "duration": 0},
                    {"time": 100, "endTime": 200, "value": [30, 40, 0], "duration": 0},
                ],
            },
        })
        clip = ScreenIMFile(data)
        actual_kf = clip.cursor_location_keyframes
        assert actual_kf[0]["value"] == [10, 20, 0]
        assert actual_kf[1]["value"] == [30, 40, 0]

    def test_cursor_location_keyframes_empty(self):
        clip = ScreenIMFile(_base(_type="ScreenIMFile"))
        assert clip.cursor_location_keyframes == []


class TestScreenIMFileSetSourceRaises:
    def test_set_source_raises_type_error(self):
        data = _base(_type="ScreenIMFile", parameters={}, effects=[])
        clip = ScreenIMFile(data)
        with pytest.raises(TypeError, match='Cannot change source on cursor overlay clips'):
            clip.set_source(1)
