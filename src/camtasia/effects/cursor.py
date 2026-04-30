"""Cursor effects: general cursor effects and click effects.

.. warning:: Unverified fixture
   The parameter names and default values in these classes are based on
   Camtasia's internal naming conventions observed in other cursor effects.
   They have NOT been verified against real Camtasia project files containing
   these specific effects. Always validate output in Camtasia before relying
   on these classes in production.
"""
from __future__ import annotations

from camtasia.effects.base import Effect, register_effect
from camtasia.effects.visual import _color_rgba, _set_color_rgba

# =====================================================================
# Existing cursor effects
# =====================================================================

@register_effect("CursorMotionBlur")
class CursorMotionBlur(Effect):
    """Cursor motion blur effect.

    Parameters:
        intensity
    """

    @property
    def intensity(self) -> float:
        """Blur intensity level."""
        return float(self.get_parameter("intensity"))

    @intensity.setter
    def intensity(self, value: float) -> None:
        self.set_parameter("intensity", value)


@register_effect("CursorShadow")
class CursorShadow(Effect):
    """Cursor shadow effect.

    Parameters:
        angle, offset, blur, opacity, color (RGBA).
    """

    @property
    def enabled(self) -> int:  # type: ignore[no-any-return]
        """Whether the effect is on (1) or off (0) at the default keyframe.

        Note: Setting this only updates the parameter's default value;
        existing keyframes on the ``enabled`` parameter are not
        modified. See ``DropShadow.enabled`` for the same caveat.
        """
        return int(self.get_parameter('enabled'))  # type: ignore[no-any-return]

    @enabled.setter
    def enabled(self, value: int) -> None:
        self.set_parameter('enabled', value)

    @property
    def angle(self) -> float:
        """Shadow angle in radians."""
        return float(self.get_parameter("angle"))

    @angle.setter
    def angle(self, value: float) -> None:
        self.set_parameter("angle", value)

    @property
    def offset(self) -> float:
        """Shadow offset distance in pixels."""
        return float(self.get_parameter("offset"))

    @offset.setter
    def offset(self, value: float) -> None:
        self.set_parameter("offset", value)

    @property
    def blur(self) -> float:
        """Shadow blur radius."""
        return float(self.get_parameter("blur"))

    @blur.setter
    def blur(self, value: float) -> None:
        self.set_parameter("blur", value)

    @property
    def opacity(self) -> float:
        """Shadow opacity from 0.0 (transparent) to 1.0 (opaque)."""
        return float(self.get_parameter("opacity"))

    @opacity.setter
    def opacity(self, value: float) -> None:
        self.set_parameter("opacity", value)

    @property
    def color(self) -> tuple[float, float, float, float]:
        """RGBA color as ``(red, green, blue, alpha)`` floats."""
        return _color_rgba(self.parameters, "color")

    @color.setter
    def color(self, rgba: tuple[float, float, float, float]) -> None:
        _set_color_rgba(self._data.setdefault('parameters', {}), "color", rgba)


@register_effect("CursorPhysics")
class CursorPhysics(Effect):
    """Cursor physics effect.

    Parameters:
        intensity, tilt
    """

    @property
    def intensity(self) -> float:
        """Physics effect intensity."""
        return float(self.get_parameter("intensity"))

    @intensity.setter
    def intensity(self, value: float) -> None:
        self.set_parameter("intensity", value)

    @property
    def tilt(self) -> float:
        """Cursor tilt amount."""
        return float(self.get_parameter("tilt"))

    @tilt.setter
    def tilt(self, value: float) -> None:
        self.set_parameter("tilt", value)


@register_effect("LeftClickScaling")
class LeftClickScaling(Effect):
    """Left-click cursor scaling effect.

    Parameters:
        scale, speed
    """

    @property
    def scale(self) -> float:
        """Click scale factor."""
        return float(self.get_parameter("scale"))

    @scale.setter
    def scale(self, value: float) -> None:
        self.set_parameter("scale", value)

    @property
    def speed(self) -> float:
        """Scaling animation speed."""
        return float(self.get_parameter("speed"))

    @speed.setter
    def speed(self, value: float) -> None:
        self.set_parameter("speed", value)


