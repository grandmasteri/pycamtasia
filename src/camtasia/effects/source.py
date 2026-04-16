"""Source effects for shader videos."""
from __future__ import annotations

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
            return padded_key # pragma: no cover
        return short_key

    def _get_color(self, index: int) -> tuple[float, float, float, float]:
        """Get RGBA for Color{index}."""
        prefix = self._color_key_prefix(index)
        return (
            float(self.get_parameter(f"{prefix}-red")),
            float(self.get_parameter(f"{prefix}-green")),
            float(self.get_parameter(f"{prefix}-blue")),
            float(self.get_parameter(f"{prefix}-alpha")),
        )

    def _set_color(self, index: int, rgba: tuple[float, float, float, float]) -> None:
        """Set RGBA for Color{index}."""
        prefix = self._color_key_prefix(index)
        self.set_parameter(f"{prefix}-red", rgba[0])
        self.set_parameter(f"{prefix}-green", rgba[1])
        self.set_parameter(f"{prefix}-blue", rgba[2])
        self.set_parameter(f"{prefix}-alpha", rgba[3])

    @property
    def color0(self) -> tuple[float, float, float, float] | None:
        """First shader color as RGBA floats, or None if not present."""
        try:
            return self._get_color(0)
        except KeyError:
            return None

    @color0.setter
    def color0(self, rgba: tuple[float, float, float, float]) -> None:
        """Set the first shader color."""
        self._set_color(0, rgba)

    @property
    def color1(self) -> tuple[float, float, float, float] | None:
        """Second shader color as RGBA floats, or None if not present."""
        try:
            return self._get_color(1)
        except KeyError:
            return None

    @color1.setter
    def color1(self, rgba: tuple[float, float, float, float]) -> None:
        """Set the second shader color."""
        self._set_color(1, rgba)

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
            x = float(self.get_parameter('MidPointX'))
            y = float(self.get_parameter('MidPointY'))
            return (x, y)
        elif 'MidPoint' in params:
            return float(self.get_parameter('MidPoint'))
        return (0.5, 0.5)

    @mid_point.setter
    def mid_point(self, value: tuple[float, float] | float) -> None:
        """Set the mid point position."""
        params = self._data.setdefault('parameters', {})
        if isinstance(value, (int, float)):
            existing = params.get('MidPoint')
            if isinstance(existing, dict):
                existing['defaultValue'] = value
            else:
                params['MidPoint'] = value
            params.pop('MidPointX', None)
            params.pop('MidPointY', None)
        else:
            params.pop('MidPoint', None)
            for key, val in [('MidPointX', value[0]), ('MidPointY', value[1])]:
                existing = params.get(key)
                if isinstance(existing, dict):
                    existing['defaultValue'] = val
                else:
                    params[key] = val

    @property
    def speed(self) -> float | None:
        """Shader animation speed, or None if not present (e.g. Lottie assets)."""
        try:
            return float(self.get_parameter("Speed"))
        except KeyError:
            return None

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
        if len(colors) not in (2, 4):
            raise ValueError('Expected 2 or 4 colors')
        for i, rgb in enumerate(colors):
            prefix = self._color_key_prefix(i)
            r, g, b = rgb[0] / 255, rgb[1] / 255, rgb[2] / 255
            self.set_parameter(f'{prefix}-red', r)
            self.set_parameter(f'{prefix}-green', g)
            self.set_parameter(f'{prefix}-blue', b)
            self.set_parameter(f'{prefix}-alpha', 1.0)
