"""Callout annotations.
"""
from __future__ import annotations

import json
from pathlib import Path

from camtasia.timeline.clips.callout import _WEIGHT_MAP

from .types import Color, FillStyle, HorizontalAlignment, StrokeStyle, VerticalAlignment

_DEFAULT_FAVORITES_DIR = Path.home() / '.pycamtasia' / 'favorites'


def save_as_favorite(callout: dict, name: str, favorites_dir: Path | None = None) -> Path:
    """Write a callout dict as JSON to the favorites directory.

    Args:
        callout: Callout definition dict.
        name: Favorite name (used as the filename stem).
        favorites_dir: Directory to store favorites. Defaults to
            ``~/.pycamtasia/favorites/``.

    Returns:
        Path to the saved JSON file.
    """
    d = favorites_dir or _DEFAULT_FAVORITES_DIR
    d.mkdir(parents=True, exist_ok=True)
    path = d / f'{name}.json'
    path.write_text(json.dumps(callout, indent=2))
    return path


def load_favorite(name: str, favorites_dir: Path | None = None) -> dict:
    """Load a callout favorite from JSON.

    Args:
        name: Favorite name (filename stem).
        favorites_dir: Directory containing favorites. Defaults to
            ``~/.pycamtasia/favorites/``.

    Returns:
        The callout definition dict.

    Raises:
        FileNotFoundError: If the favorite does not exist.
    """
    d = favorites_dir or _DEFAULT_FAVORITES_DIR
    path = d / f'{name}.json'
    return json.loads(path.read_text())


def list_favorites(favorites_dir: Path | None = None) -> list[str]:
    """List saved favorite names.

    Args:
        favorites_dir: Directory containing favorites. Defaults to
            ``~/.pycamtasia/favorites/``.

    Returns:
        Sorted list of favorite names (without ``.json`` extension).
    """
    d = favorites_dir or _DEFAULT_FAVORITES_DIR
    if not d.is_dir():
        return []
    return sorted(p.stem for p in d.glob('*.json'))


def delete_favorite(name: str, favorites_dir: Path | None = None) -> None:
    """Delete a saved favorite.

    Args:
        name: Favorite name to delete.
        favorites_dir: Directory containing favorites. Defaults to
            ``~/.pycamtasia/favorites/``.

    Raises:
        FileNotFoundError: If the favorite does not exist.
    """
    d = favorites_dir or _DEFAULT_FAVORITES_DIR
    path = d / f'{name}.json'
    path.unlink()


def _text_attributes(text: str, font_name: str, font_weight: str | int, font_size: float, font_color: Color) -> list[dict]:
    """Build the 8 standard text attribute dicts for Camtasia."""
    text_len = len(text)
    fg_color = f"({round(font_color.red*255)},{round(font_color.green*255)},{round(font_color.blue*255)},{round(font_color.opacity*255)})"
    weight_int = _WEIGHT_MAP.get(font_weight, 400) if isinstance(font_weight, str) else int(font_weight)
    return [
        {"name": "underline", "rangeEnd": text_len, "rangeStart": 0, "value": 0, "valueType": "int"},
        {"name": "fontSize", "rangeEnd": text_len, "rangeStart": 0, "value": font_size, "valueType": "double"},
        {"name": "fontName", "rangeEnd": text_len, "rangeStart": 0, "value": font_name, "valueType": "string"},
        {"name": "kerning", "rangeEnd": text_len, "rangeStart": 0, "value": 0.0, "valueType": "double"},
        {"name": "strikethrough", "rangeEnd": text_len, "rangeStart": 0, "value": 0, "valueType": "int"},
        {"name": "fontWeight", "rangeEnd": text_len, "rangeStart": 0, "value": weight_int, "valueType": "int"},
        {"name": "fontItalic", "rangeEnd": text_len, "rangeStart": 0, "value": 0, "valueType": "int"},
        {"name": "fgColor", "rangeEnd": text_len, "rangeStart": 0, "value": fg_color, "valueType": "color"},
    ]


def text(text,
         font_name,
         font_weight,
         font_size=96.0,
         font_color=None,
         height=250.0,
         width=400.0,
         horizontal_alignment=HorizontalAlignment.Center,
         vertical_alignment=VerticalAlignment.Center,
         line_spacing=0.0
         ):
    """Create a text callout annotation dict."""
    if font_color is None:
        font_color = Color(1.0, 1.0, 1.0)
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
                    "value": _text_attributes(text, font_name, font_weight, font_size, font_color),
                    "duration": 0
                }
            ]
        }
    }


def square(text,
           font_name,
           font_weight,
           font_size=64.0,
           font_color=None,
           fill_color=None,
           fill_style=FillStyle.Solid,
           stroke_color=None,
           stroke_width=2.0,
           stroke_style=StrokeStyle.Solid,
           height=150.0,
           width=350.0,
           horizontal_alignment=HorizontalAlignment.Center,
           vertical_alignment=VerticalAlignment.Center,
           line_spacing=0.0):
    """Create a square text callout annotation dict."""
    if font_color is None:
        font_color = Color(0.0, 0.0, 0.0)
    if fill_color is None:
        fill_color = Color(1.0, 1.0, 1.0)
    if stroke_color is None:
        stroke_color = Color(0.0, 0.5, 0.5)
    return {
        "kind": "remix",
        "shape": "text-rectangle",
        "style": "basic",
        "corner-radius": 0.0,
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
                    "value": _text_attributes(text, font_name, font_weight, font_size, font_color),
                    "duration": 0
                }
            ]
        }
    }


