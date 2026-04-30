"""Base clip class wrapping the underlying JSON dict."""
from __future__ import annotations

import copy
from fractions import Fraction
import sys
from typing import TYPE_CHECKING, Any, ClassVar
import warnings

if sys.version_info >= (3, 11):  # pragma: no cover
    from typing import Self
else:  # pragma: no cover
    from typing_extensions import Self

from camtasia.effects.base import Effect, effect_from_dict

if TYPE_CHECKING:
    from collections.abc import Callable

    from camtasia.timeline.track import Track

from camtasia.effects.visual import Emphasize, Glow
from camtasia.timing import seconds_to_ticks
from camtasia.types import BlendMode, ClipType, EffectName, _ClipData

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
        if self.clip_type == ClipType.AUDIO:
            return True
        if self.clip_type == 'UnifiedMedia':
            return self._data.get('video') is None
        if self.clip_type == 'StitchedMedia':
            medias = self._data.get('medias', [])
            if not medias:
                return False
            for m in medias:
                t = m.get('_type')
                if t == 'AMFile':
                    continue
                if t == 'UnifiedMedia':
                    if m.get('video') is not None:
                        return False
                    continue
                return False
            return True
        return False

    @property
    def is_video(self) -> bool:
        """Whether this clip is a video clip."""
        if self.clip_type in (ClipType.VIDEO, ClipType.SCREEN_VIDEO):
            return True
        if self.clip_type == ClipType.UNIFIED_MEDIA:
            return self._data.get('video') is not None
        if self.clip_type == 'StitchedMedia':
            for m in self._data.get('medias', []):
                if m.get('_type') in ('VMFile', 'ScreenVMFile'):
                    return True
                if m.get('_type') == 'UnifiedMedia':
                    video = m.get('video') or {}
                    if video.get('_type') in ('VMFile', 'ScreenVMFile'):
                        return True
            return False
        return False

    @property
    def is_visible(self) -> bool:
        """Whether this clip is a visual clip (not audio-only)."""
        return not self.is_audio

    @property
    def is_image(self) -> bool:
        """Whether this clip is an image clip."""
        return self.clip_type in (ClipType.IMAGE, ClipType.SCREEN_IMAGE)

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
        if self._data.get('_type') == 'UnifiedMedia':
            for sub_key in ('video', 'audio'):
                sub: dict[str, Any] = self._data.get(sub_key)  # type: ignore[assignment]
                if sub is not None:
                    sub['start'] = self._data['start']

    @property
    def duration(self) -> int:
        """Playback duration in ticks."""
        return int(self._data['duration'])

    @duration.setter
    def duration(self, value: int) -> None:
        """Set the duration."""
        old_duration = self._data.get('duration', 0)
        self._data['duration'] = value
        from camtasia.timing import parse_scalar
        scalar = parse_scalar(self._data.get('scalar', 1))
        if scalar != 0:
            md = Fraction(value) / scalar
            self._data['mediaDuration'] = int(md) if md == int(md) else str(md)
        if self._data.get('_type') in ('IMFile', 'ScreenIMFile'):
            self._data['mediaDuration'] = 1
        if self._data.get('_type') == 'UnifiedMedia':
            for sub_key in ('video', 'audio'):
                sub: dict[str, Any] = self._data.get(sub_key)  # type: ignore[assignment]
                if sub is not None:
                    sub['duration'] = self._data['duration']
                    sub['mediaDuration'] = self._data['mediaDuration']
                    sub['scalar'] = self._data.get('scalar', 1)
                    sub['mediaStart'] = self._data.get('mediaStart', 0)
                    if sub.get('_type') in ('IMFile', 'ScreenIMFile'):
                        sub['mediaDuration'] = 1
        if self._data.get('_type') == 'StitchedMedia' and old_duration > 0:
            ratio = Fraction(value) / Fraction(old_duration)
            cursor = 0
            for inner in self._data.get('medias', []):
                inner_old_dur = Fraction(str(inner.get('duration', 0)))
                new_inner_dur = round(inner_old_dur * ratio)
                inner['duration'] = new_inner_dur
                inner['start'] = cursor
                cursor += new_inner_dur
                inner_scalar = parse_scalar(inner.get('scalar', 1))
                if inner_scalar != 0:
                    inner_md = Fraction(new_inner_dur) / inner_scalar
                    inner['mediaDuration'] = int(inner_md) if inner_md == int(inner_md) else str(inner_md)
                if inner.get('_type') == 'UnifiedMedia':
                    for sub_key in ('video', 'audio'):
                        sub = inner.get(sub_key)  # type: ignore[assignment]
                        if sub is not None:
                            sub['start'] = inner['start']
                            sub['duration'] = inner['duration']
                            if 'mediaDuration' in inner:
                                sub['mediaDuration'] = inner['mediaDuration']

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
        from camtasia.timing import seconds_to_ticks
        start_ticks = seconds_to_ticks(range_start_seconds)
        end_ticks = seconds_to_ticks(range_end_seconds)
        return start_ticks <= self.start and self.start + self.duration <= end_ticks

    def intersects(self, range_start_seconds: float, range_end_seconds: float) -> bool:
        """Whether this clip overlaps with the given time range at all."""
        from camtasia.timing import seconds_to_ticks
        start_ticks = seconds_to_ticks(range_start_seconds)
        end_ticks = seconds_to_ticks(range_end_seconds)
        clip_end_ticks = self.start + self.duration
        return self.start < end_ticks and clip_end_ticks > start_ticks

    @property
    def is_muted(self) -> bool:
        """Whether this clip's audio is muted (gain == 0)."""
        if self._data.get('_type') in ('Group', 'StitchedMedia'):
            return self.volume == 0.0
        if self._data.get('_type') == 'UnifiedMedia':
            return bool(self._data.get('audio', {}).get('attributes', {}).get('gain', 1.0) == 0.0)
        return self.gain == 0.0

    def mute(self) -> Self:
        """Mute this clip's audio by setting gain to 0.

        Returns:
            ``self`` for chaining.
        """
        if self._data.get('_type') in ('Group', 'StitchedMedia'):
            self._data.setdefault('parameters', {})['volume'] = 0.0
        elif self._data.get('_type') == 'UnifiedMedia':
            audio = self._data.get('audio')
            if audio is None:
                raise ValueError('UnifiedMedia has no audio sub-clip to mute')
            audio.setdefault('attributes', {})['gain'] = 0.0
        else:
            self.gain = 0.0
        return self

    def unmute(self) -> Self:
        """Restore this clip's audio by setting gain back to 1.0.

        Inverse of :meth:`mute`. Returns ``self`` for chaining.
        """
        if self._data.get('_type') in ('Group', 'StitchedMedia'):
            self._data.setdefault('parameters', {})['volume'] = 1.0
        elif self._data.get('_type') == 'UnifiedMedia':
            audio = self._data.get('audio')
            if audio is None:
                raise ValueError('UnifiedMedia has no audio sub-clip to unmute')
            audio.setdefault('attributes', {})['gain'] = 1.0
        else:
            self.gain = 1.0
        return self

    @property
    def media_start(self) -> int | float | str | Fraction:  # type: ignore[override]
        """Offset into source media in ticks.

        May be a rational fraction string for speed-changed clips.
        """
        raw = self._data.get('mediaStart', 0) # type: ignore[typeddict-item]
        if isinstance(raw, str):
            return Fraction(raw)
        return raw

    @media_start.setter
    def media_start(self, value: int | Fraction) -> None:
        """Set the media start."""
        if isinstance(value, Fraction):
            stored = int(value) if value == int(value) else str(value)
        else:
            stored = value
        self._data['mediaStart'] = stored # type: ignore[typeddict-item]
        if self._data.get('_type') == 'UnifiedMedia':
            for sub_key in ('video', 'audio'):
                sub: dict[str, Any] = self._data.get(sub_key)  # type: ignore[assignment]
                if sub is not None:
                    sub['mediaStart'] = stored

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
        from fractions import Fraction as _F
        if isinstance(value, _F):
            stored = int(value) if value == int(value) else str(value)
        else:
            stored = value
        self._data['mediaDuration'] = stored # type: ignore[typeddict-item]
        if self._data.get('_type') == 'UnifiedMedia':
            for sub_key in ('video', 'audio'):
                sub: dict[str, Any] = self._data.get(sub_key)  # type: ignore[assignment]
                if sub is not None:
                    sub['mediaDuration'] = stored

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
        from camtasia.timing import parse_scalar
        old_scalar = parse_scalar(self._data.get('scalar', 1))
        f = Fraction(value)
        self._data['scalar'] = 1 if f == 1 else str(f)
        # Recalculate mediaDuration to maintain invariant
        if f != 0:
            md = Fraction(self._data.get('duration', 0)) / f
            self._data['mediaDuration'] = int(md) if md == int(md) else str(md)
        if self._data.get('_type') in ('IMFile', 'ScreenIMFile'):
            self._data['mediaDuration'] = 1
        if self._data.get('_type') == 'UnifiedMedia':
            for sub_key in ('video', 'audio'):
                sub: dict[str, Any] = self._data.get(sub_key)  # type: ignore[assignment]
                if sub is not None:
                    sub['scalar'] = self._data['scalar']
                    sub['mediaDuration'] = self._data['mediaDuration']
                    sub['mediaStart'] = self._data.get('mediaStart', 0)
                    if sub.get('_type') in ('IMFile', 'ScreenIMFile'):
                        sub['mediaDuration'] = 1
        if self._data.get('_type') == 'StitchedMedia' and old_scalar != 0:
            ratio = f / old_scalar
            cursor = 0
            for inner in self._data.get('medias', []):
                inner_old_dur = Fraction(str(inner.get('duration', 0)))
                new_inner_dur = round(inner_old_dur * ratio)
                inner['duration'] = new_inner_dur
                inner['start'] = cursor
                cursor += new_inner_dur
                inner_scalar = parse_scalar(inner.get('scalar', 1))
                if inner_scalar != 0:
                    inner_md = Fraction(new_inner_dur) / inner_scalar
                    inner['mediaDuration'] = int(inner_md) if inner_md == int(inner_md) else str(inner_md)
                if inner.get('_type') == 'UnifiedMedia':
                    for sub_key in ('video', 'audio'):
                        sub = inner.get(sub_key)  # type: ignore[assignment]
                        if sub is not None:
                            sub['start'] = inner['start']
                            sub['duration'] = inner['duration']
                            if 'mediaDuration' in inner:
                                sub['mediaDuration'] = inner['mediaDuration']

    def set_speed(self, speed: float) -> Self:
        """Set playback speed multiplier.

        Args:
            speed: Speed multiplier (1.0 = normal, 2.0 = double speed, 0.5 = half speed).
        """
        if speed <= 0:
            raise ValueError(f'speed must be > 0, got {speed}')
        scalar_fraction = Fraction(1) / Fraction(speed).limit_denominator(100000)
        # Save old scalar before mutation for Group idempotency
        _old_scalar = Fraction(str(self._data.get('scalar', 1))) if isinstance(self._data.get('scalar', 1), str) else Fraction(self._data.get('scalar', 1))
        self._data['scalar'] = 1 if scalar_fraction == 1 else str(scalar_fraction)
        md = Fraction(self.duration) / scalar_fraction
        self._data['mediaDuration'] = int(md) if md == int(md) else str(md)  # type: ignore[typeddict-item]
        if self._data.get('_type') in ('IMFile', 'ScreenIMFile'):
            self._data['mediaDuration'] = 1
        self._data.setdefault('metadata', {})['clipSpeedAttribute'] = {'type': 'bool', 'value': scalar_fraction != 1}
        if self._data.get('_type') == 'UnifiedMedia':
            for sub_key in ('video', 'audio'):
                sub: dict[str, Any] = self._data.get(sub_key)  # type: ignore[assignment]
                if sub is not None:
                    sub['duration'] = self._data['duration']
                    sub['mediaDuration'] = self._data['mediaDuration']
                    sub['scalar'] = self._data['scalar']
                    sub['mediaStart'] = self._data.get('mediaStart', 0)
                    sub.setdefault('metadata', {})['clipSpeedAttribute'] = {'type': 'bool', 'value': scalar_fraction != 1}
        if self._data.get('_type') == 'StitchedMedia':
            for inner in self._data.get('medias', []):
                inner['scalar'] = self._data['scalar']
                # Keep inner's own mediaDuration; recalculate duration from it
                inner_md = Fraction(str(inner.get('mediaDuration', 0)))
                new_dur = inner_md * scalar_fraction
                inner['duration'] = round(new_dur)
                inner.setdefault('metadata', {})['clipSpeedAttribute'] = {
                    'type': 'bool', 'value': scalar_fraction != 1
                }
                if inner.get('_type') == 'UnifiedMedia':
                    for sub_key in ('video', 'audio'):
                        um_sub: dict[str, Any] = inner.get(sub_key)  # type: ignore[assignment]
                        if um_sub is not None:
                            um_sub['scalar'] = inner['scalar']
                            um_sub['duration'] = inner['duration']
                            um_sub['start'] = inner['start']
                            if 'mediaDuration' in inner:
                                um_sub['mediaDuration'] = inner['mediaDuration']
                            if 'mediaStart' in inner:
                                um_sub['mediaStart'] = inner['mediaStart']
            # Re-layout starts sequentially using stored int durations
            cursor = 0
            for inner in self._data.get('medias', []):
                inner['start'] = cursor
                if inner.get('_type') == 'UnifiedMedia':
                    for sub_key in ('video', 'audio'):
                        um_sub2: dict[str, Any] = inner.get(sub_key)  # type: ignore[assignment]
                        if um_sub2 is not None:
                            um_sub2['start'] = cursor
                cursor += int(inner['duration'])
            # Compute new wrapper duration as sum of segment durations
            new_wrapper_dur = cursor
            self._data['duration'] = new_wrapper_dur
            # Recalculate mediaDuration to maintain invariant
            if scalar_fraction != 0:
                md = Fraction(new_wrapper_dur) / scalar_fraction
                self._data['mediaDuration'] = int(md) if md == int(md) else str(md)
        if self._data.get('_type') == 'Group':
            from camtasia.timing import parse_scalar
            # Undo existing scalar to recover original duration, then apply new scalar
            wrapper_scalar = _old_scalar
            wrapper_dur = Fraction(str(self._data.get('duration', 0)))
            orig_wrapper_dur = wrapper_dur / wrapper_scalar if wrapper_scalar != 0 else wrapper_dur
            grp_new_dur = orig_wrapper_dur * scalar_fraction
            self._data['duration'] = round(grp_new_dur)  # type: ignore[typeddict-item]
            self._data['scalar'] = 1 if scalar_fraction == 1 else str(scalar_fraction)
            # Recalculate mediaDuration to maintain invariant
            if scalar_fraction != 0:
                grp_md = Fraction(str(self._data['duration'])) / scalar_fraction
                self._data['mediaDuration'] = int(grp_md) if grp_md == int(grp_md) else str(grp_md)
            for inner_track in self._data.get('tracks', []):
                for inner_clip_data in inner_track.get('medias', []):
                    inner_scalar_curr = parse_scalar(inner_clip_data.get('scalar', 1))
                    orig_inner_dur = Fraction(str(inner_clip_data.get('duration', 0))) / inner_scalar_curr if inner_scalar_curr != 0 else Fraction(str(inner_clip_data.get('duration', 0)))
                    orig_inner_start = Fraction(str(inner_clip_data.get('start', 0))) / wrapper_scalar if wrapper_scalar != 0 else Fraction(str(inner_clip_data.get('start', 0)))
                    new_inner_dur = orig_inner_dur * scalar_fraction
                    new_inner_start = orig_inner_start * scalar_fraction
                    inner_clip_data['scalar'] = 1 if scalar_fraction == 1 else str(scalar_fraction)
                    inner_clip_data['start'] = round(new_inner_start)
                    inner_clip_data['duration'] = round(new_inner_dur)
                    if inner_clip_data.get('_type') in ('IMFile', 'ScreenIMFile'):
                        inner_clip_data['mediaDuration'] = 1
                    elif inner_clip_data.get('_type') not in ('StitchedMedia', 'Group') and scalar_fraction != 0:
                            inner_md = Fraction(inner_clip_data['duration']) / scalar_fraction
                            inner_clip_data['mediaDuration'] = int(inner_md) if inner_md == int(inner_md) else str(inner_md)
                    # Set clipSpeedAttribute metadata
                    inner_clip_data.setdefault('metadata', {})['clipSpeedAttribute'] = {'type': 'bool', 'value': scalar_fraction != 1}
                    # Propagate to UnifiedMedia sub-dicts
                    if inner_clip_data.get('_type') == 'UnifiedMedia':
                        for sub_key in ('video', 'audio'):
                            sub = inner_clip_data.get(sub_key)
                            if sub is not None:
                                sub['scalar'] = inner_clip_data['scalar']
                                sub['start'] = inner_clip_data['start']
                                sub['duration'] = inner_clip_data['duration']
                                if 'mediaDuration' in inner_clip_data:
                                    sub['mediaDuration'] = inner_clip_data['mediaDuration']
                                if 'mediaStart' in inner_clip_data:
                                    sub['mediaStart'] = inner_clip_data['mediaStart']
                                sub.setdefault('metadata', {})['clipSpeedAttribute'] = {'type': 'bool', 'value': scalar_fraction != 1}
                    # Re-layout StitchedMedia nested segments
                    elif inner_clip_data.get('_type') == 'StitchedMedia':
                        for inner_seg in inner_clip_data.get('medias', []):
                            seg_scalar_curr = parse_scalar(inner_seg.get('scalar', 1))
                            seg_orig_dur = Fraction(str(inner_seg.get('duration', 0))) / seg_scalar_curr if seg_scalar_curr != 0 else Fraction(str(inner_seg.get('duration', 0)))
                            seg_new_dur = seg_orig_dur * scalar_fraction
                            inner_seg['scalar'] = 1 if scalar_fraction == 1 else str(scalar_fraction)
                            inner_seg['duration'] = round(seg_new_dur)
                            inner_seg.setdefault('metadata', {})['clipSpeedAttribute'] = {'type': 'bool', 'value': scalar_fraction != 1}
                            if inner_seg.get('_type') == 'UnifiedMedia':
                                for sub_key in ('video', 'audio'):
                                    sub = inner_seg.get(sub_key)
                                    if sub is not None:
                                        sub['scalar'] = inner_seg['scalar']
                                        sub['duration'] = inner_seg['duration']
                                        sub['start'] = inner_seg['start']
                                        if 'mediaDuration' in inner_seg:
                                            sub['mediaDuration'] = inner_seg['mediaDuration']
                                        if 'mediaStart' in inner_seg:
                                            sub['mediaStart'] = inner_seg['mediaStart']
                        # Re-layout starts sequentially
                        cursor = 0
                        for inner_seg in inner_clip_data.get('medias', []):
                            inner_seg['start'] = cursor
                            if inner_seg.get('_type') == 'UnifiedMedia':
                                for sub_key in ('video', 'audio'):
                                    sub = inner_seg.get(sub_key)
                                    if sub is not None:
                                        sub['start'] = cursor
                            cursor += round(Fraction(str(inner_seg['duration'])))
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
        """Clip opacity (0.0-1.0)."""
        params = self._data.get('parameters', {})
        val = params.get('opacity', 1.0)
        return float(val['defaultValue'] if isinstance(val, dict) else val)

    @opacity.setter
    def opacity(self, value: float) -> None:
        """Set the opacity."""
        if not 0.0 <= value <= 1.0:
            raise ValueError(f'opacity must be 0.0-1.0, got {value}')
        params = self._data.setdefault('parameters', {})
        existing = params.get('opacity')
        if isinstance(existing, dict):
            existing['defaultValue'] = value
            existing.pop('keyframes', None)
        else:
            params['opacity'] = value
        tracks = self._data.get('animationTracks', {})
        if 'visual' in tracks:
            tracks['visual'] = []

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
        params = self._data.setdefault('parameters', {})
        existing = params.get('volume')
        if isinstance(existing, dict):
            existing['defaultValue'] = value
            existing.pop('keyframes', None)
        else:
            params['volume'] = value

    @property
    def is_silent(self) -> bool:
        """Whether this clip has zero volume (gain == 0 or volume == 0)."""
        if self._data.get('_type') == 'UnifiedMedia':
            audio_gain = self._data.get('audio', {}).get('attributes', {}).get('gain', 1.0)
            volume = self._data.get('parameters', {}).get('volume', 1.0)
            if isinstance(volume, dict):
                volume = volume.get('defaultValue', 1.0)
            return bool(audio_gain == 0.0 or volume == 0.0)
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
        self.start = seconds_to_ticks(start_seconds)
        return self

    def set_duration_seconds(self, duration_seconds: float) -> Self:
        """Set the clip duration in seconds.

        Args:
            duration_seconds: New duration in seconds.

        Returns:
            Self for method chaining.
        """
        self.duration = seconds_to_ticks(duration_seconds)
        return self

    def set_time_range(self, start_seconds: float, duration_seconds: float) -> Self:
        """Set both start position and duration in seconds.

        Returns self for chaining.
        """
        self.start = seconds_to_ticks(start_seconds)
        self.duration = seconds_to_ticks(duration_seconds)
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
            'leftEdgeMods': [{'group': 'Video', 'duration': seconds_to_ticks(fade_in_seconds), 'parameters': [{'name': 'opacity', 'func': 'FadeFromValueFunc', 'value': 1.0}]}],
            'rightEdgeMods': [{'group': 'Video', 'duration': seconds_to_ticks(fade_out_seconds), 'parameters': [{'name': 'opacity', 'func': 'FadeFromValueFunc', 'value': 1.0}]}],
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

    def _add_visual_tracks_for_keyframes(self, keyframes: list[dict[str, Any]]) -> None:
        """Append animationTracks.visual segments for a list of parameter keyframes.

        Each keyframe should have ``time``, ``endTime``, ``duration``, and
        optionally ``interp``. One visual segment per unique (time, endTime)
        pair is created; duplicate times from parallel parameters (e.g.,
        translation0 and translation1 with identical keyframe times) are
        deduplicated so the visual track has one segment per animation step.

        Matches the pattern observed in real TechSmith projects where a
        clip with keyframed translation0+translation1 has 1 visual segment
        per keyframe time (not 2).
        """
        visual = self._ensure_visual_tracks()
        seen: set[tuple[int, int]] = {
            (int(v.get('range', [0])[0] if v.get('range') else 0), int(v.get('endTime', 0)))
            for v in visual
        }
        for kf in keyframes:
            time = int(kf.get('time', 0))
            end_time = int(kf.get('endTime', 0))
            if (time, end_time) in seen:
                continue
            seen.add((time, end_time))
            visual.append({
                'endTime': end_time,
                'duration': int(kf.get('duration', 0)),
                'range': [time, int(kf.get('duration', 0))],
                'interp': kf.get('interp', 'linr'),
            })

    def _add_opacity_track(self, keyframes: list[dict[str, Any]], *, default_value: float = 0.0) -> None:
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
            'defaultValue': default_value,
            'keyframes': param_kfs,
        }
        # Build animationTracks.visual — one segment per keyframe
        visual = self._ensure_visual_tracks()
        for kf in keyframes:
            visual.append({'endTime': kf['endTime'], 'duration': kf['duration'], 'range': [kf['time'], kf['duration']], 'interp': 'linr'})

    def _get_existing_opacity_keyframes(self) -> list[dict[str, Any]] | None:
        """Return existing opacity keyframes in the new format, or None."""
        opacity = self._data.get('parameters', {}).get('opacity')
        if opacity is None:
            return None
        if not isinstance(opacity, dict):
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
            end = int(Fraction(str(self._data.get('duration', self._data.get('mediaDuration', 0)))))
            in_ticks = min(in_ticks, end)
            self._add_opacity_track([
                {'time': 0, 'value': 1.0, 'endTime': in_ticks, 'duration': in_ticks},
                fade_out_kf,
            ], default_value=0.0)
        else:  # pragma: no cover
            self._clear_opacity()
            in_ticks = seconds_to_ticks(duration_seconds)
            end = int(Fraction(str(self._data.get('duration', self._data.get('mediaDuration', 0)))))
            in_ticks = min(in_ticks, end)
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
        end = int(Fraction(str(self._data.get('duration', self._data.get('mediaDuration', 0)))))
        ticks = min(ticks, end)
        existing = self._get_existing_opacity_keyframes()
        if existing and existing[0]['value'] == 1.0:
            # Fade-in already exists — merge
            fade_in_kf = existing[0]
            self._clear_opacity()
            self._add_opacity_track([
                fade_in_kf,
                {'time': end - ticks, 'value': 0.0, 'endTime': end, 'duration': ticks},
            ], default_value=0.0)
        else:  # pragma: no cover
            self._clear_opacity()
            self._add_opacity_track([
                {'time': end - ticks, 'value': 0.0, 'endTime': end, 'duration': ticks},
            ], default_value=1.0)
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
        end = int(Fraction(str(self._data.get('duration', self._data.get('mediaDuration', 0)))))
        kfs: list[dict[str, Any]] = []
        if fade_in_seconds > 0:
            in_ticks = seconds_to_ticks(fade_in_seconds)
            in_ticks = min(in_ticks, end)
            kfs.append({
                'time': 0, 'value': 1.0,
                'endTime': in_ticks, 'duration': in_ticks,
            })
        if fade_out_seconds > 0:
            out_ticks = seconds_to_ticks(fade_out_seconds)
            out_ticks = min(out_ticks, end)
            kfs.append({
                'time': end - out_ticks, 'value': 0.0,
                'endTime': end, 'duration': out_ticks,
            })
        if kfs:
            dv = 0.0 if fade_in_seconds > 0 else 1.0
            self._add_opacity_track(kfs, default_value=dv)
        return self

    def set_opacity(self, opacity: float) -> Self:
        """Set a static opacity for the entire clip.

        Args:
            opacity: Opacity value (0.0-1.0).

        Returns:
            ``self`` for chaining.
        """
        if not 0.0 <= opacity <= 1.0:
            raise ValueError(f'Opacity must be 0.0-1.0, got {opacity}')
        params = self._data.setdefault('parameters', {})
        existing = params.get('opacity')
        if isinstance(existing, dict):
            existing['defaultValue'] = opacity
            existing.pop('keyframes', None)
        else:
            params['opacity'] = opacity
        tracks = self._data.get('animationTracks', {})
        if 'visual' in tracks:
            tracks['visual'] = []
        return self

    def clear_animations(self) -> Self:
        """Clear all animations: opacity keyframes, scale/position/rotation/crop/volume keyframes, and visual animation tracks.

        Returns:
            ``self`` for chaining.
        """
        params = self._data.get('parameters', {})
        for p in params.values():
            if isinstance(p, dict):
                p.pop('keyframes', None)
        self._data['animationTracks'] = {}
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
            opacity: Shadow opacity (0.0-1.0).
            angle: Shadow angle in radians.
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

    def save_lut_preset(self, preset_name: str) -> None:
        """Persist the current LutEffect parameters as a named preset.

        Finds the first ``LutEffect`` on this clip and writes its
        parameters to ``metadata.lutPresets[preset_name]`` on the
        clip's data dict (project-level persistence).

        Args:
            preset_name: Name to store the preset under.

        Raises:
            ValueError: If no LutEffect is applied to this clip.
        """
        from camtasia.effects.visual import LutEffect
        lut_effect: LutEffect | None = None
        for effect_dict in self._data.get('effects', []):
            if effect_dict.get('effectName') == EffectName.LUT_EFFECT:
                lut_effect = LutEffect(effect_dict)
                break
        if lut_effect is None:
            raise ValueError('No LutEffect found on this clip')
        import copy
        preset_data = copy.deepcopy(dict(lut_effect.parameters))
        meta = self._data.setdefault('metadata', {})
        meta.setdefault('lutPresets', {})[preset_name] = preset_data

    def add_media_matte(self, *, intensity: float = 1.0, matte_mode: int = 1, track_depth: int = 10002,
                        preset_name: str = 'Media Matte Luminosity') -> Self:
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

    _RAMP_POSITION_MAP: ClassVar[dict[str, int]] = {
        'outside': 0,
        'span': 1,
        'inside': 2,
    }

    def add_emphasize(
        self,
        *,
        ramp_position: str = 'inside',
        ramp_in_seconds: float = 0.0,
        ramp_out_seconds: float = 0.0,
        intensity: float = 0.5,
    ) -> Emphasize:
        """Add an audio emphasis effect wrapping the :class:`Emphasize` effect.

        Args:
            ramp_position: Ramp position — ``'outside'``, ``'span'``, or ``'inside'``.
            ramp_in_seconds: Ramp-in duration in seconds.
            ramp_out_seconds: Ramp-out duration in seconds.
            intensity: Emphasis strength (0.0-1.0).

        Returns:
            The created :class:`Emphasize` effect instance.

        Raises:
            ValueError: If *ramp_position* is not one of the accepted values.
        """
        if ramp_position not in self._RAMP_POSITION_MAP:
            raise ValueError(
                f"ramp_position must be 'outside', 'span', or 'inside', got {ramp_position!r}"
            )
        record: dict[str, Any] = {
            'effectName': EffectName.EMPHASIZE,
            'bypassed': False,
            'category': 'categoryAudioEffects',
            'parameters': {
                'emphasizeAmount': intensity,
                'emphasizeRampPosition': self._RAMP_POSITION_MAP[ramp_position],
                'emphasizeRampInTime': seconds_to_ticks(ramp_in_seconds),
                'emphasizeRampOutTime': seconds_to_ticks(ramp_out_seconds),
            },
        }
        self._data.setdefault('effects', []).append(record)
        return Emphasize(record)

    def add_noise_removal(self, *, amount: float = 0.8, bypassed: bool = False) -> Self:
        """Add a DFN3 VST noise-removal effect to this clip.

        Args:
            amount: Noise-removal strength (0.0 = none, 1.0 = max).
            bypassed: When True, the effect is disabled at the default keyframe.
        """
        self.add_effect({
            'effectName': 'VSTEffect-DFN3NoiseRemoval',
            'bypassed': bypassed,
            'category': 'categoryAudioEffects',
            'parameters': {
                'Amount': amount,
                'Bypass': 1.0 if bypassed else 0.0,
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
        if isinstance(existing, dict):
            existing.setdefault('keyframes', []).append(kf_entry)
        else:
            default_val = existing if isinstance(existing, (int, float)) else 0.0
            params[parameter] = {
                'type': 'double',
                'defaultValue': default_val,
                'keyframes': [kf_entry],
            }
        # For visual parameters, create a matching animationTracks.visual segment
        _VISUAL_PARAMS = {
            'opacity', 'translation0', 'translation1',
            'scale0', 'scale1', 'rotation2',
            'geometryCrop0', 'geometryCrop1', 'geometryCrop2', 'geometryCrop3',
        }
        if parameter in _VISUAL_PARAMS:
            self._add_visual_tracks_for_keyframes([kf_entry])
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
            if parameter == 'opacity':
                tracks = self._data.get('animationTracks', {})
                if 'visual' in tracks:
                    tracks['visual'] = []
        else:  # pragma: no cover
            for p in params.values():
                if isinstance(p, dict):
                    p.pop('keyframes', None)
            self._data['animationTracks'] = {}
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
        self._clear_opacity()
        from camtasia.timing import seconds_to_ticks
        dur = seconds_to_ticks(duration_seconds) if duration_seconds is not None else self.duration
        kfs = [{'endTime': dur, 'time': 0, 'value': end_opacity, 'duration': dur}]
        self._add_opacity_track(kfs, default_value=start_opacity)
        return self

    def set_position_keyframes(
        self,
        keyframes: list[tuple[float, float, float]],
        *,
        interp: str = 'linr',
    ) -> Self:
        """Set position keyframes for animated movement.

        Args:
            keyframes: List of (time_seconds, x, y) tuples.
            interp: Interpolation mode applied to all keyframes. Common
                values observed in real Camtasia projects:
                ``'linr'`` (linear, default), ``'eioe'`` (ease in/out),
                ``'easi'`` (ease in), ``'easo'`` (ease out),
                ``'bezi'`` (bezier curve). Pass a tuple of per-keyframe
                strings via :meth:`set_position_keyframes_with_interp`
                for heterogeneous easing.
        """
        from camtasia.timing import seconds_to_ticks
        params = self._data.setdefault('parameters', {})
        x_kfs = []
        y_kfs = []
        for i, (t, x, y) in enumerate(keyframes):
            ticks = seconds_to_ticks(t)
            next_ticks = seconds_to_ticks(keyframes[i + 1][0]) if i + 1 < len(keyframes) else ticks
            dur = next_ticks - ticks
            x_kfs.append({'endTime': next_ticks, 'time': ticks, 'value': x, 'duration': dur, 'interp': interp})
            y_kfs.append({'endTime': next_ticks, 'time': ticks, 'value': y, 'duration': dur, 'interp': interp})
        params['translation0'] = {'type': 'double', 'defaultValue': keyframes[-1][1], 'keyframes': x_kfs}
        params['translation1'] = {'type': 'double', 'defaultValue': keyframes[-1][2], 'keyframes': y_kfs}
        # x_kfs and y_kfs have identical timing; adding one set suffices
        self._add_visual_tracks_for_keyframes(x_kfs)
        return self

    def set_position_keyframes_with_interp(
        self,
        keyframes: list[tuple[float, float, float, str]],
    ) -> Self:
        """Set position keyframes with a per-keyframe interpolation mode.

        Args:
            keyframes: List of (time_seconds, x, y, interp) tuples. See
                :meth:`set_position_keyframes` for valid interp values.
        """
        from camtasia.timing import seconds_to_ticks
        params = self._data.setdefault('parameters', {})
        x_kfs: list[dict[str, Any]] = []
        y_kfs: list[dict[str, Any]] = []
        for i, (t, x, y, interp) in enumerate(keyframes):
            ticks = seconds_to_ticks(t)
            next_ticks = seconds_to_ticks(keyframes[i + 1][0]) if i + 1 < len(keyframes) else ticks
            dur = next_ticks - ticks
            x_kfs.append({'endTime': next_ticks, 'time': ticks, 'value': x, 'duration': dur, 'interp': interp})
            y_kfs.append({'endTime': next_ticks, 'time': ticks, 'value': y, 'duration': dur, 'interp': interp})
        params['translation0'] = {'type': 'double', 'defaultValue': keyframes[-1][1], 'keyframes': x_kfs}
        params['translation1'] = {'type': 'double', 'defaultValue': keyframes[-1][2], 'keyframes': y_kfs}
        self._add_visual_tracks_for_keyframes(x_kfs)
        return self

    def set_scale_keyframes(self, keyframes: list[tuple[float, float]]) -> Self:
        """Set scale keyframes for animated scaling.

        Args:
            keyframes: List of (time_seconds, scale) tuples.
        """
        from camtasia.timing import seconds_to_ticks
        params = self._data.setdefault('parameters', {})
        kfs = []
        for i, (t, s) in enumerate(keyframes):
            ticks = seconds_to_ticks(t)
            next_ticks = seconds_to_ticks(keyframes[i + 1][0]) if i + 1 < len(keyframes) else ticks
            dur = next_ticks - ticks
            kfs.append({'endTime': next_ticks, 'time': ticks, 'value': s, 'duration': dur})
        params['scale0'] = {'type': 'double', 'defaultValue': keyframes[-1][1], 'keyframes': kfs}
        params['scale1'] = {'type': 'double', 'defaultValue': keyframes[-1][1], 'keyframes': copy.deepcopy(kfs)}
        self._add_visual_tracks_for_keyframes(kfs)
        return self

    def set_rotation_keyframes(self, keyframes: list[tuple[float, float]]) -> Self:
        """Set rotation keyframes for animated rotation.

        Args:
            keyframes: List of (time_seconds, rotation_degrees) tuples.
        """
        import math

        from camtasia.timing import seconds_to_ticks
        params = self._data.setdefault('parameters', {})
        kfs = []
        for i, (t, deg) in enumerate(keyframes):
            ticks = seconds_to_ticks(t)
            next_ticks = seconds_to_ticks(keyframes[i + 1][0]) if i + 1 < len(keyframes) else ticks
            dur = next_ticks - ticks
            kfs.append({'endTime': next_ticks, 'time': ticks, 'value': math.radians(deg), 'duration': dur})
        params['rotation2'] = {'type': 'double', 'defaultValue': kfs[-1]['value'], 'keyframes': kfs}
        self._add_visual_tracks_for_keyframes(kfs)
        return self

    def set_crop_keyframes(self, keyframes: list[tuple[float, float, float, float, float]]) -> Self:
        """Set crop keyframes for animated cropping.

        Args:
            keyframes: List of (time_seconds, left, top, right, bottom) tuples.
                Values 0.0-1.0.
        """
        from camtasia.timing import seconds_to_ticks
        params = self._data.setdefault('parameters', {})
        last_kfs: list[dict[str, Any]] = []
        for i, name in enumerate(['geometryCrop0', 'geometryCrop1', 'geometryCrop2', 'geometryCrop3']):
            kfs = []
            for ki, kf in enumerate(keyframes):
                ticks = seconds_to_ticks(kf[0])
                next_ticks = seconds_to_ticks(keyframes[ki + 1][0]) if ki + 1 < len(keyframes) else ticks
                dur = next_ticks - ticks
                kfs.append({'endTime': next_ticks, 'time': ticks, 'value': kf[i + 1], 'duration': dur})
            params[name] = {'type': 'double', 'defaultValue': kfs[-1]['value'], 'keyframes': kfs}
            last_kfs = kfs
        # All four crop params have identical timing; dedup to one segment per time
        self._add_visual_tracks_for_keyframes(last_kfs)
        return self

    def set_volume_fade(self, start_volume: float = 1.0, end_volume: float = 0.0, duration_seconds: float | None = None) -> Self:
        """Add a volume fade keyframe animation."""
        from camtasia.timing import seconds_to_ticks
        dur = seconds_to_ticks(duration_seconds) if duration_seconds is not None else self.duration
        self._data.setdefault('parameters', {})['volume'] = {
            'type': 'double',
            'defaultValue': start_volume,
            'keyframes': [
                {'endTime': dur, 'time': 0, 'value': end_volume, 'duration': dur},
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
                fi_ticks = min(seconds_to_ticks(fade_in), dur_ticks)
                keyframes.append({'endTime': fi_ticks, 'time': 0, 'value': 1.0, 'duration': fi_ticks})
            else:
                fi_ticks = 0
            if fade_out > 0:
                fo_ticks = min(seconds_to_ticks(fade_out), dur_ticks - fi_ticks)
                if fo_ticks < 0:
                    fo_ticks = 0  # pragma: no cover  # defensive: fi_ticks is clamped to dur_ticks so dur-fi >= 0
                fo_start = dur_ticks - fo_ticks
                keyframes.append({'endTime': dur_ticks, 'time': fo_start, 'value': 0.0, 'duration': fo_ticks})
            self._clear_opacity()
            self._add_opacity_track(keyframes, default_value=0.0 if fade_in > 0 else 1.0)

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
        warnings.warn('source_path is deprecated, use source_id', DeprecationWarning, stacklevel=2)
        return self._data.get('src', '')

    @property
    def media_start_seconds(self) -> float:
        """Media start offset in seconds."""
        return float(Fraction(str(self.media_start))) / EDIT_RATE

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
        for _parameter_name, parameter_value in parameters.items():
            if isinstance(parameter_value, dict) and 'keyframes' in parameter_value:
                parameter_value.pop('keyframes')
        self._data['animationTracks'] = {}
        return self

    def copy_timing_from(self, source_clip: BaseClip) -> Self:
        """Copy start time and duration from another clip."""
        self.start = source_clip.start
        self.duration = source_clip.duration
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
        self.start = seconds_to_ticks(target_start_seconds)
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
        from camtasia.timeline.timeline import _remap_clip_ids_with_map
        id_counter = [cloned_data['id']]
        id_map: dict[int, int] = {}
        _remap_clip_ids_with_map(cloned_data, id_counter, id_map)
        target_track._data.setdefault('medias', []).append(cloned_data)
        from camtasia.timeline.clips import clip_from_dict
        return clip_from_dict(cloned_data)

    # ------------------------------------------------------------------
    # L3 — Animation axis-extensions and audio/trim helpers
    # ------------------------------------------------------------------

    def _build_param_keyframes(
        self, keyframes: list[tuple[float, float]],
    ) -> list[dict[str, Any]]:
        """Build keyframe dicts from ``(time_seconds, value)`` tuples."""
        kfs: list[dict[str, Any]] = []
        for i, (t, v) in enumerate(keyframes):
            ticks = seconds_to_ticks(t)
            next_ticks = seconds_to_ticks(keyframes[i + 1][0]) if i + 1 < len(keyframes) else ticks
            dur = next_ticks - ticks
            kfs.append({'endTime': next_ticks, 'time': ticks, 'value': v, 'duration': dur})
        return kfs

    def _set_single_param_keyframes(
        self, param_name: str, keyframes: list[tuple[float, float]], *, visual: bool = True,
    ) -> Self:
        """Write keyframes for a single parameter name."""
        kfs = self._build_param_keyframes(keyframes)
        params = self._data.setdefault('parameters', {})
        params[param_name] = {
            'type': 'double',
            'defaultValue': keyframes[-1][1],
            'keyframes': kfs,
        }
        if visual:
            self._add_visual_tracks_for_keyframes(kfs)
        return self

    def set_skew_keyframes(self, keyframes: list[tuple[float, float]]) -> Self:
        """Set skew keyframes for animated skewing.

        .. warning::
            The Camtasia parameter name ``'geometrySkew'`` is assumed.
            This has not been verified against all Camtasia versions and
            may need adjustment.

        Args:
            keyframes: List of ``(time_seconds, skew_value)`` tuples.
        """
        return self._set_single_param_keyframes('geometrySkew', keyframes)

    def set_rotation_x_keyframes(self, keyframes: list[tuple[float, float]]) -> Self:
        """Set X-axis rotation keyframes (``rotation0``).

        Args:
            keyframes: List of ``(time_seconds, radians)`` tuples.
        """
        return self._set_single_param_keyframes('rotation0', keyframes)

    def set_rotation_y_keyframes(self, keyframes: list[tuple[float, float]]) -> Self:
        """Set Y-axis rotation keyframes (``rotation1``).

        Args:
            keyframes: List of ``(time_seconds, radians)`` tuples.
        """
        return self._set_single_param_keyframes('rotation1', keyframes)

    def set_translation_z_keyframes(self, keyframes: list[tuple[float, float]]) -> Self:
        """Set Z-axis translation keyframes (``translation2``).

        Args:
            keyframes: List of ``(time_seconds, z_value)`` tuples.
        """
        return self._set_single_param_keyframes('translation2', keyframes)

    def restore_animation(self) -> Self:
        """Clear all animations and reset transforms to defaults.

        Convenience alias that calls :meth:`clear_animations` followed
        by :meth:`reset_transforms`.
        """
        self.clear_animations()
        self.reset_transforms()
        return self

    def trim_head(self, seconds: float) -> Self:
        """Trim the clip start by advancing it forward.

        Increases ``start`` and ``mediaStart`` while decreasing
        ``duration`` by the given number of seconds.

        Args:
            seconds: Seconds to trim from the beginning.
        """
        ticks = seconds_to_ticks(seconds)
        ticks = min(ticks, self.duration)
        self.start = self.start + ticks
        self.media_start = Fraction(str(self.media_start)) + Fraction(ticks)
        self.duration = self.duration - ticks
        return self

    def trim_tail(self, seconds: float) -> Self:
        """Trim the clip end by shortening its duration.

        Args:
            seconds: Seconds to trim from the end.
        """
        ticks = seconds_to_ticks(seconds)
        ticks = min(ticks, self.duration)
        self.duration = self.duration - ticks
        return self

    def silence_audio(self, start_seconds: float, end_seconds: float) -> Self:
        """Silence a region by adding volume keyframes that dip to 0.

        Inserts four keyframes: hold current volume up to *start_seconds*,
        drop to 0 at *start_seconds*, hold 0 until *end_seconds*, then
        restore to 1.0 at *end_seconds*.

        Args:
            start_seconds: Start of the silent region (clip-relative).
            end_seconds: End of the silent region (clip-relative).
        """
        self.set_volume_keyframes([
            (start_seconds, 0.0),
            (end_seconds, 1.0),
        ])
        return self

    def separate_video_and_audio(self) -> dict[str, Any] | None:
        """Extract audio data for separate insertion on another track.

        For video clips (``VMFile``, ``ScreenVMFile``) or ``UnifiedMedia``
        with an audio sub-clip, returns a partially-configured ``AMFile``
        dict that the caller can insert into a track.

        Returns:
            An ``AMFile``-shaped dict ready for track insertion, or
            ``None`` if this clip has no audio to separate.
        """
        if self.clip_type == 'UnifiedMedia':
            audio = self._data.get('audio')
            if audio is None:
                return None
            return copy.deepcopy(audio)
        if self.clip_type in ('VMFile', 'ScreenVMFile'):
            return {
                '_type': 'AMFile',
                'id': -1,
                'src': self._data.get('src', 0),
                'start': self.start,
                'duration': self.duration,
                'mediaStart': self._data.get('mediaStart', 0),
                'mediaDuration': self._data.get('mediaDuration', self.duration),
                'scalar': self._data.get('scalar', 1),
                'attributes': {'gain': 1.0},
            }
        return None

    def add_audio_fade_in(self, duration_seconds: float) -> Self:
        """Add an audio volume fade-in (0 → 1) over *duration_seconds*.

        Distinct from :meth:`fade_in` which operates on visual opacity.

        Args:
            duration_seconds: Fade duration in seconds.
        """
        return self.set_volume_keyframes([
            (0.0, 0.0),
            (duration_seconds, 1.0),
        ])

    def add_audio_fade_out(self, duration_seconds: float) -> Self:
        """Add an audio volume fade-out (1 → 0) ending at the clip's end.

        Distinct from :meth:`fade_out` which operates on visual opacity.

        Args:
            duration_seconds: Fade duration in seconds.
        """
        end = self.duration_seconds
        return self.set_volume_keyframes([
            (end - duration_seconds, 1.0),
            (end, 0.0),
        ])

    def add_audio_point(self, time_seconds: float, volume: float) -> Self:
        """Add a single volume keyframe at the given time.

        Args:
            time_seconds: Clip-relative time in seconds.
            volume: Volume level (>= 0.0).
        """
        return self.add_keyframe('volume', time_seconds, volume)

    def remove_all_audio_points(self) -> Self:
        """Clear all volume keyframes."""
        return self.clear_keyframes('volume')

    def set_volume_keyframes(self, keyframes: list[tuple[float, float]]) -> Self:
        """Set the full volume envelope via keyframes.

        Args:
            keyframes: List of ``(time_seconds, volume)`` tuples.
        """
        return self._set_single_param_keyframes('volume', keyframes, visual=False)

    # ------------------------------------------------------------------
    # L3 — Motion path, ClipSpeed effect, and animation helpers
    # ------------------------------------------------------------------

    def apply_to_all_animations(self, func: Callable[[dict[str, Any]], Any]) -> Self:
        """Call *func* on each animation entry in ``animationTracks.visual``.

        Args:
            func: Callable receiving a single animation dict.

        Returns:
            ``self`` for chaining.
        """
        for anim in self._data.get('animationTracks', {}).get('visual', []):
            func(anim)
        return self

    def apply_clip_speed_effect(self, speed: float, duration: int | None = None) -> Self:
        """Register a Camtasia-native ``ClipSpeed`` effect if not already present.

        Args:
            speed: Speed multiplier for the effect parameters.
            duration: Optional effect duration in ticks. Defaults to clip duration.

        Returns:
            ``self`` for chaining.
        """
        if self.is_effect_applied('ClipSpeed'):
            return self
        record: dict[str, Any] = {
            'effectName': 'ClipSpeed',
            'bypassed': False,
            'category': '',
            'parameters': {'speed': speed},
        }
        if duration is not None:
            record['duration'] = duration
        self._data.setdefault('effects', []).append(record)
        return self

    def set_position_keyframes_with_line_type(
        self,
        keyframes: list[tuple[float, float, float]],
        line_types: list[str],
    ) -> Self:
        """Set position keyframes tagging each with a line type.

        Args:
            keyframes: List of ``(time_seconds, x, y)`` tuples.
            line_types: Per-keyframe line type: ``'angle'``, ``'curve'``,
                or ``'combination'``.

        Returns:
            ``self`` for chaining.
        """
        params = self._data.setdefault('parameters', {})
        x_kfs: list[dict[str, Any]] = []
        y_kfs: list[dict[str, Any]] = []
        for i, (t, x, y) in enumerate(keyframes):
            ticks = seconds_to_ticks(t)
            next_ticks = seconds_to_ticks(keyframes[i + 1][0]) if i + 1 < len(keyframes) else ticks
            dur = next_ticks - ticks
            lt = line_types[i] if i < len(line_types) else 'curve'
            kf: dict[str, Any] = {
                'endTime': next_ticks, 'time': ticks, 'value': x,
                'duration': dur, 'lineType': lt,
            }
            x_kfs.append(kf)
            y_kfs.append({
                'endTime': next_ticks, 'time': ticks, 'value': y,
                'duration': dur, 'lineType': lt,
            })
        params['translation0'] = {'type': 'double', 'defaultValue': keyframes[-1][1], 'keyframes': x_kfs}
        params['translation1'] = {'type': 'double', 'defaultValue': keyframes[-1][2], 'keyframes': y_kfs}
        self._add_visual_tracks_for_keyframes(x_kfs)
        return self

    def set_position_bezier_handles(
        self,
        keyframes_with_in_out_tangents: list[dict[str, Any]],
    ) -> Self:
        """Write bezier tangent control points for position keyframes.

        Each entry must have keys: ``time``, ``x``, ``y``, and optionally
        ``in_tangent`` (dict with ``x``, ``y``) and ``out_tangent``
        (dict with ``x``, ``y``).

        Args:
            keyframes_with_in_out_tangents: Keyframe dicts with tangent data.

        Returns:
            ``self`` for chaining.
        """
        params = self._data.setdefault('parameters', {})
        x_kfs: list[dict[str, Any]] = []
        y_kfs: list[dict[str, Any]] = []
        entries = keyframes_with_in_out_tangents
        for i, entry in enumerate(entries):
            ticks = seconds_to_ticks(entry['time'])
            next_ticks = seconds_to_ticks(entries[i + 1]['time']) if i + 1 < len(entries) else ticks
            dur = next_ticks - ticks
            x_kf: dict[str, Any] = {
                'endTime': next_ticks, 'time': ticks, 'value': entry['x'],
                'duration': dur, 'interp': 'bezi',
            }
            y_kf: dict[str, Any] = {
                'endTime': next_ticks, 'time': ticks, 'value': entry['y'],
                'duration': dur, 'interp': 'bezi',
            }
            if 'in_tangent' in entry:
                x_kf['inTangent'] = entry['in_tangent']['x']
                y_kf['inTangent'] = entry['in_tangent']['y']
            if 'out_tangent' in entry:
                x_kf['outTangent'] = entry['out_tangent']['x']
                y_kf['outTangent'] = entry['out_tangent']['y']
            x_kfs.append(x_kf)
            y_kfs.append(y_kf)
        params['translation0'] = {'type': 'double', 'defaultValue': entries[-1]['x'], 'keyframes': x_kfs}
        params['translation1'] = {'type': 'double', 'defaultValue': entries[-1]['y'], 'keyframes': y_kfs}
        self._add_visual_tracks_for_keyframes(x_kfs)
        return self

    def add_motion_point(
        self,
        time_seconds: float,
        x: float,
        y: float,
        line_type: str = 'curve',
    ) -> Self:
        """Add a single motion point to existing position keyframes.

        Convenience wrapper that appends to the current translation
        keyframes or creates them if absent.

        Args:
            time_seconds: Time in seconds.
            x: X position.
            y: Y position.
            line_type: Line type tag (``'angle'``, ``'curve'``, ``'combination'``).

        Returns:
            ``self`` for chaining.
        """
        params = self._data.setdefault('parameters', {})
        ticks = seconds_to_ticks(time_seconds)
        kf_x: dict[str, Any] = {
            'endTime': ticks, 'time': ticks, 'value': x,
            'duration': 0, 'lineType': line_type,
        }
        kf_y: dict[str, Any] = {
            'endTime': ticks, 'time': ticks, 'value': y,
            'duration': 0, 'lineType': line_type,
        }
        # Patch previous keyframe's endTime/duration to point to this one
        for param_name, kf in [('translation0', kf_x), ('translation1', kf_y)]:
            existing = params.get(param_name)
            if isinstance(existing, dict) and existing.get('keyframes'):
                prev = existing['keyframes'][-1]
                prev['endTime'] = ticks
                prev['duration'] = ticks - prev['time']
                existing['keyframes'].append(kf)
                existing['defaultValue'] = kf['value']
            else:
                params[param_name] = {
                    'type': 'double',
                    'defaultValue': kf['value'],
                    'keyframes': [kf],
                }
        self._add_visual_tracks_for_keyframes([kf_x])
        return self

    def apply_motion_path(
        self,
        points: list[tuple[float, float, float]],
        *,
        easing: str = 'linear',
        auto_orient: bool = False,
        line_type: str = 'curve',
    ) -> Self:
        """Apply a MotionPath effect and set position keyframes.

        High-level wrapper that:
        1. Adds a ``MotionPath`` effect (if not already present).
        2. Sets position keyframes with the given line type.
        3. Optionally stores ``autoOrient`` metadata.

        Args:
            points: List of ``(time_seconds, x, y)`` tuples.
            easing: Easing mode stored in the effect parameters.
            auto_orient: Whether to auto-orient the clip along the path.
            line_type: Line type for all keyframes.

        Returns:
            ``self`` for chaining.
        """
        if not self.is_effect_applied('MotionPath'):
            self._data.setdefault('effects', []).append({
                'effectName': 'MotionPath',
                'bypassed': False,
                'category': 'categoryVisualEffects',
                'parameters': {'easing': easing, 'autoOrient': auto_orient},
            })
        line_types = [line_type] * len(points)
        self.set_position_keyframes_with_line_type(points, line_types)
        return self

    def set_speed_by_duration(self, target_duration_seconds: float) -> Self:
        """Set playback speed to achieve a target duration.

        Computes the required speed multiplier from the current duration
        and delegates to :meth:`set_speed`.

        Args:
            target_duration_seconds: Desired playback duration in seconds.
        """
        if target_duration_seconds <= 0:
            raise ValueError(f'target_duration_seconds must be > 0, got {target_duration_seconds}')
        speed = self.duration_seconds / target_duration_seconds
        return self.set_speed(speed)

    # ------------------------------------------------------------------
    # L2 — Crop / fit helpers
    # ------------------------------------------------------------------

    def crop_to_aspect(self, aspect_ratio: float) -> Self:
        """Add a Crop effect sized to match the given aspect ratio.

        Computes symmetric left/right or top/bottom crop values so the
        visible area matches *aspect_ratio* (width / height). Assumes
        the clip currently fills a 1:1 normalized space (the Crop effect
        works in 0.0-1.0 normalized coordinates).

        Args:
            aspect_ratio: Target width / height ratio (e.g. 16/9 ≈ 1.778).

        Returns:
            ``self`` for chaining.
        """
        if aspect_ratio <= 0:
            raise ValueError(f'aspect_ratio must be > 0, got {aspect_ratio}')
        from camtasia.effects.visual import Crop as CropEffect
        if aspect_ratio > 1.0:
            # Wider than tall — crop top/bottom
            crop_v = (1.0 - 1.0 / aspect_ratio) / 2.0
            crop_h = 0.0
        else:
            # Taller than wide — crop left/right
            crop_h = (1.0 - aspect_ratio) / 2.0
            crop_v = 0.0
        record: dict[str, Any] = {
            'effectName': 'Crop',
            'bypassed': False,
            'category': 'categoryVisualEffects',
            'parameters': {
                'left': crop_h,
                'right': crop_h,
                'top': crop_v,
                'bottom': crop_v,
            },
        }
        self._data.setdefault('effects', []).append(record)
        return self

    def fit_to_canvas(self, mode: str = 'cover') -> Self:
        """Adjust scale and translation to fit the clip to the canvas.

        Args:
            mode: Fitting strategy.
                - ``'cover'``: scale up so the clip fully covers the canvas
                  (may crop edges).
                - ``'contain'``: scale down so the entire clip is visible
                  (may show letterbox/pillarbox).
                - ``'center'``: reset scale to 1.0 and center the clip
                  (no scaling, just positioning).

        Returns:
            ``self`` for chaining.

        Raises:
            ValueError: If *mode* is not one of the accepted values.
        """
        valid_modes = {'cover', 'contain', 'center'}
        if mode not in valid_modes:
            raise ValueError(f"mode must be one of {valid_modes}, got {mode!r}")
        sx, sy = self.scale
        if mode == 'center':
            self.scale = (1.0, 1.0)
            self.translation = (0.0, 0.0)
        elif mode == 'cover':
            factor = max(sx, sy) if sx != sy else max(1.0, sx)
            self.scale = (factor, factor)
            self.translation = (0.0, 0.0)
        else:  # contain
            factor = min(sx, sy) if sx != sy else min(1.0, sx)
            self.scale = (factor, factor)
            self.translation = (0.0, 0.0)
        return self
