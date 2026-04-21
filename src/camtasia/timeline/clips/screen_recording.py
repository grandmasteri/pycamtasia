"""Screen recording clips (ScreenVMFile, ScreenIMFile)."""
from __future__ import annotations

from typing import Any, NoReturn

from typing_extensions import Self

from .base import BaseClip


class ScreenVMFile(BaseClip):
    """Screen recording video clip.

    Inherits translation, scale, and other transform helpers from
    :class:`BaseClip`.  Adds cursor effect properties.

    Args:
        data: The raw clip dict.
    """

    def set_source(self, source_id: int) -> NoReturn:
        raise TypeError('Cannot change source on screen recording video clips')

    # -- Cursor --

    def _set_cursor_param(self, key: str, value: float, interp: str = 'linr') -> None:
        """Write a cursor parameter as a dict with interp (Camtasia's cursor format)."""
        params = self._data.setdefault('parameters', {})
        if isinstance(params.get(key), dict):
            params[key]['defaultValue'] = value
        else:
            params[key] = {'type': 'double', 'defaultValue': value, 'interp': interp}

    @property
    def cursor_scale(self) -> float:
        """Cursor enlargement factor."""
        return self._get_param_value('cursorScale', 1.0)

    @cursor_scale.setter
    def cursor_scale(self, value: float) -> None:
        """Set the cursor enlargement factor."""
        self._set_cursor_param('cursorScale', value)

    @property
    def cursor_opacity(self) -> float:
        """Cursor opacity (0.0-1.0)."""
        return self._get_param_value('cursorOpacity', 1.0)

    @cursor_opacity.setter
    def cursor_opacity(self, value: float) -> None:
        """Set the cursor opacity (0.0-1.0)."""
        self._set_cursor_param('cursorOpacity', value)

    @property
    def cursor_track_level(self) -> float:
        """Cursor track level."""
        return self._get_param_value('cursorTrackLevel')

    @property
    def smooth_cursor_across_edit_duration(self) -> float:
        """Smooth cursor across edit duration setting."""
        return self._get_param_value('smoothCursorAcrossEditDuration')

    @smooth_cursor_across_edit_duration.setter
    def smooth_cursor_across_edit_duration(self, value: float) -> None:
        self._set_cursor_param('smoothCursorAcrossEditDuration', value)

    # -- Cursor effects helpers --

    def _find_effect(self, name: str) -> dict[str, Any] | None:
        """Find an effect dict by name."""
        for e in self.effects:
            if e.get('effectName') == name:
                return e
        return None

    def _get_effect_param(self, effect_name: str, param: str, default: float = 0.0) -> float:
        effect = self._find_effect(effect_name)
        if effect is None:
            return default
        p = effect.get('parameters', {}).get(param, default)
        if isinstance(p, dict):
            return float(p.get('defaultValue', default))
        return float(p)

    @property
    def cursor_motion_blur_intensity(self) -> float:
        """CursorMotionBlur intensity."""
        return self._get_effect_param('CursorMotionBlur', 'intensity')

    @property
    def cursor_shadow(self) -> dict[str, float]:
        """CursorShadow parameters."""
        e = self._find_effect('CursorShadow')
        if e is None:
            return {}
        params = e.get('parameters', {})
        return {
            k: (v.get('defaultValue', 0.0) if isinstance(v, dict) else v)
            for k, v in params.items()
        }

    @property
    def cursor_physics(self) -> dict[str, float]:
        """CursorPhysics parameters (intensity, tilt)."""
        e = self._find_effect('CursorPhysics')
        if e is None:
            return {}
        params = e.get('parameters', {})
        return {
            k: (v.get('defaultValue', 0.0) if isinstance(v, dict) else v)
            for k, v in params.items()
        }

    @property
    def left_click_scaling(self) -> dict[str, float]:
        """LeftClickScaling parameters (scale, speed)."""
        e = self._find_effect('LeftClickScaling')
        if e is None:
            return {}
        params = e.get('parameters', {})
        return {
            k: (v.get('defaultValue', 0.0) if isinstance(v, dict) else v)
            for k, v in params.items()
        }


class ScreenIMFile(BaseClip):
    """Screen recording cursor overlay clip.

    Contains per-frame cursor position keyframes.

    Args:
        data: The raw clip dict.
    """

    @property
    def cursor_image_path(self) -> str | None:
        """Cursor image path identifier."""
        return self.parameters.get('cursorImagePath')

    @cursor_image_path.setter
    def cursor_image_path(self, value: str) -> None:
        """Set the cursor image path (replaces the cursor with a custom image)."""
        self._data.setdefault('parameters', {})['cursorImagePath'] = value

    def set_source(self, source_id: int) -> NoReturn:
        raise TypeError('Cannot change source on cursor overlay clips')

    @property
    def cursor_location_keyframes(self) -> list[dict[str, Any]]:
        """Cursor location keyframes.

        Returns:
            List of dicts with ``time``, ``endTime``, ``value``, ``duration``
            keys. ``value`` is ``[x, y, z]``.
        """
        loc = self.parameters.get('cursorLocation', {})
        return loc.get('keyframes', [])  # type: ignore[no-any-return]

    def set_cursor_location_keyframes(
        self,
        keyframes: list[tuple[float, float, float]],
    ) -> Self:
        """Set custom cursor path keyframes.

        Args:
            keyframes: List of ``(time_seconds, x, y)`` tuples. The Z
                coordinate is set to 0. Must be in ascending time order.

        Returns:
            ``self`` for chaining.
        """
        from camtasia.timing import seconds_to_ticks
        kfs: list[dict[str, Any]] = []
        for i, (t, x, y) in enumerate(keyframes):
            ticks = seconds_to_ticks(t)
            next_ticks = seconds_to_ticks(keyframes[i + 1][0]) if i + 1 < len(keyframes) else ticks
            dur = next_ticks - ticks
            kfs.append({
                'endTime': next_ticks,
                'time': ticks,
                'value': [x, y, 0],
                'duration': dur,
            })
        params = self._data.setdefault('parameters', {})
        params['cursorLocation'] = {
            'type': 'point3',
            'defaultValue': [keyframes[-1][1], keyframes[-1][2], 0] if keyframes else [0, 0, 0],
            'keyframes': kfs,
        }
        return self
