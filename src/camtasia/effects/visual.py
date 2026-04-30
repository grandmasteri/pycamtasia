"""Visual effects: RoundCorners, DropShadow."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from camtasia.effects.base import Effect, register_effect

if TYPE_CHECKING:
    from camtasia.types import MaskShape


@register_effect("RoundCorners")
class RoundCorners(Effect):
    """Round corners effect.

    Parameters:
        radius, topLeft, topRight, bottomLeft, bottomRight
    """

    @property
    def radius(self) -> float:
        """Corner radius in pixels."""
        return float(self.get_parameter("radius"))

    @radius.setter
    def radius(self, value: float) -> None:
        """Set the corner radius in pixels."""
        self.set_parameter("radius", value)

    @property
    def top_left(self) -> bool:
        """Whether the top-left corner is rounded."""
        return bool(self.get_parameter("top-left"))

    @top_left.setter
    def top_left(self, value: bool) -> None:
        """Set whether the top-left corner is rounded."""
        self.set_parameter("top-left", float(value))

    @property
    def top_right(self) -> bool:
        """Whether the top-right corner is rounded."""
        return bool(self.get_parameter("top-right"))

    @top_right.setter
    def top_right(self, value: bool) -> None:
        """Set whether the top-right corner is rounded."""
        self.set_parameter("top-right", float(value))

    @property
    def bottom_left(self) -> bool:
        """Whether the bottom-left corner is rounded."""
        return bool(self.get_parameter("bottom-left"))

    @bottom_left.setter
    def bottom_left(self, value: bool) -> None:
        """Set whether the bottom-left corner is rounded."""
        self.set_parameter("bottom-left", float(value))

    @property
    def bottom_right(self) -> bool:
        """Whether the bottom-right corner is rounded."""
        return bool(self.get_parameter("bottom-right"))

    @bottom_right.setter
    def bottom_right(self, value: bool) -> None:
        """Set whether the bottom-right corner is rounded."""
        self.set_parameter("bottom-right", float(value))


def _color_rgba(params: dict[str, Any], prefix: str) -> tuple[float, float, float, float]:
    """Read RGBA color from separate parameter keys."""
    def _val(key: str) -> float:
        v = params[key]
        return float(v['defaultValue'] if isinstance(v, dict) else v)
    return (_val(f"{prefix}-red"), _val(f"{prefix}-green"),
            _val(f"{prefix}-blue"), _val(f"{prefix}-alpha"))


def _set_color_rgba(
    params: dict[str, Any], prefix: str, rgba: tuple[float, float, float, float]
) -> None:
    """Write RGBA color to separate parameter keys."""
    for suffix, value in zip(("red", "green", "blue", "alpha"), rgba):
        key = f"{prefix}-{suffix}"
        v = params.get(key)
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
        """Shadow angle in radians."""
        return float(self.get_parameter("angle"))

    @angle.setter
    def angle(self, value: float) -> None:
        """Set the shadow angle in radians."""
        self.set_parameter("angle", value)

    @property
    def enabled(self) -> int:  # type: ignore[no-any-return]
        """Whether the effect is on (1) or off (0) at the default keyframe.

        Note: This reads/writes the ``defaultValue`` of the ``enabled``
        parameter. If the parameter has keyframes (i.e., the effect is
        animated on/off over time), setting this property only changes
        the default value — it does NOT modify existing keyframes. To
        animate enabled over time, use the keyframe APIs directly on
        the parameter.
        """
        return int(self.get_parameter('enabled')) # type: ignore[no-any-return]

    @enabled.setter
    def enabled(self, value: int) -> None:
        self.set_parameter('enabled', value)


    @property
    def offset(self) -> float:
        """Shadow offset distance in pixels."""
        return float(self.get_parameter("offset"))

    @offset.setter
    def offset(self, value: float) -> None:
        """Set the shadow offset distance in pixels."""
        self.set_parameter("offset", value)

    @property
    def blur(self) -> float:
        """Shadow blur radius."""
        return float(self.get_parameter("blur"))

    @blur.setter
    def blur(self, value: float) -> None:
        """Set the shadow blur radius."""
        self.set_parameter("blur", value)

    @property
    def opacity(self) -> float:
        """Shadow opacity from 0.0 (transparent) to 1.0 (opaque)."""
        return float(self.get_parameter("opacity"))

    @opacity.setter
    def opacity(self, value: float) -> None:
        """Set the shadow opacity."""
        self.set_parameter("opacity", value)

    @property
    def color(self) -> tuple[float, float, float, float]:
        """RGBA color as ``(red, green, blue, alpha)`` floats."""
        return _color_rgba(self.parameters, "color")

    @color.setter
    def color(self, rgba: tuple[float, float, float, float]) -> None:
        """Set the RGBA shadow color."""
        _set_color_rgba(self._data.setdefault('parameters', {}), "color", rgba)


@register_effect("MotionBlur")
class MotionBlur(Effect):
    """Motion blur effect.

    Parameters:
        intensity
    """

    @property
    def intensity(self) -> float:
        """Blur intensity level."""
        return float(self.get_parameter("intensity"))

    @intensity.setter
    def intensity(self, value: float) -> None:
        """Set the blur intensity level."""
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
        return int(self.get_parameter("mask-shape"))

    @mask_shape.setter
    def mask_shape(self, value: int | MaskShape) -> None:
        """Set the mask shape identifier."""
        self.set_parameter("mask-shape", int(value))

    @property
    def mask_opacity(self) -> float:
        """Mask opacity from 0.0 (transparent) to 1.0 (opaque)."""
        return float(self.get_parameter("mask-opacity"))

    @mask_opacity.setter
    def mask_opacity(self, value: float) -> None:
        """Set the mask opacity."""
        self.set_parameter("mask-opacity", value)

    @property
    def mask_blend(self) -> float:
        """Mask edge blend (feather) amount."""
        return float(self.get_parameter("mask-blend"))

    @mask_blend.setter
    def mask_blend(self, value: float) -> None:
        """Set the mask edge blend amount."""
        self.set_parameter("mask-blend", value)

    @property
    def mask_invert(self) -> int:
        """Whether the mask is inverted (1) or normal (0)."""
        return int(self.get_parameter("mask-invert"))

    @mask_invert.setter
    def mask_invert(self, value: int) -> None:
        """Set the mask inversion state."""
        self.set_parameter("mask-invert", value)

    @property
    def mask_rotation(self) -> float:
        """Mask rotation angle in radians."""
        return float(self.get_parameter("mask-rotation"))

    @mask_rotation.setter
    def mask_rotation(self, value: float) -> None:
        """Set the mask rotation angle in radians."""
        self.set_parameter("mask-rotation", value)

    @property
    def mask_width(self) -> float:
        """Mask width, scalar or keyframed dict."""
        return self.get_parameter("mask-width")  # type: ignore[no-any-return]

    @mask_width.setter
    def mask_width(self, value: float) -> None:
        """Set the mask width."""
        self.set_parameter("mask-width", value)

    @property
    def mask_height(self) -> float:
        """Mask height, scalar or keyframed dict."""
        return self.get_parameter("mask-height")  # type: ignore[no-any-return]

    @mask_height.setter
    def mask_height(self, value: float) -> None:
        """Set the mask height."""
        self.set_parameter("mask-height", value)

    @property
    def mask_position_x(self) -> float:
        """Mask horizontal position, scalar or keyframed dict."""
        return self.get_parameter("mask-positionX")  # type: ignore[no-any-return]

    @mask_position_x.setter
    def mask_position_x(self, value: float) -> None:
        """Set the mask horizontal position."""
        self.set_parameter("mask-positionX", value)

    @property
    def mask_position_y(self) -> float:
        """Mask vertical position, scalar or keyframed dict."""
        return self.get_parameter("mask-positionY")  # type: ignore[no-any-return]

    @mask_position_y.setter
    def mask_position_y(self, value: float) -> None:
        """Set the mask vertical position."""
        self.set_parameter("mask-positionY", value)

    @property
    def mask_corner_radius(self) -> float:
        """Mask corner radius."""
        return float(self.get_parameter("mask-cornerRadius"))

    @mask_corner_radius.setter
    def mask_corner_radius(self, value: float) -> None:
        """Set the mask corner radius."""
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
        return float(self.get_parameter("radius"))

    @radius.setter
    def radius(self, value: float) -> None:
        """Set the glow spread radius."""
        self.set_parameter("radius", value)

    @property
    def intensity(self) -> float:
        """Glow intensity level."""
        return float(self.get_parameter("intensity"))

    @intensity.setter
    def intensity(self, value: float) -> None:
        """Set the glow intensity level."""
        self.set_parameter("intensity", value)


# Not registered via @register_effect — unverified against real Camtasia projects.
class BlurRegion(Effect):
    """Blur region effect.

    .. warning::
        This effect is **not registered** with ``effect_from_dict`` because it
        has not been verified against any TechSmith sample project.  Parameter
        names and semantics may differ from what Camtasia actually produces.

    Parameters:
        sigma, mask-cornerRadius, mask-invert, color-alpha
    """

    @property
    def sigma(self) -> float:
        """Gaussian blur sigma value."""
        return float(self.get_parameter("sigma"))

    @sigma.setter
    def sigma(self, value: float) -> None:
        """Set the Gaussian blur sigma value."""
        self.set_parameter("sigma", value)

    @property
    def mask_corner_radius(self) -> float:
        """Corner radius of the blur region mask."""
        return float(self.get_parameter("mask-cornerRadius"))

    @mask_corner_radius.setter
    def mask_corner_radius(self, value: float) -> None:
        """Set the corner radius of the blur region mask."""
        self.set_parameter("mask-cornerRadius", value)

    @property
    def mask_invert(self) -> int:
        """Whether the blur region mask is inverted (1) or normal (0)."""
        return int(self.get_parameter("mask-invert"))

    @mask_invert.setter
    def mask_invert(self, value: int) -> None:
        """Set the blur region mask inversion state."""
        self.set_parameter("mask-invert", value)

    @property
    def color_alpha(self) -> float:
        """Alpha channel of the blur region overlay color."""
        return float(self.get_parameter("color-alpha"))

    @color_alpha.setter
    def color_alpha(self, value: float) -> None:
        """Set the alpha channel of the blur region overlay color."""
        self.set_parameter("color-alpha", value)



@register_effect("ColorAdjustment")
class ColorAdjustment(Effect):
    """Color adjustment effect (brightness/contrast/saturation)."""

    @property
    def brightness(self) -> float:
        """Brightness multiplier (1.0 = unchanged)."""
        return float(self.get_parameter("brightness"))

    @brightness.setter
    def brightness(self, value: float) -> None:
        self.set_parameter("brightness", value)

    @property
    def contrast(self) -> float:
        """Contrast multiplier (1.0 = unchanged)."""
        return float(self.get_parameter("contrast"))

    @contrast.setter
    def contrast(self, value: float) -> None:
        self.set_parameter("contrast", value)

    @property
    def saturation(self) -> float:
        """Saturation shift."""
        return float(self.get_parameter("saturation"))

    @saturation.setter
    def saturation(self, value: float) -> None:
        self.set_parameter("saturation", value)


@register_effect("LutEffect")
class LutEffect(Effect):
    """Color grading via a .cube LUT file."""

    @property
    def lut_source(self) -> str:
        """LUT filename (e.g., 'Tasteful.cube')."""
        return str(self.get_parameter("lutSource"))

    @lut_source.setter
    def lut_source(self, value: str) -> None:
        self.set_parameter("lutSource", value)

    @property
    def intensity(self) -> float:
        """LUT strength (0.0 = off, 1.0 = full)."""
        return float(self.get_parameter("lut_intensity"))

    @intensity.setter
    def intensity(self, value: float) -> None:
        self.set_parameter("lut_intensity", value)


@register_effect("BlendModeEffect")
class BlendModeEffect(Effect):
    """Blending mode effect (e.g., multiply, screen, overlay)."""

    @property
    def mode(self) -> int:
        """Blend mode code (integer)."""
        return int(self.get_parameter("mode"))

    @mode.setter
    def mode(self, value: int) -> None:
        self.set_parameter("mode", value)

    @property
    def intensity(self) -> float:
        """Blend intensity (0.0 = off, 1.0 = full)."""
        return float(self.get_parameter("intensity"))

    @intensity.setter
    def intensity(self, value: float) -> None:
        self.set_parameter("intensity", value)

    @property
    def invert(self) -> int:
        """Whether to invert the blend (1 = invert)."""
        return int(self.get_parameter("invert"))

    @invert.setter
    def invert(self, value: int) -> None:
        self.set_parameter("invert", value)


@register_effect("Emphasize")
class Emphasize(Effect):
    """Emphasize effect — increase opacity/contrast around a focal point."""

    @property
    def amount(self) -> float:
        """Emphasis strength (0.0 = off, 1.0 = full)."""
        return float(self.get_parameter("emphasizeAmount"))

    @amount.setter
    def amount(self, value: float) -> None:
        self.set_parameter("emphasizeAmount", value)

    @property
    def ramp_position(self) -> float:
        """Ramp position within the effect range."""
        return float(self.get_parameter("emphasizeRampPosition"))

    @ramp_position.setter
    def ramp_position(self, value: float) -> None:
        self.set_parameter("emphasizeRampPosition", value)

    @property
    def ramp_in_ticks(self) -> int:
        """Ramp-in duration in editRate ticks."""
        return int(self.get_parameter("emphasizeRampInTime"))

    @ramp_in_ticks.setter
    def ramp_in_ticks(self, value: int) -> None:
        self.set_parameter("emphasizeRampInTime", value)

    @property
    def ramp_out_ticks(self) -> int:
        """Ramp-out duration in editRate ticks."""
        return int(self.get_parameter("emphasizeRampOutTime"))

    @ramp_out_ticks.setter
    def ramp_out_ticks(self, value: int) -> None:
        self.set_parameter("emphasizeRampOutTime", value)


@register_effect("Spotlight")
class Spotlight(Effect):
    """Spotlight effect — highlight a region with a colored light."""

    @property
    def brightness(self) -> float:
        """Spotlight brightness multiplier."""
        return float(self.get_parameter("brightness"))

    @brightness.setter
    def brightness(self, value: float) -> None:
        self.set_parameter("brightness", value)

    @property
    def concentration(self) -> float:
        """Light concentration / falloff."""
        return float(self.get_parameter("concentration"))

    @concentration.setter
    def concentration(self, value: float) -> None:
        self.set_parameter("concentration", value)

    @property
    def opacity(self) -> float:
        """Spotlight overlay opacity (0.0-1.0)."""
        return float(self.get_parameter("opacity"))

    @opacity.setter
    def opacity(self, value: float) -> None:
        self.set_parameter("opacity", value)

    @property
    def position(self) -> tuple[float, float]:
        """Light position (x, y) in normalized coordinates."""
        return (float(self.get_parameter("positionX")), float(self.get_parameter("positionY")))

    @position.setter
    def position(self, value: tuple[float, float]) -> None:
        self.set_parameter("positionX", value[0])
        self.set_parameter("positionY", value[1])


@register_effect("MediaMatte")
class MediaMatte(Effect):
    """Media matte — use another clip's luminance or alpha as a mask."""

    @property
    def intensity(self) -> float:
        """Matte effect intensity (0.0-1.0)."""
        return float(self.get_parameter("intensity"))

    @intensity.setter
    def intensity(self, value: float) -> None:
        self.set_parameter("intensity", value)

    @property
    def mode(self) -> int:
        """Matte mode code (integer)."""
        return int(self.get_parameter("matteMode"))

    @mode.setter
    def mode(self, value: int) -> None:
        self.set_parameter("matteMode", value)

    @property
    def track_depth(self) -> int:
        """Depth of the matte source track."""
        return int(self.get_parameter("trackDepth"))

    @track_depth.setter
    def track_depth(self, value: int) -> None:
        self.set_parameter("trackDepth", value)



