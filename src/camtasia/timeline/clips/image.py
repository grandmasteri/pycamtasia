"""Image media clip (IMFile)."""
from __future__ import annotations


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
