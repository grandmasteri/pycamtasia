"""Tests for camtasia.timeline.clips.image — IMFile clip type."""
from __future__ import annotations

from camtasia.timeline.clips import IMFile
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


def _imfile_dict(**overrides) -> dict:
    d = _base_clip_dict(
        _type="IMFile",
        id=33,
        src=6,
        start=5092080000,
        duration=26248320000,
        mediaDuration=1,
        parameters={
            "translation0": {"type": "double", "defaultValue": 10.0, "interp": "eioe"},
            "translation1": {"type": "double", "defaultValue": 20.0, "interp": "eioe"},
            "scale0": {"type": "double", "defaultValue": 0.75, "interp": "eioe"},
            "scale1": {"type": "double", "defaultValue": 0.75, "interp": "eioe"},
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
# IMFile properties
# ------------------------------------------------------------------

def test_imfile_translation() -> None:
    clip = IMFile(_imfile_dict())
    assert clip.translation == (10.0, 20.0)


def test_imfile_scale() -> None:
    clip = IMFile(_imfile_dict())
    assert clip.scale == (0.75, 0.75)


def test_imfile_translation_setter_mutates_dict() -> None:
    data = _imfile_dict()
    clip = IMFile(data)
    clip.translation = (50.0, 60.0)
    assert data["parameters"]["translation0"]["defaultValue"] == 50.0
    assert data["parameters"]["translation1"]["defaultValue"] == 60.0


def test_imfile_scale_default_when_absent() -> None:
    data = _base_clip_dict(_type="IMFile")
    clip = IMFile(data)
    assert clip.scale == (1.0, 1.0)


def test_imfile_translation_default_when_absent() -> None:
    data = _base_clip_dict(_type="IMFile")
    clip = IMFile(data)
    assert clip.translation == (0.0, 0.0)


# ------------------------------------------------------------------
# IMFile: _set_param_value, scale setter, geometry_crop, move_to, etc.
# ------------------------------------------------------------------

class TestIMFileCoverage:
    def test_set_param_value_creates_new_param(self):
        data = _base(_type="IMFile")
        clip = IMFile(data)
        clip.translation = (100.0, 200.0)
        assert data["parameters"]["translation0"] == 100.0
        assert data["parameters"]["translation1"] == 200.0

    def test_scale_setter(self):
        data = _base(_type="IMFile", parameters={
            "scale0": {"type": "double", "defaultValue": 1.0, "interp": "eioe"},
            "scale1": {"type": "double", "defaultValue": 1.0, "interp": "eioe"},
        })
        clip = IMFile(data)
        clip.scale = (2.0, 3.0)
        assert data["parameters"]["scale0"]["defaultValue"] == 2.0
        assert data["parameters"]["scale1"]["defaultValue"] == 3.0

    def test_geometry_crop_with_params(self):
        data = _base(_type="IMFile", parameters={
            "geometryCrop0": {"type": "double", "defaultValue": 0.1, "interp": "eioe"},
            "geometryCrop1": {"type": "double", "defaultValue": 0.2, "interp": "eioe"},
            "geometryCrop2": {"type": "double", "defaultValue": 0.3, "interp": "eioe"},
            "geometryCrop3": {"type": "double", "defaultValue": 0.4, "interp": "eioe"},
        })
        clip = IMFile(data)
        actual_crop = clip.geometry_crop
        assert actual_crop == {"0": 0.1, "1": 0.2, "2": 0.3, "3": 0.4}

    def test_geometry_crop_empty_when_absent(self):
        clip = IMFile(_base(_type="IMFile"))
        assert clip.geometry_crop == {}

    def test_move_to(self):
        data = _base(_type="IMFile")
        clip = IMFile(data)
        actual_result = clip.move_to(50.0, 75.0)
        assert actual_result is clip
        assert clip.translation == (50.0, 75.0)

    def test_scale_to(self):
        data = _base(_type="IMFile")
        clip = IMFile(data)
        actual_result = clip.scale_to(2.0)
        assert actual_result is clip
        assert clip.scale == (2.0, 2.0)

    def test_scale_to_xy(self):
        data = _base(_type="IMFile")
        clip = IMFile(data)
        actual_result = clip.scale_to_xy(1.5, 2.5)
        assert actual_result is clip
        assert clip.scale == (1.5, 2.5)

    def test_crop(self):
        data = _base(_type="IMFile")
        clip = IMFile(data)
        actual_result = clip.crop(left=0.1, top=0.2, right=0.3, bottom=0.4)
        assert actual_result is clip
        actual_crop = clip.geometry_crop
        assert actual_crop == {"0": 0.1, "1": 0.2, "2": 0.3, "3": 0.4}

    def test_get_param_value_raw_numeric(self):
        data = _base(_type="IMFile", parameters={"translation0": 42.0})
        clip = IMFile(data)
        assert clip.translation == (42.0, 0.0)