@register_effect("CornerPin")
class CornerPin(Effect):
    """Corner pinning — 3D perspective transform defined by four corner points.

    .. warning::
        The ``effectName`` and parameter names for this effect have not been
        directly verified against a real TechSmith fixture that uses corner
        pinning. The names below follow TechSmith's public documentation and
        Camtasia's naming conventions. If your Camtasia version rejects these
        names, please file an issue with a fixture project.

    Parameter pattern (four corner points, normalized 0.0-1.0):
        ``topLeftX``, ``topLeftY``, ``topRightX``, ``topRightY``,
        ``bottomLeftX``, ``bottomLeftY``, ``bottomRightX``, ``bottomRightY``.
    """

    @property
    def top_left(self) -> tuple[float, float]:
        return (float(self.get_parameter("topLeftX")), float(self.get_parameter("topLeftY")))

    @top_left.setter
    def top_left(self, value: tuple[float, float]) -> None:
        self.set_parameter("topLeftX", value[0])
        self.set_parameter("topLeftY", value[1])

    @property
    def top_right(self) -> tuple[float, float]:
        return (float(self.get_parameter("topRightX")), float(self.get_parameter("topRightY")))

    @top_right.setter
    def top_right(self, value: tuple[float, float]) -> None:
        self.set_parameter("topRightX", value[0])
        self.set_parameter("topRightY", value[1])

    @property
    def bottom_left(self) -> tuple[float, float]:
        return (float(self.get_parameter("bottomLeftX")), float(self.get_parameter("bottomLeftY")))

    @bottom_left.setter
    def bottom_left(self, value: tuple[float, float]) -> None:
        self.set_parameter("bottomLeftX", value[0])
        self.set_parameter("bottomLeftY", value[1])

    @property
    def bottom_right(self) -> tuple[float, float]:
        return (float(self.get_parameter("bottomRightX")), float(self.get_parameter("bottomRightY")))

    @bottom_right.setter
    def bottom_right(self, value: tuple[float, float]) -> None:
        self.set_parameter("bottomRightX", value[0])
        self.set_parameter("bottomRightY", value[1])


