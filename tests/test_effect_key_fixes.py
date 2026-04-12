"""Tests for hyphenated parameter key fixes and radial gradient compatibility."""
from camtasia.effects.visual import Mask, RoundCorners
from camtasia.effects.source import SourceEffect


def _make_effect(cls, params):
    """Create an effect instance with the given parameters dict."""
    return cls({"effectName": cls.__name__, "parameters": params})


def _param(val):
    """Wrap a value as a Camtasia parameter dict."""
    return {"defaultValue": val, "type": "double", "interp": "linr"}


class TestMaskHyphenatedKeys:
    def test_mask_properties_use_hyphens(self):
        mask = _make_effect(Mask, {
            "mask-shape": _param(2),
            "mask-opacity": _param(0.8),
            "mask-blend": _param(0.5),
            "mask-invert": _param(1),
            "mask-rotation": _param(45.0),
            "mask-width": _param(100.0),
            "mask-height": _param(200.0),
            "mask-positionX": _param(10.0),
            "mask-positionY": _param(20.0),
            "mask-cornerRadius": _param(5.0),
        })

        assert mask.mask_shape == 2
        assert mask.mask_opacity == 0.8
        assert mask.mask_blend == 0.5
        assert mask.mask_invert == 1
        assert mask.mask_rotation == 45.0
        assert mask.mask_width == 100.0
        assert mask.mask_height == 200.0
        assert mask.mask_position_x == 10.0
        assert mask.mask_position_y == 20.0
        assert mask.mask_corner_radius == 5.0


class TestRoundCornersHyphenatedKeys:
    def test_round_corners_use_hyphens(self):
        rc = _make_effect(RoundCorners, {
            "radius": _param(16.0),
            "top-left": _param(True),
            "top-right": _param(False),
            "bottom-left": _param(True),
            "bottom-right": _param(False),
        })

        assert rc.radius == 16.0
        assert rc.top_left is True
        assert rc.top_right is False
        assert rc.bottom_left is True
        assert rc.bottom_right is False


class TestSourceEffectMidPoint:
    def test_source_effect_radial_midpoint(self):
        """Radial gradient uses a single MidPoint key."""
        se = _make_effect(SourceEffect, {
            "MidPoint": _param(0.75),
        })
        assert se.mid_point == 0.75

    def test_source_effect_four_corner_midpoint(self):
        """Four-corner gradient uses MidPointX/MidPointY."""
        se = _make_effect(SourceEffect, {
            "MidPointX": _param(0.3),
            "MidPointY": _param(0.7),
        })
        assert se.mid_point == (0.3, 0.7)

    def test_source_effect_midpoint_default(self):
        """No midpoint keys returns default (0.5, 0.5)."""
        se = _make_effect(SourceEffect, {})
        assert se.mid_point == (0.5, 0.5)

    def test_color2_none_for_radial(self):
        """color2 returns None when not present (radial gradient)."""
        se = _make_effect(SourceEffect, {})
        assert se.color2 is None

    def test_color3_none_for_radial(self):
        """color3 returns None when not present (radial gradient)."""
        se = _make_effect(SourceEffect, {})
        assert se.color3 is None


class TestMaskCornerRadiusSetter:
    def test_mask_corner_radius_setter(self):
        from camtasia.effects.visual import Mask
        data = {'effectName': 'Mask', 'parameters': {'mask-cornerRadius': {'type': 'double', 'defaultValue': 0.0}}}
        mask = Mask(data)
        mask.mask_corner_radius = 16.0
        assert data['parameters']['mask-cornerRadius']['defaultValue'] == 16.0
