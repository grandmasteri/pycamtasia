"""Caption styling configuration."""
from __future__ import annotations
from typing import Any


class CaptionAttributes:
    """Timeline-level caption styling configuration.
    
    Controls the appearance of captions/subtitles when displayed.
    """
    
    def __init__(self, data: dict[str, Any]) -> None:
        self._data = data
    
    @property
    def enabled(self) -> bool:
        return self._data.get('enabled', True)
    
    @enabled.setter
    def enabled(self, value: bool) -> None:
        self._data['enabled'] = value
    
    @property
    def font_name(self) -> str:
        return self._data.get('fontName', 'Arial')
    
    @font_name.setter
    def font_name(self, value: str) -> None:
        self._data['fontName'] = value
    
    @property
    def font_size(self) -> int:
        return self._data.get('fontSize', 32)
    
    @font_size.setter
    def font_size(self, value: int) -> None:
        self._data['fontSize'] = value
    
    @property
    def background_color(self) -> list[int]:
        return self._data.get('backgroundColor', [0, 0, 0, 204])
    
    @background_color.setter
    def background_color(self, value: list[int]) -> None:
        self._data['backgroundColor'] = value
    
    @property
    def foreground_color(self) -> list[int]:
        return self._data.get('foregroundColor', [255, 255, 255, 255])
    
    @foreground_color.setter
    def foreground_color(self, value: list[int]) -> None:
        self._data['foregroundColor'] = value
    
    @property
    def lang(self) -> str:
        return self._data.get('lang', 'en')
    
    @lang.setter
    def lang(self, value: str) -> None:
        self._data['lang'] = value
    
    @property
    def alignment(self) -> int:
        return self._data.get('alignment', 0)
    
    @alignment.setter
    def alignment(self, value: int) -> None:
        self._data['alignment'] = value
    
    @property
    def opacity(self) -> float:
        return self._data.get('opacity', 0.5)
    
    @opacity.setter
    def opacity(self, value: float) -> None:
        self._data['opacity'] = value
    
    @property
    def background_enabled(self) -> bool:
        return self._data.get('backgroundEnabled', True)
    
    @background_enabled.setter
    def background_enabled(self, value: bool) -> None:
        self._data['backgroundEnabled'] = value
    
    def __repr__(self) -> str:
        return f'CaptionAttributes(font={self.font_name!r}, size={self.font_size}, lang={self.lang!r})'