@register_effect("Sepia")
class Sepia(Effect):
    """Sepia tone effect.

    .. warning::
        Parameter names have not been verified against a real TechSmith
        fixture. If your Camtasia version rejects these names, please
        file an issue with a fixture project.
    """


@register_effect("Vignette")
class Vignette(Effect):
    """Vignette darkening around edges.

    .. warning::
        Parameter names have not been verified against a real TechSmith
        fixture. If your Camtasia version rejects these names, please
        file an issue with a fixture project.

    Parameters:
        amount, falloff, color (RGBA via separate keys).
    """

    @property
    def amount(self) -> float:
        return float(self.get_parameter("amount"))

    @amount.setter
    def amount(self, value: float) -> None:
        self.set_parameter("amount", value)

    @property
    def falloff(self) -> float:
        return float(self.get_parameter("falloff"))

    @falloff.setter
    def falloff(self, value: float) -> None:
        self.set_parameter("falloff", value)

    @property
    def color(self) -> tuple[float, float, float, float]:
        return _color_rgba(self.parameters, "color")

    @color.setter
    def color(self, rgba: tuple[float, float, float, float]) -> None:
        _set_color_rgba(self._data.setdefault('parameters', {}), "color", rgba)


@register_effect("Reflection")
class Reflection(Effect):
    """Reflection effect below the clip.

    .. warning::
        Parameter names have not been verified against a real TechSmith
        fixture. If your Camtasia version rejects these names, please
        file an issue with a fixture project.

    Parameters:
        opacity, distance, falloff.
    """

    @property
    def opacity(self) -> float:
        return float(self.get_parameter("opacity"))

    @opacity.setter
    def opacity(self, value: float) -> None:
        self.set_parameter("opacity", value)

    @property
    def distance(self) -> float:
        return float(self.get_parameter("distance"))

    @distance.setter
    def distance(self, value: float) -> None:
        self.set_parameter("distance", value)

    @property
    def falloff(self) -> float:
        return float(self.get_parameter("falloff"))

    @falloff.setter
    def falloff(self, value: float) -> None:
        self.set_parameter("falloff", value)


