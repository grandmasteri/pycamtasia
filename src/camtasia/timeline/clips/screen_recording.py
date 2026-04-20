"""Screen recording clips (ScreenVMFile, ScreenIMFile)."""
from __future__ import annotations

from typing import Any, NoReturn

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
