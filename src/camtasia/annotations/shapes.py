"""Shape annotations."""

from .types import Color, FillStyle, StrokeStyle


def rectangle(fill_color=None,
              fill_style=FillStyle.Solid,
              stroke_color=None,
              stroke_width=6.0,
              stroke_style=StrokeStyle.Solid,
              height=180.0,
              width=240.0,
              corner_radius=0.0,
              gradient_stops=None,
              ):
    """Create a rectangle shape annotation dict.

    Args:
        corner_radius: Corner radius in points (0.0 = sharp corners).
        gradient_stops: Optional list of ``(position, Color)`` tuples for
            gradient fill.  When provided, *fill_style* is forced to
            ``FillStyle.Gradient``.
    """
    if fill_color is None:
        fill_color = Color(0.0, 0.0, 0.0, 0.0)
    if stroke_color is None:
        stroke_color = Color(1.0, 1.0, 1.0, 1.0)
    result = {
        "kind": "remix",
        "shape": "shape-rectangle",
        "style": "basic",
        "corner-radius": float(corner_radius),
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
    if gradient_stops is not None:
        result["fill-style"] = FillStyle.Gradient.value
        result["gradient-stops"] = [
            {"position": pos, "color-red": c.red, "color-green": c.green,
             "color-blue": c.blue, "color-opacity": c.opacity}
            for pos, c in gradient_stops
        ]
    return result


def ellipse(fill_color=None,
            fill_style=FillStyle.Solid,
            stroke_color=None,
            stroke_width=6.0,
            stroke_style=StrokeStyle.Solid,
            height=180.0,
            width=240.0,
            ):
    """Create an ellipse/circle shape annotation dict.

    Args:
        fill_color: Interior fill color.
        fill_style: Fill style (solid, gradient).
        stroke_color: Border color.
        stroke_width: Border width in points.
        stroke_style: Border style.
        height: Ellipse height in pixels.
        width: Ellipse width in pixels.

    Returns:
        Annotation definition dict with ``shape-ellipse``.
    """
    if fill_color is None:
        fill_color = Color(0.0, 0.0, 0.0, 0.0)
    if stroke_color is None:
        stroke_color = Color(1.0, 1.0, 1.0, 1.0)
    return {
        "kind": "remix",
        "shape": "shape-ellipse",
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


def triangle(fill_color=None,
             fill_style=FillStyle.Solid,
             stroke_color=None,
             stroke_width=6.0,
             stroke_style=StrokeStyle.Solid,
             height=180.0,
             width=240.0,
             ):
    """Create a triangle shape annotation dict.

    Args:
        fill_color: Interior fill color.
        fill_style: Fill style (solid, gradient).
        stroke_color: Border color.
        stroke_width: Border width in points.
        stroke_style: Border style.
        height: Triangle height in pixels.
        width: Triangle width in pixels.

    Returns:
        Annotation definition dict with ``shape-triangle``.
    """
    if fill_color is None:
        fill_color = Color(0.0, 0.0, 0.0, 0.0)
    if stroke_color is None:
        stroke_color = Color(1.0, 1.0, 1.0, 1.0)
    return {
        "kind": "remix",
        "shape": "shape-triangle",
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
