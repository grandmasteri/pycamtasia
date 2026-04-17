"""Audio media clip (AMFile)."""
from __future__ import annotations

from typing import Any
import sys
if sys.version_info >= (3, 11):  # pragma: no cover
    from typing import Self
else:  # pragma: no cover
    from typing_extensions import Self

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
        """Set the channel number string."""
        self._data['channelNumber'] = value

    @property
    def attributes(self) -> dict[str, Any]:
        """Audio attributes dict (ident, gain, mixToMono, etc.)."""
        return self._data.get('attributes', {})

    @property
    def gain(self) -> float:
        """Audio gain multiplier."""
        return float(self.attributes.get('gain', 1.0))

    @gain.setter
    def gain(self, value: float) -> None:
        """Set the audio gain multiplier."""
        self._data.setdefault('attributes', {})['gain'] = value

    @property
    def loudness_normalization(self) -> bool:
        """Whether loudness normalization is enabled."""
        return bool(self.attributes.get('loudnessNormalization', False))

    @loudness_normalization.setter
    def loudness_normalization(self, value: bool) -> None:
        """Set whether loudness normalization is enabled."""
        self._data.setdefault('attributes', {})['loudnessNormalization'] = value

    @property
    def is_muted(self) -> bool:
        """Whether the clip's gain is zero."""
        return self.gain == 0.0

    def normalize_gain(self) -> Self:
        """Enable loudness normalization on this clip.

        Camtasia uses LUFS for loudness normalization.  The target level
        is a project-level setting, not a per-clip value.

        Returns:
            self for chaining.
        """
        self._data.setdefault('attributes', {})['loudnessNormalization'] = True
        # targetLoudness is a project-level setting, not clip-level
        # Only set loudnessNormalization on the clip
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
