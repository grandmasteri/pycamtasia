"""Caption styling configuration."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar

if TYPE_CHECKING:
    from camtasia.timeline.clips.callout import Callout
    from camtasia.types import _CaptionData

_DEFAULT_PRESETS_DIR = Path.home() / '.pycamtasia' / 'dynamic_caption_presets'


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

    @property
    def position(self) -> dict[str, float]:
        """Get the caption position as ``{'x': ..., 'y': ...}``."""
        x = self._data.get('positionX', 0.5)
        y = self._data.get('positionY', 0.9)
        return {'x': float(x) if x is not None else 0.5, 'y': float(y) if y is not None else 0.9}

    @position.setter
    def position(self, value: dict[str, float]) -> None:
        """Set the caption position from ``{'x': ..., 'y': ...}``."""
        self._data['positionX'] = value['x']
        self._data['positionY'] = value['y']

    _ANCHOR_Y_MAP: ClassVar[dict[str, float]] = {'top': 0.1, 'middle': 0.5, 'bottom': 0.9}
    _Y_ANCHOR_MAP: ClassVar[dict[float, str]] = {v: k for k, v in _ANCHOR_Y_MAP.items()}

    @property
    def vertical_anchor(self) -> str:
        """Vertical anchor: ``'top'``, ``'middle'``, or ``'bottom'``."""
        raw = self._data.get('positionY', 0.9)
        y = float(raw) if raw is not None else 0.9
        return self._Y_ANCHOR_MAP.get(y, 'bottom')

    @vertical_anchor.setter
    def vertical_anchor(self, value: str) -> None:
        """Set vertical anchor: ``'top'``, ``'middle'``, or ``'bottom'``."""
        if value not in self._ANCHOR_Y_MAP:
            raise ValueError(f"vertical_anchor must be 'top', 'middle', or 'bottom', got {value!r}")
        self._data['positionY'] = self._ANCHOR_Y_MAP[value]

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


def _rgba_255_to_float(rgba: tuple[int, int, int, int]) -> tuple[float, float, float, float]:
    """Convert 0-255 RGBA to 0.0-1.0 floats."""
    return (rgba[0] / 255.0, rgba[1] / 255.0, rgba[2] / 255.0, rgba[3] / 255.0)


def apply_dynamic_style(callout: Callout, style: DynamicCaptionStyle) -> None:
    """Apply a *DynamicCaptionStyle* to a Callout clip.

    Sets the callout's font, fill color, stroke color, and background color
    from the style.  Colors in the style are 0-255 integers; the callout
    stores them as 0.0-1.0 floats.

    Args:
        callout: The Callout clip to style.
        style: The dynamic caption style to apply.
    """
    callout.text_properties = {
        'font_name': style.font_name,
        'font_size': float(style.font_size),
        'fill_color': _rgba_255_to_float(style.fill_color),
        'stroke_color': _rgba_255_to_float(style.stroke_color),
        'background_color': _rgba_255_to_float(style.background_color),
    }


def save_dynamic_caption_preset(
    style: DynamicCaptionStyle,
    name: str,
    presets_dir: Path | None = None,
) -> Path:
    """Write a *DynamicCaptionStyle* as JSON to the presets directory.

    Args:
        style: The style to persist.
        name: Preset name (used as the JSON filename stem).
        presets_dir: Override the default presets directory.

    Returns:
        Path to the written JSON file.
    """
    directory = presets_dir or _DEFAULT_PRESETS_DIR
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f'{name}.json'
    path.write_text(json.dumps(asdict(style), indent=2))
    return path


def load_dynamic_caption_preset(
    name: str,
    presets_dir: Path | None = None,
) -> DynamicCaptionStyle:
    """Load a *DynamicCaptionStyle* from the presets directory.

    Args:
        name: Preset name (filename stem without ``.json``).
        presets_dir: Override the default presets directory.

    Returns:
        The loaded style.

    Raises:
        FileNotFoundError: If the preset file does not exist.
    """
    directory = presets_dir or _DEFAULT_PRESETS_DIR
    path = directory / f'{name}.json'
    data = json.loads(path.read_text())
    # Convert color lists back to tuples
    for key in ('fill_color', 'stroke_color', 'highlight_color', 'background_color'):
        if key in data and isinstance(data[key], list):
            data[key] = tuple(data[key])
    return DynamicCaptionStyle(**data)


def list_dynamic_caption_presets(presets_dir: Path | None = None) -> list[str]:
    """List saved dynamic caption preset names.

    Args:
        presets_dir: Override the default presets directory.

    Returns:
        Sorted list of preset names (without ``.json`` extension).
    """
    directory = presets_dir or _DEFAULT_PRESETS_DIR
    if not directory.is_dir():
        return []
    return sorted(p.stem for p in directory.glob('*.json'))


def extend_dynamic_caption(
    callout_data: dict[str, Any],
    new_duration_seconds: float,
    *,
    transcript: list[dict[str, Any]] | None = None,
) -> None:
    """Rescale word timings in a dynamic caption callout to a new duration.

    Scales ``start`` and ``end`` fields in each transcript word entry
    proportionally so the transcript fits the new duration.  If no
    *transcript* is provided, looks for word timings inside
    ``callout_data['metadata']['dynamicCaptionTranscription']['words']``.

    Args:
        callout_data: The raw callout clip dict.
        new_duration_seconds: Target duration in seconds.
        transcript: Optional explicit word list; each entry must have
            ``start`` and ``end`` float keys (seconds).
    """
    from camtasia.timing import seconds_to_ticks, ticks_to_seconds

    old_duration = callout_data.get('duration', 0)
    if old_duration <= 0:
        return
    old_seconds = ticks_to_seconds(old_duration)
    if old_seconds <= 0:
        return
    ratio = new_duration_seconds / old_seconds

    words = transcript
    if words is None:
        words = (
            callout_data
            .get('metadata', {})
            .get('dynamicCaptionTranscription', {})
            .get('words')
        )
    if words:
        for w in words:
            if 'start' in w:
                w['start'] = w['start'] * ratio
            if 'end' in w:
                w['end'] = w['end'] * ratio

    callout_data['duration'] = seconds_to_ticks(new_duration_seconds)
