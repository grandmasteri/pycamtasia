"""Tests for camtasia.timeline.clips.callout — Callout clip type."""
from __future__ import annotations

import pytest

from camtasia.timeline.clips import Callout
from camtasia.timing import EDIT_RATE, seconds_to_ticks

# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _base_clip_dict(**overrides) -> dict:
    base = {
        "id": 14,
        "_type": "AMFile",
        "src": 3,
        "start": 0,
        "duration": 106051680000,
        "mediaStart": 0,
        "mediaDuration": 113484000000,
        "scalar": 1,
    }
    base.update(overrides)
    return base


def _callout_dict(**overrides) -> dict:
    d = _base_clip_dict(
        _type="Callout",
        id=60,
        **{"def": {
            "kind": "remix",
            "shape": "text",
            "style": "basic",
            "text": "Hello World",
            "width": 934.5,
            "height": 253.9,
            "horizontal-alignment": "center",
        }},
    )
    d.update(overrides)
    return d


def _base(**kw) -> dict:
    d = {
        "id": 1, "_type": "AMFile", "src": 1,
        "start": 0, "duration": EDIT_RATE * 10,
        "mediaStart": 0, "mediaDuration": EDIT_RATE * 10, "scalar": 1,
    }
    d.update(kw)
    return d


_S5 = seconds_to_ticks(5.0)


def _cov_callout_data(**overrides):
    d = {
        '_type': 'Callout', 'id': 400, 'start': 0, 'duration': _S5,
        'mediaDuration': _S5, 'mediaStart': 0, 'scalar': 1,
        'parameters': {}, 'effects': [],
        'def': {
            'text': 'Hello', 'kind': 'remix', 'shape': 'text', 'style': 'basic',
            'font': {'name': 'Arial', 'weight': 'Regular', 'size': 24.0},
            'width': 200, 'height': 100,
            'textAttributes': {
                'type': 'textAttributeList',
                'keyframes': [{
                    'endTime': 0,
                    'time': 0,
                    'duration': 0,
                    'value': [
                        {'name': 'fontName', 'value': 'Arial', 'rangeEnd': 5, 'rangeStart': 0, 'valueType': 'string'},
                        {'name': 'fontWeight', 'value': 400, 'rangeEnd': 5, 'rangeStart': 0, 'valueType': 'int'},
                        {'name': 'fontSize', 'value': 24, 'rangeEnd': 5, 'rangeStart': 0, 'valueType': 'double'},
                        {'name': 'fgColor', 'value': '(0,0,0,255)', 'rangeEnd': 5, 'rangeStart': 0, 'valueType': 'color'},
                    ]
                }]
            },
        },
    }
    d.update(overrides)
    return d


# ------------------------------------------------------------------
# Basic Callout properties
# ------------------------------------------------------------------

def test_callout_text() -> None:
    clip = Callout(_callout_dict())
    assert clip.text == "Hello World"


def test_callout_text_setter_mutates_dict() -> None:
    data = _callout_dict()
    clip = Callout(data)
    clip.text = "Updated"
    assert data["def"]["text"] == "Updated"


def test_callout_kind_shape_style() -> None:
    clip = Callout(_callout_dict())
    assert clip.kind == "remix"
    assert clip.shape == "text"
    assert clip.style == "basic"


def test_callout_dimensions() -> None:
    clip = Callout(_callout_dict())
    assert clip.width == 934.5
    assert clip.height == 253.9


def test_callout_text_default_when_no_def() -> None:
    data = _base_clip_dict(_type="Callout")
    clip = Callout(data)
    assert clip.text == ""


# ------------------------------------------------------------------
# Callout: set_size dict branch
# ------------------------------------------------------------------

class TestCalloutSetSizeDictBranch:
    def test_updates_dict_default_value(self):
        data = {
            'id': 1, '_type': 'Callout', 'src': 0, 'start': 0, 'duration': 100,
            'mediaStart': 0, 'mediaDuration': 100, 'scalar': 1,
            'metadata': {}, 'parameters': {}, 'effects': [], 'attributes': {'ident': ''},
            'animationTracks': {},
            'def': {
                'width': {'defaultValue': 100, 'keyframes': [{'time': 0, 'value': 100}]},
                'height': {'defaultValue': 50, 'keyframes': [{'time': 0, 'value': 50}]},
            },
        }
        clip = Callout(data)
        clip.set_size(200, 150)
        assert data['def']['width']['defaultValue'] == 200
        assert data['def']['height']['defaultValue'] == 150
        assert 'keyframes' not in data['def']['width']
        assert 'keyframes' not in data['def']['height']


