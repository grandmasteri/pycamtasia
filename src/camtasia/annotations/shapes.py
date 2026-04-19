"""Callout annotations.
"""

from .types import Color, FillStyle, StrokeStyle


def rectangle(fill_color=None,
              fill_style=FillStyle.Solid,
              stroke_color=None,
              stroke_width=6.0,
              stroke_style=StrokeStyle.Solid,
              height=180.0,
              width=240.0,
              ):
    """Create a rectangle shape annotation dict."""
    if fill_color is None:
        fill_color = Color(0.0, 0.0, 0.0, 0.0)
    if stroke_color is None:
        stroke_color = Color(1.0, 1.0, 1.0, 1.0)
    return {
        "kind": "remix",
        "shape": "shape-rectangle",
        "style": "basic",
        "height": float(height),
        "width": float(width),
        "fill-color-blue": fill_color.blue,
        "fill-color-green": fill_color.green,
        "fill-color-opacity": fill_color.opacity,
        "fill-color-red": fill_color.red,
        "stroke-color-blue": stroke_color.blue,
        "stroke-color-green": stroke_color.green,
        "stroke-color-opacity": stroke_color.opacity,
        "stroke-color-red": stroke_color.red,
        "stroke-width": stroke_width,
        "fill-style": fill_style.value,
        "stroke-style": stroke_style.value
    }
