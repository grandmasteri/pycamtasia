"""Source effects for shader videos."""
from __future__ import annotations

from typing import Any

from camtasia.effects.base import Effect, register_effect


@register_effect("SourceEffect")
class SourceEffect(Effect):
    """Source effect for shader video parameters.

    Parameters:
        Color0-3 (RGBA via separate keys), MidPointX, MidPointY,
        Speed, sourceFileType.
    """

    def _get_color(self, index: int) -> tuple[float, float, float, float]:
        """Get RGBA for Color{index}."""
        return (
            self.get_parameter(f"Color{index}-red"),
            self.get_parameter(f"Color{index}-green"),
            self.get_parameter(f"Color{index}-blue"),
            self.get_parameter(f"Color{index}-alpha"),
        )

    def _set_color(self, index: int, rgba: tuple[float, float, float, float]) -> None:
        """Set RGBA for Color{index}."""
        self.set_parameter(f"Color{index}-red", rgba[0])
        self.set_parameter(f"Color{index}-green", rgba[1])
        self.set_parameter(f"Color{index}-blue", rgba[2])
        self.set_parameter(f"Color{index}-alpha", rgba[3])

    @property
    def color0(self) -> tuple[float, float, float, float]:
        """First shader color as RGBA floats."""
        return self._get_color(0)

    @color0.setter
    def color0(self, rgba: tuple[float, float, float, float]) -> None:
        self._set_color(0, rgba)

    @property
    def color1(self) -> tuple[float, float, float, float]:
        """Second shader color as RGBA floats."""
        return self._get_color(1)

    @color1.setter
    def color1(self, rgba: tuple[float, float, float, float]) -> None:
        self._set_color(1, rgba)

    def _get_value(self, val: Any) -> float:
        """Extract scalar from a parameter value (dict or raw)."""
        return val['defaultValue'] if isinstance(val, dict) else val

    @property
    def color2(self) -> tuple[float, float, float, float] | None:
        """Third shader color as RGBA floats, or None if not present."""
        try:
            return self._get_color(2)
        except KeyError:
            return None

    @color2.setter
    def color2(self, rgba: tuple[float, float, float, float]) -> None:
        self._set_color(2, rgba)

    @property
    def color3(self) -> tuple[float, float, float, float] | None:
        """Fourth shader color as RGBA floats, or None if not present."""
        try:
            return self._get_color(3)
        except KeyError:
            return None

    @color3.setter
    def color3(self, rgba: tuple[float, float, float, float]) -> None:
        self._set_color(3, rgba)

    @property
    def mid_point(self) -> tuple[float, float] | float:
        """Mid point position. Returns (x, y) tuple for four-corner gradients or a single float for radial gradients."""
        params = self._data.get('parameters', {})
        if 'MidPointX' in params:
            x = self._get_value(params.get('MidPointX', 0.5))
            y = self._get_value(params.get('MidPointY', 0.5))
            return (x, y)
        elif 'MidPoint' in params:
            return self._get_value(params.get('MidPoint', 0.5))
        return (0.5, 0.5)

    @mid_point.setter
    def mid_point(self, xy: tuple[float, float]) -> None:
        self.set_parameter("MidPointX", xy[0])
        self.set_parameter("MidPointY", xy[1])

    @property
    def speed(self) -> float:
        """Shader animation speed."""
        return self.get_parameter("Speed")

    @speed.setter
    def speed(self, value: float) -> None:
        self.set_parameter("Speed", value)

    @property
    def source_file_type(self) -> str:
        """Source file type identifier for the shader."""
        return self.get_parameter("sourceFileType")

    def set_shader_colors(
        self,
        color0: tuple[int, int, int],
        color1: tuple[int, int, int],
        color2: tuple[int, int, int],
        color3: tuple[int, int, int],
    ) -> None:
        """Set all four shader colours from 0-255 RGB tuples.

        Alpha is set to 1.0 for all colours.

        Args:
            color0: ``(r, g, b)`` with values 0–255.
            color1: ``(r, g, b)`` with values 0–255.
            color2: ``(r, g, b)`` with values 0–255.
            color3: ``(r, g, b)`` with values 0–255.
        """
        for i, rgb in enumerate((color0, color1, color2, color3)):
            self._set_color(i, (rgb[0] / 255, rgb[1] / 255, rgb[2] / 255, 1.0))