# ------------------------------------------------------------------
# Callout: set_font
# ------------------------------------------------------------------

class TestCalloutSetFontWithIntWeight:
    def test_set_font_int_weight_updates_keyframes(self):
        d = _cov_callout_data()
        c = Callout(d)
        c.set_font('Montserrat', weight=700, size=48)
        attrs = {a['name']: a['value'] for a in d['def']['textAttributes']['keyframes'][0]['value']}
        assert attrs['fontName'] == 'Montserrat'
        assert attrs['fontWeight'] == 700
        assert attrs['fontSize'] == 48

    def test_set_font_string_weight(self):
        d = _cov_callout_data()
        c = Callout(d)
        c.set_font('Roboto', weight='Bold', size=36)
        attrs = {a['name']: a['value'] for a in d['def']['textAttributes']['keyframes'][0]['value']}
        assert attrs['fontWeight'] == 700


# ------------------------------------------------------------------
# Callout: set_colors
# ------------------------------------------------------------------

class TestCalloutSetColorsWithFgColor:
    def test_set_colors_updates_fgcolor_in_keyframes(self):
        d = _cov_callout_data()
        c = Callout(d)
        c.set_colors(font_color=(0.0, 1.0, 0.0))
        attrs = {a['name']: a['value'] for a in d['def']['textAttributes']['keyframes'][0]['value']}
        assert attrs['fgColor'] == '(0,255,0,255)'

    def test_set_colors_with_alpha(self):
        d = _cov_callout_data()
        c = Callout(d)
        c.set_colors(font_color=(1.0, 0.0, 0.0, 0.5))
        attrs = {a['name']: a['value'] for a in d['def']['textAttributes']['keyframes'][0]['value']}
        assert '128' in attrs['fgColor'] or '127' in attrs['fgColor']


# ------------------------------------------------------------------
# Callout: definition property
# ------------------------------------------------------------------

class TestCalloutDefinitionProperty:
    def test_definition_returns_def_dict(self):
        d = _cov_callout_data()
        c = Callout(d)
        defn = c.definition
        assert defn['text'] == 'Hello'

    def test_definition_empty_when_no_def(self):
        d = _cov_callout_data()
        del d['def']
        c = Callout(d)
        assert c.definition == {}


# ------------------------------------------------------------------
# Callout: set_source raises
# ------------------------------------------------------------------

class TestCalloutSetSourceRaises:
    def test_set_source_raises_type_error(self):
        c = Callout(_cov_callout_data())
        with pytest.raises(TypeError, match='Callout clips do not have a source ID'):
            c.set_source(1)


# ------------------------------------------------------------------
# Callout: text setter updates ranges
# ------------------------------------------------------------------

class TestCalloutTextSetterUpdatesRanges:
    def test_text_setter_updates_keyframe_ranges(self):
        d = _cov_callout_data()
        c = Callout(d)
        c.text = 'New longer text'
        for kf in d['def']['textAttributes']['keyframes']:
            for attr in kf['value']:
                assert attr['rangeEnd'] == len('New longer text')
                assert attr['rangeStart'] == 0


# ------------------------------------------------------------------
# Callout: dimension setters with dict values
# ------------------------------------------------------------------

class TestCalloutDimensionSettersWithDictValues:
    def test_width_setter_with_dict_value(self):
        d = _cov_callout_data()
        d['def']['width'] = {'defaultValue': 200, 'keyframes': [{'time': 0, 'value': 200}]}
        c = Callout(d)
        c.width = 300
        assert d['def']['width']['defaultValue'] == 300
        assert 'keyframes' not in d['def']['width']

    def test_height_setter_with_dict_value(self):
        d = _cov_callout_data()
        d['def']['height'] = {'defaultValue': 100, 'keyframes': [{'time': 0, 'value': 100}]}
        c = Callout(d)
        c.height = 200
        assert d['def']['height']['defaultValue'] == 200
        assert 'keyframes' not in d['def']['height']

    def test_corner_radius_setter_with_dict_value(self):
        d = _cov_callout_data()
        d['def']['corner-radius'] = {'defaultValue': 5, 'keyframes': [{'time': 0, 'value': 5}]}
        c = Callout(d)
        c.corner_radius = 10
        assert d['def']['corner-radius']['defaultValue'] == 10
        assert 'keyframes' not in d['def']['corner-radius']