# =====================================================================
# New general cursor effects
# =====================================================================

@register_effect("CursorColor")
class CursorColor(Effect):
    """Cursor color overlay effect.

    .. warning:: Unverified fixture — parameter names inferred from convention.

    Parameters:
        fillColor (RGBA), outlineColor (RGBA)
    """

    @property
    def fill_color(self) -> tuple[float, float, float, float]:
        """Fill RGBA color."""
        return _color_rgba(self.parameters, "fillColor")

    @fill_color.setter
    def fill_color(self, rgba: tuple[float, float, float, float]) -> None:
        _set_color_rgba(self._data.setdefault('parameters', {}), "fillColor", rgba)

    @property
    def outline_color(self) -> tuple[float, float, float, float]:
        """Outline RGBA color."""
        return _color_rgba(self.parameters, "outlineColor")

    @outline_color.setter
    def outline_color(self, rgba: tuple[float, float, float, float]) -> None:
        _set_color_rgba(self._data.setdefault('parameters', {}), "outlineColor", rgba)


@register_effect("CursorGlow")
class CursorGlow(Effect):
    """Cursor glow effect.

    .. warning:: Unverified fixture — parameter names inferred from convention.

    Parameters:
        color (RGBA), opacity, radius
    """

    @property
    def color(self) -> tuple[float, float, float, float]:
        """Glow RGBA color."""
        return _color_rgba(self.parameters, "color")

    @color.setter
    def color(self, rgba: tuple[float, float, float, float]) -> None:
        _set_color_rgba(self._data.setdefault('parameters', {}), "color", rgba)

    @property
    def opacity(self) -> float:
        """Glow opacity."""
        return float(self.get_parameter("opacity"))

    @opacity.setter
    def opacity(self, value: float) -> None:
        self.set_parameter("opacity", value)

    @property
    def radius(self) -> float:
        """Glow radius in pixels."""
        return float(self.get_parameter("radius"))

    @radius.setter
    def radius(self, value: float) -> None:
        self.set_parameter("radius", value)


@register_effect("CursorHighlight")
class CursorHighlight(Effect):
    """Cursor highlight effect.

    .. warning:: Unverified fixture — parameter names inferred from convention.

    Parameters:
        size, color (RGBA), opacity
    """

    @property
    def size(self) -> float:
        """Highlight size in pixels."""
        return float(self.get_parameter("size"))

    @size.setter
    def size(self, value: float) -> None:
        self.set_parameter("size", value)

    @property
    def color(self) -> tuple[float, float, float, float]:
        """Highlight RGBA color."""
        return _color_rgba(self.parameters, "color")

    @color.setter
    def color(self, rgba: tuple[float, float, float, float]) -> None:
        _set_color_rgba(self._data.setdefault('parameters', {}), "color", rgba)

    @property
    def opacity(self) -> float:
        """Highlight opacity."""
        return float(self.get_parameter("opacity"))

    @opacity.setter
    def opacity(self, value: float) -> None:
        self.set_parameter("opacity", value)


@register_effect("CursorIsolation")
class CursorIsolation(Effect):
    """Cursor isolation (dim-around) effect.

    .. warning:: Unverified fixture — parameter names inferred from convention.

    Parameters:
        size, feather
    """

    @property
    def size(self) -> float:
        """Isolation region size."""
        return float(self.get_parameter("size"))

    @size.setter
    def size(self, value: float) -> None:
        self.set_parameter("size", value)

    @property
    def feather(self) -> float:
        """Edge feather amount."""
        return float(self.get_parameter("feather"))

    @feather.setter
    def feather(self, value: float) -> None:
        self.set_parameter("feather", value)


