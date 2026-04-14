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
        return self._data.get('attributes', {})  # type: ignore[no-any-return]

    @property
    def volume(self) -> float:
        """Volume / gain from attributes."""
        return float(self.attributes.get('gain', 1.0))

    @volume.setter
    def volume(self, value: float) -> None:
        self._data.setdefault('attributes', {})['gain'] = value

    @property
    def segment_count(self) -> int:
        """Number of nested clip segments."""
        return len(self._data.get('medias', []))

    @property
    def min_media_start(self) -> int:
        return int(self._data.get('minMediaStart', 0))

    def clear_segments(self) -> None:
        """Remove all nested segments."""
        self._data['medias'] = []