# ------------------------------------------------------------------
# Callout: setters, fill/stroke color, set_font, set_colors,
#   resize, add_behavior, tail_position, corner_radius, horizontal_alignment
# ------------------------------------------------------------------

class TestCalloutSetters:
    def test_text_setter_creates_def_if_absent(self):
        data = _base(_type="Callout")
        clip = Callout(data)
        clip.text = "new"
        assert data["def"]["text"] == "new"

    def test_style_setter(self):
        data = _base(_type="Callout", **{"def": {"style": "basic"}})
        clip = Callout(data)
        clip.style = "fancy"
        assert data["def"]["style"] == "fancy"

    def test_width_setter(self):
        data = _base(_type="Callout", **{"def": {}})
        clip = Callout(data)
        clip.width = 500.0
        assert data["def"]["width"] == 500.0

    def test_height_setter(self):
        data = _base(_type="Callout", **{"def": {}})
        clip = Callout(data)
        clip.height = 300.0
        assert data["def"]["height"] == 300.0

    def test_horizontal_alignment_setter(self):
        data = _base(_type="Callout", **{"def": {}})
        clip = Callout(data)
        clip.horizontal_alignment = "left"
        assert data["def"]["horizontal-alignment"] == "left"


class TestCalloutColors:
    def test_fill_color_reads_defaults(self):
        clip = Callout(_base(_type="Callout"))
        assert clip.fill_color == (0.0, 0.0, 0.0, 1.0)

    def test_fill_color_setter(self):
        data = _base(_type="Callout", **{"def": {}})
        clip = Callout(data)
        clip.fill_color = (0.1, 0.2, 0.3, 0.4)
        assert data["def"]["fill-color-red"] == 0.1
        assert data["def"]["fill-color-opacity"] == 0.4

    def test_stroke_color_reads_defaults(self):
        clip = Callout(_base(_type="Callout"))
        assert clip.stroke_color == (0.0, 0.0, 0.0, 1.0)

    def test_stroke_color_setter(self):
        data = _base(_type="Callout", **{"def": {}})
        clip = Callout(data)
        clip.stroke_color = (0.5, 0.6, 0.7, 0.8)
        assert data["def"]["stroke-color-blue"] == 0.7

    def test_corner_radius_default(self):
        clip = Callout(_base(_type="Callout"))
        assert clip.corner_radius == 0.0

    def test_corner_radius_setter(self):
        data = _base(_type="Callout", **{"def": {}})
        clip = Callout(data)
        clip.corner_radius = 12.0
        assert data["def"]["corner-radius"] == 12.0

    def test_tail_position_default(self):
        clip = Callout(_base(_type="Callout"))
        assert clip.tail_position == (0.0, 0.0)

    def test_tail_position_setter(self):
        data = _base(_type="Callout", **{"def": {}})
        clip = Callout(data)
        clip.tail_position = (10.0, 20.0)
        assert data["def"]["tail-x"] == 10.0
        assert data["def"]["tail-y"] == 20.0


class TestCalloutConvenience:
    def test_set_font(self):
        data = _base(_type="Callout", **{"def": {}})
        clip = Callout(data)
        actual_result = clip.set_font("Arial", "Bold", 48.0)
        assert actual_result is clip
        assert data["def"]["font"]["name"] == "Arial"
        assert data["def"]["font"]["weight"] == "Bold"
        assert data["def"]["font"]["size"] == 48.0

    def test_set_colors_fill_only(self):
        data = _base(_type="Callout", **{"def": {}})
        clip = Callout(data)
        actual_result = clip.set_colors(fill=(1.0, 0.0, 0.0, 1.0))
        assert actual_result is clip
        assert data["def"]["fill-color-red"] == 1.0

    def test_set_colors_stroke_only(self):
        data = _base(_type="Callout", **{"def": {}})
        clip = Callout(data)
        clip.set_colors(stroke=(0.0, 1.0, 0.0, 0.5))
        assert data["def"]["stroke-color-green"] == 1.0

    def test_set_colors_font_color(self):
        data = _base(_type="Callout", **{"def": {}})
        clip = Callout(data)
        clip.set_colors(font_color=(0.1, 0.2, 0.3))
        assert data["def"]["font"]["color-red"] == 0.1
        assert data["def"]["font"]["color-green"] == 0.2
        assert data["def"]["font"]["color-blue"] == 0.3

    def test_resize(self):
        data = _base(_type="Callout", **{"def": {}})
        clip = Callout(data)
        actual_result = clip.resize(800.0, 600.0)
        assert actual_result is clip
        assert clip.width == 800.0
        assert clip.height == 600.0

    def test_add_behavior(self):
        data = _base(_type="Callout", **{"def": {}})
        data['duration'] = 705600000 * 10  # 10 seconds
        clip = Callout(data)
        actual_result = clip.add_behavior("reveal")
        assert actual_result is clip  # chaining
        assert data["effects"][0]["_type"] == "GenericBehaviorEffect"
        assert data["effects"][0]["effectName"] == "reveal"
        assert data["effects"][0]["metadata"]["presetName"] == "Reveal"

    def test_font_default(self):
        clip = Callout(_base(_type="Callout"))
        assert clip.font == {}

    def test_kind_default(self):
        clip = Callout(_base(_type="Callout"))
        assert clip.kind == ""

    def test_shape_default(self):
        clip = Callout(_base(_type="Callout"))
        assert clip.shape == ""

    def test_style_default(self):
        clip = Callout(_base(_type="Callout"))
        assert clip.style == ""


