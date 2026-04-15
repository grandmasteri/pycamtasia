"""Color utilities for Camtasia projects."""

from __future__ import annotations


def hex_rgb(argument: str) -> tuple[int, ...]:
    """Convert the argument string to a tuple of integers.
    """
    h = argument.lstrip("#")
    num_digits = len(h)
    if num_digits == 3:
        return (
            int(h[0], 16),
            int(h[1], 16),
            int(h[2], 16),
        )
    elif num_digits == 4:
        return (
            int(h[0], 16),
            int(h[1], 16),
            int(h[2], 16),
            int(h[3], 16),
        )
    elif num_digits == 6:
        return (
            int(h[0:2], 16),
            int(h[2:4], 16),
            int(h[4:6], 16),
        )
    elif num_digits == 8:
        return (
            int(h[0:2], 16),
            int(h[2:4], 16),
            int(h[4:6], 16),
            int(h[6:8], 16),
        )
    else:
        raise ValueError(f"Could not interpret {argument!r} as RGB or RGBA hex color")


class RGBA:
    """RGBA color value with channel range 0–255."""

    MINIMUM_CHANNEL: int = 0
    MAXIMUM_CHANNEL: int = 255

    @classmethod
    def from_hex(cls, color: str) -> RGBA:
        """Create an RGBA instance from a hex color string."""
        channels = hex_rgb(color)
        if len(channels) == 3:
            return cls(*channels, alpha=cls.MAXIMUM_CHANNEL)
        return cls(*channels)

    @classmethod
    def from_floats(cls, red: float, green: float, blue: float, alpha: float) -> RGBA:
        """Create an RGBA instance from 0.0–1.0 float channel values."""
        return cls(
            round(red * cls.MAXIMUM_CHANNEL),
            round(green * cls.MAXIMUM_CHANNEL),
            round(blue * cls.MAXIMUM_CHANNEL),
            round(alpha * cls.MAXIMUM_CHANNEL),
        )

    def __init__(self, red: int, green: int, blue: int, alpha: int) -> None:
        if not (self.MINIMUM_CHANNEL <= red <= self.MAXIMUM_CHANNEL):
            raise ValueError(
                f"RGBA red channel {red} out of range {self.MINIMUM_CHANNEL} "
                f"to {self.MAXIMUM_CHANNEL}"
            )

        if not (self.MINIMUM_CHANNEL <= green <= self.MAXIMUM_CHANNEL):
            raise ValueError(
                f"RGBA green channel {green} out of range {self.MINIMUM_CHANNEL} "
                f"to {self.MAXIMUM_CHANNEL}"
            )

        if not (self.MINIMUM_CHANNEL <= blue <= self.MAXIMUM_CHANNEL):
            raise ValueError(
                f"RGBA blue channel {blue} out of range {self.MINIMUM_CHANNEL} "
                f"to {self.MAXIMUM_CHANNEL}"
            )

        if not (self.MINIMUM_CHANNEL <= alpha <= self.MAXIMUM_CHANNEL):
            raise ValueError(
                f"RGBA alpha channel {alpha} out of range {self.MINIMUM_CHANNEL} "
                f"to {self.MAXIMUM_CHANNEL}"
            )

        self._red = red
        self._green = green
        self._blue = blue
        self._alpha = alpha

    @property
    def red(self) -> int:
        """Red channel value (0–255)."""
        return self._red

    @property
    def green(self) -> int:
        """Green channel value (0–255)."""
        return self._green

    @property
    def blue(self) -> int:
        """Blue channel value (0–255)."""
        return self._blue

    @property
    def alpha(self) -> int:
        """Alpha channel value (0–255)."""
        return self._alpha

    def as_tuple(self) -> tuple[int, int, int, int]:
        """Return the color as an ``(red, green, blue, alpha)`` tuple."""
        return (self.red, self.green, self.blue, self.alpha)

    def _key(self) -> tuple[int, int, int, int]:
        return self.as_tuple()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, type(self)):
            return NotImplemented
        return self._key() == other._key()

    def __hash__(self) -> int:
        return hash(self._key())

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(red={self.red}, green={self.green}, "
            f"blue={self.blue}, alpha={self.alpha})"
        )
