"""Audio effects — typed wrappers over Camtasia audio effect dicts."""
from __future__ import annotations

from camtasia.effects.base import Effect, register_effect


@register_effect("VSTEffect-DFN3NoiseRemoval")
class NoiseRemoval(Effect):
    """DFN3 noise-removal VST effect.

    Parameters:
        amount: noise-removal strength (0.0 = no removal, 1.0 = max)
        bypassed: 1 to disable the effect at default keyframe
        sensitivity: detection sensitivity (0.0-1.0)
        reduction: noise reduction level (0.0-1.0)
    """

    @property
    def amount(self) -> float:
        """Noise-removal strength (0.0-1.0)."""
        return float(self.get_parameter("Amount"))

    @amount.setter
    def amount(self, value: float) -> None:
        self.set_parameter("Amount", value)

    @property
    def bypass(self) -> float:
        """Bypass flag (0 = active, 1 = bypassed)."""
        return float(self.get_parameter("Bypass"))

    @bypass.setter
    def bypass(self, value: float) -> None:
        self.set_parameter("Bypass", value)

    @property
    def sensitivity(self) -> float:
        """Detection sensitivity (0.0-1.0)."""
        return float(self.get_parameter("Sensitivity"))

    @sensitivity.setter
    def sensitivity(self, value: float) -> None:
        self.set_parameter("Sensitivity", value)

    @property
    def reduction(self) -> float:
        """Noise reduction level (0.0-1.0)."""
        return float(self.get_parameter("Reduction"))

    @reduction.setter
    def reduction(self, value: float) -> None:
        self.set_parameter("Reduction", value)


@register_effect("AudioCompression")
class AudioCompression(Effect):
    """Audio dynamic range compression effect.

    Parameters:
        ratio: compression ratio
        threshold: threshold level in dB
        gain: output gain in dB
        volumeVariation: volume variation amount
    """

    @property
    def ratio(self) -> float:
        """Compression ratio."""
        return float(self.get_parameter("ratio"))

    @ratio.setter
    def ratio(self, value: float) -> None:
        self.set_parameter("ratio", value)

    @property
    def threshold(self) -> float:
        """Threshold level in dB."""
        return float(self.get_parameter("threshold"))

    @threshold.setter
    def threshold(self, value: float) -> None:
        self.set_parameter("threshold", value)

    @property
    def gain(self) -> float:
        """Output gain in dB."""
        return float(self.get_parameter("gain"))

    @gain.setter
    def gain(self, value: float) -> None:
        self.set_parameter("gain", value)

    @property
    def volume_variation(self) -> float:
        """Volume variation amount."""
        return float(self.get_parameter("volumeVariation"))

    @volume_variation.setter
    def volume_variation(self, value: float) -> None:
        self.set_parameter("volumeVariation", value)


@register_effect("Pitch")
class Pitch(Effect):
    """Audio pitch shift effect.

    .. note::
        This effect is only available on macOS versions of Camtasia.

    Parameters:
        pitch: pitch shift amount (semitones)
        easeIn: ease-in duration
        easeOut: ease-out duration
    """

    @property
    def pitch(self) -> float:
        """Pitch shift amount (semitones)."""
        return float(self.get_parameter("pitch"))

    @pitch.setter
    def pitch(self, value: float) -> None:
        self.set_parameter("pitch", value)

    @property
    def ease_in(self) -> float:
        """Ease-in duration."""
        return float(self.get_parameter("easeIn"))

    @ease_in.setter
    def ease_in(self, value: float) -> None:
        self.set_parameter("easeIn", value)

    @property
    def ease_out(self) -> float:
        """Ease-out duration."""
        return float(self.get_parameter("easeOut"))

    @ease_out.setter
    def ease_out(self, value: float) -> None:
        self.set_parameter("easeOut", value)


@register_effect("ClipSpeedAudio")
class ClipSpeedAudio(Effect):
    """Audio clip speed effect.

    Registered as ``ClipSpeedAudio`` to avoid registry collision with a
    potential video ``ClipSpeed`` effect (the registry is a plain dict and
    does not support duplicate keys).

    Parameters:
        speed: playback speed multiplier
        duration: effect duration in ticks
    """

    @property
    def speed(self) -> float:
        """Playback speed multiplier."""
        return float(self.get_parameter("speed"))

    @speed.setter
    def speed(self, value: float) -> None:
        self.set_parameter("speed", value)

    @property
    def effect_duration(self) -> float:
        """Effect duration in ticks."""
        return float(self.get_parameter("duration"))

    @effect_duration.setter
    def effect_duration(self, value: float) -> None:
        self.set_parameter("duration", value)