@register_effect("CursorMagnify")
class CursorMagnify(Effect):
    """Cursor magnification effect.

    .. warning:: Unverified fixture — parameter names inferred from convention.

    Parameters:
        scale, size
    """

    @property
    def scale(self) -> float:
        """Magnification scale factor."""
        return float(self.get_parameter("scale"))

    @scale.setter
    def scale(self, value: float) -> None:
        self.set_parameter("scale", value)

    @property
    def size(self) -> float:
        """Magnification region size."""
        return float(self.get_parameter("size"))

    @size.setter
    def size(self, value: float) -> None:
        self.set_parameter("size", value)


@register_effect("CursorSpotlight")
class CursorSpotlight(Effect):
    """Cursor spotlight effect.

    .. warning:: Unverified fixture — parameter names inferred from convention.

    Parameters:
        size, opacity, blur, color (RGBA)
    """

    @property
    def size(self) -> float:
        """Spotlight size."""
        return float(self.get_parameter("size"))

    @size.setter
    def size(self, value: float) -> None:
        self.set_parameter("size", value)

    @property
    def opacity(self) -> float:
        """Spotlight opacity."""
        return float(self.get_parameter("opacity"))

    @opacity.setter
    def opacity(self, value: float) -> None:
        self.set_parameter("opacity", value)

    @property
    def blur(self) -> float:
        """Spotlight blur radius."""
        return float(self.get_parameter("blur"))

    @blur.setter
    def blur(self, value: float) -> None:
        self.set_parameter("blur", value)

    @property
    def color(self) -> tuple[float, float, float, float]:
        """Spotlight RGBA color."""
        return _color_rgba(self.parameters, "color")

    @color.setter
    def color(self, rgba: tuple[float, float, float, float]) -> None:
        _set_color_rgba(self._data.setdefault('parameters', {}), "color", rgba)


@register_effect("CursorGradient")
class CursorGradient(Effect):
    """Cursor gradient overlay effect.

    .. warning:: Unverified fixture — parameter names inferred from convention.

    Parameters:
        color (RGBA), size, opacity
    """

    @property
    def color(self) -> tuple[float, float, float, float]:
        """Gradient RGBA color."""
        return _color_rgba(self.parameters, "color")

    @color.setter
    def color(self, rgba: tuple[float, float, float, float]) -> None:
        _set_color_rgba(self._data.setdefault('parameters', {}), "color", rgba)

    @property
    def size(self) -> float:
        """Gradient size."""
        return float(self.get_parameter("size"))

    @size.setter
    def size(self, value: float) -> None:
        self.set_parameter("size", value)

    @property
    def opacity(self) -> float:
        """Gradient opacity."""
        return float(self.get_parameter("opacity"))

    @opacity.setter
    def opacity(self, value: float) -> None:
        self.set_parameter("opacity", value)


@register_effect("CursorLens")
class CursorLens(Effect):
    """Cursor lens distortion effect.

    .. warning:: Unverified fixture — parameter names inferred from convention.

    Parameters:
        scale, size
    """

    @property
    def scale(self) -> float:
        """Lens distortion scale."""
        return float(self.get_parameter("scale"))

    @scale.setter
    def scale(self, value: float) -> None:
        self.set_parameter("scale", value)

    @property
    def size(self) -> float:
        """Lens region size."""
        return float(self.get_parameter("size"))

    @size.setter
    def size(self, value: float) -> None:
        self.set_parameter("size", value)


@register_effect("CursorNegative")
class CursorNegative(Effect):
    """Cursor negative (invert) effect.

    .. warning:: Unverified fixture — parameter names inferred from convention.

    Parameters:
        size, feather
    """

    @property
    def size(self) -> float:
        """Negative region size."""
        return float(self.get_parameter("size"))

    @size.setter
    def size(self, value: float) -> None:
        self.set_parameter("size", value)

    @property
    def feather(self) -> float:
        """Edge feather amount."""
        return float(self.get_parameter("feather"))

    @feather.setter
    def feather(self, value: float) -> None:
        self.set_parameter("feather", value)


