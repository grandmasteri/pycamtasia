"""Image media clip (IMFile)."""
from __future__ import annotations

from typing import Self

from .base import BaseClip


class IMFile(BaseClip):
    """Image media file clip.

    Provides access to translation, scale, and geometry crop parameters.

    Args:
        data: The raw clip dict.
    """

    def _get_param_value(self, key: str, default: float = 0.0) -> float:
        """Get a parameter's defaultValue or raw numeric value."""
        param = self.parameters.get(key, default)
        if isinstance(param, dict):
            return param.get('defaultValue', default)
        return param

    def _set_param_value(self, key: str, value: float) -> None:
        """Set a parameter's defaultValue, creating the param dict if needed."""
        params = self._data.setdefault('parameters', {})
        if isinstance(params.get(key), dict):
            params[key]['defaultValue'] = value
        else:
            params[key] = {'type': 'double', 'defaultValue': value, 'interp': 'eioe'}

    @property
    def translation(self) -> tuple[float, float]:
        """``(x, y)`` translation."""
        return (
            self._get_param_value('translation0'),
            self._get_param_value('translation1'),
        )

    @translation.setter
    def translation(self, value: tuple[float, float]) -> None:
        self._set_param_value('translation0', value[0])
        self._set_param_value('translation1', value[1])

    @property
    def scale(self) -> tuple[float, float]:
        """``(x, y)`` scale factors."""
        return (
            self._get_param_value('scale0', 1.0),
            self._get_param_value('scale1', 1.0),
        )

    @scale.setter
    def scale(self, value: tuple[float, float]) -> None:
        self._set_param_value('scale0', value[0])
        self._set_param_value('scale1', value[1])

    @property
    def geometry_crop(self) -> dict[str, float]:
        """Geometry crop values (keys ``0`` through ``3``)."""
        return {
            str(i): self._get_param_value(f'geometryCrop{i}')
            for i in range(4)
            if f'geometryCrop{i}' in self.parameters
        }

    # ------------------------------------------------------------------
    # L2 — Transform helpers
    # ------------------------------------------------------------------

    def move_to(self, x: float, y: float) -> Self:
        """Set the clip's canvas translation.

        Args:
            x: Horizontal position.
            y: Vertical position.

        Returns:
            ``self`` for chaining.
        """
        self._set_param_value('translation0', x)
        self._set_param_value('translation1', y)
        return self

    def scale_to(self, factor: float) -> Self:
        """Set uniform scale on both axes.

        Args:
            factor: Scale factor (1.0 = native size).

        Returns:
            ``self`` for chaining.
        """
        self._set_param_value('scale0', factor)
        self._set_param_value('scale1', factor)
        return self

    def scale_to_xy(self, x: float, y: float) -> Self:
        """Set non-uniform scale.

        Args:
            x: Horizontal scale factor.
            y: Vertical scale factor.

        Returns:
            ``self`` for chaining.
        """
        self._set_param_value('scale0', x)
        self._set_param_value('scale1', y)
        return self

    def crop(
        self,
        left: float = 0,
        top: float = 0,
        right: float = 0,
        bottom: float = 0,
    ) -> Self:
        """Set geometry crop fractions.

        Args:
            left: Fraction to crop from the left edge (0.0–1.0).
            top: Fraction to crop from the top edge.
            right: Fraction to crop from the right edge.
            bottom: Fraction to crop from the bottom edge.

        Returns:
            ``self`` for chaining.
        """
        self._set_param_value('geometryCrop0', left)
        self._set_param_value('geometryCrop1', top)
        self._set_param_value('geometryCrop2', right)
        self._set_param_value('geometryCrop3', bottom)
        return self
