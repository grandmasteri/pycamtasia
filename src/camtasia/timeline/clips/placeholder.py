from __future__ import annotations

from typing import NoReturn

from camtasia.timeline.clips.base import BaseClip


class PlaceholderMedia(BaseClip):
    """A placeholder clip for missing or to-be-added media."""

    def set_source(self, source_id: int) -> NoReturn:
        """Not supported on PlaceholderMedia."""
        raise TypeError('Cannot set_source on PlaceholderMedia; replace the clip instead')

    @property
    def title(self) -> str:
        """Title text for the placeholder clip."""
        val = self._data.get('metadata', {}).get('placeHolderTitle', '')
        return val if val is not None else ''

    @title.setter
    def title(self, value: str) -> None:
        """Set the title text for the placeholder clip."""
        self._data.setdefault('metadata', {})['placeHolderTitle'] = value

    @property
    def subtitle(self) -> str:
        """Subtitle text for the placeholder clip."""
        val = self._data.get('metadata', {}).get('placeHolderSubTitle', '')
        return val if val is not None else ''

    @subtitle.setter
    def subtitle(self, value: str) -> None:
        """Set the subtitle text for the placeholder clip."""
        self._data.setdefault('metadata', {})['placeHolderSubTitle'] = value

    @property
    def width(self) -> float:
        """Width of the placeholder in pixels."""
        return float(self._data.get('attributes', {}).get('widthAttr', 0.0))

    @property
    def height(self) -> float:
        """Height of the placeholder in pixels."""
        return float(self._data.get('attributes', {}).get('heightAttr', 0.0))