@register_effect("StaticNoise")
class StaticNoise(Effect):
    """Static noise / film grain overlay.

    .. warning::
        Parameter names have not been verified against a real TechSmith
        fixture. If your Camtasia version rejects these names, please
        file an issue with a fixture project.

    Parameters:
        intensity.
    """

    @property
    def intensity(self) -> float:
        return float(self.get_parameter("intensity"))

    @intensity.setter
    def intensity(self, value: float) -> None:
        self.set_parameter("intensity", value)


@register_effect("Tiling")
class Tiling(Effect):
    """Tile/repeat the clip image.

    .. warning::
        Parameter names have not been verified against a real TechSmith
        fixture. If your Camtasia version rejects these names, please
        file an issue with a fixture project.

    Parameters:
        scale, positionX, positionY, opacity.
    """

    @property
    def scale(self) -> float:
        return float(self.get_parameter("scale"))

    @scale.setter
    def scale(self, value: float) -> None:
        self.set_parameter("scale", value)

    @property
    def position_x(self) -> float:
        return float(self.get_parameter("positionX"))

    @position_x.setter
    def position_x(self, value: float) -> None:
        self.set_parameter("positionX", value)

    @property
    def position_y(self) -> float:
        return float(self.get_parameter("positionY"))

    @position_y.setter
    def position_y(self, value: float) -> None:
        self.set_parameter("positionY", value)

    @property
    def opacity(self) -> float:
        return float(self.get_parameter("opacity"))

    @opacity.setter
    def opacity(self, value: float) -> None:
        self.set_parameter("opacity", value)


