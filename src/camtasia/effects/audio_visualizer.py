"""Audio visualizer effect — typed wrapper over Camtasia audio visualizer dict.

.. warning::
    **Unverified fixture.** The ``AudioVisualizer`` effect dict structure has
    not been validated against a real Camtasia project export.  The parameter
    names and layout are *plausible* extrapolations from existing audio-effect
    patterns.  Before relying on this in production, capture a real
    ``AudioVisualizer`` effect from Camtasia's JSON output and reconcile any
    differences.
"""
from __future__ import annotations

from camtasia.effects.base import Effect, register_effect


@register_effect('AudioVisualizer')
class AudioVisualizer(Effect):
    """Audio visualizer overlay effect.

    Renders a visual representation of the audio waveform on the timeline.

    .. warning::
        Unverified fixture — parameter names are extrapolated, not captured
        from a real Camtasia project.  See module docstring.

    Args:
        data: The raw effect dict from the project JSON.

    Parameters:
        type: Visualizer style (``'bars'``, ``'wave'``, ``'circular'``,
              ``'spectrum'``).
        color-red / color-green / color-blue / color-alpha: RGBA colour.
        height: Visualizer height in pixels.
        sensitivity: Audio sensitivity (0.0-1.0).
    """

    VALID_TYPES = frozenset({'bars', 'wave', 'circular', 'spectrum'})

    # -- type ----------------------------------------------------------

    @property
    def type(self) -> str:
        """Visualizer style (``'bars'``, ``'wave'``, ``'circular'``, ``'spectrum'``)."""
        return str(self.get_parameter('type'))

    @type.setter
    def type(self, value: str) -> None:
        if value not in self.VALID_TYPES:
            raise ValueError(
                f"Invalid visualizer type {value!r}; "
                f"expected one of {sorted(self.VALID_TYPES)}"
            )
        self.set_parameter('type', value)

    # -- color ---------------------------------------------------------

    @property
    def color(self) -> tuple[float, float, float, float]:
        """RGBA colour tuple."""
        return (
            float(self.get_parameter('color-red')),
            float(self.get_parameter('color-green')),
            float(self.get_parameter('color-blue')),
            float(self.get_parameter('color-alpha')),
        )

    @color.setter
    def color(self, value: tuple[float, float, float, float]) -> None:
        r, g, b, a = value
        self.set_parameter('color-red', r)
        self.set_parameter('color-green', g)
        self.set_parameter('color-blue', b)
        self.set_parameter('color-alpha', a)

    # -- height --------------------------------------------------------

    @property
    def height(self) -> float:
        """Visualizer height in pixels."""
        return float(self.get_parameter('height'))

    @height.setter
    def height(self, value: float) -> None:
        self.set_parameter('height', value)

    # -- sensitivity ---------------------------------------------------

    @property
    def sensitivity(self) -> float:
        """Audio sensitivity (0.0-1.0)."""
        return float(self.get_parameter('sensitivity'))

    @sensitivity.setter
    def sensitivity(self, value: float) -> None:
        self.set_parameter('sensitivity', value)
