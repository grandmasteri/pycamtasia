"""Tests for transform helpers consolidated in BaseClip."""
from __future__ import annotations

import math

from camtasia.timeline.clips import IMFile, ScreenVMFile, VMFile


def _vmfile_dict(**overrides) -> dict:
    d = {
        "id": 1, "_type": "VMFile", "src": 1,
        "start": 0, "duration": 705600000, "mediaStart": 0,
        "mediaDuration": 705600000, "scalar": 1,
    }
    d.update(overrides)
    return d


def _imfile_dict(**overrides) -> dict:
    d = {
        "id": 2, "_type": "IMFile", "src": 2,
        "start": 0, "duration": 705600000, "mediaStart": 0,
        "mediaDuration": 1, "scalar": 1,
        "parameters": {
            "translation0": {"type": "double", "defaultValue": 10.0, "interp": "eioe"},
            "translation1": {"type": "double", "defaultValue": 20.0, "interp": "eioe"},
            "scale0": {"type": "double", "defaultValue": 0.75, "interp": "eioe"},
            "scale1": {"type": "double", "defaultValue": 0.75, "interp": "eioe"},
        },
    }
    d.update(overrides)
    return d


def _screen_vmfile_dict(**overrides) -> dict:
    d = {
        "id": 3, "_type": "ScreenVMFile", "src": 3,
        "start": 0, "duration": 705600000, "mediaStart": 0,
        "mediaDuration": 705600000, "scalar": 1,
        "parameters": {
            "translation0": 100.0,
            "translation1": 200.0,
        },
    }
    d.update(overrides)
    return d


# -- VMFile inherits move_to / scale_to from BaseClip --

def test_vmfile_move_to() -> None:
    clip = VMFile(_vmfile_dict())
    clip.move_to(50.0, 75.0)
    assert clip.translation == (50.0, 75.0)


def test_vmfile_scale_to() -> None:
    clip = VMFile(_vmfile_dict())
    clip.scale_to(2.0)
    assert clip.scale == (2.0, 2.0)


def test_vmfile_rotation() -> None:
    clip = VMFile(_vmfile_dict())
    clip.rotation = math.pi / 4
    assert clip.rotation == math.pi / 4


# -- IMFile still works via inheritance --

def test_imfile_move_to() -> None:
    clip = IMFile(_imfile_dict())
    clip.move_to(99.0, 88.0)
    assert clip.translation == (99.0, 88.0)


def test_imfile_scale_to() -> None:
    clip = IMFile(_imfile_dict())
    clip.scale_to(0.5)
    assert clip.scale == (0.5, 0.5)


# -- ScreenVMFile translation still works via inheritance --

def test_screen_vmfile_translation_inherited() -> None:
    clip = ScreenVMFile(_screen_vmfile_dict())
    assert clip.translation == (100.0, 200.0)


# -- _get_param_value reads both scalar and dict formats --

def test_get_param_value_reads_scalar() -> None:
    clip = VMFile(_vmfile_dict(parameters={"translation0": 42.0}))
    assert clip._get_param_value("translation0") == 42.0


def test_get_param_value_reads_dict() -> None:
    clip = VMFile(_vmfile_dict(parameters={
        "translation0": {"type": "double", "defaultValue": 55.0},
    }))
    assert clip._get_param_value("translation0") == 55.0


def test_get_param_value_returns_default_when_absent() -> None:
    clip = VMFile(_vmfile_dict())
    assert clip._get_param_value("nonexistent", 7.0) == 7.0


# -- _set_param_value writes compact scalar for new params --

def test_set_param_value_writes_compact_scalar() -> None:
    data = _vmfile_dict()
    clip = VMFile(data)
    clip._set_param_value("translation0", 123.0)
    assert data["parameters"]["translation0"] == 123.0


# -- _set_param_value updates defaultValue for existing dict params --

def test_set_param_value_updates_default_value_for_dict() -> None:
    data = _imfile_dict()
    clip = IMFile(data)
    clip._set_param_value("translation0", 999.0)
    assert data["parameters"]["translation0"]["defaultValue"] == 999.0
    # dict structure preserved
    assert "type" in data["parameters"]["translation0"]


# -- crop sets geometry crop values --

def test_crop_sets_values() -> None:
    clip = VMFile(_vmfile_dict())
    clip.crop(left=0.1, top=0.2, right=0.3, bottom=0.4)
    assert clip._get_param_value("geometryCrop0") == 0.1
    assert clip._get_param_value("geometryCrop1") == 0.2
    assert clip._get_param_value("geometryCrop2") == 0.3
    assert clip._get_param_value("geometryCrop3") == 0.4


# -- chaining works --

def test_move_to_returns_self() -> None:
    clip = VMFile(_vmfile_dict())
    result = clip.move_to(1, 2)
    assert result is clip


def test_scale_to_returns_self() -> None:
    clip = VMFile(_vmfile_dict())
    result = clip.scale_to(1.5)
    assert result is clip


def test_scale_to_xy_returns_self() -> None:
    clip = VMFile(_vmfile_dict())
    result = clip.scale_to_xy(1.0, 2.0)
    assert result is clip
    assert clip.scale == (1.0, 2.0)


def test_crop_returns_self() -> None:
    clip = VMFile(_vmfile_dict())
    result = clip.crop(left=0.1)
    assert result is clip


def test_chaining_multiple_calls() -> None:
    clip = VMFile(_vmfile_dict())
    clip.move_to(10, 20).scale_to(2.0).crop(left=0.1)
    assert clip.translation == (10.0, 20.0)
    assert clip.scale == (2.0, 2.0)
    assert clip._get_param_value("geometryCrop0") == 0.1