@register_effect("TornEdge")
class TornEdge(Effect):
    """Torn/ripped edge effect.

    .. warning::
        Parameter names have not been verified against a real TechSmith
        fixture. If your Camtasia version rejects these names, please
        file an issue with a fixture project.

    Parameters:
        jaggedness, margin.
    """

    @property
    def jaggedness(self) -> float:
        return float(self.get_parameter("jaggedness"))

    @jaggedness.setter
    def jaggedness(self, value: float) -> None:
        self.set_parameter("jaggedness", value)

    @property
    def margin(self) -> float:
        return float(self.get_parameter("margin"))

    @margin.setter
    def margin(self, value: float) -> None:
        self.set_parameter("margin", value)


@register_effect("CRTMonitor")
class CRTMonitor(Effect):
    """CRT monitor / retro TV effect.

    .. warning::
        Parameter names have not been verified against a real TechSmith
        fixture. If your Camtasia version rejects these names, please
        file an issue with a fixture project.

    Parameters:
        scanline, curvature, intensity.
    """

    @property
    def scanline(self) -> float:
        return float(self.get_parameter("scanline"))

    @scanline.setter
    def scanline(self, value: float) -> None:
        self.set_parameter("scanline", value)

    @property
    def curvature(self) -> float:
        return float(self.get_parameter("curvature"))

    @curvature.setter
    def curvature(self, value: float) -> None:
        self.set_parameter("curvature", value)

    @property
    def intensity(self) -> float:
        return float(self.get_parameter("intensity"))

    @intensity.setter
    def intensity(self, value: float) -> None:
        self.set_parameter("intensity", value)