class TestCalloutHorizontalAlignmentGetter:
    def test_horizontal_alignment_from_def(self):
        data = _base(_type="Callout", **{"def": {"horizontal-alignment": "right"}})
        clip = Callout(data)
        assert clip.horizontal_alignment == "right"


class TestCalloutStrokeColorAnimated:
    def test_stroke_color_setter_preserves_keyframes(self, project):
        keyframes = [{'time': 0, 'value': 0.5}, {'time': 100, 'value': 1.0}]
        data = {
            '_type': 'Callout', 'id': 99, 'start': 0, 'duration': 100,
            'mediaStart': 0, 'mediaDuration': 100, 'scalar': 1,
            'parameters': {}, 'effects': [], 'metadata': {}, 'animationTracks': {},
            'def': {
                'stroke-color-red': {'defaultValue': 0.1, 'keyframes': list(keyframes)},
                'stroke-color-green': {'defaultValue': 0.2, 'keyframes': list(keyframes)},
                'stroke-color-blue': {'defaultValue': 0.3, 'keyframes': list(keyframes)},
                'stroke-color-opacity': {'defaultValue': 0.4, 'keyframes': list(keyframes)},
            },
        }
        callout = Callout(data)
        callout.stroke_color = (0.9, 0.8, 0.7, 0.6)
        d = callout.definition
        assert d['stroke-color-red']['defaultValue'] == 0.9
        assert d['stroke-color-green']['defaultValue'] == 0.8
        assert d['stroke-color-blue']['defaultValue'] == 0.7
        assert d['stroke-color-opacity']['defaultValue'] == 0.6
        assert 'keyframes' not in d['stroke-color-red']


class TestCalloutStrokeColorAnimatedGetter:
    def test_stroke_color_getter_with_animated_dict(self):
        data = {
            '_type': 'Callout', 'id': 1, 'start': 0, 'duration': 100,
            'def': {
                'stroke-color-red': {'type': 'double', 'defaultValue': 0.5, 'keyframes': [{'time': 0, 'value': 0.5}]},
                'stroke-color-green': 0.3,
                'stroke-color-blue': 0.1,
                'stroke-color-opacity': 1.0,
            },
        }
        callout = Callout(data)
        r, _g, _b, _a = callout.stroke_color
        assert r == 0.5


class TestCalloutFillColorAnimatedSetter:
    def test_fill_color_setter_preserves_keyframes(self):
        data = {
            '_type': 'Callout', 'id': 1, 'start': 0, 'duration': 100,
            'def': {
                'fill-color-red': {'type': 'double', 'defaultValue': 0.5, 'keyframes': [{'time': 0, 'value': 0.5}]},
                'fill-color-green': {'type': 'double', 'defaultValue': 0.3, 'keyframes': []},
                'fill-color-blue': 0.1,
                'fill-color-opacity': 1.0,
            },
        }
        callout = Callout(data)
        callout.fill_color = (0.9, 0.8, 0.7, 0.6)
        assert data['def']['fill-color-red']['defaultValue'] == 0.9
        assert 'keyframes' not in data['def']['fill-color-red']
        assert data['def']['fill-color-blue'] == 0.7
