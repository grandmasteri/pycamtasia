"""Tests for new visual effect classes added in visual.py."""
from __future__ import annotations

import pytest

from camtasia.effects.base import effect_from_dict
from camtasia.effects.visual import (
    Border,
    Colorize,
    ColorTint,
    CRTMonitor,
    Mosaic,
    OutlineEdges,
    Reflection,
    Sepia,
    StaticNoise,
    Tiling,
    TornEdge,
    Vignette,
    WindowSpotlight,
)


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
# effect_from_dict dispatch for all new effects
# ------------------------------------------------------------------

@pytest.mark.parametrize(
    ("effect_name", "expected_class"),
    [
        ("Sepia", Sepia),
        ("Vignette", Vignette),
        ("Reflection", Reflection),
        ("StaticNoise", StaticNoise),
        ("Tiling", Tiling),
        ("TornEdge", TornEdge),
        ("CRTMonitor", CRTMonitor),
        ("Mosaic", Mosaic),
        ("OutlineEdges", OutlineEdges),
        ("WindowSpotlight", WindowSpotlight),
        ("ColorTint", ColorTint),
        ("Border", Border),
        ("Colorize", Colorize),
    ],
)
def test_effect_from_dict_dispatches(effect_name: str, expected_class: type) -> None:
    data = {"effectName": effect_name, "parameters": {}}
    assert type(effect_from_dict(data)) is expected_class


# ------------------------------------------------------------------
# Sepia — no parameters, just registration
# ------------------------------------------------------------------

class TestSepia:
    def test_name(self):
        actual = Sepia({"effectName": "Sepia", "parameters": {}})
        assert actual.name == "Sepia"


# ------------------------------------------------------------------
# Vignette
# ------------------------------------------------------------------

class TestVignette:
    def _make(self):
        return _make("Vignette", {
            "amount": 0.5, "falloff": 0.3,
            "color-red": 0.0, "color-green": 0.0,
            "color-blue": 0.0, "color-alpha": 1.0,
        })

    def test_read(self):
        actual = Vignette(self._make())
        assert actual.amount == 0.5
        assert actual.falloff == 0.3
        assert actual.color == (0.0, 0.0, 0.0, 1.0)

    def test_write(self):
        data = self._make()
        actual = Vignette(data)
        actual.amount = 0.8
        actual.falloff = 0.6
        actual.color = (0.1, 0.2, 0.3, 0.9)
        assert data["parameters"]["amount"]["defaultValue"] == 0.8
        assert data["parameters"]["falloff"]["defaultValue"] == 0.6
        assert data["parameters"]["color-red"]["defaultValue"] == 0.1
        assert data["parameters"]["color-alpha"]["defaultValue"] == 0.9


# ------------------------------------------------------------------
# Reflection
# ------------------------------------------------------------------

class TestReflection:
    def _make(self):
        return _make("Reflection", {"opacity": 0.5, "distance": 10.0, "falloff": 0.3})

    def test_read(self):
        actual = Reflection(self._make())
        assert actual.opacity == 0.5
        assert actual.distance == 10.0
        assert actual.falloff == 0.3

    def test_write(self):
        data = self._make()
        actual = Reflection(data)
        actual.opacity = 0.8
        actual.distance = 20.0
        actual.falloff = 0.6
        assert data["parameters"]["opacity"]["defaultValue"] == 0.8
        assert data["parameters"]["distance"]["defaultValue"] == 20.0
        assert data["parameters"]["falloff"]["defaultValue"] == 0.6


# ------------------------------------------------------------------
# StaticNoise
# ------------------------------------------------------------------

class TestStaticNoise:
    def test_read_write(self):
        data = _make("StaticNoise", {"intensity": 0.4})
        actual = StaticNoise(data)
        assert actual.intensity == 0.4
        actual.intensity = 0.9
        assert data["parameters"]["intensity"]["defaultValue"] == 0.9


# ------------------------------------------------------------------
# Tiling
# ------------------------------------------------------------------

