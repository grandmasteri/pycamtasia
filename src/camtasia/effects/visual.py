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
        """Corner radius in pixels."""
        return self.get_parameter("radius")

    @radius.setter
    def radius(self, value: float) -> None:
        self.set_parameter("radius", value)

    @property
    def top_left(self) -> bool:
        """Whether the top-left corner is rounded."""
        return self.get_parameter("top-left")

    @top_left.setter
    def top_left(self, value: bool) -> None:
        self.set_parameter("top-left", value)

    @property
    def top_right(self) -> bool:
        """Whether the top-right corner is rounded."""
        return self.get_parameter("top-right")

    @top_right.setter
    def top_right(self, value: bool) -> None:
        self.set_parameter("top-right", value)

    @property
    def bottom_left(self) -> bool:
        """Whether the bottom-left corner is rounded."""
        return self.get_parameter("bottom-left")

    @bottom_left.setter
    def bottom_left(self, value: bool) -> None:
        self.set_parameter("bottom-left", value)

    @property
    def bottom_right(self) -> bool:
        """Whether the bottom-right corner is rounded."""
        return self.get_parameter("bottom-right")

    @bottom_right.setter
    def bottom_right(self, value: bool) -> None:
        self.set_parameter("bottom-right", value)


def _color_rgba(params: dict[str, Any], prefix: str) -> tuple[float, float, float, float]:
    """Read RGBA color from separate parameter keys."""
    def _val(key: str) -> float:
        v = params[key]
        return v['defaultValue'] if isinstance(v, dict) else v
    return (_val(f"{prefix}-red"), _val(f"{prefix}-green"),
            _val(f"{prefix}-blue"), _val(f"{prefix}-alpha"))


def _set_color_rgba(
    params: dict[str, Any], prefix: str, rgba: tuple[float, float, float, float]
) -> None:
    """Write RGBA color to separate parameter keys."""
    for suffix, value in zip(("red", "green", "blue", "alpha"), rgba):
        key = f"{prefix}-{suffix}"
        v = params[key]
        if isinstance(v, dict):
            v["defaultValue"] = value
        else:
            params[key] = value


@register_effect("DropShadow")
class DropShadow(Effect):
    """Drop shadow effect.

    Parameters:
        angle, offset, blur, opacity, color (RGBA via separate keys).
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


@register_effect("MotionBlur")
class MotionBlur(Effect):
    """Motion blur effect.

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


@register_effect("Mask")
class Mask(Effect):
    """Mask effect.

    Parameters:
        mask-shape, mask-opacity, mask-blend, mask-invert, mask-rotation,
        mask-width, mask-height, mask-positionX, mask-positionY, mask-cornerRadius.

    Width, height, and position parameters may be keyframed (dict with
    ``keyframes`` array) or simple scalar values.
    """

    @property
    def mask_shape(self) -> int:
        """Mask shape identifier."""
        return self.get_parameter("mask-shape")

    @mask_shape.setter
    def mask_shape(self, value: int) -> None:
        self.set_parameter("mask-shape", value)

    @property
    def mask_opacity(self) -> float:
        """Mask opacity from 0.0 (transparent) to 1.0 (opaque)."""
        return self.get_parameter("mask-opacity")

    @mask_opacity.setter
    def mask_opacity(self, value: float) -> None:
        self.set_parameter("mask-opacity", value)

    @property
    def mask_blend(self) -> float:
        """Mask edge blend (feather) amount."""
        return self.get_parameter("mask-blend")

    @mask_blend.setter
    def mask_blend(self, value: float) -> None:
        self.set_parameter("mask-blend", value)

    @property
    def mask_invert(self) -> int:
        """Whether the mask is inverted (1) or normal (0)."""
        return self.get_parameter("mask-invert")

    @mask_invert.setter
    def mask_invert(self, value: int) -> None:
        self.set_parameter("mask-invert", value)

    @property
    def mask_rotation(self) -> float:
        """Mask rotation angle in degrees."""
        return self.get_parameter("mask-rotation")

    @mask_rotation.setter
    def mask_rotation(self, value: float) -> None:
        self.set_parameter("mask-rotation", value)

    @property
    def mask_width(self) -> float | dict:
        """Mask width, scalar or keyframed dict."""
        return self.get_parameter("mask-width")

    @mask_width.setter
    def mask_width(self, value: float | dict) -> None:
        self.set_parameter("mask-width", value)

    @property
    def mask_height(self) -> float | dict:
        """Mask height, scalar or keyframed dict."""
        return self.get_parameter("mask-height")

    @mask_height.setter
    def mask_height(self, value: float | dict) -> None:
        self.set_parameter("mask-height", value)

    @property
    def mask_position_x(self) -> float | dict:
        """Mask horizontal position, scalar or keyframed dict."""
        return self.get_parameter("mask-positionX")

    @mask_position_x.setter
    def mask_position_x(self, value: float | dict) -> None:
        self.set_parameter("mask-positionX", value)

    @property
    def mask_position_y(self) -> float | dict:
        """Mask vertical position, scalar or keyframed dict."""
        return self.get_parameter("mask-positionY")

    @mask_position_y.setter
    def mask_position_y(self, value: float | dict) -> None:
        self.set_parameter("mask-positionY", value)

    @property
    def mask_corner_radius(self) -> float:
        """Mask corner radius."""
        return self.get_parameter("mask-cornerRadius")

    @mask_corner_radius.setter
    def mask_corner_radius(self, value: float) -> None:
        self.set_parameter("mask-cornerRadius", value)


@register_effect("Glow")
class Glow(Effect):
    """Bloom/glow post-processing effect.

    Parameters:
        radius, intensity
    """

    @property
    def radius(self) -> float:
        """Glow spread radius."""
        return self.get_parameter("radius")

    @radius.setter
    def radius(self, value: float) -> None:
        self.set_parameter("radius", value)

    @property
    def intensity(self) -> float:
        """Glow intensity level."""
        return self.get_parameter("intensity")

    @intensity.setter
    def intensity(self, value: float) -> None:
        self.set_parameter("intensity", value)


@register_effect("BlurRegion")
class BlurRegion(Effect):
    """Blur region effect.

    Parameters:
        sigma, mask-cornerRadius, mask-invert, color-alpha
    """

    @property
    def sigma(self) -> float:
        """Gaussian blur sigma value."""
        return self.get_parameter("sigma")

    @sigma.setter
    def sigma(self, value: float) -> None:
        self.set_parameter("sigma", value)

    @property
    def mask_corner_radius(self) -> float:
        """Corner radius of the blur region mask."""
        return self.get_parameter("mask-cornerRadius")

    @mask_corner_radius.setter
    def mask_corner_radius(self, value: float) -> None:
        self.set_parameter("mask-cornerRadius", value)

    @property
    def mask_invert(self) -> int:
        """Whether the blur region mask is inverted (1) or normal (0)."""
        return self.get_parameter("mask-invert")

    @mask_invert.setter
    def mask_invert(self, value: int) -> None:
        self.set_parameter("mask-invert", value)

    @property
    def color_alpha(self) -> float:
        """Alpha channel of the blur region overlay color."""
        return self.get_parameter("color-alpha")

    @color_alpha.setter
    def color_alpha(self, value: float) -> None:
        self.set_parameter("color-alpha", value)