@register_effect("CursorSmoothing")
class CursorSmoothing(Effect):
    """Cursor motion smoothing effect.

    .. warning:: Unverified fixture — parameter names inferred from convention.

    Parameters:
        level
    """

    @property
    def level(self) -> float:
        """Smoothing level."""
        return float(self.get_parameter("level"))

    @level.setter
    def level(self, value: float) -> None:
        self.set_parameter("level", value)


# =====================================================================
# Click effects — Left and Right variants
# =====================================================================

def _click_burst_class(name: str) -> type[Effect]:
    """Factory for ClickBurst effect classes (color, size, opacity, duration).

    .. warning:: Unverified fixture — parameter names inferred from convention.
    """
    class _ClickBurst(Effect):
        __doc__ = f"""{name} click burst effect.

        .. warning:: Unverified fixture — parameter names inferred from convention.

        Parameters:
            color (RGBA), size, opacity, duration
        """

        @property
        def color(self) -> tuple[float, float, float, float]:
            """Burst RGBA color."""
            return _color_rgba(self.parameters, "color")

        @color.setter
        def color(self, rgba: tuple[float, float, float, float]) -> None:
            _set_color_rgba(self._data.setdefault('parameters', {}), "color", rgba)

        @property
        def size(self) -> float:
            """Burst size."""
            return float(self.get_parameter("size"))

        @size.setter
        def size(self, value: float) -> None:
            self.set_parameter("size", value)

        @property
        def opacity(self) -> float:
            """Burst opacity."""
            return float(self.get_parameter("opacity"))

        @opacity.setter
        def opacity(self, value: float) -> None:
            self.set_parameter("opacity", value)

        @property
        def duration(self) -> float:
            """Burst duration in seconds."""
            return float(self.get_parameter("duration"))

        @duration.setter
        def duration(self, value: float) -> None:
            self.set_parameter("duration", value)

    _ClickBurst.__name__ = name
    _ClickBurst.__qualname__ = name
    return _ClickBurst


# Burst 1-4, Left and Right
LeftClickBurst1 = register_effect("LeftClickBurst1")(_click_burst_class("LeftClickBurst1"))
LeftClickBurst2 = register_effect("LeftClickBurst2")(_click_burst_class("LeftClickBurst2"))
LeftClickBurst3 = register_effect("LeftClickBurst3")(_click_burst_class("LeftClickBurst3"))
LeftClickBurst4 = register_effect("LeftClickBurst4")(_click_burst_class("LeftClickBurst4"))
RightClickBurst1 = register_effect("RightClickBurst1")(_click_burst_class("RightClickBurst1"))
RightClickBurst2 = register_effect("RightClickBurst2")(_click_burst_class("RightClickBurst2"))
RightClickBurst3 = register_effect("RightClickBurst3")(_click_burst_class("RightClickBurst3"))
RightClickBurst4 = register_effect("RightClickBurst4")(_click_burst_class("RightClickBurst4"))


def _click_zoom_class(name: str) -> type[Effect]:
    """Factory for ClickZoom effect classes (scale, size, duration).

    .. warning:: Unverified fixture — parameter names inferred from convention.
    """
    class _ClickZoom(Effect):
        __doc__ = f"""{name} click zoom effect.

        .. warning:: Unverified fixture — parameter names inferred from convention.

        Parameters:
            scale, size, duration
        """

        @property
        def scale(self) -> float:
            """Zoom scale factor."""
            return float(self.get_parameter("scale"))

        @scale.setter
        def scale(self, value: float) -> None:
            self.set_parameter("scale", value)

        @property
        def size(self) -> float:
            """Zoom region size."""
            return float(self.get_parameter("size"))

        @size.setter
        def size(self, value: float) -> None:
            self.set_parameter("size", value)

        @property
        def duration(self) -> float:
            """Zoom duration in seconds."""
            return float(self.get_parameter("duration"))

        @duration.setter
        def duration(self, value: float) -> None:
            self.set_parameter("duration", value)

    _ClickZoom.__name__ = name
    _ClickZoom.__qualname__ = name
    return _ClickZoom


