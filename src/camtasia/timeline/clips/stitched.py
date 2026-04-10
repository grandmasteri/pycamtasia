"""Stitched (spliced) media clip."""
from __future__ import annotations

from typing import Any, TYPE_CHECKING

from .base import BaseClip

if TYPE_CHECKING:
    pass


class StitchedMedia(BaseClip):
    """Container for multiple spliced segments from the same source.

    The parent ``mediaStart``/``duration`` defines a window into the
    child timeline formed by the ``medias`` array.

    Args:
        data: The raw clip dict.
    """

    @property
    def nested_clips(self) -> list[BaseClip]:
        """Child clip segments.

        Returns:
            List of typed clip instances created via ``clip_from_dict``.
        """
        from . import clip_from_dict
        return [clip_from_dict(m) for m in self._data.get('medias', [])]

    @property
    def attributes(self) -> dict[str, Any]:
        """Clip attributes dict."""
        return self._data.get('attributes', {})

    @property
    def volume(self) -> float:
        """Volume / gain from attributes."""
        return self.attributes.get('gain', 1.0)

    @volume.setter
    def volume(self, value: float) -> None:
        self._data.setdefault('attributes', {})['gain'] = value

    @property
    def source_effect(self) -> dict[str, Any] | None:
        """Source effect applied to the stitched media, or ``None``."""
        return self._data.get('sourceEffect')
