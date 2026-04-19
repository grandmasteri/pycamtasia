from __future__ import annotations

import sys

if sys.version_info >= (3, 11):  # pragma: no cover
    pass
else:  # pragma: no cover
    pass

from typing import NoReturn

from camtasia.timeline.clips.base import BaseClip


class PlaceholderMedia(BaseClip):
    """A placeholder clip for missing or to-be-added media."""

    def set_source(self, source_id: int) -> NoReturn:
        """Not supported on PlaceholderMedia."""
        raise TypeError('Cannot set_source on PlaceholderMedia; replace the clip instead')

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