LeftClickZoom = register_effect("LeftClickZoom")(_click_zoom_class("LeftClickZoom"))
RightClickZoom = register_effect("RightClickZoom")(_click_zoom_class("RightClickZoom"))


def _click_rings_class(name: str) -> type[Effect]:
    """Factory for ClickRings effect classes (color, size, opacity, duration).

    .. warning:: Unverified fixture — parameter names inferred from convention.
    """
    class _ClickRings(Effect):
        __doc__ = f"""{name} click rings effect.

        .. warning:: Unverified fixture — parameter names inferred from convention.

        Parameters:
            color (RGBA), size, opacity, duration
        """

        @property
        def color(self) -> tuple[float, float, float, float]:
            """Rings RGBA color."""
            return _color_rgba(self.parameters, "color")

        @color.setter
        def color(self, rgba: tuple[float, float, float, float]) -> None:
            _set_color_rgba(self._data.setdefault('parameters', {}), "color", rgba)

        @property
        def size(self) -> float:
            """Rings size."""
            return float(self.get_parameter("size"))

        @size.setter
        def size(self, value: float) -> None:
            self.set_parameter("size", value)

        @property
        def opacity(self) -> float:
            """Rings opacity."""
            return float(self.get_parameter("opacity"))

        @opacity.setter
        def opacity(self, value: float) -> None:
            self.set_parameter("opacity", value)

        @property
        def duration(self) -> float:
            """Rings duration in seconds."""
            return float(self.get_parameter("duration"))

        @duration.setter
        def duration(self, value: float) -> None:
            self.set_parameter("duration", value)

    _ClickRings.__name__ = name
    _ClickRings.__qualname__ = name
    return _ClickRings


LeftClickRings = register_effect("LeftClickRings")(_click_rings_class("LeftClickRings"))
RightClickRings = register_effect("RightClickRings")(_click_rings_class("RightClickRings"))


def _click_ripple_class(name: str) -> type[Effect]:
    """Factory for ClickRipple effect classes (size, opacity, duration).

    .. warning:: Unverified fixture — parameter names inferred from convention.
    """
    class _ClickRipple(Effect):
        __doc__ = f"""{name} click ripple effect.

        .. warning:: Unverified fixture — parameter names inferred from convention.

        Parameters:
            size, opacity, duration
        """

        @property
        def size(self) -> float:
            """Ripple size."""
            return float(self.get_parameter("size"))

        @size.setter
        def size(self, value: float) -> None:
            self.set_parameter("size", value)

        @property
        def opacity(self) -> float:
            """Ripple opacity."""
            return float(self.get_parameter("opacity"))

        @opacity.setter
        def opacity(self, value: float) -> None:
            self.set_parameter("opacity", value)

        @property
        def duration(self) -> float:
            """Ripple duration in seconds."""
            return float(self.get_parameter("duration"))

        @duration.setter
        def duration(self, value: float) -> None:
            self.set_parameter("duration", value)

    _ClickRipple.__name__ = name
    _ClickRipple.__qualname__ = name
    return _ClickRipple


LeftClickRipple = register_effect("LeftClickRipple")(_click_ripple_class("LeftClickRipple"))
RightClickRipple = register_effect("RightClickRipple")(_click_ripple_class("RightClickRipple"))


def _click_scope_class(name: str) -> type[Effect]:
    """Factory for ClickScope effect classes (color, size, opacity).

    .. warning:: Unverified fixture — parameter names inferred from convention.
    """
    class _ClickScope(Effect):
        __doc__ = f"""{name} click scope effect.

        .. warning:: Unverified fixture — parameter names inferred from convention.

        Parameters:
            color (RGBA), size, opacity
        """

        @property
        def color(self) -> tuple[float, float, float, float]:
            """Scope RGBA color."""
            return _color_rgba(self.parameters, "color")

        @color.setter
        def color(self, rgba: tuple[float, float, float, float]) -> None:
            _set_color_rgba(self._data.setdefault('parameters', {}), "color", rgba)

        @property
        def size(self) -> float:
            """Scope size."""
            return float(self.get_parameter("size"))

        @size.setter
        def size(self, value: float) -> None:
            self.set_parameter("size", value)

        @property
        def opacity(self) -> float:
            """Scope opacity."""
            return float(self.get_parameter("opacity"))

        @opacity.setter
        def opacity(self, value: float) -> None:
            self.set_parameter("opacity", value)

    _ClickScope.__name__ = name
    _ClickScope.__qualname__ = name
    return _ClickScope


