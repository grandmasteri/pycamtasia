"""Tests for set_shader_colors with variable color counts."""
from __future__ import annotations

from camtasia.effects.source import SourceEffect


def _radial_effect():
    """SourceEffect with only 2 colors (radial gradient)."""
    return {
        "effectName": "SourceEffect",
        "parameters": {
            "Color0-red": 0.0, "Color0-green": 0.0,
            "Color0-blue": 0.0, "Color0-alpha": 1.0,
            "Color1-red": 1.0, "Color1-green": 1.0,
            "Color1-blue": 1.0, "Color1-alpha": 1.0,
            "MidPoint": 0.5,
            "Speed": 5.0,
            "sourceFileType": "tscshadervid",
        },
    }


def _four_corner_effect():
    """SourceEffect with 4 colors (four-corner gradient)."""
    return {
        "effectName": "SourceEffect",
        "parameters": {
            "Color0-red": 0.0, "Color0-green": 0.0,
            "Color0-blue": 0.0, "Color0-alpha": 1.0,
            "Color1-red": 1.0, "Color1-green": 0.0,
            "Color1-blue": 0.0, "Color1-alpha": 1.0,
            "Color2-red": 0.0, "Color2-green": 1.0,
            "Color2-blue": 0.0, "Color2-alpha": 1.0,
            "Color3-red": 0.0, "Color3-green": 0.0,
            "Color3-blue": 1.0, "Color3-alpha": 1.0,
            "MidPointX": 0.5, "MidPointY": 0.5,
            "Speed": 5.0,
            "sourceFileType": "tscshadervid",
        },
    }


def test_set_shader_colors_two_colors():
    effect = SourceEffect(_radial_effect())
    effect.set_shader_colors((255, 0, 0), (0, 255, 0))
    assert effect.color0 == (1.0, 0.0, 0.0, 1.0)
    assert effect.color1 == (0.0, 1.0, 0.0, 1.0)


def test_set_shader_colors_four_colors():
    effect = SourceEffect(_four_corner_effect())
    effect.set_shader_colors((255, 0, 0), (0, 255, 0), (0, 0, 255), (128, 128, 128))
    assert effect.color0 == (1.0, 0.0, 0.0, 1.0)
    assert effect.color1 == (0.0, 1.0, 0.0, 1.0)
    assert effect.color2 == (0.0, 0.0, 1.0, 1.0)
    r, g, b, a = effect.color3
    assert abs(r - 128 / 255) < 1e-9
    assert a == 1.0


class TestMidPointSetter:
    def test_mid_point_setter_radial(self):
        from camtasia.effects.source import SourceEffect
        data = {'parameters': {'MidPoint': 0.5}}
        se = SourceEffect(data)
        se.mid_point = 0.7
        assert data['parameters']['MidPoint'] == 0.7

    def test_mid_point_setter_four_corner(self):
        from camtasia.effects.source import SourceEffect
        data = {'parameters': {'MidPointX': 0.5, 'MidPointY': 0.5}}
        se = SourceEffect(data)
        se.mid_point = (0.3, 0.8)
        assert data['parameters']['MidPointX'] == 0.3
        assert data['parameters']['MidPointY'] == 0.8
