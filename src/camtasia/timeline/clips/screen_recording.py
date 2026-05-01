"""Screen recording clips (ScreenVMFile, ScreenIMFile)."""
from __future__ import annotations

import enum
from typing import Any, ClassVar, NoReturn

from typing_extensions import Self

from .base import BaseClip


class CursorType(enum.Enum):
    """Predefined cursor type sentinels for :meth:`ScreenIMFile.set_cursor_type`."""

    ARROW = 'cursor://arrow'
    HAND = 'cursor://hand'
    IBEAM = 'cursor://ibeam'
    CROSSHAIR = 'cursor://crosshair'
    WAIT = 'cursor://wait'
    HELP = 'cursor://help'
    TEXT = 'cursor://text'
    NO_CURSOR = 'cursor://none'


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

    def _set_cursor_param_keyframes(
        self, key: str, keyframes: list[tuple[float, float]],
    ) -> None:
        """Write keyframed cursor parameter from ``(time_seconds, value)`` tuples."""
        from camtasia.timing import seconds_to_ticks
        kfs: list[dict[str, Any]] = []
        for i, (t, v) in enumerate(keyframes):
            ticks = seconds_to_ticks(t)
            next_ticks = seconds_to_ticks(keyframes[i + 1][0]) if i + 1 < len(keyframes) else ticks
            kfs.append({
                'endTime': next_ticks,
                'time': ticks,
                'value': v,
                'duration': next_ticks - ticks,
            })
        params = self._data.setdefault('parameters', {})
        params[key] = {
            'type': 'double',
            'defaultValue': keyframes[-1][1] if keyframes else 0.0,
            'interp': 'linr',
            'keyframes': kfs,
        }

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

    @cursor_track_level.setter
    def cursor_track_level(self, value: float) -> None:
        """Set the cursor track level."""
        self._set_cursor_param('cursorTrackLevel', value)

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

    # -- Cursor keyframe methods --

    def set_cursor_scale_keyframes(self, keyframes: list[tuple[float, float]]) -> None:
        """Set cursor scale keyframes.

        Args:
            keyframes: List of ``(time_seconds, scale)`` tuples in ascending
                time order.
        """
        self._set_cursor_param_keyframes('cursorScale', keyframes)

    def set_cursor_opacity_keyframes(self, keyframes: list[tuple[float, float]]) -> None:
        """Set cursor opacity keyframes.

        Args:
            keyframes: List of ``(time_seconds, opacity)`` tuples in ascending
                time order.
        """
        self._set_cursor_param_keyframes('cursorOpacity', keyframes)

    def hide_cursor(self) -> None:
        """Set cursor opacity to 0.0 for the whole clip."""
        self.cursor_opacity = 0.0

    def show_cursor(self) -> None:
        """Set cursor opacity to 1.0 for the whole clip."""
        self.cursor_opacity = 1.0

    @property
    def cursor_elevation(self) -> float:
        """Cursor elevation.

        .. warning::
            The ``cursorElevation`` key has not been observed in any
            TechSmith fixture. This property writes to
            ``metadata.cursorElevation`` — verify against a real project
            before relying on it.
        """
        return float(self._data.get('metadata', {}).get('cursorElevation', 0.0))

    @cursor_elevation.setter
    def cursor_elevation(self, value: float) -> None:
        self._data.setdefault('metadata', {})['cursorElevation'] = value


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

    @cursor_location_keyframes.setter
    def cursor_location_keyframes(self, keyframes: list[tuple[float, float, float]]) -> None:
        """Set cursor location keyframes from ``(time_seconds, x, y)`` tuples."""
        self.set_cursor_location_keyframes(keyframes)

    _INTERP_MAP: ClassVar[dict[str, str]] = {
        'linear': 'linr',
        'ease-in': 'easi',
        'ease-out': 'easo',
    }

    _LINE_TYPE_INTERP: ClassVar[dict[str, str]] = {
        'straight': 'linr',
        'curved': 'bezi',
        'bezier': 'bezi',
    }

    def set_cursor_location_keyframes(
        self,
        keyframes: list[tuple[float, float, float]],
        *,
        line_types: list[str] | None = None,
        bezier_handles: list[tuple[tuple[float, float], tuple[float, float]]] | None = None,
        easing: list[str] | None = None,
    ) -> Self:
        """Set custom cursor path keyframes.

        Args:
            keyframes: List of ``(time_seconds, x, y)`` tuples. The Z
                coordinate is set to 0. Must be in ascending time order.
            line_types: Per-keyframe line type — ``'straight'`` or
                ``'curved'``/``'bezier'``. When set to a bezier type the
                keyframe ``interp`` is written as ``'bezi'``.
            bezier_handles: Per-keyframe ``(in_tangent, out_tangent)``
                pairs where each tangent is ``(x, y)``. Implies bezier
                interpolation.
            easing: Per-keyframe easing — ``'linear'``, ``'ease-in'``,
                or ``'ease-out'``. Overrides the interpolation code
                derived from *line_types*.

        Returns:
            ``self`` for chaining.
        """
        from camtasia.timing import seconds_to_ticks
        kfs: list[dict[str, Any]] = []
        for i, (t, x, y) in enumerate(keyframes):
            ticks = seconds_to_ticks(t)
            next_ticks = seconds_to_ticks(keyframes[i + 1][0]) if i + 1 < len(keyframes) else ticks
            dur = next_ticks - ticks
            kf: dict[str, Any] = {
                'endTime': next_ticks,
                'time': ticks,
                'value': [x, y, 0],
                'duration': dur,
            }
            # Determine interp code: easing > line_types > default (none)
            if easing and i < len(easing):
                kf['interp'] = self._INTERP_MAP.get(easing[i], easing[i])
            elif line_types and i < len(line_types):
                kf['interp'] = self._LINE_TYPE_INTERP.get(line_types[i], 'linr')
            # Bezier tangent handles
            if bezier_handles and i < len(bezier_handles):
                in_tan, out_tan = bezier_handles[i]
                kf['inTangent'] = list(in_tan)
                kf['outTangent'] = list(out_tan)
                if 'interp' not in kf:
                    kf['interp'] = 'bezi'
            kfs.append(kf)
        params = self._data.setdefault('parameters', {})
        params['cursorLocation'] = {
            'type': 'point',
            'defaultValue': [keyframes[-1][1], keyframes[-1][2], 0] if keyframes else [0, 0, 0],
            'keyframes': kfs,
        }
        return self

    def set_cursor_location_with_bezier(
        self,
        keyframes: list[tuple[float, float, float, tuple[float, float], tuple[float, float]]],
    ) -> Self:
        """Set cursor path keyframes with bezier tangent handles.

        Convenience wrapper around :meth:`set_cursor_location_keyframes`
        that unpacks per-point tangent data.

        Args:
            keyframes: List of ``(time_seconds, x, y, in_tangent, out_tangent)``
                tuples where each tangent is ``(x, y)``.

        Returns:
            ``self`` for chaining.
        """
        points = [(t, x, y) for t, x, y, _in, _out in keyframes]
        handles = [(in_t, out_t) for _, _, _, in_t, out_t in keyframes]
        return self.set_cursor_location_keyframes(
            points, bezier_handles=handles,
        )

    @property
    def cursor_track_level(self) -> float:
        """Cursor track level."""
        return self._get_param_value('cursorTrackLevel')

    @cursor_track_level.setter
    def cursor_track_level(self, value: float) -> None:
        """Set the cursor track level."""
        params = self._data.setdefault('parameters', {})
        existing = params.get('cursorTrackLevel')
        if isinstance(existing, dict):
            existing['defaultValue'] = value
        else:
            params['cursorTrackLevel'] = {
                'type': 'double', 'defaultValue': value, 'interp': 'linr',
            }

    # -- Cursor path editing --

    def add_cursor_point(self, time_seconds: float, x: float, y: float) -> None:
        """Insert a cursor position keyframe at the given time.

        The keyframe is inserted in sorted order by time. If a keyframe
        already exists at the exact time, it is replaced.

        Args:
            time_seconds: Time in seconds.
            x: Cursor X coordinate.
            y: Cursor Y coordinate.
        """
        from camtasia.timing import seconds_to_ticks
        ticks = seconds_to_ticks(time_seconds)
        params = self._data.setdefault('parameters', {})
        loc = params.setdefault('cursorLocation', {'type': 'point', 'keyframes': []})
        kfs: list[dict[str, Any]] = loc.setdefault('keyframes', [])
        # Remove existing keyframe at same time
        kfs[:] = [kf for kf in kfs if kf['time'] != ticks]
        new_kf: dict[str, Any] = {
            'endTime': ticks, 'time': ticks, 'value': [x, y, 0], 'duration': 0,
        }
        # Insert in sorted order
        idx = 0
        for i, kf in enumerate(kfs):
            if kf['time'] > ticks:
                break
            idx = i + 1
        kfs.insert(idx, new_kf)
        # Recompute durations for adjacent keyframes
        self._recompute_cursor_durations(kfs)

    def delete_cursor_point(
        self, time_seconds: float, *, tolerance_seconds: float = 0.001,
    ) -> None:
        """Remove the cursor keyframe closest to the given time.

        Args:
            time_seconds: Target time in seconds.
            tolerance_seconds: Maximum distance in seconds for a match.

        Raises:
            ValueError: If no keyframe is within tolerance.
        """
        from camtasia.timing import seconds_to_ticks
        ticks = seconds_to_ticks(time_seconds)
        tol_ticks = seconds_to_ticks(tolerance_seconds)
        kfs = self._get_cursor_kfs()
        best_idx = None
        best_dist = tol_ticks + 1
        for i, kf in enumerate(kfs):
            dist = abs(kf['time'] - ticks)
            if dist < best_dist:
                best_dist = dist
                best_idx = i
        if best_idx is None or best_dist > tol_ticks:
            raise ValueError(
                f'No cursor keyframe within {tolerance_seconds}s of {time_seconds}s'
            )
        kfs.pop(best_idx)
        self._recompute_cursor_durations(kfs)

    def move_cursor_point(
        self, time_seconds: float, new_x: float, new_y: float,
    ) -> None:
        """Move the cursor keyframe at the given time to new coordinates.

        Args:
            time_seconds: Time of the keyframe to move.
            new_x: New X coordinate.
            new_y: New Y coordinate.

        Raises:
            ValueError: If no keyframe exists at the given time.
        """
        from camtasia.timing import seconds_to_ticks
        ticks = seconds_to_ticks(time_seconds)
        for kf in self._get_cursor_kfs():
            if kf['time'] == ticks:
                kf['value'] = [new_x, new_y, 0]
                return
        raise ValueError(f'No cursor keyframe at {time_seconds}s')

    def smooth_cursor_path(self, *, window: int = 3) -> None:
        """Apply a simple moving-average smoother to cursor location keyframes.

        Only X and Y coordinates are smoothed; Z and timing are preserved.

        Args:
            window: Number of keyframes in the averaging window (must be odd
                and >= 3).
        """
        kfs = self._get_cursor_kfs()
        if len(kfs) < window:
            return
        half = window // 2
        smoothed: list[tuple[float, float]] = []
        for i in range(len(kfs)):
            lo = max(0, i - half)
            hi = min(len(kfs), i + half + 1)
            xs = [kfs[j]['value'][0] for j in range(lo, hi)]
            ys = [kfs[j]['value'][1] for j in range(lo, hi)]
            smoothed.append((sum(xs) / len(xs), sum(ys) / len(ys)))
        for i, (sx, sy) in enumerate(smoothed):
            kfs[i]['value'] = [sx, sy, kfs[i]['value'][2]]

    def straighten_cursor_path(
        self, start_seconds: float, end_seconds: float,
    ) -> None:
        """Remove intermediate cursor keyframes between two times.

        Keeps the first keyframe at or after *start_seconds* and the last
        keyframe at or before *end_seconds*, removing everything in between.

        Args:
            start_seconds: Start of the range in seconds.
            end_seconds: End of the range in seconds.
        """
        from camtasia.timing import seconds_to_ticks
        start_ticks = seconds_to_ticks(start_seconds)
        end_ticks = seconds_to_ticks(end_seconds)
        kfs = self._get_cursor_kfs()
        in_range = [i for i, kf in enumerate(kfs)
                     if start_ticks <= kf['time'] <= end_ticks]
        if len(in_range) <= 2:
            return
        # Keep first and last in range, remove the rest
        to_remove = in_range[1:-1]
        for idx in reversed(to_remove):
            kfs.pop(idx)
        self._recompute_cursor_durations(kfs)

    def restore_cursor_path(self) -> None:
        """Clear custom cursor location keyframes.

        Removes the ``cursorLocation`` parameter entry entirely, restoring
        the original recorded cursor path.
        """
        params = self._data.get('parameters', {})
        params.pop('cursorLocation', None)

    def split_cursor_path(self, time_seconds: float) -> None:
        """Split the cursor path at the given time.

        Inserts a duplicate keyframe at *time_seconds* by interpolating
        the position from surrounding keyframes, creating a hard break
        in the path.

        Args:
            time_seconds: Split point in seconds.
        """
        from camtasia.timing import seconds_to_ticks
        ticks = seconds_to_ticks(time_seconds)
        kfs = self._get_cursor_kfs()
        # Find surrounding keyframes
        before = None
        after = None
        for kf in kfs:
            if kf['time'] <= ticks:
                before = kf
            if kf['time'] >= ticks and after is None:
                after = kf
        if before is None or after is None:
            return
        if before['time'] == ticks:
            # Already a keyframe at this time — insert a duplicate
            x, y, z = before['value']
        elif before is after:
            x, y, z = before['value']
        else:
            # Linear interpolation
            span = after['time'] - before['time']
            t = (ticks - before['time']) / span if span else 0
            x = before['value'][0] + t * (after['value'][0] - before['value'][0])
            y = before['value'][1] + t * (after['value'][1] - before['value'][1])
            z = 0
        # Insert two keyframes at the split point (with duration 0)
        new_kf_a: dict[str, Any] = {
            'endTime': ticks, 'time': ticks, 'value': [x, y, z], 'duration': 0,
        }
        new_kf_b: dict[str, Any] = {
            'endTime': ticks, 'time': ticks, 'value': [x, y, z], 'duration': 0,
        }
        idx = 0
        for i, kf in enumerate(kfs):
            if kf['time'] > ticks:
                break
            idx = i + 1
        kfs.insert(idx, new_kf_b)
        kfs.insert(idx, new_kf_a)
        self._recompute_cursor_durations(kfs)

    def set_no_cursor_at(self, time_seconds: float) -> None:
        """Hide the cursor at a specific time by swapping the cursor image.

        Inserts a keyframe-like marker that sets the cursor image path to
        a ``'no_cursor'`` sentinel. This is implemented by adding a cursor
        point at the given time and recording the sentinel in the
        ``cursorImagePath`` parameter.

        .. note::
            Camtasia does not natively support per-keyframe cursor image
            changes. This method sets the clip-level ``cursorImagePath``
            to ``'no_cursor'`` and adds a positional keyframe as a marker.

        Args:
            time_seconds: Time at which to hide the cursor.
        """
        self.cursor_image_path = 'no_cursor'
        self.add_cursor_point(time_seconds, 0, 0)

    # -- Cursor replacement / import --

    _VALID_CURSOR_EXTENSIONS = frozenset({'.bmp', '.jpeg', '.jpg', '.png', '.tif', '.tiff'})

    def replace_cursor(self, path: str, scope: str = 'current') -> Self:
        """Replace the cursor image for this clip.

        Args:
            path: Path or identifier for the replacement cursor image.
            scope: Replacement scope — ``'current'`` replaces only this
                clip's cursor, ``'similar'`` or ``'all'`` also writes
                ``metadata.cursorReplaceScope``.

        Returns:
            ``self`` for chaining.

        Raises:
            ValueError: If *scope* is not one of the accepted values.
        """
        valid_scopes = {'current', 'similar', 'all'}
        if scope not in valid_scopes:
            raise ValueError(f"scope must be one of {valid_scopes!r}, got {scope!r}")
        self.cursor_image_path = path
        if scope != 'current':
            self._data.setdefault('metadata', {})['cursorReplaceScope'] = scope
        return self

    def import_custom_cursor(self, image_path: str) -> Self:
        """Import a custom cursor image after validating its extension.

        Supported formats: BMP, JPEG, PNG, TIF.

        Args:
            image_path: Filesystem path to the cursor image.

        Returns:
            ``self`` for chaining.

        Raises:
            ValueError: If the file extension is not supported.
        """
        import os
        _, ext = os.path.splitext(image_path)
        if ext.lower() not in self._VALID_CURSOR_EXTENSIONS:
            raise ValueError(
                f"Unsupported cursor image extension {ext!r}; "
                f"expected one of {sorted(self._VALID_CURSOR_EXTENSIONS)}"
            )
        return self.replace_cursor(image_path)

    def unpack_rev_media(self) -> bool:
        """Check if this clip references a Rev-packed source and flag for unpacking.

        Inspects the clip's source reference for ``.trec`` indicators. If
        found, sets ``metadata.needsUnpack`` to ``True``.

        Returns:
            ``True`` if the clip was flagged for unpacking, ``False`` otherwise.
        """
        src = self._data.get('src')
        src_str = str(src) if src is not None else ''
        needs = '.trec' in src_str
        if not needs:
            # Also check metadata for rev-packed indicators
            meta = self._data.get('metadata', {})
            needs = bool(meta.get('revPacked'))
        if needs:
            self._data.setdefault('metadata', {})['needsUnpack'] = True
        return needs

    def extend_cursor_path(self, time_seconds: float) -> None:
        """Extend cursor keyframes to reach the given time.

        If the last keyframe ends before *time_seconds*, a new keyframe
        is appended at *time_seconds* copying the last known cursor
        position.

        Args:
            time_seconds: Target end time in seconds.
        """
        from camtasia.timing import seconds_to_ticks
        target_ticks = seconds_to_ticks(time_seconds)
        kfs = self._get_cursor_kfs()
        if not kfs:
            return
        last = kfs[-1]
        if last['time'] >= target_ticks:
            return
        new_kf: dict[str, Any] = {
            'endTime': target_ticks,
            'time': target_ticks,
            'value': list(last['value']),
            'duration': 0,
        }
        kfs.append(new_kf)
        self._recompute_cursor_durations(kfs)

    def set_cursor_type(self, cursor_type: CursorType) -> Self:
        """Set the cursor to a predefined type via sentinel path.

        Args:
            cursor_type: A :class:`CursorType` enum member.

        Returns:
            ``self`` for chaining.
        """
        self.cursor_image_path = cursor_type.value
        return self

    # -- Internal helpers --

    def _get_cursor_kfs(self) -> list[dict[str, Any]]:
        """Return the mutable keyframes list for cursorLocation."""
        params = self._data.get('parameters', {})
        loc = params.get('cursorLocation', {})
        kfs: list[dict[str, Any]] = loc.get('keyframes', [])
        return kfs

    @staticmethod
    def _recompute_cursor_durations(kfs: list[dict[str, Any]]) -> None:
        """Recompute ``duration`` and ``endTime`` for each keyframe."""
        for i in range(len(kfs)):
            if i + 1 < len(kfs):
                kfs[i]['duration'] = kfs[i + 1]['time'] - kfs[i]['time']
                kfs[i]['endTime'] = kfs[i + 1]['time']
            else:
                kfs[i]['duration'] = 0
                kfs[i]['endTime'] = kfs[i]['time']
