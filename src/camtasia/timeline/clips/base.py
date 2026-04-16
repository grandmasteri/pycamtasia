"""Base clip class wrapping the underlying JSON dict."""
from __future__ import annotations

from fractions import Fraction
from collections.abc import Callable
from typing import Any, TYPE_CHECKING
import sys
if sys.version_info >= (3, 11):  # pragma: no cover
    from typing import Self
else:  # pragma: no cover
    from typing_extensions import Self

from camtasia.effects.base import Effect, effect_from_dict

if TYPE_CHECKING:
    from camtasia.timeline.track import Track

from camtasia.effects.visual import Glow
from camtasia.timing import seconds_to_ticks
from camtasia.types import BlendMode, ClipSummary, ClipType, EffectName, _ClipData

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
        self._data: _ClipData = data  # type: ignore[assignment]

    # ------------------------------------------------------------------
    # Core properties (read/write unless noted)
    # ------------------------------------------------------------------

    @property
    def id(self) -> int:
        """Unique clip ID."""
        return int(self._data['id'])

    @property
    def clip_type(self) -> str:
        """The ``_type`` string (e.g. ``'AMFile'``, ``'VMFile'``)."""
        return self._data['_type']

    @property
    def is_audio(self) -> bool:
        """Whether this clip is an audio clip."""
        return self.clip_type == ClipType.AUDIO

    @property
    def is_video(self) -> bool:
        """Whether this clip is a video clip."""
        return self.clip_type in (ClipType.VIDEO, ClipType.SCREEN_VIDEO)

    @property
    def is_visible(self) -> bool:
        """Whether this clip is a visual clip (not audio-only)."""
        return not self.is_audio

    @property
    def is_image(self) -> bool:
        """Whether this clip is an image clip."""
        return self.clip_type == ClipType.IMAGE

    @property
    def is_group(self) -> bool:
        """Whether this clip is a group clip."""
        return self.clip_type == ClipType.GROUP

    @property
    def is_callout(self) -> bool:
        """Whether this clip is a callout clip."""
        return self.clip_type == ClipType.CALLOUT

    @property
    def is_stitched(self) -> bool:
        """Whether this clip is a stitched media clip."""
        return self.clip_type == ClipType.STITCHED_MEDIA

    @property
    def is_placeholder(self) -> bool:
        """Whether this clip is a placeholder clip."""
        return self.clip_type == ClipType.PLACEHOLDER

    @property
    def start(self) -> int:
        """Timeline position in ticks."""
        return int(self._data['start'])

    @start.setter
    def start(self, value: int) -> None:
        """Set the start."""
        self._data['start'] = value

    @property
    def duration(self) -> int:
        """Playback duration in ticks."""
        return int(self._data['duration'])

    @duration.setter
    def duration(self, value: int) -> None:
        """Set the duration."""
        self._data['duration'] = value

    @property
    def end_seconds(self) -> float:
        """End time in seconds (start + duration)."""
        from camtasia.timing import ticks_to_seconds
        return ticks_to_seconds(self.start + self.duration)

    @property
    def time_range(self) -> tuple[float, float]:
        """(start_seconds, end_seconds) tuple."""
        return (self.start_seconds, self.end_seconds)

    @property
    def time_range_formatted(self) -> str:
        """Time range as 'MM:SS - MM:SS' string."""
        def _fmt(seconds: float) -> str:
            minutes: int = int(seconds // 60)
            remaining: int = int(seconds % 60)
            return f'{minutes}:{remaining:02d}'
        return f'{_fmt(self.start_seconds)} - {_fmt(self.end_seconds)}'

    @property
    def gain(self) -> float:
        """Audio gain (0.0 = muted, 1.0 = full volume)."""
        return float(self._data.get('attributes', {}).get('gain', 1.0))

    @gain.setter
    def gain(self, value: float) -> None:
        """Set the gain."""
        self._data.setdefault('attributes', {})['gain'] = value

    def is_at(self, time_seconds: float) -> bool:
        """Whether this clip spans the given time point."""
        from camtasia.timing import seconds_to_ticks
        t = seconds_to_ticks(time_seconds)
        return self.start <= t < self.start + self.duration

    def is_between(self, range_start_seconds: float, range_end_seconds: float) -> bool:
        """Whether this clip falls entirely within the given time range."""
        return self.start_seconds >= range_start_seconds and self.end_seconds <= range_end_seconds

    def intersects(self, range_start_seconds: float, range_end_seconds: float) -> bool:
        """Whether this clip overlaps with the given time range at all."""
        return self.start_seconds < range_end_seconds and self.end_seconds > range_start_seconds

    @property
    def is_muted(self) -> bool:
        """Whether this clip's audio is muted (gain == 0)."""
        return self.gain == 0.0

    def mute(self) -> Self:
        """Mute this clip's audio by setting gain to 0.

        Returns:
            ``self`` for chaining.
        """
        self.gain = 0.0
        return self

    @property
    def media_start(self) -> int | float | str | Fraction:  # type: ignore[override]
        """Offset into source media in ticks.

        May be a rational fraction string for speed-changed clips.
        """
        raw = self._data['mediaStart'] # type: ignore[typeddict-item]
        if isinstance(raw, str):
            return Fraction(raw)
        return raw

    @media_start.setter
    def media_start(self, value: int | Fraction) -> None:
        """Set the media start."""
        self._data['mediaStart'] = value # type: ignore[typeddict-item]

    @property
    def media_duration(self) -> int | float | str | Fraction:  # type: ignore[override]
        """Source media window in ticks."""
        raw = self._data.get('mediaDuration', self._data.get('duration', 0))  # type: ignore[typeddict-item]
        if isinstance(raw, str):
            return Fraction(raw)
        return raw

    @media_duration.setter
    def media_duration(self, value: int | Fraction) -> None:
        """Set the media duration."""
        self._data['mediaDuration'] = value # type: ignore[typeddict-item]

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
        """Set the scalar."""
        self._data['scalar'] = str(Fraction(value))

    def set_speed(self, speed: float) -> Self:
        """Set playback speed multiplier.

        Args:
            speed: Speed multiplier (1.0 = normal, 2.0 = double speed, 0.5 = half speed).
        """
        if speed <= 0:
            raise ValueError(f'speed must be > 0, got {speed}')
        scalar_fraction = Fraction(1) / Fraction(speed).limit_denominator(100000)
        self._data['scalar'] = 1 if speed == 1.0 else str(scalar_fraction)
        self._data['mediaDuration'] = int(self.duration / float(scalar_fraction)) # type: ignore[typeddict-item]
        self._data.setdefault('metadata', {})['clipSpeedAttribute'] = {'type': 'bool', 'value': True}
        return self

    @property
    def speed(self) -> float:
        """Current playback speed multiplier."""
        from camtasia.timing import scalar_to_speed
        return float(scalar_to_speed(self.scalar))

    @property
    def has_effects(self) -> bool:
        """Whether this clip has any effects applied."""
        return bool(self._data.get('effects'))

    @property
    def effect_count(self) -> int:
        """Number of effects on this clip."""
        return len(self._data.get('effects', []))

    @property
    def keyframe_count(self) -> int:
        """Total number of keyframes across all parameters."""
        total_keyframes: int = 0
        for parameter_value in self._data.get('parameters', {}).values():
            if isinstance(parameter_value, dict) and 'keyframes' in parameter_value:
                total_keyframes += len(parameter_value['keyframes'])
        return total_keyframes

    @property
    def is_at_origin(self) -> bool:
        """Whether this clip starts at time 0."""
        return self.start == 0

    @property
    def effect_names(self) -> list[str]:
        """Names of all effects on this clip."""
        return [e.get('effectName', '?') for e in self._data.get('effects', [])]

    @property
    def effects(self) -> list[dict[str, Any]]:
        """Raw effect dicts (will be wrapped by the effects module later)."""
        return self._data.get('effects', [])

    def remove_effect_by_name(self, effect_name: str | EffectName) -> int:
        """Remove all effects with the given name. Returns count removed."""
        effects = self._data.get('effects', [])
        original = len(effects)
        self._data['effects'] = [e for e in effects if e.get('effectName') != effect_name]
        return original - len(self._data['effects'])

    def is_effect_applied(self, effect_name: str | EffectName) -> bool:
        """Check if a specific effect is applied to this clip.

        Args:
            effect_name: The effect name string or :class:`EffectName` enum member.

        Returns:
            True if at least one effect with the given name exists on this clip.
        """
        return any(
            effect_dict.get('effectName') == effect_name
            for effect_dict in self._data.get('effects', [])
        )

    @property
    def parameters(self) -> dict[str, Any]:
        """Clip parameters dict."""
        return self._data.get('parameters', {})

    @property
    def opacity(self) -> float:
        """Clip opacity (0.0–1.0)."""
        params = self._data.get('parameters', {})
        val = params.get('opacity', 1.0)
        return float(val['defaultValue'] if isinstance(val, dict) else val)

    @opacity.setter
    def opacity(self, value: float) -> None:
        """Set the opacity."""
        if not 0.0 <= value <= 1.0:
            raise ValueError(f'opacity must be 0.0-1.0, got {value}')
        self._data.setdefault('parameters', {})['opacity'] = value

    @property
    def volume(self) -> float:
        """Audio volume (>= 0.0)."""
        params = self._data.get('parameters', {})
        val = params.get('volume', 1.0)
        return float(val['defaultValue'] if isinstance(val, dict) else val)

    @volume.setter
    def volume(self, value: float) -> None:
        """Set the volume."""
        if value < 0.0:
            raise ValueError(f'volume must be >= 0.0, got {value}')
        self._data.setdefault('parameters', {})['volume'] = value

    @property
    def is_silent(self) -> bool:
        """Whether this clip has zero volume (gain == 0 or volume == 0)."""
        return self.gain == 0.0 or self.volume == 0.0

    @property
    def metadata(self) -> dict[str, Any]:
        """Clip metadata dict."""
        return self._data.get('metadata', {})

    def set_metadata(self, metadata_key: str, metadata_value: Any) -> Self:
        """Set a metadata value on this clip."""
        self._data.setdefault('metadata', {})[metadata_key] = metadata_value
        return self

    def get_metadata(self, metadata_key: str, default: Any = None) -> Any:
        """Get a metadata value from this clip."""
        return self._data.get('metadata', {}).get(metadata_key, default)

    def clear_metadata(self) -> Self:
        """Remove all metadata from this clip.

        Returns:
            ``self`` for chaining.
        """
        self._data['metadata'] = {}
        return self

    @property
    def animation_tracks(self) -> dict[str, Any]:
        """Animation tracks dict."""
        return self._data.get('animationTracks', {})

    @property
    def visual_animations(self) -> list[dict[str, Any]]:
        """Visual animation array from animationTracks."""
        return self.animation_tracks.get('visual', [])  # type: ignore[no-any-return]

    @property
    def source_id(self) -> int | None:
        """Source bin ID (``src`` field), or ``None`` if absent."""
        return self._data.get('src')

    def set_source(self, source_id: int) -> Self:
        """Change the media source reference for this clip."""
        self._data['src'] = source_id
        return self

    @property
    def source_effect(self) -> dict[str, Any] | None:
        """Source effect applied to this clip, or ``None``."""
        return self._data.get('sourceEffect')

    def set_source_effect(
        self,
        *,
        color0: tuple[int, int, int] | None = None,
        color1: tuple[int, int, int] | None = None,
        color2: tuple[int, int, int] | None = None,
        color3: tuple[int, int, int] | None = None,
        mid_point: float | tuple[float, float] = 0.5,
        speed: float = 5.0,
        source_file_type: str = 'tscshadervid',
    ) -> None:
        """Create or replace the clip's sourceEffect for shader backgrounds.

        Colors are 0-255 RGB tuples. They're converted to 0.0-1.0 internally.
        """
        params: dict[str, Any] = {}
        for i, color in enumerate([color0, color1, color2, color3]):
            if color is not None:
                r, g, b = color
                params[f'Color{i}-red'] = r / 255
                params[f'Color{i}-green'] = g / 255
                params[f'Color{i}-blue'] = b / 255
                params[f'Color{i}-alpha'] = 1.0
        if isinstance(mid_point, tuple):
            params['MidPointX'] = mid_point[0]
            params['MidPointY'] = mid_point[1]
        else:
            params['MidPoint'] = mid_point
        params['Speed'] = speed
        params['sourceFileType'] = source_file_type

        self._data['sourceEffect'] = {
            'effectName': 'SourceEffect',
            'bypassed': False,
            'category': '',
            'parameters': params,
        }

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------

    @property
    def start_seconds(self) -> float:
        """Timeline position in seconds."""
        return self.start / EDIT_RATE

    @start_seconds.setter
    def start_seconds(self, value: float) -> None:
        """Set the start_seconds."""
        self.start = seconds_to_ticks(value)

    @property
    def duration_seconds(self) -> float:
        """Playback duration in seconds."""
        return self.duration / EDIT_RATE

    @duration_seconds.setter
    def duration_seconds(self, value: float) -> None:
        """Set the duration_seconds."""
        self.duration = seconds_to_ticks(value)

    def is_shorter_than(self, threshold_seconds: float) -> bool:
        """Whether this clip's duration is less than the given threshold."""
        return self.duration_seconds < threshold_seconds

    def set_start_seconds(self, start_seconds: float) -> Self:
        """Set the clip start position in seconds.

        Args:
            start_seconds: New start position in seconds.

        Returns:
            Self for method chaining.
        """
        from camtasia.timing import seconds_to_ticks
        self._data['start'] = seconds_to_ticks(start_seconds)
        return self

    def set_duration_seconds(self, duration_seconds: float) -> Self:
        """Set the clip duration in seconds.

        Args:
            duration_seconds: New duration in seconds.

        Returns:
            Self for method chaining.
        """
        from camtasia.timing import seconds_to_ticks
        self._data['duration'] = seconds_to_ticks(duration_seconds)
        return self

    def set_time_range(self, start_seconds: float, duration_seconds: float) -> Self:
        """Set both start position and duration in seconds.

        Returns self for chaining.
        """
        self._data['start'] = seconds_to_ticks(start_seconds)
        self._data['duration'] = seconds_to_ticks(duration_seconds)
        return self

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BaseClip):
            return NotImplemented
        return self._data is other._data or self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(id={self.id}, "
            f"start={self.start_seconds:.2f}s, "
            f"duration={self.duration_seconds:.2f}s)"
        )

    def __str__(self) -> str:
        return f'{self.clip_type}(id={self.id}, {self.duration_seconds:.1f}s)'

    # ------------------------------------------------------------------
    # L2 convenience — time-bounded effects
    # ------------------------------------------------------------------

    def copy_effects_from(self, source: BaseClip) -> Self:
        """Copy all effects from another clip.

        Deep copies the source clip's effects array into this clip.
        Existing effects on this clip are preserved (new effects appended).

        Args:
            source: Clip to copy effects from.

        Returns:
            self for chaining.
        """
        import copy
        source_effects = source._data.get('effects', [])
        self._data.setdefault('effects', []).extend(copy.deepcopy(source_effects))
        return self

    def duplicate_effects_to(self, target_clip: BaseClip) -> Self:
        """Copy all effects from this clip to another clip.

        Convenience wrapper around :meth:`copy_effects_from` that reads
        from *self* and writes to *target_clip*.

        Args:
            target_clip: Clip that will receive this clip's effects.

        Returns:
            self for chaining.
        """
        target_clip.copy_effects_from(self)
        return self

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
            'effectName': EffectName.GLOW,
            'bypassed': False,
            'category': 'categoryVisualEffects',
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
        return tracks.setdefault('visual', [])  # type: ignore[no-any-return]

    def _remove_opacity_tracks(self) -> None:
        """Remove all opacity entries from ``animationTracks.visual``."""
        visual = self._data.get('animationTracks', {}).get('visual')
        if visual is not None:
            self._data['animationTracks']['visual'] = [
                t for t in visual if t.get('track') != 'opacity'
            ]

    def _add_opacity_track(self, keyframes: list[dict[str, Any]]) -> None:
        """Add opacity animation via parameters.opacity and animationTracks.visual.

        Follows the Camtasia v10 pattern observed in real projects:
        each keyframe specifies a TARGET value, and the corresponding
        visual segment defines the animation duration to reach that target.

        For fade-in + fade-out: 2 keyframes, 2 visual segments.
        For fade-in only: 1 keyframe, 1 visual segment.
        For fade-out only: 1 keyframe, 1 visual segment.
        """
        # Build parameters.opacity keyframes — each has endTime and duration
        # matching the visual segment it corresponds to.
        param_kfs = []
        for kf in keyframes:
            param_kfs.append({
                'endTime': kf['endTime'],
                'time': kf['time'],
                'value': kf['value'],
                'duration': kf['duration'],
            })
        params = self._data.setdefault('parameters', {})
        params['opacity'] = {
            'type': 'double',
            'defaultValue': 0.0,
            'keyframes': param_kfs,
        }
        # Build animationTracks.visual — one segment per keyframe
        visual = self._ensure_visual_tracks()
        for kf in keyframes:
            visual.append({'endTime': kf['endTime'], 'duration': kf['duration']})

    def _get_existing_opacity_keyframes(self) -> list[dict[str, Any]] | None:
        """Return existing opacity keyframes in the new format, or None."""
        opacity = self._data.get('parameters', {}).get('opacity')
        if opacity is None:
            return None
        kfs = opacity.get('keyframes')
        if not kfs:
            return None
        return [{'time': kf['time'], 'value': kf['value'],
                 'endTime': kf['endTime'], 'duration': kf['duration']} for kf in kfs]

    def _clear_opacity(self) -> None:
        """Remove all opacity state: visual segments and parameters.opacity."""
        tracks = self._data.get('animationTracks', {})
        if 'visual' in tracks:
            tracks['visual'] = []
        params = self._data.get('parameters', {})
        params.pop('opacity', None)

    def fade_in(self, duration_seconds: float) -> Self:
        """Add an opacity fade-in (0 → 1) over *duration_seconds*.

        If a fade-out already exists, merges into a single unified animation.

        Args:
            duration_seconds: Fade duration in seconds.

        Returns:
            ``self`` for chaining.
        """
        existing = self._get_existing_opacity_keyframes()
        if existing and existing[-1]['value'] == 0.0:
            # Fade-out already exists — merge
            fade_out_kf = existing[-1]
            self._clear_opacity()
            in_ticks = seconds_to_ticks(duration_seconds)
            self._add_opacity_track([
                {'time': 0, 'value': 1.0, 'endTime': in_ticks, 'duration': in_ticks},
                fade_out_kf,
            ])
        else:  # pragma: no cover
            in_ticks = seconds_to_ticks(duration_seconds)
            self._add_opacity_track([
                {'time': 0, 'value': 1.0, 'endTime': in_ticks, 'duration': in_ticks},
            ])
        return self

    def fade_out(self, duration_seconds: float) -> Self:
        """Add an opacity fade-out (1 → 0) ending at the clip's end.

        If a fade-in already exists, merges into a single unified animation.

        Args:
            duration_seconds: Fade duration in seconds.

        Returns:
            ``self`` for chaining.
        """
        ticks = seconds_to_ticks(duration_seconds)
        end = int(self._data.get('duration', self.media_duration))
        existing = self._get_existing_opacity_keyframes()
        if existing and existing[0]['value'] == 1.0:
            # Fade-in already exists — merge
            fade_in_kf = existing[0]
            self._clear_opacity()
            self._add_opacity_track([
                fade_in_kf,
                {'time': end - ticks, 'value': 0.0, 'endTime': end, 'duration': ticks},
            ])
        else:  # pragma: no cover
            self._add_opacity_track([
                {'time': end - ticks, 'value': 0.0, 'endTime': end, 'duration': ticks},
            ])
        return self

    def fade(
        self,
        fade_in_seconds: float = 0.0,
        fade_out_seconds: float = 0.0,
    ) -> Self:
        """Apply fade-in and/or fade-out, replacing existing opacity animations.

        Uses the Camtasia v10 keyframe pattern: each keyframe specifies a
        target opacity value, and its duration defines the animation period.

        Args:
            fade_in_seconds: Fade-in duration (0 to skip).
            fade_out_seconds: Fade-out duration (0 to skip).

        Returns:
            ``self`` for chaining.
        """
        self._clear_opacity()
        end = int(self._data.get('duration', self.media_duration))
        kfs: list[dict[str, Any]] = []
        if fade_in_seconds > 0:
            in_ticks = seconds_to_ticks(fade_in_seconds)
            kfs.append({
                'time': 0, 'value': 1.0,
                'endTime': in_ticks, 'duration': in_ticks,
            })
        if fade_out_seconds > 0:
            out_ticks = seconds_to_ticks(fade_out_seconds)
            kfs.append({
                'time': end - out_ticks, 'value': 0.0,
                'endTime': end, 'duration': out_ticks,
            })
        if kfs:
            self._add_opacity_track(kfs)
        return self

    def set_opacity(self, opacity: float) -> Self:
        """Set a static opacity for the entire clip.

        Args:
            opacity: Opacity value (0.0–1.0).

        Returns:
            ``self`` for chaining.
        """
        if not 0.0 <= opacity <= 1.0:
            raise ValueError(f'Opacity must be 0.0-1.0, got {opacity}')
        self._clear_opacity()
        end = int(self._data.get('duration', self.media_duration))
        self._add_opacity_track([
            {'time': 0, 'value': opacity, 'endTime': end, 'duration': end},
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
        enabled: int = 1,
    ) -> Effect:
        """Add a drop-shadow effect.

        Args:
            offset: Shadow offset distance.
            blur: Blur radius.
            opacity: Shadow opacity (0.0–1.0).
            angle: Shadow angle in degrees.
            color: RGB colour tuple.
            enabled: Whether the shadow is enabled (1=on, 0=off).

        Returns:
            Wrapped :class:`DropShadow` effect.
        """
        return self.add_effect({
            'effectName': EffectName.DROP_SHADOW,
            'bypassed': False,
            'category': 'categoryVisualEffects',
            'parameters': {
                'angle': angle,
                'enabled': enabled,
                'offset': offset,
                'blur': blur,
                'opacity': opacity,
                'color-red': color[0],
                'color-green': color[1],
                'color-blue': color[2],
                'color-alpha': 1.0,
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
            'effectName': EffectName.GLOW,
            'bypassed': False,
            'category': 'categoryVisualEffects',
            'parameters': {
                'radius': radius,
                'intensity': intensity,
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
            'effectName': EffectName.ROUND_CORNERS,
            'bypassed': False,
            'category': 'categoryVisualEffects',
            'parameters': {
                'radius': radius,
                'top-left': 1.0,
                'top-right': 1.0,
                'bottom-left': 1.0,
                'bottom-right': 1.0,
            },
        })

    def add_color_adjustment(
        self,
        *,
        brightness: float = 0.0,
        contrast: float = 0.0,
        saturation: float = 1.0,
        channel: int = 0,
        shadow_ramp_start: float = 0.0,
        shadow_ramp_end: float = 0.0,
        highlight_ramp_start: float = 1.0,
        highlight_ramp_end: float = 1.0,
    ) -> Self:
        """Add a color adjustment effect.

        Args:
            brightness: -1.0 to 1.0 (0 = no change).
            contrast: -1.0 to 1.0 (0 = no change).
            saturation: 0.0 to 3.0 (1.0 = no change).
            channel: Color channel (0 = all).
            shadow_ramp_start: Shadow ramp start (0.0-1.0).
            shadow_ramp_end: Shadow ramp end (0.0-1.0).
            highlight_ramp_start: Highlight ramp start (0.0-1.0).
            highlight_ramp_end: Highlight ramp end (0.0-1.0).
        """
        self.add_effect({
            'effectName': EffectName.COLOR_ADJUSTMENT,
            'bypassed': False,
            'category': 'categoryVisualEffects',
            'parameters': {
                'brightness': brightness,
                'contrast': contrast,
                'saturation': saturation,
                'channel': channel,
                'shadowRampStart': shadow_ramp_start,
                'shadowRampEnd': shadow_ramp_end,
                'highlightRampStart': highlight_ramp_start,
                'highlightRampEnd': highlight_ramp_end,
            },
        })
        return self

    def add_border(
        self,
        *,
        width: float = 4.0,
        color: tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0),
        corner_radius: float = 0.0,
    ) -> Self:
        """Add a border effect.

        Args:
            width: Border width in pixels.
            color: RGBA color as 0.0-1.0 floats.
            corner_radius: Corner rounding radius.
        """
        r, g, b, a = color
        self.add_effect({
            'effectName': 'Border',
            'bypassed': False,
            'category': 'categoryVisualEffects',
            'parameters': {
                'width': width,
                'color-red': r,
                'color-green': g,
                'color-blue': b,
                'color-alpha': a,
                'corner-radius': corner_radius,
            },
        })
        return self

    def add_colorize(
        self,
        *,
        color: tuple[float, float, float] = (0.5, 0.5, 0.5),
        intensity: float = 0.5,
    ) -> Self:
        """Add a colorize/tint effect.

        Args:
            color: RGB color as 0.0-1.0 floats.
            intensity: Effect intensity 0.0-1.0.
        """
        r, g, b = color
        self.add_effect({
            'effectName': 'Colorize',
            'bypassed': False,
            'category': 'categoryVisualEffects',
            'parameters': {
                'color-red': r,
                'color-green': g,
                'color-blue': b,
                'intensity': intensity,
            },
        })
        return self

    def add_spotlight(
        self,
        *,
        brightness: float = 0.5,
        concentration: float = 0.5,
        opacity: float = 0.35,
        color: tuple[float, float, float, float] = (1.0, 1.0, 1.0, 0.35),
    ) -> Self:
        """Add a spotlight effect."""
        self.add_effect({
            'effectName': EffectName.SPOTLIGHT,
            'bypassed': False,
            'category': 'categoryVisualEffects',
            'parameters': {
                'color-red': color[0],
                'color-green': color[1],
                'color-blue': color[2],
                'color-alpha': color[3],
                'brightness': brightness,
                'concentration': concentration,
                'opacity': opacity,
                'positionX': 0.0,
                'positionY': 0.0,
                'directionX': 0.0,
                'directionY': 0.0,
            },
        })
        return self

    def add_lut_effect(self, *, intensity: float = 1.0, preset_name: str = '') -> Self:
        """Add a color LUT (Look-Up Table) effect.

        Args:
            intensity: Effect intensity 0.0-1.0.
            preset_name: Optional preset name for metadata.
        """
        self.add_effect({
            'effectName': EffectName.LUT_EFFECT,
            'bypassed': False,
            'category': 'categoryVisualEffects',
            'parameters': {
                'lutSource': '',
                'lut_intensity': intensity,
                'channel': 0,
                'shadowRampStart': 0.0,
                'shadowRampEnd': 0.0,
                'highlightRampStart': 1.0,
                'highlightRampEnd': 1.0,
            },
            'metadata': {'presetName': preset_name} if preset_name else {},
        })
        return self

    def add_media_matte(self, *, intensity: float = 1.0, matte_mode: int = 1, track_depth: int = 10002,
                        preset_name: str = 'Media Matte Luminasity') -> Self:
        """Add a media matte compositing effect.

        Uses one track as a transparency mask for this clip.

        Args:
            intensity: Effect intensity 0.0-1.0.
            matte_mode: Matte mode (1 = alpha, 2 = inverted alpha).
            track_depth: Track depth for matte source.
            preset_name: Preset name for metadata.
        """
        self.add_effect({
            'effectName': EffectName.MEDIA_MATTE,
            'bypassed': False,
            'category': 'categoryVisualEffects',
            'parameters': {
                'intensity': intensity,
                'matteMode': matte_mode,
                'trackDepth': track_depth,
            },
            'metadata': {
                'presetName': preset_name,
            },
        })
        return self

    def add_motion_blur(self, *, intensity: float = 1.0) -> Self:
        """Add a motion blur effect."""
        self.add_effect({
            'effectName': EffectName.MOTION_BLUR,
            'bypassed': False,
            'category': 'categoryVisualEffects',
            'parameters': {'intensity': intensity},
        })
        return self

    def add_emphasize(self, *, amount: float = 0.5) -> Self:
        """Add an audio emphasis effect.

        Args:
            amount: Emphasis amount 0.0-1.0.
        """
        self.add_effect({
            'effectName': EffectName.EMPHASIZE,
            'bypassed': False,
            'category': 'categoryAudioEffects',
            'parameters': {
                'emphasizeAmount': amount,
                'emphasizeRampPosition': 0,
                'emphasizeRampInTime': EDIT_RATE,
                'emphasizeRampOutTime': EDIT_RATE,
            },
        })
        return self

    def add_blend_mode(self, *, mode: int | BlendMode = BlendMode.NORMAL, intensity: float = 1.0) -> Self:
        """Add a blend mode compositing effect.

        Args:
            mode: Blend mode (3=multiply, 16=normal, etc.).
            intensity: Effect intensity 0.0-1.0.
        """
        self.add_effect({
            'effectName': EffectName.BLEND_MODE,
            'bypassed': False,
            'category': 'categoryVisualEffects',
            'parameters': {
                'mode': mode,
                'intensity': intensity,
                'invert': 0,
                'channel': 0,
                'shadowRampStart': 0.0,
                'shadowRampEnd': 0.0,
                'highlightRampStart': 1.0,
                'highlightRampEnd': 1.0,
            },
        })
        return self

    def remove_effects(self) -> Self:
        """Remove all effects from this clip.

        Returns:
            ``self`` for chaining.
        """
        self._data['effects'] = []
        return self

    # ------------------------------------------------------------------
    # L2 — Transform parameter helpers
    # ------------------------------------------------------------------

    def _get_param_value(self, key: str, default: float = 0.0) -> float:
        """Read a parameter value from either scalar or dict format."""
        param = self.parameters.get(key, default)
        if isinstance(param, dict):
            return float(param.get('defaultValue', default))
        return float(param)

    def _set_param_value(self, key: str, value: float) -> None:
        """Write a parameter as compact scalar, or update defaultValue if dict exists."""
        params = self._data.setdefault('parameters', {})
        existing = params.get(key)
        if isinstance(existing, dict):
            existing['defaultValue'] = value
        else:  # pragma: no cover
            params[key] = value

    @property
    def translation(self) -> tuple[float, float]:
        """``(x, y)`` translation."""
        return (
            self._get_param_value('translation0'),
            self._get_param_value('translation1'),
        )

    @translation.setter
    def translation(self, value: tuple[float, float]) -> None:
        """Set the translation."""
        self._set_param_value('translation0', value[0])
        self._set_param_value('translation1', value[1])

    @property
    def scale(self) -> tuple[float, float]:
        """``(x, y)`` scale factors."""
        return (
            self._get_param_value('scale0', 1.0),
            self._get_param_value('scale1', 1.0),
        )

    @scale.setter
    def scale(self, value: tuple[float, float]) -> None:
        """Set the scale."""
        self._set_param_value('scale0', value[0])
        self._set_param_value('scale1', value[1])

    @property
    def rotation(self) -> float:
        """Z-rotation in radians (stored as ``rotation2``)."""
        return self._get_param_value('rotation2')

    @rotation.setter
    def rotation(self, value: float) -> None:
        """Set the rotation."""
        self._set_param_value('rotation2', value)

    def move_to(self, x: float, y: float) -> Self:
        """Set the clip's canvas translation.

        Returns:
            ``self`` for chaining.
        """
        self._set_param_value('translation0', x)
        self._set_param_value('translation1', y)
        return self

    def scale_to(self, factor: float) -> Self:
        """Set uniform scale on both axes.

        Returns:
            ``self`` for chaining.
        """
        self._set_param_value('scale0', factor)
        self._set_param_value('scale1', factor)
        return self

    def scale_to_xy(self, x: float, y: float) -> Self:
        """Set non-uniform scale.

        Returns:
            ``self`` for chaining.
        """
        self._set_param_value('scale0', x)
        self._set_param_value('scale1', y)
        return self

    def crop(
        self,
        left: float = 0,
        top: float = 0,
        right: float = 0,
        bottom: float = 0,
    ) -> Self:
        """Set geometry crop values (non-negative floats, pixel or fractional).

        Returns:
            ``self`` for chaining.
        """
        for name, val in [('left', left), ('top', top), ('right', right), ('bottom', bottom)]:
            if val < 0:
                raise ValueError(f'Crop {name} must be non-negative, got {val}')
        self._set_param_value('geometryCrop0', left)
        self._set_param_value('geometryCrop1', top)
        self._set_param_value('geometryCrop2', right)
        self._set_param_value('geometryCrop3', bottom)
        return self

    # ------------------------------------------------------------------
    # L2 — Keyframe animation API
    # ------------------------------------------------------------------

    def add_keyframe(
        self,
        parameter: str,
        time_seconds: float,
        value: float,
        duration_seconds: float = 0.0,
        interp: str = 'eioe',
    ) -> Self:
        """Add a keyframe to a clip parameter.

        Returns:
            ``self`` for chaining.
        """
        params = self._data.setdefault('parameters', {})
        time_ticks = seconds_to_ticks(time_seconds)
        dur_ticks = seconds_to_ticks(duration_seconds) if duration_seconds > 0 else 0
        end_ticks = time_ticks + dur_ticks if dur_ticks else time_ticks

        kf_entry: dict[str, Any] = {
            'endTime': end_ticks,
            'time': time_ticks,
            'value': value,
            'duration': dur_ticks,
        }
        if interp:
            kf_entry['interp'] = interp

        existing = params.get(parameter)
        if isinstance(existing, dict) and 'keyframes' in existing:
            existing['keyframes'].append(kf_entry)
        else:  # pragma: no cover
            default_val = existing if isinstance(existing, (int, float)) else (
                existing.get('defaultValue', 0.0) if isinstance(existing, dict) else 0.0
            )
            params[parameter] = {
                'type': 'double',
                'defaultValue': default_val,
                'keyframes': [kf_entry],
            }
        return self

    def summary(self) -> str:
        """Human-readable clip summary."""
        lines: list[str] = [
            f'{self.clip_type}(id={self.id})',
            f'  Time: {self.time_range_formatted}',
            f'  Duration: {self.duration_seconds:.2f}s',
        ]
        if self.scalar != 1:
            lines.append(f'  Speed: {self.speed:.2f}x')
        effects = self._data.get('effects', [])
        if effects:
            names = [e.get('effectName', '?') for e in effects]
            lines.append(f'  Effects: {", ".join(names)}')
        return '\n'.join(lines)

    def describe(self) -> str:
        """Human-readable clip description."""
        from camtasia.timing import ticks_to_seconds
        lines = [f'{type(self).__name__} (id={self.id})']
        lines.append(f'  Time: {ticks_to_seconds(self.start):.2f}s - {ticks_to_seconds(self.start + self.duration):.2f}s ({ticks_to_seconds(self.duration):.2f}s)')
        if self.has_effects:
            names = [e.get('effectName', '?') for e in self._data.get('effects', [])]
            lines.append(f'  Effects: {", ".join(names)}')
        return '\n'.join(lines)

    def clone(self) -> BaseClip:
        """Create a deep copy of this clip with a new ID."""
        import copy
        cloned_data: dict[str, Any] = copy.deepcopy(dict(self._data))
        # ID will be assigned when added to a track
        cloned_data['id'] = -1  # sentinel, must be reassigned
        from camtasia.timeline.clips import clip_from_dict
        return clip_from_dict(cloned_data)

    def clear_keyframes(self, parameter: str | None = None) -> Self:
        """Remove keyframes from a parameter, or all parameters if *parameter* is ``None``.

        Returns:
            ``self`` for chaining.
        """
        params = self._data.get('parameters', {})
        if parameter is not None:
            p = params.get(parameter)
            if isinstance(p, dict):
                p.pop('keyframes', None)
        else:  # pragma: no cover
            for p in params.values():
                if isinstance(p, dict):
                    p.pop('keyframes', None)
        return self

    def reset_transforms(self) -> Self:
        """Reset position, scale, and rotation to defaults."""
        self.move_to(0, 0)
        self.scale_to(1.0)
        self.rotation = 0.0
        return self

    def remove_all_effects(self) -> Self:
        """Remove all effects from this clip."""
        self._data['effects'] = []
        return self

    def set_opacity_fade(self, start_opacity: float = 1.0, end_opacity: float = 0.0, duration_seconds: float | None = None) -> Self:
        """Add an opacity fade keyframe animation."""
        from camtasia.timing import seconds_to_ticks
        dur = seconds_to_ticks(duration_seconds) if duration_seconds else self.duration
        self._data.setdefault('parameters', {})['opacity'] = {
            'type': 'double',
            'defaultValue': start_opacity,
            'keyframes': [
                {'endTime': dur, 'time': 0, 'value': start_opacity, 'duration': dur},
                {'endTime': dur, 'time': dur, 'value': end_opacity, 'duration': 0},
            ],
        }
        return self

    def set_position_keyframes(self, keyframes: list[tuple[float, float, float]]) -> Self:
        """Set position keyframes for animated movement.

        Args:
            keyframes: List of (time_seconds, x, y) tuples.
        """
        from camtasia.timing import seconds_to_ticks
        params = self._data.setdefault('parameters', {})
        x_kfs = []
        y_kfs = []
        for t, x, y in keyframes:
            ticks = seconds_to_ticks(t)
            x_kfs.append({'endTime': ticks, 'time': ticks, 'value': x, 'duration': 0})
            y_kfs.append({'endTime': ticks, 'time': ticks, 'value': y, 'duration': 0})
        params['translation0'] = {'type': 'double', 'defaultValue': keyframes[0][1], 'keyframes': x_kfs}
        params['translation1'] = {'type': 'double', 'defaultValue': keyframes[0][2], 'keyframes': y_kfs}
        return self

    def set_scale_keyframes(self, keyframes: list[tuple[float, float]]) -> Self:
        """Set scale keyframes for animated scaling.

        Args:
            keyframes: List of (time_seconds, scale) tuples.
        """
        from camtasia.timing import seconds_to_ticks
        params = self._data.setdefault('parameters', {})
        kfs = []
        for t, s in keyframes:
            ticks = seconds_to_ticks(t)
            kfs.append({'endTime': ticks, 'time': ticks, 'value': s, 'duration': 0})
        params['scale0'] = {'type': 'double', 'defaultValue': keyframes[0][1], 'keyframes': kfs}
        params['scale1'] = {'type': 'double', 'defaultValue': keyframes[0][1], 'keyframes': list(kfs)}
        return self

    def set_rotation_keyframes(self, keyframes: list[tuple[float, float]]) -> Self:
        """Set rotation keyframes for animated rotation.

        Args:
            keyframes: List of (time_seconds, rotation_degrees) tuples.
        """
        from camtasia.timing import seconds_to_ticks
        import math
        params = self._data.setdefault('parameters', {})
        kfs = []
        for t, deg in keyframes:
            ticks = seconds_to_ticks(t)
            kfs.append({'endTime': ticks, 'time': ticks, 'value': math.radians(deg), 'duration': 0})
        params['rotation2'] = {'type': 'double', 'defaultValue': kfs[0]['value'], 'keyframes': kfs}
        return self

    def set_crop_keyframes(self, keyframes: list[tuple[float, float, float, float, float]]) -> Self:
        """Set crop keyframes for animated cropping.

        Args:
            keyframes: List of (time_seconds, left, top, right, bottom) tuples.
                Values 0.0-1.0.
        """
        from camtasia.timing import seconds_to_ticks
        params = self._data.setdefault('parameters', {})
        for i, name in enumerate(['geometryCrop0', 'geometryCrop1', 'geometryCrop2', 'geometryCrop3']):
            kfs = []
            for kf in keyframes:
                ticks = seconds_to_ticks(kf[0])
                kfs.append({'endTime': ticks, 'time': ticks, 'value': kf[i + 1], 'duration': 0})
            params[name] = {'type': 'double', 'defaultValue': kfs[0]['value'], 'keyframes': kfs}
        return self

    def set_volume_fade(self, start_volume: float = 1.0, end_volume: float = 0.0, duration_seconds: float | None = None) -> Self:
        """Add a volume fade keyframe animation."""
        from camtasia.timing import seconds_to_ticks
        dur = seconds_to_ticks(duration_seconds) if duration_seconds else self.duration
        self._data.setdefault('parameters', {})['volume'] = {
            'type': 'double',
            'defaultValue': start_volume,
            'keyframes': [
                {'endTime': 0, 'time': 0, 'value': start_volume, 'duration': 0},
                {'endTime': dur, 'time': dur, 'value': end_volume, 'duration': 0},
            ],
        }
        return self

    def animate(
        self,
        *,
        fade_in: float = 0.0,
        fade_out: float = 0.0,
        scale_from: float | None = None,
        scale_to: float | None = None,
        move_from: tuple[float, float] | None = None,
        move_to: tuple[float, float] | None = None,
    ) -> Self:
        """Apply common animations in one call.

        Args:
            fade_in: Fade-in duration in seconds (0 = no fade).
            fade_out: Fade-out duration in seconds (0 = no fade).
            scale_from: Starting scale (None = no scale animation).
            scale_to: Ending scale (None = no scale animation).
            move_from: Starting (x, y) position (None = no movement).
            move_to: Ending (x, y) position (None = no movement).
        """
        from camtasia.timing import ticks_to_seconds
        dur = ticks_to_seconds(self.duration)

        if fade_in > 0 or fade_out > 0:
            from camtasia.timing import seconds_to_ticks
            dur_ticks = self.duration
            keyframes: list[dict] = []
            if fade_in > 0:
                fi_ticks = seconds_to_ticks(fade_in)
                keyframes.append({'endTime': fi_ticks, 'time': 0, 'value': 1.0, 'duration': fi_ticks})
            if fade_out > 0:
                fo_ticks = seconds_to_ticks(fade_out)
                fo_start = dur_ticks - fo_ticks
                keyframes.append({'endTime': dur_ticks, 'time': fo_start, 'value': 0.0, 'duration': fo_ticks})
            self._data.setdefault('parameters', {})['opacity'] = {
                'type': 'double',
                'defaultValue': 0.0 if fade_in > 0 else 1.0,
                'keyframes': keyframes,
            }

        if scale_from is not None and scale_to is not None:
            self.set_scale_keyframes([(0.0, scale_from), (dur, scale_to)])

        if move_from is not None and move_to is not None:
            self.set_position_keyframes([
                (0.0, move_from[0], move_from[1]),
                (dur, move_to[0], move_to[1]),
            ])

        return self

    def to_dict(self) -> dict[str, Any]:
        """Return a summary dict of this clip's key properties."""
        from camtasia.timing import ticks_to_seconds
        result = {
            'id': self.id,
            'type': self.clip_type,
            'start_seconds': ticks_to_seconds(self.start),
            'duration_seconds': ticks_to_seconds(self.duration),
            'end_seconds': self.end_seconds,
        }
        if self.source_id is not None:
            result['source_id'] = self.source_id
        if self.has_effects:
            result['effects'] = [e.get('effectName', '?') for e in self._data.get('effects', [])]
        return result

    @property
    def source_path(self) -> int | str:
        """Source bin ID (int) or empty string if absent (from the 'src' field)."""
        return self._data.get('src', '')

    @property
    def media_start_seconds(self) -> float:
        """Media start offset in seconds."""
        from camtasia.timing import ticks_to_seconds
        return float(ticks_to_seconds(int(Fraction(str(self.media_start)))))

    def overlaps_with(self, other_clip: BaseClip) -> bool:
        """Check if this clip's time range overlaps with another clip."""
        self_end: int = self.start + self.duration
        other_end: int = other_clip.start + other_clip.duration
        return self.start < other_end and other_clip.start < self_end

    def distance_to(self, other_clip: BaseClip) -> float:
        """Gap in seconds between this clip and another (negative if overlapping)."""
        from camtasia.timing import ticks_to_seconds
        self_end: int = self.start + self.duration
        other_start: int = other_clip.start
        gap_ticks: int = other_start - self_end
        return float(ticks_to_seconds(gap_ticks))

    @property
    def has_keyframes(self) -> bool:
        """Whether any parameter has keyframe animation."""
        for parameter_value in self._data.get('parameters', {}).values():
            if isinstance(parameter_value, dict) and 'keyframes' in parameter_value:
                return True
        return False

    def clear_all_keyframes(self) -> Self:
        """Remove keyframes from ALL parameters, keeping default values."""
        parameters: dict[str, Any] = self._data.get('parameters', {})
        for parameter_name, parameter_value in parameters.items():
            if isinstance(parameter_value, dict) and 'keyframes' in parameter_value:
                parameters[parameter_name] = parameter_value.get('defaultValue', 0)
        return self

    def copy_timing_from(self, source_clip: BaseClip) -> Self:
        """Copy start time and duration from another clip."""
        self._data['start'] = source_clip.start
        self._data['duration'] = source_clip.duration
        return self

    def matches_type(self, clip_type: str | ClipType) -> bool:
        """Check if this clip matches the given type."""
        return self.clip_type == clip_type

    def matches_any_type(self, *clip_types: str | ClipType) -> bool:
        """Check if this clip matches any of the given types."""
        return any(self.matches_type(ct) for ct in clip_types)

    def snap_to_seconds(self, target_start_seconds: float) -> Self:
        """Move this clip to start at the given time in seconds."""
        from camtasia.timing import seconds_to_ticks
        self._data['start'] = seconds_to_ticks(target_start_seconds)
        return self

    def is_longer_than(self, threshold_seconds: float) -> bool:
        """Whether this clip's duration exceeds the given threshold."""
        return self.duration_seconds > threshold_seconds

    def apply_if(self, predicate: Callable[[BaseClip], bool], operation: Callable[[BaseClip], Any]) -> Self:
        """Apply an operation only if the predicate is true for this clip."""
        if predicate(self):
            operation(self)
        return self

    def copy_to_track(self, target_track: Track) -> BaseClip:
        """Copy this clip to another track, preserving timing and effects.

        Creates a deep copy of the clip data, assigns a new ID from the
        target track, and appends it to the target track's media list.

        Args:
            target_track: The track to copy this clip into.

        Returns:
            The newly created clip on the target track.
        """
        import copy
        cloned_data: dict[str, Any] = copy.deepcopy(dict(self._data))
        cloned_data['id'] = target_track._next_clip_id()
        target_track._data.setdefault('medias', []).append(cloned_data)
        from camtasia.timeline.clips import clip_from_dict
        return clip_from_dict(cloned_data)
