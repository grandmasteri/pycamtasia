"""Tests for sketch_motion_callout annotation factory."""
from __future__ import annotations

import pytest

from camtasia.annotations.callouts import sketch_motion_callout


class TestSketchMotionCalloutDefaults:
    def test_default_shape_is_circle(self):
        result = sketch_motion_callout()
        assert result['shape'] == 'circle'

    def test_default_kind(self):
        result = sketch_motion_callout()
        assert result['kind'] == 'sketch-motion'
        assert result['style'] == 'basic'

    def test_default_color_is_red(self):
        result = sketch_motion_callout()
        assert result['stroke-color-red'] == 1.0
        assert result['stroke-color-green'] == 0.0
        assert result['stroke-color-blue'] == 0.0
        assert result['stroke-color-opacity'] == 1.0

    def test_default_stroke_width(self):
        result = sketch_motion_callout()
        assert result['stroke-width'] == 4.0

    def test_default_draw_time(self):
        result = sketch_motion_callout()
        assert result['draw-time'] == 1.0

    def test_default_size(self):
        result = sketch_motion_callout()
        assert result['width'] == 200.0
        assert result['height'] == 200.0

    def test_default_position(self):
        result = sketch_motion_callout()
        assert result['position-x'] == 960.0
        assert result['position-y'] == 540.0


class TestSketchMotionCalloutShapes:
    @pytest.mark.parametrize('shape', ['circle', 'arrow', 'underline', 'rectangle'])
    def test_valid_shapes_accepted(self, shape):
        result = sketch_motion_callout(shape)
        assert result['shape'] == shape

    def test_invalid_shape_raises(self):
        with pytest.raises(ValueError, match="shape must be one of"):
            sketch_motion_callout('hexagon')


class TestSketchMotionCalloutCustomValues:
    def test_custom_color(self):
        result = sketch_motion_callout(color=(0.2, 0.4, 0.6, 0.8))
        assert result['stroke-color-red'] == 0.2
        assert result['stroke-color-green'] == 0.4
        assert result['stroke-color-blue'] == 0.6
        assert result['stroke-color-opacity'] == 0.8

    def test_custom_stroke_width(self):
        result = sketch_motion_callout(stroke_width=10.0)
        assert result['stroke-width'] == 10.0

    def test_custom_draw_time(self):
        result = sketch_motion_callout(draw_time_seconds=2.5)
        assert result['draw-time'] == 2.5

    def test_custom_size(self):
        result = sketch_motion_callout(size=(400, 300))
        assert result['width'] == 400.0
        assert result['height'] == 300.0

    def test_custom_position(self):
        result = sketch_motion_callout(position=(100, 200))
        assert result['position-x'] == 100.0
        assert result['position-y'] == 200.0


class TestSketchMotionCalloutTypes:
    def test_all_values_are_float(self):
        result = sketch_motion_callout(size=(100, 100), position=(0, 0))
        for key in ('width', 'height', 'position-x', 'position-y',
                     'stroke-color-red', 'stroke-width', 'draw-time'):
            assert isinstance(result[key], float), f"{key} should be float"


class TestSketchMotionCalloutExport:
    def test_importable_from_annotations_package(self):
        from camtasia.annotations import sketch_motion_callout as imported
        assert imported is sketch_motion_callout