class TestTiling:
    def _make(self):
        return _make("Tiling", {
            "scale": 2.0, "positionX": 0.5, "positionY": 0.5, "opacity": 1.0,
        })

    def test_read(self):
        actual = Tiling(self._make())
        assert actual.scale == 2.0
        assert actual.position_x == 0.5
        assert actual.position_y == 0.5
        assert actual.opacity == 1.0

    def test_write(self):
        data = self._make()
        actual = Tiling(data)
        actual.scale = 3.0
        actual.position_x = 0.2
        actual.position_y = 0.8
        actual.opacity = 0.5
        assert data["parameters"]["scale"]["defaultValue"] == 3.0
        assert data["parameters"]["positionX"]["defaultValue"] == 0.2
        assert data["parameters"]["positionY"]["defaultValue"] == 0.8
        assert data["parameters"]["opacity"]["defaultValue"] == 0.5


# ------------------------------------------------------------------
# TornEdge
# ------------------------------------------------------------------

class TestTornEdge:
    def test_read_write(self):
        data = _make("TornEdge", {"jaggedness": 0.5, "margin": 10.0})
        actual = TornEdge(data)
        assert actual.jaggedness == 0.5
        assert actual.margin == 10.0
        actual.jaggedness = 0.8
        actual.margin = 20.0
        assert data["parameters"]["jaggedness"]["defaultValue"] == 0.8
        assert data["parameters"]["margin"]["defaultValue"] == 20.0


# ------------------------------------------------------------------
# CRTMonitor
# ------------------------------------------------------------------

class TestCRTMonitor:
    def test_read_write(self):
        data = _make("CRTMonitor", {"scanline": 0.5, "curvature": 0.3, "intensity": 0.7})
        actual = CRTMonitor(data)
        assert actual.scanline == 0.5
        assert actual.curvature == 0.3
        assert actual.intensity == 0.7
        actual.scanline = 0.8
        actual.curvature = 0.6
        actual.intensity = 1.0
        assert data["parameters"]["scanline"]["defaultValue"] == 0.8
        assert data["parameters"]["curvature"]["defaultValue"] == 0.6
        assert data["parameters"]["intensity"]["defaultValue"] == 1.0


# ------------------------------------------------------------------
# Mosaic
# ------------------------------------------------------------------

class TestMosaic:
    def test_read_write(self):
        data = _make("Mosaic", {"pixelSize": 8.0})
        actual = Mosaic(data)
        assert actual.pixel_size == 8.0
        actual.pixel_size = 16.0
        assert data["parameters"]["pixelSize"]["defaultValue"] == 16.0


# ------------------------------------------------------------------
# OutlineEdges
# ------------------------------------------------------------------

class TestOutlineEdges:
    def test_read_write(self):
        data = _make("OutlineEdges", {"threshold": 0.3, "intensity": 0.7})
        actual = OutlineEdges(data)
        assert actual.threshold == 0.3
        assert actual.intensity == 0.7
        actual.threshold = 0.5
        actual.intensity = 1.0
        assert data["parameters"]["threshold"]["defaultValue"] == 0.5
        assert data["parameters"]["intensity"]["defaultValue"] == 1.0


# ------------------------------------------------------------------
# WindowSpotlight — no parameters, just registration
# ------------------------------------------------------------------

class TestWindowSpotlight:
    def test_name(self):
        actual = WindowSpotlight({"effectName": "WindowSpotlight", "parameters": {}})
        assert actual.name == "WindowSpotlight"


# ------------------------------------------------------------------
# ColorTint
# ------------------------------------------------------------------

