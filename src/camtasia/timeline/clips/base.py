"""Base clip class wrapping the underlying JSON dict."""
from __future__ import annotations

from fractions import Fraction
from typing import Any, Self

from camtasia.effects.base import Effect, effect_from_dict
from camtasia.effects.visual import Glow
from camtasia.timing import seconds_to_ticks

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

    # ------------------------------------------------------------------
    # L2 convenience — time-bounded effects
    # ------------------------------------------------------------------

    def add_glow_timed(
        self,
        start_seconds: float,
        duration_seconds: float,
        radius: float = 35.0,
        intensity: float = 0.35,
        fade_in_seconds: float = 0.4,
        fade_out_seconds: float = 1.0,
    ) -> Glow:
        """Add a time-bounded glow effect with fade-in/out.

        Args:
            start_seconds: Effect start relative to clip, in seconds.
            duration_seconds: Effect duration in seconds.
            radius: Glow radius.
            intensity: Glow intensity.
            fade_in_seconds: Fade-in duration in seconds.
            fade_out_seconds: Fade-out duration in seconds.

        Returns:
            The created :class:`Glow` effect.
        """
        record: dict[str, Any] = {
            'effectName': 'Glow',
            'bypassed': False,
            'category': 'visual',
            'start': seconds_to_ticks(start_seconds),
            'duration': seconds_to_ticks(duration_seconds),
            'parameters': {
                'radius': {'type': 'double', 'defaultValue': radius, 'interp': 'linr'},
                'intensity': {'type': 'double', 'defaultValue': intensity, 'interp': 'linr'},
            },
            'leftEdgeMods': [{'type': 'fadeIn', 'duration': seconds_to_ticks(fade_in_seconds)}],
            'rightEdgeMods': [{'type': 'fadeOut', 'duration': seconds_to_ticks(fade_out_seconds)}],
        }
        self._data.setdefault('effects', []).append(record)
        return Glow(record)

    # ------------------------------------------------------------------
    # L2 — Animation helpers
    # ------------------------------------------------------------------

    def _ensure_visual_tracks(self) -> list[dict[str, Any]]:
        """Return the ``animationTracks.visual`` list, creating it if absent."""
        tracks = self._data.setdefault('animationTracks', {})
        return tracks.setdefault('visual', [])

    def _remove_opacity_tracks(self) -> None:
        """Remove all opacity entries from ``animationTracks.visual``."""
        visual = self._data.get('animationTracks', {}).get('visual')
        if visual is not None:
            self._data['animationTracks']['visual'] = [
                t for t in visual if t.get('track') != 'opacity'
            ]

    def _add_opacity_track(self, keyframes: list[dict[str, Any]]) -> None:
        """Append an opacity animation track entry with the given keyframes."""
        self._ensure_visual_tracks().append({
            'endOffset': 0,
            'startOffset': 0,
            'track': 'opacity',
            'keyframes': keyframes,
        })

    def fade_in(self, duration_seconds: float) -> Self:
        """Add an opacity fade-in (0 → 1) over *duration_seconds*.

        Args:
            duration_seconds: Fade duration in seconds.

        Returns:
            ``self`` for chaining.
        """
        ticks = seconds_to_ticks(duration_seconds)
        self._add_opacity_track([
            {'time': 0, 'value': '0', 'interp': 'linr'},
            {'time': ticks, 'value': '1', 'interp': 'linr'},
        ])
        return self

    def fade_out(self, duration_seconds: float) -> Self:
        """Add an opacity fade-out (1 → 0) ending at the clip's media end.

        Args:
            duration_seconds: Fade duration in seconds.

        Returns:
            ``self`` for chaining.
        """
        ticks = seconds_to_ticks(duration_seconds)
        end = int(self.media_duration)
        self._add_opacity_track([
            {'time': end - ticks, 'value': '1', 'interp': 'linr'},
            {'time': end, 'value': '0', 'interp': 'linr'},
        ])
        return self

    def fade(
        self,
        fade_in_seconds: float = 0.0,
        fade_out_seconds: float = 0.0,
    ) -> Self:
        """Apply fade-in and/or fade-out, replacing existing opacity animations.

        Args:
            fade_in_seconds: Fade-in duration (0 to skip).
            fade_out_seconds: Fade-out duration (0 to skip).

        Returns:
            ``self`` for chaining.
        """
        self._remove_opacity_tracks()
        end = int(self.media_duration)
        kf: list[dict[str, Any]] = []
        if fade_in_seconds > 0:
            in_ticks = seconds_to_ticks(fade_in_seconds)
            kf.append({'time': 0, 'value': '0', 'interp': 'linr'})
            kf.append({'time': in_ticks, 'value': '1', 'interp': 'linr'})
        if fade_out_seconds > 0:
            out_ticks = seconds_to_ticks(fade_out_seconds)
            # If no fade-in, anchor full opacity at the start of the fade-out
            if not kf:
                kf.append({'time': end - out_ticks, 'value': '1', 'interp': 'linr'})
            elif kf[-1]['time'] < end - out_ticks:
                kf.append({'time': end - out_ticks, 'value': '1', 'interp': 'linr'})
            kf.append({'time': end, 'value': '0', 'interp': 'linr'})
        if kf:
            self._add_opacity_track(kf)
        return self

    def set_opacity(self, opacity: float) -> Self:
        """Set a static opacity for the entire clip.

        Args:
            opacity: Opacity value (0.0–1.0).

        Returns:
            ``self`` for chaining.
        """
        self._remove_opacity_tracks()
        self._add_opacity_track([
            {'time': 0, 'value': str(opacity), 'interp': 'linr'},
        ])
        return self

    def clear_animations(self) -> Self:
        """Remove all visual animation entries from the clip.

        Returns:
            ``self`` for chaining.
        """
        self._data.setdefault('animationTracks', {})['visual'] = []
        return self

    # ------------------------------------------------------------------
    # L2 — Effect helpers
    # ------------------------------------------------------------------

    def add_effect(self, effect_data: dict[str, Any]) -> Effect:
        """Append a raw effect dict to this clip's effects list.

        Args:
            effect_data: A complete Camtasia effect dict.

        Returns:
            Wrapped :class:`Effect` instance.
        """
        self._data.setdefault('effects', []).append(effect_data)
        return effect_from_dict(effect_data)

    def add_drop_shadow(
        self,
        offset: float = 5,
        blur: float = 10,
        opacity: float = 0.5,
        angle: float = 5.5,
        color: tuple[float, float, float] = (0, 0, 0),
    ) -> Effect:
        """Add a drop-shadow effect.

        Args:
            offset: Shadow offset distance.
            blur: Blur radius.
            opacity: Shadow opacity (0.0–1.0).
            angle: Shadow angle in degrees.
            color: RGB colour tuple.

        Returns:
            Wrapped :class:`DropShadow` effect.
        """
        return self.add_effect({
            'effectName': 'DropShadow',
            'bypassed': False,
            'category': 'visual',
            'parameters': {
                'angle': {'type': 'double', 'defaultValue': angle, 'interp': 'linr'},
                'offset': {'type': 'double', 'defaultValue': offset, 'interp': 'linr'},
                'blur': {'type': 'double', 'defaultValue': blur, 'interp': 'linr'},
                'opacity': {'type': 'double', 'defaultValue': opacity, 'interp': 'linr'},
                'color-red': {'type': 'double', 'defaultValue': color[0], 'interp': 'linr'},
                'color-green': {'type': 'double', 'defaultValue': color[1], 'interp': 'linr'},
                'color-blue': {'type': 'double', 'defaultValue': color[2], 'interp': 'linr'},
                'color-alpha': {'type': 'double', 'defaultValue': 1.0, 'interp': 'linr'},
            },
        })

    def add_glow(self, radius: float = 35.0, intensity: float = 0.35) -> Effect:
        """Add a glow/bloom effect.

        Args:
            radius: Glow radius.
            intensity: Glow intensity.

        Returns:
            Wrapped :class:`Glow` effect.
        """
        return self.add_effect({
            'effectName': 'Glow',
            'bypassed': False,
            'category': 'visual',
            'parameters': {
                'radius': {'type': 'double', 'defaultValue': radius, 'interp': 'linr'},
                'intensity': {'type': 'double', 'defaultValue': intensity, 'interp': 'linr'},
            },
        })

    def add_round_corners(self, radius: float = 12.0) -> Effect:
        """Add a rounded-corners effect.

        Args:
            radius: Corner radius.

        Returns:
            Wrapped :class:`RoundCorners` effect.
        """
        return self.add_effect({
            'effectName': 'RoundCorners',
            'bypassed': False,
            'category': 'visual',
            'parameters': {
                'radius': {'type': 'double', 'defaultValue': radius, 'interp': 'linr'},
                'topLeft': {'type': 'double', 'defaultValue': True, 'interp': 'linr'},
                'topRight': {'type': 'double', 'defaultValue': True, 'interp': 'linr'},
                'bottomLeft': {'type': 'double', 'defaultValue': True, 'interp': 'linr'},
                'bottomRight': {'type': 'double', 'defaultValue': True, 'interp': 'linr'},
            },
        })

    def remove_effects(self) -> Self:
        """Remove all effects from this clip.

        Returns:
            ``self`` for chaining.
        """
        self._data['effects'] = []
        return self
