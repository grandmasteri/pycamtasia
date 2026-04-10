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


@register_effect("MotionBlur")
class MotionBlur(Effect):
    """Motion blur effect.

    Parameters:
        intensity
    """

    @property
    def intensity(self) -> float:
        return self.get_parameter("intensity")

    @intensity.setter
    def intensity(self, value: float) -> None:
        self.set_parameter("intensity", value)


@register_effect("Mask")
class Mask(Effect):
    """Mask effect.

    Parameters:
        mask_shape, mask_opacity, mask_blend, mask_invert, mask_rotation,
        mask_width, mask_height, mask_position_x, mask_position_y.

    Width, height, and position parameters may be keyframed (dict with
    ``keyframes`` array) or simple scalar values.
    """

    @property
    def mask_shape(self) -> int:
        return self.get_parameter("mask_shape")

    @mask_shape.setter
    def mask_shape(self, value: int) -> None:
        self.set_parameter("mask_shape", value)

    @property
    def mask_opacity(self) -> float:
        return self.get_parameter("mask_opacity")

    @mask_opacity.setter
    def mask_opacity(self, value: float) -> None:
        self.set_parameter("mask_opacity", value)

    @property
    def mask_blend(self) -> float:
        return self.get_parameter("mask_blend")

    @mask_blend.setter
    def mask_blend(self, value: float) -> None:
        self.set_parameter("mask_blend", value)

    @property
    def mask_invert(self) -> int:
        return self.get_parameter("mask_invert")

    @mask_invert.setter
    def mask_invert(self, value: int) -> None:
        self.set_parameter("mask_invert", value)

    @property
    def mask_rotation(self) -> float:
        return self.get_parameter("mask_rotation")

    @mask_rotation.setter
    def mask_rotation(self, value: float) -> None:
        self.set_parameter("mask_rotation", value)

    @property
    def mask_width(self) -> float | dict:
        return self.get_parameter("mask_width")

    @mask_width.setter
    def mask_width(self, value: float | dict) -> None:
        self.set_parameter("mask_width", value)

    @property
    def mask_height(self) -> float | dict:
        return self.get_parameter("mask_height")

    @mask_height.setter
    def mask_height(self, value: float | dict) -> None:
        self.set_parameter("mask_height", value)

    @property
    def mask_position_x(self) -> float | dict:
        return self.get_parameter("mask_positionX")

    @mask_position_x.setter
    def mask_position_x(self, value: float | dict) -> None:
        self.set_parameter("mask_positionX", value)

    @property
    def mask_position_y(self) -> float | dict:
        return self.get_parameter("mask_positionY")

    @mask_position_y.setter
    def mask_position_y(self, value: float | dict) -> None:
        self.set_parameter("mask_positionY", value)


@register_effect("Glow")
class Glow(Effect):
    """Bloom/glow post-processing effect.

    Parameters:
        radius, intensity
    """

    @property
    def radius(self) -> float:
        return self.get_parameter("radius")

    @radius.setter
    def radius(self, value: float) -> None:
        self.set_parameter("radius", value)

    @property
    def intensity(self) -> float:
        return self.get_parameter("intensity")

    @intensity.setter
    def intensity(self, value: float) -> None:
        self.set_parameter("intensity", value)


@register_effect("BlurRegion")
class BlurRegion(Effect):
    """Blur region effect.

    Parameters:
        sigma, mask_corner_radius, mask_invert, color_alpha
    """

    @property
    def sigma(self) -> float:
        return self.get_parameter("sigma")

    @sigma.setter
    def sigma(self, value: float) -> None:
        self.set_parameter("sigma", value)

    @property
    def mask_corner_radius(self) -> float:
        return self.get_parameter("mask_corner_radius")

    @mask_corner_radius.setter
    def mask_corner_radius(self, value: float) -> None:
        self.set_parameter("mask_corner_radius", value)

    @property
    def mask_invert(self) -> int:
        return self.get_parameter("mask_invert")

    @mask_invert.setter
    def mask_invert(self, value: int) -> None:
        self.set_parameter("mask_invert", value)

    @property
    def color_alpha(self) -> float:
        return self.get_parameter("color_alpha")

    @color_alpha.setter
    def color_alpha(self, value: float) -> None:
        self.set_parameter("color_alpha", value)