LeftClickScope = register_effect("LeftClickScope")(_click_scope_class("LeftClickScope"))
RightClickScope = register_effect("RightClickScope")(_click_scope_class("RightClickScope"))


def _click_target_class(name: str) -> type[Effect]:
    """Factory for ClickTarget effect classes (color, size, opacity).

    .. warning:: Unverified fixture — parameter names inferred from convention.
    """
    class _ClickTarget(Effect):
        __doc__ = f"""{name} click target effect.

        .. warning:: Unverified fixture — parameter names inferred from convention.

        Parameters:
            color (RGBA), size, opacity
        """

        @property
        def color(self) -> tuple[float, float, float, float]:
            """Target RGBA color."""
            return _color_rgba(self.parameters, "color")

        @color.setter
        def color(self, rgba: tuple[float, float, float, float]) -> None:
            _set_color_rgba(self._data.setdefault('parameters', {}), "color", rgba)

        @property
        def size(self) -> float:
            """Target size."""
            return float(self.get_parameter("size"))

        @size.setter
        def size(self, value: float) -> None:
            self.set_parameter("size", value)

        @property
        def opacity(self) -> float:
            """Target opacity."""
            return float(self.get_parameter("opacity"))

        @opacity.setter
        def opacity(self, value: float) -> None:
            self.set_parameter("opacity", value)

    _ClickTarget.__name__ = name
    _ClickTarget.__qualname__ = name
    return _ClickTarget


LeftClickTarget = register_effect("LeftClickTarget")(_click_target_class("LeftClickTarget"))
RightClickTarget = register_effect("RightClickTarget")(_click_target_class("RightClickTarget"))


def _click_warp_class(name: str) -> type[Effect]:
    """Factory for ClickWarp effect classes (intensity, size, duration).

    .. warning:: Unverified fixture — parameter names inferred from convention.
    """
    class _ClickWarp(Effect):
        __doc__ = f"""{name} click warp effect.

        .. warning:: Unverified fixture — parameter names inferred from convention.

        Parameters:
            intensity, size, duration
        """

        @property
        def intensity(self) -> float:
            """Warp intensity."""
            return float(self.get_parameter("intensity"))

        @intensity.setter
        def intensity(self, value: float) -> None:
            self.set_parameter("intensity", value)

        @property
        def size(self) -> float:
            """Warp size."""
            return float(self.get_parameter("size"))

        @size.setter
        def size(self, value: float) -> None:
            self.set_parameter("size", value)

        @property
        def duration(self) -> float:
            """Warp duration in seconds."""
            return float(self.get_parameter("duration"))

        @duration.setter
        def duration(self, value: float) -> None:
            self.set_parameter("duration", value)

    _ClickWarp.__name__ = name
    _ClickWarp.__qualname__ = name
    return _ClickWarp


LeftClickWarp = register_effect("LeftClickWarp")(_click_warp_class("LeftClickWarp"))
RightClickWarp = register_effect("RightClickWarp")(_click_warp_class("RightClickWarp"))