@register_effect("Mosaic")
class Mosaic(Effect):
    """Mosaic / pixelation effect.

    .. warning::
        Parameter names have not been verified against a real TechSmith
        fixture. If your Camtasia version rejects these names, please
        file an issue with a fixture project.

    Parameters:
        pixelSize.
    """

    @property
    def pixel_size(self) -> float:
        return float(self.get_parameter("pixelSize"))

    @pixel_size.setter
    def pixel_size(self, value: float) -> None:
        self.set_parameter("pixelSize", value)


@register_effect("OutlineEdges")
class OutlineEdges(Effect):
    """Edge detection / outline effect.

    .. warning::
        Parameter names have not been verified against a real TechSmith
        fixture. If your Camtasia version rejects these names, please
        file an issue with a fixture project.

    Parameters:
        threshold, intensity.
    """

    @property
    def threshold(self) -> float:
        return float(self.get_parameter("threshold"))

    @threshold.setter
    def threshold(self, value: float) -> None:
        self.set_parameter("threshold", value)

    @property
    def intensity(self) -> float:
        return float(self.get_parameter("intensity"))

    @intensity.setter
    def intensity(self, value: float) -> None:
        self.set_parameter("intensity", value)


@register_effect("WindowSpotlight")
class WindowSpotlight(Effect):
    """Window spotlight effect.

    .. warning::
        Parameter names have not been verified against a real TechSmith
        fixture. If your Camtasia version rejects these names, please
        file an issue with a fixture project.
    """


@register_effect("ColorTint")
class ColorTint(Effect):
    """Two-tone color tint (light/dark regions).

    .. warning::
        Parameter names have not been verified against a real TechSmith
        fixture. If your Camtasia version rejects these names, please
        file an issue with a fixture project.

    Parameters:
        lightColor (RGBA), darkColor (RGBA) — via separate keys.
    """

    @property
    def light_color(self) -> tuple[float, float, float, float]:
        return _color_rgba(self.parameters, "lightColor")

    @light_color.setter
    def light_color(self, rgba: tuple[float, float, float, float]) -> None:
        _set_color_rgba(self._data.setdefault('parameters', {}), "lightColor", rgba)

    @property
    def dark_color(self) -> tuple[float, float, float, float]:
        return _color_rgba(self.parameters, "darkColor")

    @dark_color.setter
    def dark_color(self, rgba: tuple[float, float, float, float]) -> None:
        _set_color_rgba(self._data.setdefault('parameters', {}), "darkColor", rgba)


