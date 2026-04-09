"""Audio media clip (AMFile)."""
from __future__ import annotations

from typing import Any

from .base import BaseClip


class AMFile(BaseClip):
    """Audio media file clip.

    Wraps an ``AMFile`` JSON dict. Adds audio-specific properties for
    channel selection, gain, and loudness normalization.

    Args:
        data: The raw clip dict.
    """

    @property
    def channel_number(self) -> str:
        """Channel number string (e.g. ``'0'``, ``'0,1'``)."""
        return self._data.get('channelNumber', '0')

    @channel_number.setter
    def channel_number(self, value: str) -> None:
        self._data['channelNumber'] = value

    @property
    def attributes(self) -> dict[str, Any]:
        """Audio attributes dict (ident, gain, mixToMono, etc.)."""
        return self._data.get('attributes', {})

    @property
    def gain(self) -> float:
        """Audio gain multiplier."""
        return self.attributes.get('gain', 1.0)

    @gain.setter
    def gain(self, value: float) -> None:
        self._data.setdefault('attributes', {})['gain'] = value

    @property
    def loudness_normalization(self) -> bool:
        """Whether loudness normalization is enabled."""
        return self.attributes.get('loudnessNormalization', False)

    @loudness_normalization.setter
    def loudness_normalization(self, value: bool) -> None:
        self._data.setdefault('attributes', {})['loudnessNormalization'] = value
