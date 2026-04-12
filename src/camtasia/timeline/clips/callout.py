"""Callout (text overlay) clip."""
from __future__ import annotations

from typing import Any, Self

from .base import BaseClip


class CalloutBuilder:
    """Fluent builder for creating styled Callout clips.

    Usage:
        builder = CalloutBuilder('Hello World')
        builder.font('Montserrat', weight=700, size=48)
        builder.color(fill=(0, 0, 0, 255), font=(255, 255, 255, 255))
        builder.position(100, 200)
        builder.size(400, 100)
        # Then pass builder to track.add_callout_from_builder()
    """

    def __init__(self, text: str) -> None:
        self.text = text
        self._font_name: str = 'Montserrat'
        self._font_weight: int = 400
        self._font_size: float = 36.0
        self._fill_color: tuple[int, int, int, int] | None = None
        self._font_color: tuple[int, int, int, int] | None = None
        self._stroke_color: tuple[int, int, int, int] | None = None
        self._x: float = 0.0
        self._y: float = 0.0
        self._width: float | None = None
        self._height: float | None = None
        self._alignment: str = 'center'

    def font(self, name: str = 'Montserrat', *, weight: int = 400, size: float = 36.0) -> CalloutBuilder:
        """Set font properties."""
        self._font_name = name
        self._font_weight = weight
        self._font_size = size
        return self

    def color(
        self,
        *,
        fill: tuple[int, int, int, int] | None = None,
        font: tuple[int, int, int, int] | None = None,
        stroke: tuple[int, int, int, int] | None = None,
    ) -> CalloutBuilder:
        """Set colors as RGBA 0-255 tuples."""
        self._fill_color = fill
        self._font_color = font
        self._stroke_color = stroke
        return self

    def position(self, x: float, y: float) -> CalloutBuilder:
        """Set canvas position."""
        self._x = x
        self._y = y
        return self

    def size(self, width: float, height: float) -> CalloutBuilder:
        """Set dimensions."""
        self._width = width
        self._height = height
        return self

    def alignment(self, align: str) -> CalloutBuilder:
        """Set horizontal alignment ('left', 'center', 'right')."""
        self._alignment = align
        return self