@register_effect("Border")
class Border(Effect):
    """Border effect around a clip.

    Parameters:
        width, color (RGBA via separate keys), corner-radius.
    """

    @property
    def width(self) -> float:
        return float(self.get_parameter("width"))

    @width.setter
    def width(self, value: float) -> None:
        self.set_parameter("width", value)

    @property
    def color(self) -> tuple[float, float, float, float]:
        return _color_rgba(self.parameters, "color")

    @color.setter
    def color(self, rgba: tuple[float, float, float, float]) -> None:
        _set_color_rgba(self._data.setdefault('parameters', {}), "color", rgba)

    @property
    def corner_radius(self) -> float:
        return float(self.get_parameter("corner-radius"))

    @corner_radius.setter
    def corner_radius(self, value: float) -> None:
        self.set_parameter("corner-radius", value)


@register_effect("Colorize")
class Colorize(Effect):
    """Colorize / tint effect.

    Parameters:
        color (RGB via separate keys), intensity.
    """

    @property
    def color(self) -> tuple[float, float, float]:
        """RGB color as ``(red, green, blue)`` floats."""
        params = self.parameters
        return (
            float(params["color-red"]["defaultValue"] if isinstance(params["color-red"], dict) else params["color-red"]),
            float(params["color-green"]["defaultValue"] if isinstance(params["color-green"], dict) else params["color-green"]),
            float(params["color-blue"]["defaultValue"] if isinstance(params["color-blue"], dict) else params["color-blue"]),
        )

    @color.setter
    def color(self, rgb: tuple[float, float, float]) -> None:
        params = self._data.setdefault('parameters', {})
        for suffix, value in zip(("red", "green", "blue"), rgb):
            key = f"color-{suffix}"
            v = params.get(key)
            if isinstance(v, dict):
                v["defaultValue"] = value
            else:
                params[key] = value

    @property
    def intensity(self) -> float:
        return float(self.get_parameter("intensity"))

    @intensity.setter
    def intensity(self, value: float) -> None:
        self.set_parameter("intensity", value)


@register_effect("ChromaKey")
class ChromaKey(Effect):
    """Chroma key / green-screen removal.

    .. warning::
        The ``effectName`` and parameter names for this effect have not been
        directly verified against a real TechSmith fixture that uses chroma
        keying. The names below follow Camtasia's naming conventions. If
        your Camtasia version rejects these names, please file an issue.

    Parameters:
        ``color-red``/``-green``/``-blue``/``-alpha`` (key color to remove),
        ``tolerance`` (0.0-1.0), ``softness`` (0.0-1.0),
        ``defringe`` (0.0-1.0), ``invert`` (0 or 1).
    """

    @property
    def color(self) -> tuple[float, float, float, float]:
        return (
            float(self.get_parameter("color-red")),
            float(self.get_parameter("color-green")),
            float(self.get_parameter("color-blue")),
            float(self.get_parameter("color-alpha")),
        )

    @color.setter
    def color(self, value: tuple[float, float, float, float]) -> None:
        self.set_parameter("color-red", value[0])
        self.set_parameter("color-green", value[1])
        self.set_parameter("color-blue", value[2])
        self.set_parameter("color-alpha", value[3])

    @property
    def tolerance(self) -> float:
        return float(self.get_parameter("tolerance"))

    @tolerance.setter
    def tolerance(self, value: float) -> None:
        self.set_parameter("tolerance", value)

    @property
    def softness(self) -> float:
        return float(self.get_parameter("softness"))

    @softness.setter
    def softness(self, value: float) -> None:
        self.set_parameter("softness", value)

    @property
    def defringe(self) -> float:
        return float(self.get_parameter("defringe"))

    @defringe.setter
    def defringe(self, value: float) -> None:
        self.set_parameter("defringe", value)

    @property
    def invert(self) -> int:
        return int(self.get_parameter("invert"))

    @invert.setter
    def invert(self, value: int) -> None:
        self.set_parameter("invert", value)
