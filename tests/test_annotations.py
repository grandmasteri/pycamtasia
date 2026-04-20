import pytest

from camtasia.annotations.callouts import arrow, highlight, keystroke_callout, square


def test_arrow_default_values():
    result = arrow()
    assert result['kind'] == 'remix'
    assert result['shape'] == 'arrow'
    assert result['style'] == 'basic'
    assert result['tail-x'] == 0
    assert result['tail-y'] == 0
    assert result['head-x'] == 100
    assert result['head-y'] == 0
    assert result['stroke-color-red'] == 1.0
    assert result['stroke-color-green'] == 0.0
    assert result['stroke-color-blue'] == 0.0
    assert result['stroke-width']['defaultValue'] == 3.0


def test_arrow_custom_values():
    result = arrow(tail=(10, 20), head=(300, 400), color=(0.0, 1.0, 0.5), width=5.0)
    assert result['tail-x'] == 10
    assert result['tail-y'] == 20
    assert result['head-x'] == 300
    assert result['head-y'] == 400
    assert result['stroke-color-red'] == 0.0
    assert result['stroke-color-green'] == 1.0
    assert result['stroke-color-blue'] == 0.5
    assert result['stroke-width']['defaultValue'] == 5.0


def test_highlight_default_values():
    result = highlight()
    assert result['kind'] == 'remix'
    assert result['shape'] == 'shape-rectangle'
    assert result['style'] == 'basic'
    assert result['width'] == 200
    assert result['height'] == 100
    assert result['fill-color-red'] == 1.0
    assert result['fill-color-green'] == 1.0
    assert result['fill-color-blue'] == 0.0
    assert result['fill-color-opacity'] == 0.3
    assert result['fill-style'] == 'solid'
    assert result['corner-radius'] == 0.0


def test_highlight_custom_color():
    result = highlight(color=(0.5, 0.5, 0.8, 0.7))
    assert result['fill-color-red'] == 0.5
    assert result['fill-color-green'] == 0.5
    assert result['fill-color-blue'] == 0.8
    assert result['fill-color-opacity'] == 0.7


def test_keystroke_callout_text():
    result = keystroke_callout('Ctrl+C')
    assert result['kind'] == 'remix'
    assert result['shape'] == 'text'
    assert result['style'] == 'keystroke'
    assert result['text'] == 'Ctrl+C'
    assert result['font']['name'] == 'Montserrat'
    assert result['font']['weight'] == 'Bold'
    assert result['font']['size'] == 24.0


def test_keystroke_callout_custom_font_size():
    result = keystroke_callout('Cmd+Shift+S', font_size=36.0)
    assert result['text'] == 'Cmd+Shift+S'
    assert result['font']['size'] == 36.0



def test_square_callout_line_spacing():
    result = square('Hello', 'Arial', 'Bold', line_spacing=1.5)
    assert result['line-spacing'] == 1.5
    assert result['kind'] == 'remix'
    assert result['shape'] == 'text-rectangle'


# ── Bug fix: keystroke_callout missing textAttributes ────────────────


class TestKeystrokeCalloutTextAttributes:
    def test_has_text_attributes(self):
        result = keystroke_callout('Ctrl+C')
        assert 'textAttributes' in result
        assert result['textAttributes']['type'] == 'textAttributeList'
        kfs = result['textAttributes']['keyframes']
        assert len(kfs) == 1
        attrs = kfs[0]['value']
        names = {a['name'] for a in attrs}
        assert 'fontSize' in names
        assert 'fontName' in names
        assert 'fgColor' in names

    def test_has_standard_keys(self):
        result = keystroke_callout('Ctrl+C')
        assert 'corner-radius' in result
        assert 'enable-ligatures' in result
        assert 'hasDropShadow' in result
        assert 'width' in result
        assert 'height' in result

    def test_text_attributes_range_matches_text(self):
        result = keystroke_callout('Cmd+Shift+S')
        kf = result['textAttributes']['keyframes'][0]
        for attr in kf['value']:
            assert attr['rangeEnd'] == len('Cmd+Shift+S')


# ── Bug 8: _text_attributes uses round() not int() for colors ──


class TestTextAttributesColorRounding:
    """Color values should use round() to avoid truncation errors."""

    def test_color_rounds_not_truncates(self):
        from camtasia.annotations.callouts import _text_attributes
        from camtasia.annotations.types import Color

        # 0.502 * 255 = 128.01 → int() gives 128, round() gives 128 — same
        # 0.999 * 255 = 254.745 → int() gives 254, round() gives 255
        color = Color(0.999, 0.999, 0.999, 0.999)
        attrs = _text_attributes('X', 'Arial', 'Regular', 12.0, color)
        fg = next(a for a in attrs if a['name'] == 'fgColor')
        # With round(), all channels should be 255
        assert fg['value'] == '(255,255,255,255)'

    def test_color_half_value_rounds_correctly(self):
        from camtasia.annotations.callouts import _text_attributes
        from camtasia.annotations.types import Color

        # 0.5 * 255 = 127.5 → int() gives 127, round() gives 128
        color = Color(0.5, 0.5, 0.5, 0.5)
        attrs = _text_attributes('X', 'Arial', 'Regular', 12.0, color)
        fg = next(a for a in attrs if a['name'] == 'fgColor')
        assert fg['value'] == '(128,128,128,128)'


# ── Bug 9: keystroke_callout font dict includes color and tracking ──


