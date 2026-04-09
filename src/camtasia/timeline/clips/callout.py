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
