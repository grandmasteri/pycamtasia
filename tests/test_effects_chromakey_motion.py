"""Tests for ChromaKey.hue, CornerPin derived properties, MotionPath, BackgroundRemoval."""
from __future__ import annotations

import pytest

from camtasia.effects.base import effect_from_dict
from camtasia.effects.visual import (
    BackgroundRemoval,
    ChromaKey,
    CornerPin,
    MotionPath,
)
from camtasia.timing import EDIT_RATE


def _param(value, type_: str = "double", interp: str = "linr") -> dict:
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
        ("MotionPath", MotionPath),
        ("BackgroundRemoval", BackgroundRemoval),
    ],
)
def test_effect_from_dict_dispatches(effect_name: str, expected_class: type) -> None:
    data = {"effectName": effect_name, "parameters": {}}
    assert type(effect_from_dict(data)) is expected_class


# ------------------------------------------------------------------
# ChromaKey.hue
# ------------------------------------------------------------------

class TestChromaKeyHue:
    def _make(self):
        return _make("ChromaKey", {
            "color-red": 0.0, "color-green": 1.0, "color-blue": 0.0,
            "color-alpha": 1.0, "tolerance": 0.3, "softness": 0.1,
            "defringe": 0.0, "hue": 120.0, "invert": 0,
        })

    def test_read(self):
        actual = ChromaKey(self._make())
        assert actual.hue == 120.0

    def test_write(self):
        data = self._make()
        actual = ChromaKey(data)
        actual.hue = 240.0
        assert data["parameters"]["hue"]["defaultValue"] == 240.0


# ------------------------------------------------------------------
# CornerPin derived properties
# ------------------------------------------------------------------

class TestCornerPinDerived:
    def _make(self, tl=(0.0, 0.0), tr=(1.0, 0.0), bl=(0.0, 1.0), br=(1.0, 1.0)):
        return _make("CornerPin", {
            "topLeftX": tl[0], "topLeftY": tl[1],
            "topRightX": tr[0], "topRightY": tr[1],
            "bottomLeftX": bl[0], "bottomLeftY": bl[1],
            "bottomRightX": br[0], "bottomRightY": br[1],
        })

    def test_position_centroid(self):
        actual = CornerPin(self._make())
        assert actual.position == (0.5, 0.5)

    def test_position_asymmetric(self):
        actual = CornerPin(self._make(
            tl=(0.1, 0.2), tr=(0.9, 0.2), bl=(0.1, 0.8), br=(0.9, 0.8),
        ))
        assert actual.position == pytest.approx((0.5, 0.5))

    def test_skew_zero_for_rectangle(self):
        actual = CornerPin(self._make())
        assert actual.skew == pytest.approx(0.0)

    def test_skew_nonzero(self):
        # Top edge shorter than bottom edge → negative skew
        actual = CornerPin(self._make(
            tl=(0.2, 0.0), tr=(0.8, 0.0), bl=(0.0, 1.0), br=(1.0, 1.0),
        ))
        assert actual.skew == pytest.approx(0.6 - 1.0)

    def test_rotation_zero_for_horizontal(self):
        actual = CornerPin(self._make())
        assert actual.rotation == pytest.approx(0.0)

    def test_rotation_45_degrees(self):
        actual = CornerPin(self._make(
            tl=(0.0, 0.0), tr=(1.0, 1.0), bl=(0.0, 1.0), br=(1.0, 1.0),
        ))
        assert actual.rotation == pytest.approx(45.0)

    def test_add_keyframe_valid(self):
        data = self._make()
        actual = CornerPin(data)
        actual.add_keyframe(1.0, 'topLeft', 0.1, 0.2)
        params = data["parameters"]
        assert params["topLeftX"]["keyframes"] == [
            {"time": int(1.0 * EDIT_RATE), "value": 0.1, "interp": "linr"},
        ]
        assert params["topLeftY"]["keyframes"] == [
            {"time": int(1.0 * EDIT_RATE), "value": 0.2, "interp": "linr"},
        ]

    def test_add_keyframe_invalid_corner(self):
        actual = CornerPin(self._make())
        with pytest.raises(ValueError, match="corner must be one of"):
            actual.add_keyframe(0.0, 'center', 0.5, 0.5)

    def test_add_multiple_keyframes(self):
        data = self._make()
        actual = CornerPin(data)
        actual.add_keyframe(0.0, 'bottomRight', 1.0, 1.0)
        actual.add_keyframe(2.0, 'bottomRight', 0.8, 0.9)
        kfs = data["parameters"]["bottomRightX"]["keyframes"]
        assert len(kfs) == 2
        assert kfs[1]["value"] == 0.8


