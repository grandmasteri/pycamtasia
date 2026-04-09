"""Callout (text overlay) clip."""
from __future__ import annotations

from typing import Any

from .base import BaseClip


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