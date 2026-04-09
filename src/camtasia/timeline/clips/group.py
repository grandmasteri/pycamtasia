"""Group (compound) clip."""
from __future__ import annotations

from typing import Any

from .base import BaseClip


class GroupTrack:
    """A track inside a Group clip.

    Args:
        data: The raw track dict from the Group's ``tracks`` array.
    """

    def __init__(self, data: dict[str, Any]) -> None:
        self._data = data

    @property
    def track_index(self) -> int:
        """Track index within the group."""
        return self._data.get('trackIndex', 0)

    @property
    def clips(self) -> list[BaseClip]:
        """Clips on this group track.

        Returns:
            List of typed clip instances created via ``clip_from_dict``.
        """
        from . import clip_from_dict
        return [clip_from_dict(m) for m in self._data.get('medias', [])]

    @property
    def parameters(self) -> dict[str, Any]:
        """Track parameters dict."""
        return self._data.get('parameters', {})

    def __repr__(self) -> str:
        return f"GroupTrack(index={self.track_index}, clips={len(self._data.get('medias', []))})"


class Group(BaseClip):
    """Compound clip containing its own internal tracks.

    Args:
        data: The raw clip dict.
    """

    @property
    def tracks(self) -> list[GroupTrack]:
        """Internal tracks, each with their own clips."""
        return [GroupTrack(t) for t in self._data.get('tracks', [])]

    @property
    def attributes(self) -> dict[str, Any]:
        """Group attributes dict (ident, widthAttr, heightAttr)."""
        return self._data.get('attributes', {})

    @property
    def ident(self) -> str:
        """Group name / identifier."""
        return self.attributes.get('ident', '')

    @property
    def width(self) -> float:
        """Group width."""
        return self.attributes.get('widthAttr', 0.0)

    @property
    def height(self) -> float:
        """Group height."""
        return self.attributes.get('heightAttr', 0.0)