# ------------------------------------------------------------------
# MotionPath
# ------------------------------------------------------------------

class TestMotionPath:
    def _make(self):
        return {
            "effectName": "MotionPath",
            "bypassed": False,
            "category": "categoryVisualEffects",
            "parameters": {
                "autoOrient": _param(1.0),
                "lineType": _param("curve"),
                "positionX": {
                    "type": "double", "defaultValue": 0.0, "interp": "linr",
                    "keyframes": [
                        {"time": 0, "value": 0.0, "interp": "linr"},
                        {"time": 100, "value": 0.5, "interp": "linr"},
                    ],
                },
                "positionY": {
                    "type": "double", "defaultValue": 0.0, "interp": "linr",
                    "keyframes": [
                        {"time": 0, "value": 0.0, "interp": "linr"},
                        {"time": 100, "value": 0.8, "interp": "linr"},
                    ],
                },
            },
        }

    def test_auto_orient_read(self):
        actual = MotionPath(self._make())
        assert actual.auto_orient is True

    def test_auto_orient_write(self):
        data = self._make()
        actual = MotionPath(data)
        actual.auto_orient = False
        assert data["parameters"]["autoOrient"]["defaultValue"] == 0.0

    def test_line_type_read(self):
        actual = MotionPath(self._make())
        assert actual.line_type == "curve"

    def test_line_type_write(self):
        data = self._make()
        actual = MotionPath(data)
        actual.line_type = "angle"
        assert data["parameters"]["lineType"]["defaultValue"] == "angle"

    def test_keyframes(self):
        actual = MotionPath(self._make())
        expected = [
            {"time": 0, "x": 0.0, "y": 0.0},
            {"time": 100, "x": 0.5, "y": 0.8},
        ]
        assert actual.keyframes == expected

    def test_keyframes_empty(self):
        data = _make("MotionPath", {"autoOrient": 0.0, "lineType": "angle"})
        actual = MotionPath(data)
        assert actual.keyframes == []


# ------------------------------------------------------------------
# BackgroundRemoval
# ------------------------------------------------------------------

class TestBackgroundRemoval:
    def _make(self):
        return _make("BackgroundRemoval", {
            "intensity": 0.8, "edgeSoftness": 0.3, "invert": 0.0,
        })

    def test_read(self):
        actual = BackgroundRemoval(self._make())
        assert actual.intensity == 0.8
        assert actual.edge_softness == 0.3
        assert actual.invert is False

    def test_write(self):
        data = self._make()
        actual = BackgroundRemoval(data)
        actual.intensity = 0.5
        actual.edge_softness = 0.7
        actual.invert = True
        assert data["parameters"]["intensity"]["defaultValue"] == 0.5
        assert data["parameters"]["edgeSoftness"]["defaultValue"] == 0.7
        assert data["parameters"]["invert"]["defaultValue"] == 1.0


# ------------------------------------------------------------------
# Serialization round-trip
# ------------------------------------------------------------------

class TestSerializationRoundTrip:
    @pytest.mark.parametrize("effect_name", ["MotionPath", "BackgroundRemoval"])
    def test_data_identity(self, effect_name: str):
        data = {"effectName": effect_name, "parameters": {}}
        actual = effect_from_dict(data)
        assert actual.data is data
