"""Tests for camtasia.annotations.shapes module — rectangle, ellipse, triangle."""
from __future__ import annotations

import pytest

from camtasia.annotations.shapes import ellipse, rectangle, triangle
from camtasia.annotations.types import Color, FillStyle, StrokeStyle


class TestRectangle:
    """Tests for the rectangle annotation factory."""

    def test_default_rectangle(self):
        actual_result = rectangle()
        expected_result = {
            "kind": "remix",
            "shape": "shape-rectangle",
            "style": "basic",
            "corner-radius": 0.0,
            "height": 180.0,
            "width": 240.0,
            "fill-color-blue": 0.0,
            "fill-color-green": 0.0,
            "fill-color-opacity": 0.0,
            "fill-color-red": 0.0,
            "stroke-color-blue": 1.0,
            "stroke-color-green": 1.0,
            "stroke-color-opacity": 1.0,
            "stroke-color-red": 1.0,
            "stroke-width": 6.0,
            "fill-style": "solid",
            "stroke-style": "solid",
        }
        assert actual_result == expected_result

    def test_custom_rectangle(self):
        actual_result = rectangle(
            fill_color=Color(0.5, 0.5, 0.5, 0.8),
            fill_style=FillStyle.Gradient,
            stroke_color=Color(1.0, 0.0, 0.0, 1.0),
            stroke_width=3.0,
            stroke_style=StrokeStyle.Dash,
            height=100.0,
            width=200.0,
        )
        assert actual_result["fill-color-red"] == 0.5
        assert actual_result["fill-color-opacity"] == 0.8
        assert actual_result["fill-style"] == "gradient"
        assert actual_result["stroke-style"] == "dash"
        assert actual_result["height"] == 100.0
        assert actual_result["width"] == 200.0
        assert actual_result["stroke-width"] == 3.0

    def test_corner_radius(self):
        actual_result = rectangle(corner_radius=12.0)
        assert actual_result["corner-radius"] == 12.0

    def test_corner_radius_default_zero(self):
        actual_result = rectangle()
        assert actual_result["corner-radius"] == 0.0


class TestEllipse:
    """Tests for the ellipse annotation factory."""

    def test_default_ellipse(self):
        actual_result = ellipse()
        assert actual_result["shape"] == "shape-ellipse"
        assert actual_result["kind"] == "remix"
        assert actual_result["style"] == "basic"
        assert actual_result["height"] == 180.0
        assert actual_result["width"] == 240.0

    def test_custom_ellipse(self):
        actual_result = ellipse(
            fill_color=Color(1.0, 0.0, 0.0, 1.0),
            stroke_color=Color(0.0, 1.0, 0.0, 1.0),
            stroke_width=4.0,
            height=100.0,
            width=100.0,
        )
        assert actual_result["fill-color-red"] == 1.0
        assert actual_result["stroke-color-green"] == 1.0
        assert actual_result["stroke-width"] == 4.0
        assert actual_result["height"] == 100.0
        assert actual_result["width"] == 100.0


class TestTriangle:
    """Tests for the triangle annotation factory."""

    def test_default_triangle(self):
        actual_result = triangle()
        assert actual_result["shape"] == "shape-triangle"
        assert actual_result["kind"] == "remix"
        assert actual_result["style"] == "basic"
        assert actual_result["height"] == 180.0
        assert actual_result["width"] == 240.0

    def test_custom_triangle(self):
        actual_result = triangle(
            fill_color=Color(0.0, 0.0, 1.0, 0.5),
            stroke_style=StrokeStyle.Dot,
            height=200.0,
            width=300.0,
        )
        assert actual_result["fill-color-blue"] == 1.0
        assert actual_result["fill-color-opacity"] == 0.5
        assert actual_result["stroke-style"] == "dot"
        assert actual_result["height"] == 200.0
        assert actual_result["width"] == 300.0


class TestColorValidation:
    def test_color_rejects_out_of_range_component(self):
        with pytest.raises(ValueError, match='Color red component'):
            Color(red=1.5, green=0.0, blue=0.0)
