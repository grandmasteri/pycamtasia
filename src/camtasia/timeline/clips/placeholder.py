from __future__ import annotations
from camtasia.timeline.clips.base import BaseClip


class PlaceholderMedia(BaseClip):
    """A placeholder clip for missing or to-be-added media."""

    @property
    def subtitle(self) -> str:
        return self._data.get('metadata', {}).get('placeHolderSubTitle', '')

    @subtitle.setter
    def subtitle(self, value: str) -> None:
        self._data.setdefault('metadata', {})['placeHolderSubTitle'] = value

    @property
    def width(self) -> float:
        return self._data.get('attributes', {}).get('width', 0.0)

    @property
    def height(self) -> float:
        return self._data.get('attributes', {}).get('height', 0.0)
