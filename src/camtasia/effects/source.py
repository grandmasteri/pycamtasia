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

    def _color_key_prefix(self, index: int) -> str:
        """Get the correct color key prefix (Color0 or Color000 for Lottie)."""
        short_key = f"Color{index}"
        padded_key = f"Color{index:03d}"
        # Check which format exists in the parameters
        params = self._data.get('parameters', {})
        if f"{padded_key}-red" in params:
            return padded_key
        return short_key

    def _get_color(self, index: int) -> tuple[float, float, float, float]:
        """Get RGBA for Color{index}."""
        prefix = self._color_key_prefix(index)
        return (
            self.get_parameter(f"{prefix}-red"),
            self.get_parameter(f"{prefix}-green"),
            self.get_parameter(f"{prefix}-blue"),
            self.get_parameter(f"{prefix}-alpha"),
        )

    def _set_color(self, index: int, rgba: tuple[float, float, float, float]) -> None:
        """Set RGBA for Color{index}."""
        prefix = self._color_key_prefix(index)
        self.set_parameter(f"{prefix}-red", rgba[0])
        self.set_parameter(f"{prefix}-green", rgba[1])
        self.set_parameter(f"{prefix}-blue", rgba[2])
        self.set_parameter(f"{prefix}-alpha", rgba[3])

    @property
    def color0(self) -> tuple[float, float, float, float]:
        """First shader color as RGBA floats."""
        return self._get_color(0)

    @color0.setter
    def color0(self, rgba: tuple[float, float, float, float]) -> None:
        """Set the first shader color."""
        self._set_color(0, rgba)

    @property
    def color1(self) -> tuple[float, float, float, float]:
        """Second shader color as RGBA floats."""
        return self._get_color(1)

    @color1.setter
    def color1(self, rgba: tuple[float, float, float, float]) -> None:
        """Set the second shader color."""
        self._set_color(1, rgba)

    def _get_value(self, val: Any) -> float:
        """Extract scalar from a parameter value (dict or raw)."""
        return float(val['defaultValue'] if isinstance(val, dict) else val)

    @property
    def color2(self) -> tuple[float, float, float, float] | None:
        """Third shader color as RGBA floats, or None if not present."""
        try:
            return self._get_color(2)
        except KeyError:
            return None

    @color2.setter
    def color2(self, rgba: tuple[float, float, float, float]) -> None:
        """Set the third shader color."""
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
        """Set the fourth shader color."""
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
    def mid_point(self, value: tuple[float, float] | float) -> None:
        """Set the mid point position."""
        params = self._data.setdefault('parameters', {})
        if isinstance(value, (int, float)):
            params['MidPoint'] = value
        else:
            params['MidPointX'] = value[0]
            params['MidPointY'] = value[1]

    @property
    def speed(self) -> float:
        """Shader animation speed."""
        return float(self.get_parameter("Speed"))

    @speed.setter
    def speed(self, value: float) -> None:
        """Set the shader animation speed."""
        self.set_parameter("Speed", value)

    @property
    def source_file_type(self) -> str:
        """Source file type identifier for the shader."""
        return str(self.get_parameter("sourceFileType"))

    def set_shader_colors(self, *colors: tuple[int, int, int]) -> None:
        """Set shader colours from 0-255 RGB tuples.

        Accepts 2 colors (radial gradient) or 4 colors (four-corner gradient).
        Alpha is set to 1.0 for all colours.

        Args:
            colors: ``(r, g, b)`` tuples with values 0–255.
        """
        params = self._data.setdefault('parameters', {})
        for i, rgb in enumerate(colors):
            prefix = self._color_key_prefix(i)
            r, g, b = rgb[0] / 255, rgb[1] / 255, rgb[2] / 255
            params[f'{prefix}-red'] = r
            params[f'{prefix}-green'] = g
            params[f'{prefix}-blue'] = b
            params[f'{prefix}-alpha'] = 1.0
