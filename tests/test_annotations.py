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