def _click_sound_class(name: str) -> type[Effect]:
    """Factory for ClickSound effect classes (volume, soundId).

    .. warning:: Unverified fixture — parameter names inferred from convention.
    """
    class _ClickSound(Effect):
        __doc__ = f"""{name} click sound effect.

        .. warning:: Unverified fixture — parameter names inferred from convention.

        Parameters:
            volume, soundId
        """

        @property
        def volume(self) -> float:
            """Sound volume."""
            return float(self.get_parameter("volume"))

        @volume.setter
        def volume(self, value: float) -> None:
            self.set_parameter("volume", value)

        @property
        def sound_id(self) -> str:
            """Sound identifier."""
            return str(self.get_parameter("soundId"))

        @sound_id.setter
        def sound_id(self, value: str) -> None:
            self.set_parameter("soundId", value)

    _ClickSound.__name__ = name
    _ClickSound.__qualname__ = name
    return _ClickSound


LeftClickSound = register_effect("LeftClickSound")(_click_sound_class("LeftClickSound"))
RightClickSound = register_effect("RightClickSound")(_click_sound_class("RightClickSound"))


@register_effect("CursorPathCreator")
class CursorPathCreator(Effect):
    """Cursor path creator effect — defines a synthetic cursor path via keyframes.

    .. warning:: Unverified fixture — parameter names inferred from convention.

    Use :meth:`add_point` to build a cursor path from scratch, then attach
    the effect to any clip via :meth:`BaseClip.add_cursor_path_creator`.

    Parameters:
        cursorPath (point array stored as keyframes)
    """

    @property
    def keyframes(self) -> list[dict[str, float]]:
        """Return the cursor path as a list of ``{time, x, y}`` dicts.

        Times are in seconds; coordinates are canvas pixels.
        """
        from camtasia.timing import ticks_to_seconds
        path = self.parameters.get('cursorPath', {})
        result: list[dict[str, float]] = []
        for kf in path.get('keyframes', []):
            val = kf.get('value', [0, 0, 0])
            result.append({
                'time': ticks_to_seconds(kf['time']),
                'x': float(val[0]),
                'y': float(val[1]),
            })
        return result

    def add_point(self, time_seconds: float, x: float, y: float) -> None:
        """Append a cursor position keyframe.

        Args:
            time_seconds: Time in seconds.
            x: Cursor X coordinate.
            y: Cursor Y coordinate.
        """
        from camtasia.timing import seconds_to_ticks
        ticks = seconds_to_ticks(time_seconds)
        params = self._data.setdefault('parameters', {})
        path = params.setdefault('cursorPath', {
            'type': 'point', 'defaultValue': [0, 0, 0], 'keyframes': [],
        })
        kfs: list[dict] = path.setdefault('keyframes', [])
        new_kf = {
            'endTime': ticks, 'time': ticks,
            'value': [x, y, 0], 'duration': 0,
        }
        # Insert in sorted order
        idx = 0
        for i, kf in enumerate(kfs):
            if kf['time'] > ticks:
                break
            idx = i + 1
        kfs.insert(idx, new_kf)
        # Recompute durations
        for i in range(len(kfs)):
            if i + 1 < len(kfs):
                kfs[i]['duration'] = kfs[i + 1]['time'] - kfs[i]['time']
                kfs[i]['endTime'] = kfs[i + 1]['time']
            else:
                kfs[i]['duration'] = 0
                kfs[i]['endTime'] = kfs[i]['time']

    def clear_points(self) -> None:
        """Remove all cursor path keyframes."""
        path = self._data.get('parameters', {}).get('cursorPath', {})
        if 'keyframes' in path:
            path['keyframes'] = []


@register_effect("RightClickScaling")
class RightClickScaling(Effect):
    """Right-click cursor scaling effect (mirror of LeftClickScaling).

    .. warning:: Unverified fixture — parameter names inferred from convention.

    Parameters:
        scale, speed
    """

    @property
    def scale(self) -> float:
        """Click scale factor."""
        return float(self.get_parameter("scale"))

    @scale.setter
    def scale(self, value: float) -> None:
        self.set_parameter("scale", value)

    @property
    def speed(self) -> float:
        """Scaling animation speed."""
        return float(self.get_parameter("speed"))

    @speed.setter
    def speed(self, value: float) -> None:
        self.set_parameter("speed", value)
