"""Tests for advanced visual effects: gesture, hotspot, zoom, device frame, freeze."""
from __future__ import annotations

import pytest

from camtasia.effects.base import effect_from_dict
from camtasia.effects.visual import (
    DeviceFrame,
    FreezeRegion,
    GesturePinch,
    GestureSwipe,
    GestureTap,
    Hotspot,
    ZoomNPan,
)


def _param(value: object, type_: str = "double", interp: str = "linr") -> dict:
    return {"type": type_, "defaultValue": value, "interp": interp}


def _make(name: str, params: dict) -> dict:
    return {
        "effectName": name,
        "bypassed": False,
        "category": "categoryVisualEffects",
        "parameters": {k: _param(v) for k, v in params.items()},
    }


# ------------------------------------------------------------------
# effect_from_dict dispatch
# ------------------------------------------------------------------

@pytest.mark.parametrize(
    ("effect_name", "expected_class"),
    [
        ("GestureTap", GestureTap),
        ("GestureSwipe", GestureSwipe),
        ("GesturePinch", GesturePinch),
        ("Hotspot", Hotspot),
        ("ZoomNPan", ZoomNPan),
        ("DeviceFrame", DeviceFrame),
        ("FreezeRegion", FreezeRegion),
    ],
)
def test_effect_from_dict_dispatches(effect_name: str, expected_class: type) -> None:
    data = {"effectName": effect_name, "parameters": {}}
    assert type(effect_from_dict(data)) is expected_class


# ------------------------------------------------------------------
# GestureTap
# ------------------------------------------------------------------

class TestGestureTap:
    def test_read_write(self) -> None:
        data = _make("GestureTap", {"positionX": 100.0, "positionY": 200.0, "duration": 0.5})
        tap = GestureTap(data)
        assert tap.position == (100.0, 200.0)
        assert tap.duration == 0.5
        tap.position = (300.0, 400.0)
        tap.duration = 1.0
        assert data["parameters"]["positionX"]["defaultValue"] == 300.0
        assert data["parameters"]["positionY"]["defaultValue"] == 400.0
        assert data["parameters"]["duration"]["defaultValue"] == 1.0


# ------------------------------------------------------------------
# GestureSwipe
# ------------------------------------------------------------------

class TestGestureSwipe:
    def test_read_write(self) -> None:
        data = _make("GestureSwipe", {
            "startPositionX": 0.0, "startPositionY": 0.0,
            "endPositionX": 100.0, "endPositionY": 200.0,
            "duration": 0.3,
        })
        swipe = GestureSwipe(data)
        assert swipe.start_position == (0.0, 0.0)
        assert swipe.end_position == (100.0, 200.0)
        assert swipe.duration == 0.3
        swipe.start_position = (10.0, 20.0)
        swipe.end_position = (300.0, 400.0)
        swipe.duration = 0.8
        assert data["parameters"]["startPositionX"]["defaultValue"] == 10.0
        assert data["parameters"]["startPositionY"]["defaultValue"] == 20.0
        assert data["parameters"]["endPositionX"]["defaultValue"] == 300.0
        assert data["parameters"]["endPositionY"]["defaultValue"] == 400.0
        assert data["parameters"]["duration"]["defaultValue"] == 0.8


# ------------------------------------------------------------------
# GesturePinch
# ------------------------------------------------------------------

class TestGesturePinch:
    def test_read_write(self) -> None:
        data = _make("GesturePinch", {
            "centerX": 50.0, "centerY": 50.0,
            "startScale": 1.0, "endScale": 2.0,
            "duration": 0.5,
        })
        pinch = GesturePinch(data)
        assert pinch.center == (50.0, 50.0)
        assert pinch.start_scale == 1.0
        assert pinch.end_scale == 2.0
        assert pinch.duration == 0.5
        pinch.center = (75.0, 25.0)
        pinch.start_scale = 0.5
        pinch.end_scale = 3.0
        pinch.duration = 1.0
        assert data["parameters"]["centerX"]["defaultValue"] == 75.0
        assert data["parameters"]["centerY"]["defaultValue"] == 25.0
        assert data["parameters"]["startScale"]["defaultValue"] == 0.5
        assert data["parameters"]["endScale"]["defaultValue"] == 3.0
        assert data["parameters"]["duration"]["defaultValue"] == 1.0


