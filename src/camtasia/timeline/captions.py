"""Caption styling configuration."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from camtasia.types import _CaptionData


@dataclass
class DynamicCaptionStyle:
    """Style preset for dynamic (word-highlighted) captions.

    Attributes:
        name: Human-readable style name.
        font_name: Font family name.
        font_size: Font size in points.
        fill_color: Text fill color as ``(r, g, b, a)`` 0-255.
        stroke_color: Text stroke color as ``(r, g, b, a)`` 0-255.
        stroke_width: Stroke width in pixels.
        highlight_color: Active-word highlight color as ``(r, g, b, a)`` 0-255.
        background_color: Caption background color as ``(r, g, b, a)`` 0-255.
    """

    name: str
    font_name: str = 'Arial'
    font_size: int = 32
    fill_color: tuple[int, int, int, int] = (255, 255, 255, 255)
    stroke_color: tuple[int, int, int, int] = (0, 0, 0, 255)
    stroke_width: int = 2
    highlight_color: tuple[int, int, int, int] = (255, 255, 0, 255)
    background_color: tuple[int, int, int, int] = (0, 0, 0, 180)


DEFAULT_DYNAMIC_STYLES: dict[str, DynamicCaptionStyle] = {
    'classic': DynamicCaptionStyle(
        name='classic',
        font_name='Arial',
        font_size=32,
        fill_color=(255, 255, 255, 255),
        stroke_color=(0, 0, 0, 255),
        stroke_width=2,
        highlight_color=(255, 255, 0, 255),
        background_color=(0, 0, 0, 180),
    ),
    'bold': DynamicCaptionStyle(
        name='bold',
        font_name='Montserrat',
        font_size=48,
        fill_color=(255, 255, 255, 255),
        stroke_color=(0, 0, 0, 255),
        stroke_width=3,
        highlight_color=(0, 200, 255, 255),
        background_color=(0, 0, 0, 220),
    ),
    'minimal': DynamicCaptionStyle(
        name='minimal',
        font_name='Helvetica',
        font_size=28,
        fill_color=(220, 220, 220, 255),
        stroke_color=(0, 0, 0, 0),
        stroke_width=0,
        highlight_color=(255, 200, 50, 255),
        background_color=(0, 0, 0, 0),
    ),
}


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
        """Get the caption text alignment (0=center, 1=left, 2=right)."""
        return int(self._data.get('alignment', 0))

    @alignment.setter
    def alignment(self, value: int) -> None:
        """Set the caption text alignment (0=center, 1=left, 2=right)."""
        if value not in (0, 1, 2):
            raise ValueError(f'alignment must be 0 (center), 1 (left), or 2 (right), got {value}')
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

    @property
    def default_duration_seconds(self) -> float:
        """Get the default caption duration in seconds."""
        return float(self._data.get('defaultDurationSeconds', 4.0))

    @default_duration_seconds.setter
    def default_duration_seconds(self, value: float) -> None:
        """Set the default caption duration in seconds (must be > 0)."""
        if value <= 0:
            raise ValueError(f'default_duration_seconds must be > 0, got {value}')
        self._data['defaultDurationSeconds'] = value

    def __repr__(self) -> str:
        return f'CaptionAttributes(font={self.font_name!r}, size={self.font_size}, lang={self.lang!r})'

    def active_word_at(
        self,
        time_seconds: float,
        words: list[str],
        clip_duration_seconds: float,
    ) -> str | None:
        """Return the word that should be highlighted at a given time.

        Stub implementation: assumes even distribution of words across the
        clip duration.

        Args:
            time_seconds: Playback time in seconds (relative to clip start).
            words: Ordered list of caption words.
            clip_duration_seconds: Total clip duration in seconds.

        Returns:
            The active word, or None if *time_seconds* is out of range or
            *words* is empty.
        """
        if not words or clip_duration_seconds <= 0:
            return None
        if time_seconds < 0 or time_seconds > clip_duration_seconds:
            return None
        word_duration = clip_duration_seconds / len(words)
        index = int(time_seconds / word_duration)
        index = min(index, len(words) - 1)
        return words[index]