def arrow(
    *,
    tail: tuple[float, float] = (0, 0),
    head: tuple[float, float] = (100, 0),
    color: tuple[float, ...] | None = None,
    stroke_color: Color | None = None,
    fill_color: Color | None = None,
    width: float = 3.0,
) -> dict:
    """Create an arrow annotation dict."""
    if color is not None and stroke_color is not None:
        raise ValueError('Specify either color or stroke_color, not both')
    if stroke_color is None:
        if color is not None:
            stroke_color = Color(color[0], color[1], color[2], color[3] if len(color) > 3 else 1.0)
        else:
            stroke_color = Color(1.0, 0.0, 0.0)
    if fill_color is None:
        fill_color = stroke_color
    return {
        'kind': 'remix',
        'shape': 'arrow',
        'style': 'basic',
        'tail-x': tail[0],
        'tail-y': tail[1],
        'head-x': head[0],
        'head-y': head[1],
        'stroke-color-red': stroke_color.red,
        'stroke-color-green': stroke_color.green,
        'stroke-color-blue': stroke_color.blue,
        'stroke-color-opacity': stroke_color.opacity,
        'stroke-width': float(width),
        'fill-color-red': fill_color.red,
        'fill-color-green': fill_color.green,
        'fill-color-blue': fill_color.blue,
        'fill-color-opacity': fill_color.opacity,
        'fill-style': 'solid',
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
        'width': width,
        'height': height,
        'fill-color-red': r,
        'fill-color-green': g,
        'fill-color-blue': b,
        'fill-color-opacity': a,
        'fill-style': 'solid',
        'corner-radius': 0.0,
        'stroke-color-red': 0.0,
        'stroke-color-green': 0.0,
        'stroke-color-blue': 0.0,
        'stroke-color-opacity': 0.0,
        'stroke-width': 0.0,
        'stroke-style': 'none',
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
    font_color = Color(1.0, 1.0, 1.0)
    return {
        'kind': 'remix',
        'shape': 'text',
        'style': 'keystroke',
        'text': keys,
        'corner-radius': 5.0,
        'enable-ligatures': 0.0,
        'hasDropShadow': 0.0,
        'width': 400.0,
        'height': 100.0,
        'word-wrap': 1.0,
        'line-spacing': 0.0,
        'horizontal-alignment': 'center',
        'vertical-alignment': 'center',
        'resize-behavior': 'resizeText',
        'fill-color-red': 0.2,
        'fill-color-green': 0.2,
        'fill-color-blue': 0.2,
        'fill-color-opacity': 0.9,
        'fill-style': 'solid',
        'stroke-color-red': 0.8,
        'stroke-color-green': 0.8,
        'stroke-color-blue': 0.8,
        'stroke-color-opacity': 1.0,
        'stroke-width': 1.0,
        'stroke-style': 'solid',
        'font': {
            'color-blue': font_color.blue,
            'color-green': font_color.green,
            'color-red': font_color.red,
            'color-opacity': font_color.opacity,
            'size': font_size,
            'tracking': 0.0,
            'name': 'Montserrat',
            'weight': 'Bold',
        },
        'textAttributes': {
            'type': 'textAttributeList',
            'keyframes': [
                {
                    'endTime': 0,
                    'time': 0,
                    'value': _text_attributes(keys, 'Montserrat', 'Bold', font_size, font_color),
                    'duration': 0,
                }
            ],
        },
    }


_SKETCH_SHAPES = frozenset({'circle', 'arrow', 'underline', 'rectangle'})


def sketch_motion_callout(
    shape: str = 'circle',
    *,
    color: tuple[float, float, float, float] = (1, 0, 0, 1),
    stroke_width: float = 4.0,
    draw_time_seconds: float = 1.0,
    size: tuple[float, float] = (200, 200),
    position: tuple[float, float] = (960, 540),
) -> dict:
    """Build a sketch-motion annotation dict matching Camtasia's schema.

    Args:
        shape: Sketch shape. Must be one of 'circle', 'arrow',
            'underline', or 'rectangle'.
        color: RGBA stroke color as floats in [0.0, 1.0].
        stroke_width: Stroke width in points.
        draw_time_seconds: Time in seconds for the draw-on animation.
        size: (width, height) of the annotation in pixels.
        position: (x, y) center position on the canvas.

    Returns:
        Annotation definition dict suitable for a Callout clip's ``def`` key.

    Raises:
        ValueError: If *shape* is not in the allowed set.
    """
    if shape not in _SKETCH_SHAPES:
        raise ValueError(
            f"shape must be one of {sorted(_SKETCH_SHAPES)}, got {shape!r}"
        )
    r, g, b, a = color
    w, h = size
    x, y = position
    return {
        'kind': 'sketch-motion',
        'shape': shape,
        'style': 'basic',
        'width': float(w),
        'height': float(h),
        'position-x': float(x),
        'position-y': float(y),
        'stroke-color-red': float(r),
        'stroke-color-green': float(g),
        'stroke-color-blue': float(b),
        'stroke-color-opacity': float(a),
        'stroke-width': float(stroke_width),
        'draw-time': float(draw_time_seconds),
    }
