"""Caption styling configuration."""
from __future__ import annotations
from typing import Any

from camtasia.types import _CaptionData


class CaptionAttributes:
    """Timeline-level caption styling configuration.
    
    Controls the appearance of captions/subtitles when displayed.
    """
    
    def __init__(self, data: dict[str, Any]) -> None:
        self._data: _CaptionData = data  # type: ignore[assignment]
    
    @property
    def enabled(self) -> bool:
        """Get whether captions are enabled."""
        return bool(self._data.get('enabled', True))
    
    @enabled.setter
    def enabled(self, value: bool) -> None:
        """Set whether captions are enabled."""
        self._data['enabled'] = value
    
    @property
    def font_name(self) -> str:
        """Get the caption font name."""
        return self._data.get('fontName', 'Arial')
    
    @font_name.setter
    def font_name(self, value: str) -> None:
        """Set the caption font name."""
        self._data['fontName'] = value
    
    @property
    def font_size(self) -> int:
        """Get the caption font size."""
        return int(self._data.get('fontSize', 32))
    
    @font_size.setter
    def font_size(self, value: int) -> None:
        """Set the caption font size (must be >= 1)."""
        if value < 1:
            raise ValueError(f'font_size must be >= 1, got {value}')
        self._data['fontSize'] = value
    
    @property
    def background_color(self) -> list[int]:
        """Get the caption background color as an RGBA list."""
        return self._data.get('backgroundColor', [0, 0, 0, 204])
    
    @background_color.setter
    def background_color(self, value: list[int]) -> None:
        """Set the caption background color as an RGBA list."""
        self._data['backgroundColor'] = value
    
    @property
    def foreground_color(self) -> list[int]:
        """Get the caption foreground color as an RGBA list."""
        return self._data.get('foregroundColor', [255, 255, 255, 255])
    
    @foreground_color.setter
    def foreground_color(self, value: list[int]) -> None:
        """Set the caption foreground color as an RGBA list."""
        self._data['foregroundColor'] = value
    
    @property
    def lang(self) -> str:
        """Get the caption language code."""
        return self._data.get('lang', 'en')
    
    @lang.setter
    def lang(self, value: str) -> None:
        """Set the caption language code."""
        self._data['lang'] = value
    
    @property
    def alignment(self) -> int:
        """Get the caption text alignment (0=left, 1=center, 2=right)."""
        return int(self._data.get('alignment', 0))
    
    @alignment.setter
    def alignment(self, value: int) -> None:
        """Set the caption text alignment (0=left, 1=center, 2=right)."""
        if value not in (0, 1, 2):
            raise ValueError(f'alignment must be 0 (left), 1 (center), or 2 (right), got {value}')
        self._data['alignment'] = value
    
    @property
    def opacity(self) -> float:
        """Get the caption background opacity (0.0-1.0)."""
        return float(self._data.get('opacity', 0.5))
    
    @opacity.setter
    def opacity(self, value: float) -> None:
        """Set the caption background opacity (0.0-1.0)."""
        if not 0.0 <= value <= 1.0:
            raise ValueError(f'opacity must be 0.0-1.0, got {value}')
        self._data['opacity'] = value
    
    @property
    def background_enabled(self) -> bool:
        """Get whether the caption background is enabled."""
        return bool(self._data.get('backgroundEnabled', True))
    
    @background_enabled.setter
    def background_enabled(self, value: bool) -> None:
        """Set whether the caption background is enabled."""
        self._data['backgroundEnabled'] = value
    
    def __repr__(self) -> str:
        return f'CaptionAttributes(font={self.font_name!r}, size={self.font_size}, lang={self.lang!r})'