class TestKeystrokeCalloutFontColor:
    """keystroke_callout font dict must include color-* and tracking keys."""

    def test_font_has_color_keys(self):
        result = keystroke_callout('Ctrl+C')
        font = result['font']
        assert 'color-red' in font
        assert 'color-green' in font
        assert 'color-blue' in font
        assert 'color-opacity' not in font
        assert font['color-red'] == 1.0
        assert font['color-green'] == 1.0
        assert font['color-blue'] == 1.0

    def test_font_has_tracking(self):
        result = keystroke_callout('Ctrl+C')
        assert result['font']['tracking'] == 0.0


# ── Bug 10: keystroke_callout hasDropShadow should be 0.0 not False ──


class TestKeystrokeCalloutDropShadowType:
    """hasDropShadow must be 0.0 (float), not False (bool)."""

    def test_has_drop_shadow_is_float(self):
        result = keystroke_callout('Ctrl+C')
        assert result['hasDropShadow'] == 0.0
        assert isinstance(result['hasDropShadow'], float)
        assert not isinstance(result['hasDropShadow'], bool)


class TestKeystrokeCalloutStandardKeys:
    """keystroke_callout must include the same layout keys as text()."""

    def test_has_word_wrap(self):
        result = keystroke_callout('Ctrl+C')
        assert result['word-wrap'] == 1.0

    def test_has_line_spacing(self):
        result = keystroke_callout('Ctrl+C')
        assert result['line-spacing'] == 0.0

    def test_has_horizontal_alignment(self):
        result = keystroke_callout('Ctrl+C')
        assert result['horizontal-alignment'] == 'center'

    def test_has_vertical_alignment(self):
        result = keystroke_callout('Ctrl+C')
        assert result['vertical-alignment'] == 'center'

    def test_has_resize_behavior(self):
        result = keystroke_callout('Ctrl+C')
        assert result['resize-behavior'] == 'resizeText'


# ── Bug 9: arrow() color vs stroke_color conflict ──────────────────


class TestArrowColorStrokeColorConflict:
    def test_explicit_stroke_color_preserved_when_color_absent(self):
        from camtasia.annotations.types import Color
        sc = Color(0.1, 0.2, 0.3, 0.9)
        result = arrow(stroke_color=sc)
        assert result['stroke-color-red'] == 0.1
        assert result['stroke-color-green'] == 0.2
        assert result['stroke-color-blue'] == 0.3
        assert result['stroke-color-opacity'] == 0.9

    def test_color_and_stroke_color_raises(self):
        from camtasia.annotations.types import Color
        with pytest.raises(ValueError, match='either color or stroke_color'):
            arrow(color=(0.5, 0.5, 0.5), stroke_color=Color(1.0, 0.0, 0.0))

    def test_color_tuple_used_when_no_stroke_color(self):
        result = arrow(color=(0.1, 0.2, 0.3))
        assert result['stroke-color-red'] == 0.1
        assert result['stroke-color-green'] == 0.2
        assert result['stroke-color-blue'] == 0.3
        assert result['stroke-color-opacity'] == 1.0


# ── Bug 10: arrow() color parameter alpha support ──────────────────


class TestArrowColorAlpha:
    def test_color_4_tuple_preserves_alpha(self):
        result = arrow(color=(0.1, 0.2, 0.3, 0.4))
        assert result['stroke-color-opacity'] == 0.4

    def test_color_3_tuple_defaults_alpha_to_one(self):
        result = arrow(color=(0.1, 0.2, 0.3))
        assert result['stroke-color-opacity'] == 1.0



# ── Bug 10: highlight() uses flat values matching rectangle() ──


class TestHighlightFlatValues:
    """highlight() should use flat scalar values, not animated-parameter dicts."""

    def test_width_is_flat(self):
        result = highlight(width=300)
        assert result['width'] == 300
        assert not isinstance(result['width'], dict)

    def test_height_is_flat(self):
        result = highlight(height=150)
        assert result['height'] == 150
        assert not isinstance(result['height'], dict)

    def test_fill_colors_are_flat(self):
        result = highlight(color=(0.5, 0.6, 0.7, 0.8))
        assert result['fill-color-red'] == 0.5
        assert result['fill-color-green'] == 0.6
        assert result['fill-color-blue'] == 0.7
        assert result['fill-color-opacity'] == 0.8
        assert not isinstance(result['fill-color-red'], dict)

    def test_has_corner_radius(self):
        result = highlight()
        assert result['corner-radius'] == 0.0

    def test_no_stroke_width_key(self):
        result = highlight()
        assert 'stroke-width' not in result


class TestSquareDefaultStrokeColor:
    """Bug 13: square() default stroke_color should use float 0.0, not int 0."""

    def test_default_stroke_color_is_valid(self):
        result = square("test", "Helvetica", "Bold")
        # stroke-color-red should be 0.0 (float), not 0 (int)
        assert result['stroke-color-red'] == 0.0
        assert isinstance(result['stroke-color-red'], float)
        assert result['stroke-color-green'] == 0.5
        assert result['stroke-color-blue'] == 0.5


class TestCalloutFontNoColorOpacity:
    """Bug 13: text()/square() font dict should not include color-opacity."""

    def test_text_font_no_color_opacity(self):
        from camtasia.annotations.callouts import text
        result = text('Hello', 'Arial', 'Bold')
        assert 'color-opacity' not in result['font']

    def test_square_font_no_color_opacity(self):
        from camtasia.annotations.callouts import square
        result = square('Hello', 'Arial', 'Bold')
        assert 'color-opacity' not in result['font']

    def test_keystroke_font_no_color_opacity(self):
        result = keystroke_callout('Ctrl+C')
        assert 'color-opacity' not in result['font']
