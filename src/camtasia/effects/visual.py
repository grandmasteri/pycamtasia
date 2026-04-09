"""Visual effects: RoundCorners, DropShadow."""
from __future__ import annotations

from typing import Any

from camtasia.effects.base import Effect, register_effect


@register_effect("RoundCorners")
class RoundCorners(Effect):
    """Round corners effect.

    Parameters:
        radius, topLeft, topRight, bottomLeft, bottomRight
    """

    @property
    def radius(self) -> float:
        return self.get_parameter("radius")

    @radius.setter
    def radius(self, value: float) -> None:
        self.set_parameter("radius", value)

    @property
    def top_left(self) -> bool:
        return self.get_parameter("topLeft")

    @top_left.setter
    def top_left(self, value: bool) -> None:
        self.set_parameter("topLeft", value)

    @property
    def top_right(self) -> bool:
        return self.get_parameter("topRight")

    @top_right.setter
    def top_right(self, value: bool) -> None:
        self.set_parameter("topRight", value)

    @property
    def bottom_left(self) -> bool:
        return self.get_parameter("bottomLeft")

    @bottom_left.setter
    def bottom_left(self, value: bool) -> None:
        self.set_parameter("bottomLeft", value)

    @property
    def bottom_right(self) -> bool:
        return self.get_parameter("bottomRight")

    @bottom_right.setter
    def bottom_right(self, value: bool) -> None:
        self.set_parameter("bottomRight", value)


def _color_rgba(params: dict[str, Any], prefix: str) -> tuple[float, float, float, float]:
    """Read RGBA color from separate parameter keys."""
    return (
        params[f"{prefix}-red"]["defaultValue"],
        params[f"{prefix}-green"]["defaultValue"],
        params[f"{prefix}-blue"]["defaultValue"],
        params[f"{prefix}-alpha"]["defaultValue"],
    )


def _set_color_rgba(
    params: dict[str, Any], prefix: str, rgba: tuple[float, float, float, float]
) -> None:
    """Write RGBA color to separate parameter keys."""
    params[f"{prefix}-red"]["defaultValue"] = rgba[0]
    params[f"{prefix}-green"]["defaultValue"] = rgba[1]
    params[f"{prefix}-blue"]["defaultValue"] = rgba[2]
    params[f"{prefix}-alpha"]["defaultValue"] = rgba[3]


@register_effect("DropShadow")
class DropShadow(Effect):
    """Drop shadow effect.

    Parameters:
        angle, offset, blur, opacity, color (RGBA via separate keys).
    """

    @property
    def angle(self) -> float:
        return self.get_parameter("angle")

    @angle.setter
    def angle(self, value: float) -> None:
        self.set_parameter("angle", value)

    @property
    def offset(self) -> float:
        return self.get_parameter("offset")

    @offset.setter
    def offset(self, value: float) -> None:
        self.set_parameter("offset", value)

    @property
    def blur(self) -> float:
        return self.get_parameter("blur")

    @blur.setter
    def blur(self, value: float) -> None:
        self.set_parameter("blur", value)

    @property
    def opacity(self) -> float:
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
