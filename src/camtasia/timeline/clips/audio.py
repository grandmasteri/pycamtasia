"""Audio media clip (AMFile)."""
from __future__ import annotations

from typing import Any, Self

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
        return self._data.get('channelNumber', '0')  # type: ignore[no-any-return]

    @channel_number.setter
    def channel_number(self, value: str) -> None:
        self._data['channelNumber'] = value

    @property
    def attributes(self) -> dict[str, Any]:
        """Audio attributes dict (ident, gain, mixToMono, etc.)."""
        return self._data.get('attributes', {})  # type: ignore[no-any-return]

    @property
    def gain(self) -> float:
        """Audio gain multiplier."""
        return float(self.attributes.get('gain', 1.0))

    @gain.setter
    def gain(self, value: float) -> None:
        self._data.setdefault('attributes', {})['gain'] = value

    @property
    def loudness_normalization(self) -> bool:
        """Whether loudness normalization is enabled."""
        return bool(self.attributes.get('loudnessNormalization', False))

    @loudness_normalization.setter
    def loudness_normalization(self, value: bool) -> None:
        self._data.setdefault('attributes', {})['loudnessNormalization'] = value

    @property
    def is_muted(self) -> bool:
        """Whether the clip's gain is zero."""
        return self.gain == 0.0

    def normalize_gain(self, target_db: float = -23.0) -> Self:
        """Set loudness normalization target.

        Camtasia uses LUFS for loudness normalization.
        Common targets: -23 LUFS (EBU R128), -16 LUFS (podcast).

        Args:
            target_db: Target loudness in LUFS (default -23.0).

        Returns:
            self for chaining.
        """
        self._data.setdefault('attributes', {})['loudnessNormalization'] = True
        self._data.setdefault('metadata', {})['targetLoudness'] = target_db
        return self

    def set_gain(self, gain: float) -> Self:
        """Set the audio gain (volume multiplier).

        Args:
            gain: Volume multiplier (0.0 = silent, 1.0 = normal, 2.0 = double).

        Returns:
            self for chaining.
        """
        if gain < 0:
            raise ValueError(f'Gain must be non-negative, got {gain}')
        self._data.setdefault('attributes', {})['gain'] = gain
        return self
