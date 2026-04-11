"""Image media clip (IMFile)."""
from __future__ import annotations

from .base import BaseClip


class IMFile(BaseClip):
    """Image media file clip.

    Inherits translation, scale, crop, and other transform helpers from
    :class:`BaseClip`.  Adds a read-only :attr:`geometry_crop` convenience
    property.

    Args:
        data: The raw clip dict.
    """

    @property
    def geometry_crop(self) -> dict[str, float]:
        """Geometry crop values (keys ``0`` through ``3``)."""
        return {
            str(i): self._get_param_value(f'geometryCrop{i}')
            for i in range(4)
            if f'geometryCrop{i}' in self.parameters
        }
