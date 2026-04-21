"""Audio effects — typed wrappers over Camtasia audio effect dicts."""
from __future__ import annotations

from camtasia.effects.base import Effect, register_effect


@register_effect("VSTEffect-DFN3NoiseRemoval")
class NoiseRemoval(Effect):
    """DFN3 noise-removal VST effect.

    Parameters:
        amount: noise-removal strength (0.0 = no removal, 1.0 = max)
        bypassed: 1 to disable the effect at default keyframe
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
