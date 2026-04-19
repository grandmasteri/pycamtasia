"""Tests for the CalloutBuilder fluent API."""
from __future__ import annotations

from typing import Any

from camtasia.timeline.clips.callout import CalloutBuilder
from camtasia.timeline.track import Track


def _make_track() -> Track:
    attrs: dict[str, Any] = {"ident": "Track 1"}
    data: dict[str, Any] = {"trackIndex": 0, "medias": []}
    return Track(attrs, data)


class TestBuilderDefaults:
    def test_builder_defaults(self):
        b = CalloutBuilder("Hello")
        assert b.text == "Hello"
        assert b._font_name == "Montserrat"
        assert b._font_weight == 400
        assert b._font_size == 36.0
        assert b._fill_color is None
        assert b._font_color is None
        assert b._stroke_color is None
        assert b._x == 0.0
        assert b._y == 0.0
        assert b._width is None
        assert b._height is None
        assert b._alignment == "center"


class TestBuilderFontChaining:
    def test_builder_font_chaining(self):
        b = CalloutBuilder("Hi")
        result = b.font("Arial", weight=700, size=48.0)
        assert result is b
        assert b._font_name == "Arial"
        assert b._font_weight == 700
        assert b._font_size == 48.0


class TestBuilderColorChaining:
    def test_builder_color_chaining(self):
        b = CalloutBuilder("Hi")
        result = b.color(
            fill=(0, 0, 0, 255),
            font=(255, 255, 255, 255),
            stroke=(128, 128, 128, 255),
        )
        assert result is b
        assert b._fill_color == (0, 0, 0, 255)
        assert b._font_color == (255, 255, 255, 255)
        assert b._stroke_color == (128, 128, 128, 255)


class TestBuilderPositionChaining:
    def test_builder_position_chaining(self):
        b = CalloutBuilder("Hi")
        result = b.position(100.5, -200.3)
        assert result is b
        assert b._x == 100.5
        assert b._y == -200.3


class TestBuilderSizeChaining:
    def test_builder_size_chaining(self):
        b = CalloutBuilder("Hi")
        result = b.size(400.0, 100.0)
        assert result is b
        assert b._width == 400.0
        assert b._height == 100.0


class TestAddCalloutFromBuilderCreatesClip:
    def test_add_callout_from_builder_creates_clip(self):
        track = _make_track()
        b = CalloutBuilder("Test Text")
        clip = track.add_callout_from_builder(b, 1.0, 5.0)
        assert clip.text == "Test Text"
        assert clip.clip_type == "Callout"
        assert len(track) == 1


class TestAddCalloutFromBuilderAppliesFont:
    def test_add_callout_from_builder_applies_font(self):
        track = _make_track()
        b = CalloutBuilder("Styled")
        b.font("Arial", weight=700, size=48.0)
        clip = track.add_callout_from_builder(b, 0, 3)
        assert clip.font["name"] == "Arial"
        assert clip.font["size"] == 48.0


class TestAddCalloutFromBuilderAppliesPosition:
    def test_add_callout_from_builder_applies_position(self):
        track = _make_track()
        b = CalloutBuilder("Moved")
        b.position(150.0, -75.0)
        clip = track.add_callout_from_builder(b, 0, 3)
        assert clip._data["parameters"]["translation0"] == 150.0
        assert clip._data["parameters"]["translation1"] == -75.0


class TestBuilderAlignment:
    def test_alignment_chaining(self):
        builder = CalloutBuilder('test')
        actual_result = builder.alignment('left')
        assert actual_result is builder
        assert builder._alignment == 'left'


class TestBuilderWithAllOptions:
    def test_add_callout_with_size_and_colors(self):
        data = {'trackIndex': 0, 'medias': []}
        t = Track({'ident': 'test'}, data)
        builder = CalloutBuilder('styled')
        builder.font('Arial', weight=700, size=24)
        builder.color(fill=(255, 0, 0, 255), font=(0, 255, 0, 255), stroke=(0, 0, 255, 255))
        builder.size(200, 50)
        actual_clip = t.add_callout_from_builder(builder, 0.0, 5.0)
        assert actual_clip.text == 'styled'
