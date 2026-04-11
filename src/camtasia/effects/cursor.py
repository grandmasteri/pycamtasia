"""Cursor effects: CursorMotionBlur, CursorShadow, CursorPhysics, LeftClickScaling."""
from __future__ import annotations

from camtasia.effects.base import Effect, register_effect
from camtasia.effects.visual import _color_rgba, _set_color_rgba


@register_effect("CursorMotionBlur")
class CursorMotionBlur(Effect):
    """Cursor motion blur effect.

    Parameters:
        intensity
    """

    @property
    def intensity(self) -> float:
        """Blur intensity level."""
        return self.get_parameter("intensity")

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
    def angle(self) -> float:
        """Shadow angle in degrees."""
        return self.get_parameter("angle")

    @angle.setter
    def angle(self, value: float) -> None:
        self.set_parameter("angle", value)

    @property
    def offset(self) -> float:
        """Shadow offset distance in pixels."""
        return self.get_parameter("offset")

    @offset.setter
    def offset(self, value: float) -> None:
        self.set_parameter("offset", value)

    @property
    def blur(self) -> float:
        """Shadow blur radius."""
        return self.get_parameter("blur")

    @blur.setter
    def blur(self, value: float) -> None:
        self.set_parameter("blur", value)

    @property
    def opacity(self) -> float:
        """Shadow opacity from 0.0 (transparent) to 1.0 (opaque)."""
        return self.get_parameter("opacity")

    @opacity.setter
    def opacity(self, value: float) -> None:
        self.set_parameter("opacity", value)

    @property
    def color(self) -> tuple[float, float, float, float]:
        """RGBA color as ``(red, green, blue, alpha)`` floats."""
        return _color_rgba(self.parameters, "color")

    @color.setter
    def color(self, rgba: tuple[float, float, float, float]) -> None:
        _set_color_rgba(self.parameters, "color", rgba)


@register_effect("CursorPhysics")
class CursorPhysics(Effect):
    """Cursor physics effect.

    Parameters:
        intensity, tilt
    """

    @property
    def intensity(self) -> float:
        """Physics effect intensity."""
        return self.get_parameter("intensity")

    @intensity.setter
    def intensity(self, value: float) -> None:
        self.set_parameter("intensity", value)

    @property
    def tilt(self) -> float:
        """Cursor tilt amount."""
        return self.get_parameter("tilt")

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
        return self.get_parameter("scale")

    @scale.setter
    def scale(self, value: float) -> None:
        self.set_parameter("scale", value)

    @property
    def speed(self) -> float:
        """Scaling animation speed."""
        return self.get_parameter("speed")

    @speed.setter
    def speed(self, value: float) -> None:
        self.set_parameter("speed", value)