class Callout(BaseClip):
    """Text overlay / annotation clip.

    The callout definition lives in the ``def`` key of the clip dict.

    Args:
        data: The raw clip dict.
    """

    @property
    def definition(self) -> dict[str, Any]:
        """The full callout ``def`` dict."""
        return self._data.get('def', {})

    @property
    def text(self) -> str:
        """Callout text content."""
        return self.definition.get('text', '')

    @text.setter
    def text(self, value: str) -> None:
        self._data.setdefault('def', {})['text'] = value

    @property
    def font(self) -> dict[str, Any]:
        """Font definition dict."""
        return self.definition.get('font', {})

    @property
    def kind(self) -> str:
        """Callout kind (e.g. ``'remix'``)."""
        return self.definition.get('kind', '')

    @property
    def shape(self) -> str:
        """Callout shape (e.g. ``'text'``)."""
        return self.definition.get('shape', '')

    @property
    def style(self) -> str:
        """Callout style (e.g. ``'basic'``)."""
        return self.definition.get('style', '')

    @style.setter
    def style(self, value: str) -> None:
        self._data.setdefault('def', {})['style'] = value

    @property
    def width(self) -> float:
        """Callout width."""
        return self.definition.get('width', 0.0)

    @width.setter
    def width(self, value: float) -> None:
        self._data.setdefault('def', {})['width'] = value

    @property
    def height(self) -> float:
        """Callout height."""
        return self.definition.get('height', 0.0)

    @height.setter
    def height(self, value: float) -> None:
        self._data.setdefault('def', {})['height'] = value

    @property
    def horizontal_alignment(self) -> str:
        """Horizontal text alignment (e.g. ``'center'``)."""
        return self.definition.get('horizontal-alignment', '')

    @horizontal_alignment.setter
    def horizontal_alignment(self, value: str) -> None:
        self._data.setdefault('def', {})['horizontal-alignment'] = value

    @property
    def fill_color(self) -> tuple[float, float, float, float]:
        """Fill color as ``(r, g, b, opacity)``."""
        d = self.definition
        return (
            d.get('fill-color-red', 0.0),
            d.get('fill-color-green', 0.0),
            d.get('fill-color-blue', 0.0),
            d.get('fill-color-opacity', 1.0),
        )

    @fill_color.setter
    def fill_color(self, rgba: tuple[float, float, float, float]) -> None:
        d = self._data.setdefault('def', {})
        d['fill-color-red'] = rgba[0]
        d['fill-color-green'] = rgba[1]
        d['fill-color-blue'] = rgba[2]
        d['fill-color-opacity'] = rgba[3]

    @property
    def stroke_color(self) -> tuple[float, float, float, float]:
        """Stroke color as ``(r, g, b, opacity)``."""
        d = self.definition
        return (
            d.get('stroke-color-red', 0.0),
            d.get('stroke-color-green', 0.0),
            d.get('stroke-color-blue', 0.0),
            d.get('stroke-color-opacity', 1.0),
        )

    @stroke_color.setter
    def stroke_color(self, rgba: tuple[float, float, float, float]) -> None:
        d = self._data.setdefault('def', {})
        d['stroke-color-red'] = rgba[0]
        d['stroke-color-green'] = rgba[1]
        d['stroke-color-blue'] = rgba[2]
        d['stroke-color-opacity'] = rgba[3]

    @property
    def corner_radius(self) -> float:
        """Corner radius for rounded shapes."""
        return self.definition.get('corner-radius', 0.0)

    @corner_radius.setter
    def corner_radius(self, value: float) -> None:
        self._data.setdefault('def', {})['corner-radius'] = value

    @property
    def tail_position(self) -> tuple[float, float]:
        """Tail position as ``(x, y)``."""
        d = self.definition
        return (d.get('tail-x', 0.0), d.get('tail-y', 0.0))

    @tail_position.setter
    def tail_position(self, xy: tuple[float, float]) -> None:
        d = self._data.setdefault('def', {})
        d['tail-x'] = xy[0]
        d['tail-y'] = xy[1]

    # ------------------------------------------------------------------
    # L2 convenience methods
    # ------------------------------------------------------------------

    def set_font(
        self,
        name: str,
        weight: str = 'Regular',
        size: float = 64.0,
    ) -> Self:
        """Update the callout's font properties.

        Args:
            name: Font family name (e.g. ``'Arial'``).
            weight: Font weight (e.g. ``'Regular'``, ``'Bold'``).
            size: Font size in points.

        Returns:
            Self for chaining.
        """
        font = self._data.setdefault('def', {}).setdefault('font', {})
        font['name'] = name
        font['weight'] = weight
        font['size'] = size
        return self

    def set_colors(
        self,
        fill: tuple[float, float, float, float] | None = None,
        stroke: tuple[float, float, float, float] | None = None,
        font_color: tuple[float, float, float] | None = None,
    ) -> Self:
        """Set fill, stroke, and/or font RGBA colors.

        Args:
            fill: Fill color as ``(r, g, b, opacity)``, or ``None`` to skip.
            stroke: Stroke color as ``(r, g, b, opacity)``, or ``None`` to skip.
            font_color: Font color as ``(r, g, b)``, or ``None`` to skip.

        Returns:
            Self for chaining.
        """
        if fill is not None:
            self.fill_color = fill
        if stroke is not None:
            self.stroke_color = stroke
        if font_color is not None:
            font = self._data.setdefault('def', {}).setdefault('font', {})
            font['color-red'] = font_color[0]
            font['color-green'] = font_color[1]
            font['color-blue'] = font_color[2]
        return self

    def resize(self, width: float, height: float) -> Self:
        """Set callout dimensions.

        Args:
            width: New width.
            height: New height.

        Returns:
            Self for chaining.
        """
        self.width = width
        self.height = height
        return self

    def position(self, x: float, y: float) -> Self:
        """Set the callout's position on the canvas.

        Args:
            x: Horizontal translation.
            y: Vertical translation.

        Returns:
            Self for chaining.
        """
        params = self._data.setdefault('parameters', {})
        params['translation0'] = x
        params['translation1'] = y
        return self

    def set_alignment(self, horizontal: str, vertical: str) -> Self:
        """Set text alignment.

        Args:
            horizontal: Horizontal alignment (e.g. ``'center'``, ``'left'``).
            vertical: Vertical alignment (e.g. ``'center'``, ``'top'``).

        Returns:
            Self for chaining.
        """
        d = self._data.setdefault('def', {})
        d['horizontal-alignment'] = horizontal
        d['vertical-alignment'] = vertical
        return self

    def set_size(self, width: float, height: float) -> Self:
        """Set callout dimensions and enable text resizing.

        Args:
            width: Callout width.
            height: Callout height.

        Returns:
            Self for chaining.
        """
        d = self._data.setdefault('def', {})
        d['width'] = width
        d['height'] = height
        d['resize-behavior'] = 'resizeText'
        return self

    def add_behavior(self, preset: str = 'Reveal') -> Self:
        """Add a text behavior animation effect.

        Args:
            preset: Behavior preset name (``'Reveal'``, ``'Sliding'``).

        Returns:
            Self for chaining.
        """
        from camtasia.templates.behavior_presets import get_behavior_preset
        effect = get_behavior_preset(preset, self.duration)
        self._data.setdefault('effects', []).append(effect)
        return self