class TestColorTint:
    def _make(self):
        return _make("ColorTint", {
            "lightColor-red": 1.0, "lightColor-green": 0.9,
            "lightColor-blue": 0.8, "lightColor-alpha": 1.0,
            "darkColor-red": 0.1, "darkColor-green": 0.0,
            "darkColor-blue": 0.2, "darkColor-alpha": 1.0,
        })

    def test_read(self):
        actual = ColorTint(self._make())
        assert actual.light_color == (1.0, 0.9, 0.8, 1.0)
        assert actual.dark_color == (0.1, 0.0, 0.2, 1.0)

    def test_write(self):
        data = self._make()
        actual = ColorTint(data)
        actual.light_color = (0.5, 0.6, 0.7, 0.8)
        actual.dark_color = (0.2, 0.3, 0.4, 0.5)
        assert data["parameters"]["lightColor-red"]["defaultValue"] == 0.5
        assert data["parameters"]["lightColor-alpha"]["defaultValue"] == 0.8
        assert data["parameters"]["darkColor-red"]["defaultValue"] == 0.2
        assert data["parameters"]["darkColor-alpha"]["defaultValue"] == 0.5


# ------------------------------------------------------------------
# Border
# ------------------------------------------------------------------

class TestBorder:
    def _make(self):
        return _make("Border", {
            "width": 4.0,
            "color-red": 1.0, "color-green": 1.0,
            "color-blue": 1.0, "color-alpha": 1.0,
            "corner-radius": 0.0,
        })

    def test_read(self):
        actual = Border(self._make())
        assert actual.width == 4.0
        assert actual.color == (1.0, 1.0, 1.0, 1.0)
        assert actual.corner_radius == 0.0

    def test_write(self):
        data = self._make()
        actual = Border(data)
        actual.width = 8.0
        actual.color = (0.5, 0.3, 0.1, 0.9)
        actual.corner_radius = 5.0
        assert data["parameters"]["width"]["defaultValue"] == 8.0
        assert data["parameters"]["color-red"]["defaultValue"] == 0.5
        assert data["parameters"]["color-alpha"]["defaultValue"] == 0.9
        assert data["parameters"]["corner-radius"]["defaultValue"] == 5.0


# ------------------------------------------------------------------
# Colorize
# ------------------------------------------------------------------

class TestColorize:
    def _make(self):
        return _make("Colorize", {
            "color-red": 0.5, "color-green": 0.5, "color-blue": 0.5,
            "intensity": 0.5,
        })

    def test_read(self):
        actual = Colorize(self._make())
        assert actual.color == (0.5, 0.5, 0.5)
        assert actual.intensity == 0.5

    def test_write(self):
        data = self._make()
        actual = Colorize(data)
        actual.color = (0.1, 0.2, 0.3)
        actual.intensity = 0.8
        assert data["parameters"]["color-red"]["defaultValue"] == 0.1
        assert data["parameters"]["color-green"]["defaultValue"] == 0.2
        assert data["parameters"]["color-blue"]["defaultValue"] == 0.3
        assert data["parameters"]["intensity"]["defaultValue"] == 0.8

    def test_flat_scalar_color(self):
        """Colorize with flat scalar params (as produced by add_colorize)."""
        data = {
            "effectName": "Colorize",
            "parameters": {
                "color-red": 0.5, "color-green": 0.5, "color-blue": 0.5,
                "intensity": 0.5,
            },
        }
        actual = Colorize(data)
        assert actual.color == (0.5, 0.5, 0.5)
        actual.color = (0.9, 0.8, 0.7)
        assert data["parameters"]["color-red"] == 0.9
        assert data["parameters"]["color-green"] == 0.8
        assert data["parameters"]["color-blue"] == 0.7


# ------------------------------------------------------------------
# Serialization round-trip: effect_from_dict → data preserved
# ------------------------------------------------------------------

class TestSerializationRoundTrip:
    @pytest.mark.parametrize("effect_name", [
        "Sepia", "Vignette", "Reflection", "StaticNoise", "Tiling",
        "TornEdge", "CRTMonitor", "Mosaic", "OutlineEdges",
        "WindowSpotlight", "ColorTint", "Border", "Colorize",
    ])
    def test_data_identity(self, effect_name: str):
        data = {"effectName": effect_name, "parameters": {}}
        actual = effect_from_dict(data)
        assert actual.data is data