# ------------------------------------------------------------------
# Hotspot
# ------------------------------------------------------------------

class TestHotspot:
    def test_read_write(self) -> None:
        data = _make("Hotspot", {
            "url": "https://example.com",
            "action": "openURL",
            "pause": 1.0,
            "javascript": "alert('hi')",
        })
        hs = Hotspot(data)
        assert hs.url == "https://example.com"
        assert hs.action == "openURL"
        assert hs.pause is True
        assert hs.javascript == "alert('hi')"
        hs.url = "https://other.com"
        hs.action = "goToTime"
        hs.pause = False
        hs.javascript = ""
        assert data["parameters"]["url"]["defaultValue"] == "https://other.com"
        assert data["parameters"]["action"]["defaultValue"] == "goToTime"
        assert data["parameters"]["pause"]["defaultValue"] == 0.0
        assert data["parameters"]["javascript"]["defaultValue"] == ""


# ------------------------------------------------------------------
# ZoomNPan
# ------------------------------------------------------------------

class TestZoomNPan:
    def test_read_write(self) -> None:
        data = _make("ZoomNPan", {"scale": 1.5, "positionX": 0.25, "positionY": 0.75})
        znp = ZoomNPan(data)
        assert znp.scale == 1.5
        assert znp.position_x == 0.25
        assert znp.position_y == 0.75
        znp.scale = 2.0
        znp.position_x = 0.5
        znp.position_y = 0.5
        assert data["parameters"]["scale"]["defaultValue"] == 2.0
        assert data["parameters"]["positionX"]["defaultValue"] == 0.5
        assert data["parameters"]["positionY"]["defaultValue"] == 0.5


# ------------------------------------------------------------------
# DeviceFrame (effect, distinct from builders/device_frame.py)
# ------------------------------------------------------------------

class TestDeviceFrame:
    def test_read_write(self) -> None:
        data = _make("DeviceFrame", {"frameType": "phone", "frameId": "iphone-14"})
        df = DeviceFrame(data)
        assert df.frame_type == "phone"
        assert df.frame_id == "iphone-14"
        df.frame_type = "tablet"
        df.frame_id = "ipad-pro"
        assert data["parameters"]["frameType"]["defaultValue"] == "tablet"
        assert data["parameters"]["frameId"]["defaultValue"] == "ipad-pro"


# ------------------------------------------------------------------
# FreezeRegion
# ------------------------------------------------------------------

class TestFreezeRegion:
    def test_read_write(self) -> None:
        data = _make("FreezeRegion", {
            "positionX": 10.0, "positionY": 20.0,
            "width": 200.0, "height": 100.0,
        })
        fr = FreezeRegion(data)
        assert fr.position_x == 10.0
        assert fr.position_y == 20.0
        assert fr.width == 200.0
        assert fr.height == 100.0
        fr.position_x = 50.0
        fr.position_y = 60.0
        fr.width = 400.0
        fr.height = 300.0
        assert data["parameters"]["positionX"]["defaultValue"] == 50.0
        assert data["parameters"]["positionY"]["defaultValue"] == 60.0
        assert data["parameters"]["width"]["defaultValue"] == 400.0
        assert data["parameters"]["height"]["defaultValue"] == 300.0


# ------------------------------------------------------------------
# Serialization round-trip: effect_from_dict → data preserved
# ------------------------------------------------------------------

class TestSerializationRoundTrip:
    @pytest.mark.parametrize("effect_name", [
        "GestureTap", "GestureSwipe", "GesturePinch",
        "Hotspot", "ZoomNPan", "DeviceFrame", "FreezeRegion",
    ])
    def test_data_identity(self, effect_name: str) -> None:
        data = {"effectName": effect_name, "parameters": {}}
        actual = effect_from_dict(data)
        assert actual.data is data
