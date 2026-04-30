from __future__ import annotations

from fractions import Fraction
from typing import Any, NoReturn

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

    def replace_with(self, media_dict: dict[str, Any], mode: str = 'ripple') -> dict[str, Any]:
        """Substitute this placeholder's media data in-place.

        A simple path for replacing placeholder media where
        :meth:`set_source` raises.

        Args:
            media_dict: New media dict (must include ``_type``, ``duration``).
            mode: Replacement strategy:
                - ``'ripple'``: adopt the new media's duration.
                - ``'clip_speed'``: keep current duration, set scalar.
                - ``'from_end'``: align end points (shift start).
                - ``'from_start'``: keep current start and duration.

        Returns:
            The updated clip data dict.

        Raises:
            ValueError: If *mode* is not one of the accepted values.
        """
        valid_modes = {'ripple', 'clip_speed', 'from_end', 'from_start'}
        if mode not in valid_modes:
            raise ValueError(f"mode must be one of {sorted(valid_modes)}, got {mode!r}")

        new_type = str(media_dict.get('_type', self._data.get('_type', '')))
        new_duration = int(media_dict.get('duration', self._data.get('duration', 0)))
        old_duration = int(self._data.get('duration', 0))

        self._data['_type'] = new_type
        if 'src' in media_dict:
            self._data['src'] = media_dict['src']

        if mode == 'ripple':
            self._data['duration'] = new_duration
            self._data['mediaDuration'] = new_duration
        elif mode == 'clip_speed':
            if new_duration > 0:
                scalar = Fraction(old_duration, new_duration)
                self._data['scalar'] = 1 if scalar == 1 else str(scalar)
            self._data['mediaDuration'] = new_duration
        elif mode == 'from_end':
            old_end = self.start + old_duration
            self._data['duration'] = new_duration
            self._data['mediaDuration'] = new_duration
            self._data['start'] = old_end - new_duration
        else:  # from_start
            pass  # keep current start and duration

        return dict(self._data)
