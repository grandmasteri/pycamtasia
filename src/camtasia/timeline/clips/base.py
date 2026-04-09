"""Base clip class wrapping the underlying JSON dict."""
from __future__ import annotations

from fractions import Fraction
from typing import Any

EDIT_RATE = 705_600_000
"""Ticks per second. Divisible by 30fps, 60fps, 44100Hz, 48000Hz."""


class BaseClip:
    """Base class for all timeline clip types.

    Wraps a reference to the underlying JSON dict. Mutations go directly
    to the dict so ``project.save()`` always writes the current state.

    Args:
        data: The raw clip dict from the project JSON.
    """

    def __init__(self, data: dict[str, Any]) -> None:
        self._data = data

    # ------------------------------------------------------------------
    # Core properties (read/write unless noted)
    # ------------------------------------------------------------------

    @property
    def id(self) -> int:
        """Unique clip ID."""
        return self._data['id']

    @property
    def clip_type(self) -> str:
        """The ``_type`` string (e.g. ``'AMFile'``, ``'VMFile'``)."""
        return self._data['_type']

    @property
    def start(self) -> int:
        """Timeline position in ticks."""
        return self._data['start']

    @start.setter
    def start(self, value: int) -> None:
        self._data['start'] = value

    @property
    def duration(self) -> int:
        """Playback duration in ticks."""
        return self._data['duration']

    @duration.setter
    def duration(self, value: int) -> None:
        self._data['duration'] = value

    @property
    def media_start(self) -> int | Fraction:
        """Offset into source media in ticks.

        May be a rational fraction string for speed-changed clips.
        """
        raw = self._data['mediaStart']
        if isinstance(raw, str):
            return Fraction(raw)
        return raw

    @media_start.setter
    def media_start(self, value: int | Fraction) -> None:
        self._data['mediaStart'] = value

    @property
    def media_duration(self) -> int | Fraction:
        """Source media window in ticks."""
        raw = self._data['mediaDuration']
        if isinstance(raw, str):
            return Fraction(raw)
        return raw

    @media_duration.setter
    def media_duration(self, value: int | Fraction) -> None:
        self._data['mediaDuration'] = value

    @property
    def scalar(self) -> Fraction:
        """Speed scalar as a ``Fraction``.

        Parses from int, float, or string like ``'51/101'``.
        """
        raw = self._data.get('scalar', 1)
        if isinstance(raw, str):
            return Fraction(raw)
        return Fraction(raw)

    @scalar.setter
    def scalar(self, value: Fraction | int | float | str) -> None:
        self._data['scalar'] = str(Fraction(value))

    def set_speed(self, speed: float) -> None:
        """Set playback speed.

        Args:
            speed: Multiplier where 1.0 is normal, 2.0 is double speed.
                Internally stored as ``1/speed`` since scalar represents
                the fraction of source consumed per output tick.
        """
        self.scalar = Fraction(1, 1) / Fraction(speed).limit_denominator(10000)

    @property
    def effects(self) -> list[dict[str, Any]]:
        """Raw effect dicts (will be wrapped by the effects module later)."""
        return self._data.get('effects', [])

    @property
    def parameters(self) -> dict[str, Any]:
        """Clip parameters dict."""
        return self._data.get('parameters', {})

    @property
    def metadata(self) -> dict[str, Any]:
        """Clip metadata dict."""
        return self._data.get('metadata', {})

    @property
    def animation_tracks(self) -> dict[str, Any]:
        """Animation tracks dict."""
        return self._data.get('animationTracks', {})

    @property
    def visual_animations(self) -> list[dict[str, Any]]:
        """Visual animation array from animationTracks."""
        return self.animation_tracks.get('visual', [])

    @property
    def source_id(self) -> int | None:
        """Source bin ID (``src`` field), or ``None`` if absent."""
        return self._data.get('src')

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------

    @property
    def start_seconds(self) -> float:
        """Timeline position in seconds."""
        return self.start / EDIT_RATE

    @property
    def duration_seconds(self) -> float:
        """Playback duration in seconds."""
        return self.duration / EDIT_RATE

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(id={self.id}, "
            f"start={self.start_seconds:.2f}s, "
            f"duration={self.duration_seconds:.2f}s)"
        )
