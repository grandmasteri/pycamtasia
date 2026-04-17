"""Callout annotations.
"""

from .types import Color, FillStyle, HorizontalAlignment, StrokeStyle, VerticalAlignment


def text(text,
         font_name,
         font_weight,
         font_size=96.0,
         font_color=Color(1.0, 1.0, 1.0),
         height=250.0,
         width=400.0,
         horizontal_alignment=HorizontalAlignment.Center,
         vertical_alignment=VerticalAlignment.Center,
         line_spacing=0.0
         ):
    """Create a text callout annotation dict."""
    return {
        "kind": "remix",
        "shape": "text",
        "style": "basic",
        "height": float(height),
        "line-spacing": line_spacing,
        "width": float(width),
        "word-wrap": 1.0,
        "horizontal-alignment": horizontal_alignment.value,
        "resize-behavior": "resizeText",
        "text": text,
        "vertical-alignment": vertical_alignment.value,
        "font": {
            "color-blue": font_color.blue,
            "color-green": font_color.green,
            "color-red": font_color.red,
            "color-opacity": font_color.opacity,
            "size": font_size,
            "tracking": 0.0,
            "name": font_name,
            "weight": font_weight
        },
        "textAttributes": {
            "type": "textAttributeList",
            "keyframes": [
                {
                    "endTime": 0,
                    "time": 0,
                    "value": [],
                    "duration": 0
                }
            ]
        }
    }


def square(text,
           font_name,
           font_weight,
           font_size=64.0,
           font_color=Color(0.0, 0.0, 0.0),
           fill_color=Color(1.0, 1.0, 1.0),
           fill_style=FillStyle.Solid,
           stroke_color=Color(0, 0.5, 0.5),
           stroke_width=2.0,
           stroke_style=StrokeStyle.Solid,
           height=150.0,
           width=350.0,
           horizontal_alignment=HorizontalAlignment.Center,
           vertical_alignment=VerticalAlignment.Center,
           line_spacing=0.0):
    """Create a square text callout annotation dict."""
    return {
        "kind": "remix",
        "shape": "text-rectangle",
        "style": "basic",
        "fill-color-blue": fill_color.blue,
        "fill-color-green": fill_color.green,
        "fill-color-opacity": fill_color.opacity,
        "fill-color-red": fill_color.red,
        "height": float(height),
        "line-spacing": line_spacing,
        "stroke-color-blue": stroke_color.blue,
        "stroke-color-green": stroke_color.green,
        "stroke-color-opacity": stroke_color.opacity,
        "stroke-color-red": stroke_color.red,
        "stroke-width": float(stroke_width),
        "tail-x": 0.0,
        "tail-y": -20.0,
        "width": float(width),
        "word-wrap": 1.0,
        "fill-style": fill_style.value,
        "horizontal-alignment": horizontal_alignment.value,
        "resize-behavior": "resizeText",
        "stroke-style": stroke_style.value,
        "text": text,
        "vertical-alignment": vertical_alignment.value,
        "font": {
            "color-blue": font_color.blue,
            "color-green": font_color.green,
            "color-opacity": font_color.opacity,
            "color-red": font_color.red,
            "size": font_size,
            "tracking": 0.0,
            "name": font_name,
            "weight": font_weight
        },
        "textAttributes": {
            "type": "textAttributeList",
            "keyframes": [
                {
                    "endTime": 0,
                    "time": 0,
                    "value": [],
                    "duration": 0
                }
            ]
        }
    }


def arrow(
    *,
    tail: tuple[float, float] = (0, 0),
    head: tuple[float, float] = (100, 0),
    color: tuple[float, float, float] | None = None,
    stroke_color: Color = Color(1.0, 0.0, 0.0),
    width: float = 3.0,
) -> dict:
    """Create an arrow annotation dict."""
    if color is not None:
        stroke_color = Color(color[0], color[1], color[2])
    return {
        'kind': 'remix',
        'shape': 'arrow',
        'style': 'basic',
        'tail-x': tail[0],
        'tail-y': tail[1],
        'head-x': head[0],
        'head-y': head[1],
        'stroke-color-red': {'type': 'double', 'defaultValue': stroke_color.red, 'interp': 'linr'},
        'stroke-color-green': {'type': 'double', 'defaultValue': stroke_color.green, 'interp': 'linr'},
        'stroke-color-blue': {'type': 'double', 'defaultValue': stroke_color.blue, 'interp': 'linr'},
        'stroke-color-opacity': {'type': 'double', 'defaultValue': stroke_color.opacity, 'interp': 'linr'},
        'stroke-width': {'type': 'double', 'defaultValue': width, 'interp': 'linr'},
    }


def highlight(
    *,
    width: float = 200,
    height: float = 100,
    color: tuple[float, float, float, float] = (1.0, 1.0, 0.0, 0.3),
) -> dict:
    """Create a highlight annotation dict."""
    r, g, b, a = color
    return {
        'kind': 'remix',
        'shape': 'shape-rectangle',
        'style': 'basic',
        'width': {'type': 'double', 'defaultValue': width, 'interp': 'linr'},
        'height': {'type': 'double', 'defaultValue': height, 'interp': 'linr'},
        'fill-color-red': {'type': 'double', 'defaultValue': r, 'interp': 'linr'},
        'fill-color-green': {'type': 'double', 'defaultValue': g, 'interp': 'linr'},
        'fill-color-blue': {'type': 'double', 'defaultValue': b, 'interp': 'linr'},
        'fill-color-opacity': {'type': 'double', 'defaultValue': a, 'interp': 'linr'},
        'fill-style': 'solid',
        'stroke-width': {'type': 'double', 'defaultValue': 0.0, 'interp': 'linr'},
    }


def keystroke_callout(
    keys: str,
    *,
    font_size: float = 24.0,
) -> dict:
    """Create a keystroke callout annotation dict.

    Args:
        keys: Key combination string (e.g. 'Ctrl+C', 'Cmd+Shift+S').
        font_size: Font size for the keystroke text.
    """
    return {
        'kind': 'remix',
        'shape': 'text',
        'style': 'keystroke',
        'text': keys,
        'font': {
            'name': 'Montserrat',
            'weight': 'Bold',
            'size': {'type': 'double', 'defaultValue': font_size, 'interp': 'linr'},
        },
    }
