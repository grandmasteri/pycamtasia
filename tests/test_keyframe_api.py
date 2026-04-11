"""Tests for the keyframe animation API on BaseClip."""
from __future__ import annotations

from camtasia.timeline.clips import VMFile
from camtasia.timing import seconds_to_ticks


def _vmfile_dict(**overrides) -> dict:
    d = {
        "id": 1, "_type": "VMFile", "src": 1,
        "start": 0, "duration": 705600000, "mediaStart": 0,
        "mediaDuration": 705600000, "scalar": 1,
    }
    d.update(overrides)
    return d


# -- add_keyframe creates parameter with keyframes array --

def test_add_keyframe_creates_parameter() -> None:
    clip = VMFile(_vmfile_dict())
    clip.add_keyframe("scale0", 0.0, 1.0)
    param = clip.parameters["scale0"]
    assert param["type"] == "double"
    assert param["defaultValue"] == 0.0
    kf = param["keyframes"]
    assert [(k["time"], k["value"], k["interp"]) for k in kf] == [(0, 1.0, "eioe")]


# -- add_keyframe appends to existing keyframes --

def test_add_keyframe_appends_to_existing() -> None:
    clip = VMFile(_vmfile_dict())
    clip.add_keyframe("scale0", 0.0, 1.0)
    clip.add_keyframe("scale0", 1.0, 2.0)
    assert [kf["value"] for kf in clip.parameters["scale0"]["keyframes"]] == [1.0, 2.0]


# -- add_keyframe preserves existing scalar as defaultValue --

def test_add_keyframe_preserves_scalar_as_default() -> None:
    data = _vmfile_dict(parameters={"scale0": 1.5})
    clip = VMFile(data)
    clip.add_keyframe("scale0", 0.5, 2.0)
    param = clip.parameters["scale0"]
    assert param["defaultValue"] == 1.5
    assert [kf["value"] for kf in param["keyframes"]] == [2.0]


# -- add_keyframe returns self (chaining) --

def test_add_keyframe_returns_self() -> None:
    clip = VMFile(_vmfile_dict())
    result = clip.add_keyframe("scale0", 0.0, 1.0)
    assert result is clip


# -- add_keyframe with duration --

def test_add_keyframe_with_duration() -> None:
    clip = VMFile(_vmfile_dict())
    clip.add_keyframe("opacity", 0.0, 1.0, duration_seconds=0.5)
    kf = clip.parameters["opacity"]["keyframes"][0]
    expected_dur = seconds_to_ticks(0.5)
    assert kf["duration"] == expected_dur
    assert kf["endTime"] == expected_dur  # time=0 + dur


# -- clear_keyframes removes from specific parameter --

def test_clear_keyframes_specific_parameter() -> None:
    clip = VMFile(_vmfile_dict())
    clip.add_keyframe("scale0", 0.0, 1.0)
    clip.add_keyframe("scale1", 0.0, 1.0)
    clip.clear_keyframes("scale0")
    assert "keyframes" not in clip.parameters["scale0"]
    assert "keyframes" in clip.parameters["scale1"]


# -- clear_keyframes(None) removes from all parameters --

def test_clear_keyframes_all() -> None:
    clip = VMFile(_vmfile_dict())
    clip.add_keyframe("scale0", 0.0, 1.0)
    clip.add_keyframe("scale1", 0.0, 1.0)
    clip.clear_keyframes(None)
    assert "keyframes" not in clip.parameters["scale0"]
    assert "keyframes" not in clip.parameters["scale1"]


# -- clear_keyframes on scalar param is no-op --

def test_clear_keyframes_scalar_noop() -> None:
    data = _vmfile_dict(parameters={"scale0": 1.5})
    clip = VMFile(data)
    clip.clear_keyframes("scale0")
    assert clip.parameters["scale0"] == 1.5


# -- clear_keyframes returns self --

def test_clear_keyframes_returns_self() -> None:
    clip = VMFile(_vmfile_dict())
    result = clip.clear_keyframes("scale0")
    assert result is clip
