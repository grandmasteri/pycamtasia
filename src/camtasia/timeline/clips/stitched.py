"""Stitched (spliced) media clip."""
from __future__ import annotations

from typing import Any, NoReturn, TYPE_CHECKING

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
    def segment_count(self) -> int:
        """Number of nested clip segments."""
        return len(self._data.get('medias', []))

    def set_source(self, source_id: int) -> NoReturn:
        raise TypeError('StitchedMedia clips do not have a top-level source ID')

    @property
    def min_media_start(self) -> float:
        """Minimum media start offset in frames."""
        return float(self._data.get('minMediaStart', 0))

    def clear_segments(self) -> None:
        """Remove all nested segments."""
        self._data['medias'] = []
