from __future__ import annotations
from camtasia.timeline.clips.base import BaseClip


class PlaceholderMedia(BaseClip):
    """A placeholder clip for missing or to-be-added media."""

    @property
    def subtitle(self) -> str:
        """Subtitle text for the placeholder clip."""
        return self._data.get('metadata', {}).get('placeHolderSubTitle', '')  # type: ignore[no-any-return]

    @subtitle.setter
    def subtitle(self, value: str) -> None:
        """Set the subtitle text for the placeholder clip."""
        self._data.setdefault('metadata', {})['placeHolderSubTitle'] = value

    @property
    def width(self) -> float:
        """Width of the placeholder in pixels."""
        return float(self._data.get('attributes', {}).get('width', 0.0))

    @property
    def height(self) -> float:
        """Height of the placeholder in pixels."""
        return float(self._data.get('attributes', {}).get('height', 0.0))
