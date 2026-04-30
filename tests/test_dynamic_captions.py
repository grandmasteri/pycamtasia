"""Tests for DynamicCaptionStyle, active_word_at, and Callout text_properties/canvas_rect."""
from __future__ import annotations

import pytest

from camtasia.timeline.captions import (
    CaptionAttributes,
    DEFAULT_DYNAMIC_STYLES,
    DynamicCaptionStyle,
)
from camtasia.timeline.clips.callout import Callout


# ---------------------------------------------------------------------------
# DynamicCaptionStyle dataclass
# ---------------------------------------------------------------------------


class TestDynamicCaptionStyle:
    def test_default_values(self):
        style = DynamicCaptionStyle(name='test')
        assert style.name == 'test'
        assert style.font_name == 'Arial'
        assert style.font_size == 32
        assert style.fill_color == (255, 255, 255, 255)
        assert style.stroke_color == (0, 0, 0, 255)
        assert style.stroke_width == 2
        assert style.highlight_color == (255, 255, 0, 255)
        assert style.background_color == (0, 0, 0, 180)

    def test_custom_values(self):
        style = DynamicCaptionStyle(
            name='custom',
            font_name='Courier',
            font_size=24,
            fill_color=(100, 200, 50, 128),
            stroke_color=(10, 20, 30, 40),
            stroke_width=5,
            highlight_color=(0, 0, 255, 255),
            background_color=(50, 50, 50, 200),
        )
        assert style.font_name == 'Courier'
        assert style.font_size == 24
        assert style.stroke_width == 5

    def test_equality(self):
        a = DynamicCaptionStyle(name='a', font_size=32)
        b = DynamicCaptionStyle(name='a', font_size=32)
        assert a == b

    def test_inequality(self):
        a = DynamicCaptionStyle(name='a')
        b = DynamicCaptionStyle(name='b')
        assert a != b


# ---------------------------------------------------------------------------
# DEFAULT_DYNAMIC_STYLES
# ---------------------------------------------------------------------------


class TestDefaultDynamicStyles:
    def test_has_expected_keys(self):
        assert set(DEFAULT_DYNAMIC_STYLES.keys()) == {'classic', 'bold', 'minimal'}

    def test_classic_style(self):
        style = DEFAULT_DYNAMIC_STYLES['classic']
        assert style.name == 'classic'
        assert style.font_name == 'Arial'
        assert style.font_size == 32

    def test_bold_style(self):
        style = DEFAULT_DYNAMIC_STYLES['bold']
        assert style.name == 'bold'
        assert style.font_name == 'Montserrat'
        assert style.font_size == 48

    def test_minimal_style(self):
        style = DEFAULT_DYNAMIC_STYLES['minimal']
        assert style.name == 'minimal'
        assert style.stroke_width == 0


# ---------------------------------------------------------------------------
# CaptionAttributes.active_word_at
# ---------------------------------------------------------------------------


class TestActiveWordAt:
    def _make_attrs(self) -> CaptionAttributes:
        return CaptionAttributes({})

    def test_first_word(self):
        attrs = self._make_attrs()
        assert attrs.active_word_at(0.0, ['hello', 'world'], 2.0) == 'hello'

    def test_second_word(self):
        attrs = self._make_attrs()
        assert attrs.active_word_at(1.5, ['hello', 'world'], 2.0) == 'world'

    def test_exact_boundary(self):
        attrs = self._make_attrs()
        # At exactly 1.0s with 2 words over 2.0s, word_duration=1.0, index=1
        assert attrs.active_word_at(1.0, ['hello', 'world'], 2.0) == 'world'

    def test_end_of_clip(self):
        attrs = self._make_attrs()
        assert attrs.active_word_at(2.0, ['hello', 'world'], 2.0) == 'world'

    def test_empty_words(self):
        attrs = self._make_attrs()
        assert attrs.active_word_at(0.5, [], 2.0) is None

    def test_zero_duration(self):
        attrs = self._make_attrs()
        assert attrs.active_word_at(0.0, ['hello'], 0.0) is None

    def test_negative_time(self):
        attrs = self._make_attrs()
        assert attrs.active_word_at(-1.0, ['hello'], 2.0) is None

    def test_time_past_duration(self):
        attrs = self._make_attrs()
        assert attrs.active_word_at(3.0, ['hello'], 2.0) is None

    def test_single_word(self):
        attrs = self._make_attrs()
        assert attrs.active_word_at(0.5, ['only'], 1.0) == 'only'


# ---------------------------------------------------------------------------
# Callout.text_properties
# ---------------------------------------------------------------------------


def _make_callout(**overrides: object) -> Callout:
    """Build a minimal Callout clip dict."""
    data: dict = {
        '_type': 'Callout',
        'id': 1,
        'start': 0,
        'duration': 705_600_000,
        'mediaStart': 0,
        'mediaDuration': 705_600_000,
        'scalar': 1,
        'parameters': {},
        'effects': [],
        'def': {
            'kind': 'remix',
            'shape': 'text',
            'style': 'basic',
            'text': 'Hello',
            'font': {'name': 'Arial', 'size': 36.0, 'weight': 'Regular'},
            'fill-color-red': 1.0,
            'fill-color-green': 1.0,
            'fill-color-blue': 1.0,
            'fill-color-opacity': 1.0,
            'stroke-color-red': 0.0,
            'stroke-color-green': 0.0,
            'stroke-color-blue': 0.0,
            'stroke-color-opacity': 1.0,
            'width': 400.0,
            'height': 100.0,
        },
    }
    data.update(overrides)
    return Callout(data)


class TestCalloutTextProperties:
    def test_getter(self):
        callout = _make_callout()
        props = callout.text_properties
        assert props['font_name'] == 'Arial'
        assert props['font_size'] == 36.0
        assert props['fill_color'] == (1.0, 1.0, 1.0, 1.0)
        assert props['stroke_color'] == (0.0, 0.0, 0.0, 1.0)

    def test_setter_font(self):
        callout = _make_callout()
        callout.text_properties = {'font_name': 'Courier', 'font_size': 24.0}
        assert callout.text_properties['font_name'] == 'Courier'
        assert callout.text_properties['font_size'] == 24.0

    def test_setter_fill_color(self):
        callout = _make_callout()
        callout.text_properties = {'fill_color': (0.5, 0.5, 0.5, 0.8)}
        assert callout.fill_color == (0.5, 0.5, 0.5, 0.8)

    def test_setter_partial_update(self):
        callout = _make_callout()
        callout.text_properties = {'font_name': 'Helvetica'}
        # font_size should remain unchanged
        assert callout.text_properties['font_size'] == 36.0
        assert callout.text_properties['font_name'] == 'Helvetica'


# ---------------------------------------------------------------------------
# Callout.canvas_rect
# ---------------------------------------------------------------------------


class TestCalloutCanvasRect:
    def test_getter(self):
        callout = _make_callout()
        x, y, w, h = callout.canvas_rect
        assert w == 400.0
        assert h == 100.0

    def test_setter(self):
        callout = _make_callout()
        callout.canvas_rect = (50.0, 75.0, 300.0, 80.0)
        assert callout.canvas_rect == (50.0, 75.0, 300.0, 80.0)

    def test_roundtrip(self):
        callout = _make_callout()
        original = callout.canvas_rect
        callout.canvas_rect = (10.0, 20.0, 500.0, 150.0)
        assert callout.canvas_rect != original
        callout.canvas_rect = original
        assert callout.canvas_rect == original
