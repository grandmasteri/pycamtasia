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
    assert result['width']['defaultValue'] == 200
    assert result['height']['defaultValue'] == 100
    assert result['fill-color-red']['defaultValue'] == 1.0
    assert result['fill-color-green']['defaultValue'] == 1.0
    assert result['fill-color-blue']['defaultValue'] == 0.0
    assert result['fill-color-opacity']['defaultValue'] == 0.3
    assert result['fill-style'] == 'solid'
    assert result['stroke-width']['defaultValue'] == 0.0


def test_highlight_custom_color():
    result = highlight(color=(0.5, 0.5, 0.8, 0.7))
    assert result['fill-color-red']['defaultValue'] == 0.5
    assert result['fill-color-green']['defaultValue'] == 0.5
    assert result['fill-color-blue']['defaultValue'] == 0.8
    assert result['fill-color-opacity']['defaultValue'] == 0.7


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
        assert 'color-opacity' in font
        assert font['color-red'] == 1.0
        assert font['color-green'] == 1.0
        assert font['color-blue'] == 1.0
        assert font['color-opacity'] == 1.0

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
