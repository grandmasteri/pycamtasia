"""Callout (text overlay) clip."""
from __future__ import annotations

import sys
from typing import Any, NoReturn

if sys.version_info >= (3, 11):  # pragma: no cover
    from typing import Self
else:  # pragma: no cover
    from typing_extensions import Self

from camtasia.types import BehaviorPreset, CalloutShape

from .base import BaseClip

_WEIGHT_MAP = {'Thin': 100, 'Light': 300, 'Regular': 400, 'Medium': 500, 'Bold': 700, 'Black': 900}
_WEIGHT_REVERSE = {v: k for k, v in _WEIGHT_MAP.items()}


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
        if fill is not None:
            self._fill_color = fill
        if font is not None:
            self._font_color = font
        if stroke is not None:
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

    def set_source(self, source_id: int) -> NoReturn:
        raise TypeError('Callout clips do not have a source ID')

    @property
    def definition(self) -> dict[str, Any]:
        """The full callout ``def`` dict."""
        return self._data.get('def', {})  # type: ignore[return-value]

    @property
    def text(self) -> str:
        """Callout text content."""
        return str(self.definition.get('text', ''))

    @text.setter
    def text(self, value: str) -> None:
        """Set the callout text content."""
        d = self._data.setdefault('def', {})  # type: ignore[typeddict-item]
        d['text'] = value
        for kf in d.get('textAttributes', {}).get('keyframes', []):
            for attr in kf.get('value', []):
                attr['rangeEnd'] = len(value)

    @property
    def font(self) -> dict[str, Any]:
        """Font definition dict."""
        return self.definition.get('font', {})  # type: ignore[no-any-return]

    @property
    def kind(self) -> str:
        """Callout kind (e.g. ``'remix'``)."""
        return str(self.definition.get('kind', ''))

    @property
    def shape(self) -> str:
        """Callout shape (e.g. ``'text'``)."""
        return str(self.definition.get('shape', ''))

    @shape.setter
    def shape(self, value: str | CalloutShape) -> None:
        """Set the callout shape."""
        self._data.setdefault('def', {})['shape'] = str(value.value if isinstance(value, CalloutShape) else value)  # type: ignore[typeddict-item]

    @property
    def style(self) -> str:
        """Callout style (e.g. ``'basic'``)."""
        return str(self.definition.get('style', ''))

    @style.setter
    def style(self, value: str) -> None:
        """Set the callout style."""
        self._data.setdefault('def', {})['style'] = value  # type: ignore[typeddict-item]

    @property
    def width(self) -> float:
        """Callout width."""
        val = self.definition.get('width', 0.0)
        return float(val['defaultValue'] if isinstance(val, dict) else val)

    @width.setter
    def width(self, value: float) -> None:
        """Set the callout width."""
        d = self._data.setdefault('def', {})  # type: ignore[typeddict-item]
        existing = d.get('width')
        if isinstance(existing, dict):
            existing['defaultValue'] = value
            existing.pop('keyframes', None)
        else:
            d['width'] = value

    @property
    def height(self) -> float:
        """Callout height."""
        val = self.definition.get('height', 0.0)
        return float(val['defaultValue'] if isinstance(val, dict) else val)

    @height.setter
    def height(self, value: float) -> None:
        """Set the callout height."""
        d = self._data.setdefault('def', {})  # type: ignore[typeddict-item]
        existing = d.get('height')
        if isinstance(existing, dict):
            existing['defaultValue'] = value
            existing.pop('keyframes', None)
        else:
            d['height'] = value

    @property
    def horizontal_alignment(self) -> str:
        """Horizontal text alignment (e.g. ``'center'``)."""
        return str(self.definition.get('horizontal-alignment', ''))

    @horizontal_alignment.setter
    def horizontal_alignment(self, value: str) -> None:
        """Set the horizontal text alignment."""
        self._data.setdefault('def', {})['horizontal-alignment'] = value  # type: ignore[typeddict-item]

    @property
    def fill_color(self) -> tuple[float, float, float, float]:
        """Fill color as ``(r, g, b, opacity)``."""
        d = self.definition

        def _val(key: str, default: float) -> float:
            v = d.get(key, default)
            return float(v['defaultValue']) if isinstance(v, dict) else float(v)

        return (
            _val('fill-color-red', 0.0),
            _val('fill-color-green', 0.0),
            _val('fill-color-blue', 0.0),
            _val('fill-color-opacity', 1.0),
        )

    @fill_color.setter
    def fill_color(self, rgba: tuple[float, float, float, float]) -> None:
        """Set the fill color as an (r, g, b, opacity) tuple."""
        d = self._data.setdefault('def', {})  # type: ignore[typeddict-item]
        color_keys = ('fill-color-red', 'fill-color-green', 'fill-color-blue', 'fill-color-opacity')
        for key, val in zip(color_keys, rgba):
            existing = d.get(key)
            if isinstance(existing, dict):
                existing['defaultValue'] = val
                existing.pop('keyframes', None)
            else:
                d[key] = val

    @property
    def stroke_color(self) -> tuple[float, float, float, float]:
        """Stroke color as ``(r, g, b, opacity)``."""
        d = self.definition

        def _val(key: str, default: float) -> float:
            v = d.get(key, default)
            return float(v['defaultValue']) if isinstance(v, dict) else float(v)

        return (
            _val('stroke-color-red', 0.0),
            _val('stroke-color-green', 0.0),
            _val('stroke-color-blue', 0.0),
            _val('stroke-color-opacity', 1.0),
        )

    @stroke_color.setter
    def stroke_color(self, rgba: tuple[float, float, float, float]) -> None:
        """Set the stroke color as an (r, g, b, opacity) tuple."""
        d = self._data.setdefault('def', {})  # type: ignore[typeddict-item]
        color_keys = ('stroke-color-red', 'stroke-color-green', 'stroke-color-blue', 'stroke-color-opacity')
        for key, val in zip(color_keys, rgba):
            existing = d.get(key)
            if isinstance(existing, dict):
                existing['defaultValue'] = val
                existing.pop('keyframes', None)
            else:
                d[key] = val

    @property
    def corner_radius(self) -> float:
        """Corner radius for rounded shapes."""
        val = self.definition.get('corner-radius', 0.0)
        return float(val['defaultValue'] if isinstance(val, dict) else val)

    @corner_radius.setter
    def corner_radius(self, value: float) -> None:
        """Set the corner radius for rounded shapes."""
        d = self._data.setdefault('def', {})  # type: ignore[typeddict-item]
        existing = d.get('corner-radius')
        if isinstance(existing, dict):
            existing['defaultValue'] = value
            existing.pop('keyframes', None)
        else:
            d['corner-radius'] = value

    @property
    def tail_position(self) -> tuple[float, float]:
        """Tail position as ``(x, y)``."""
        d = self.definition
        return (d.get('tail-x', 0.0), d.get('tail-y', 0.0))

    @tail_position.setter
    def tail_position(self, xy: tuple[float, float]) -> None:
        """Set the tail position as an (x, y) tuple."""
        d = self._data.setdefault('def', {})  # type: ignore[typeddict-item]
        d['tail-x'] = xy[0]
        d['tail-y'] = xy[1]

    # ------------------------------------------------------------------
    # L2 convenience methods
    # ------------------------------------------------------------------

    def set_font(
        self,
        name: str,
        weight: str | int = 'Regular',
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
        font = self._data.setdefault('def', {}).setdefault('font', {})  # type: ignore[typeddict-item]
        font['name'] = name
        if isinstance(weight, int):
            if weight not in _WEIGHT_REVERSE:
                raise ValueError(
                    f'weight {weight} is not a standard font weight. '
                    f'Valid weights: {sorted(_WEIGHT_REVERSE.keys())}'
                )
            font['weight'] = _WEIGHT_REVERSE[weight]
        else:
            if weight not in _WEIGHT_MAP:
                raise ValueError(
                    f'weight {weight!r} is not a standard font weight. '
                    f'Valid weights: {sorted(_WEIGHT_MAP.keys())}'
                )
            font['weight'] = weight
        font['size'] = size
        for kf in self._data.get('def', {}).get('textAttributes', {}).get('keyframes', []):  # type: ignore[attr-defined]
            for attr in kf.get('value', []):
                if attr.get('name') == 'fontName':
                    attr['value'] = name
                elif attr.get('name') == 'fontWeight':
                    attr['value'] = weight if isinstance(weight, int) else _WEIGHT_MAP.get(weight, 400)
                elif attr.get('name') == 'fontSize':
                    attr['value'] = size
        return self

    def set_colors(
        self,
        fill: tuple[float, float, float, float] | None = None,
        stroke: tuple[float, float, float, float] | None = None,
        font_color: tuple[float, ...] | None = None,
    ) -> Self:
        """Set fill, stroke, and/or font RGBA colors.

        Args:
            fill: Fill color as ``(r, g, b, opacity)``, or ``None`` to skip.
            stroke: Stroke color as ``(r, g, b, opacity)``, or ``None`` to skip.
            font_color: Font color as ``(r, g, b, opacity)``, or ``None`` to skip.

        Returns:
            Self for chaining.
        """
        if fill is not None:
            self.fill_color = fill
        if stroke is not None:
            self.stroke_color = stroke
        if font_color is not None:
            font = self._data.setdefault('def', {}).setdefault('font', {})  # type: ignore[typeddict-item]
            font['color-red'] = font_color[0]
            font['color-green'] = font_color[1]
            font['color-blue'] = font_color[2]
            font['color-opacity'] = font_color[3] if len(font_color) > 3 else 1.0
            for kf in self._data.get('def', {}).get('textAttributes', {}).get('keyframes', []):  # type: ignore[attr-defined]
                for attr in kf.get('value', []):
                    if attr.get('name') == 'fgColor':
                        r, g, b = round(font_color[0]*255), round(font_color[1]*255), round(font_color[2]*255)
                        a = round(font_color[3]*255) if len(font_color) > 3 else 255
                        attr['value'] = f'({r},{g},{b},{a})'
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
        """Set the callout position.

        .. deprecated:: Use :meth:`move_to` instead (inherited from BaseClip).
        """
        self.move_to(x, y)
        return self

    def set_alignment(self, horizontal: str, vertical: str) -> Self:
        """Set text alignment.

        Args:
            horizontal: Horizontal alignment (e.g. ``'center'``, ``'left'``).
            vertical: Vertical alignment (e.g. ``'center'``, ``'top'``).

        Returns:
            Self for chaining.
        """
        d = self._data.setdefault('def', {})  # type: ignore[typeddict-item]
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
        d = self._data.setdefault('def', {})  # type: ignore[typeddict-item]
        for key, value in [('width', width), ('height', height)]:
            existing = d.get(key)
            if isinstance(existing, dict):
                existing['defaultValue'] = value
                existing.pop('keyframes', None)
            else:
                d[key] = value
        d['resize-behavior'] = 'resizeText'
        return self

    def add_behavior(self, preset: str | BehaviorPreset = BehaviorPreset.REVEAL) -> Self:
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
