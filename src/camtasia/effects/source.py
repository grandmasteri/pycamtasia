"""Source effects for shader videos."""
from __future__ import annotations

from typing import Any, Tuple

from camtasia.effects.base import Effect, register_effect


@register_effect("SourceEffect")
class SourceEffect(Effect):
    """Source effect for shader video parameters.

    Parameters:
        Color0-3 (RGBA via separate keys), MidPointX, MidPointY,
        Speed, sourceFileType.
    """

    def _get_color(self, index: int) -> Tuple[float, float, float, float]:
        """Get RGBA for Color{index}."""
        p = self.parameters
        return (
            p[f"Color{index}-red"]["defaultValue"],
            p[f"Color{index}-green"]["defaultValue"],
            p[f"Color{index}-blue"]["defaultValue"],
            p[f"Color{index}-alpha"]["defaultValue"],
        )

    def _set_color(self, index: int, rgba: Tuple[float, float, float, float]) -> None:
        """Set RGBA for Color{index}."""
        p = self.parameters
        p[f"Color{index}-red"]["defaultValue"] = rgba[0]
        p[f"Color{index}-green"]["defaultValue"] = rgba[1]
        p[f"Color{index}-blue"]["defaultValue"] = rgba[2]
        p[f"Color{index}-alpha"]["defaultValue"] = rgba[3]

    @property
    def color0(self) -> Tuple[float, float, float, float]:
        return self._get_color(0)

    @color0.setter
    def color0(self, rgba: Tuple[float, float, float, float]) -> None:
        self._set_color(0, rgba)

    @property
    def color1(self) -> Tuple[float, float, float, float]:
        return self._get_color(1)

    @color1.setter
    def color1(self, rgba: Tuple[float, float, float, float]) -> None:
        self._set_color(1, rgba)

    @property
    def color2(self) -> Tuple[float, float, float, float]:
        return self._get_color(2)

    @color2.setter
    def color2(self, rgba: Tuple[float, float, float, float]) -> None:
        self._set_color(2, rgba)

    @property
    def color3(self) -> Tuple[float, float, float, float]:
        return self._get_color(3)

    @color3.setter
    def color3(self, rgba: Tuple[float, float, float, float]) -> None:
        self._set_color(3, rgba)

    @property
    def mid_point(self) -> Tuple[float, float]:
        """Mid point as ``(x, y)``."""
        return (
            self.get_parameter("MidPointX"),
            self.get_parameter("MidPointY"),
        )

    @mid_point.setter
    def mid_point(self, xy: Tuple[float, float]) -> None:
        self.set_parameter("MidPointX", xy[0])
        self.set_parameter("MidPointY", xy[1])

    @property
    def speed(self) -> float:
        return self.get_parameter("Speed")

    @speed.setter
    def speed(self, value: float) -> None:
        self.set_parameter("Speed", value)

    @property
    def source_file_type(self) -> str:
        return self.get_parameter("sourceFileType")
