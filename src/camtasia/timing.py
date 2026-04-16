"""Camtasia timing system: tick conversions, rational scalars, and duration formatting.

Camtasia uses an editRate of 705,600,000 ticks per second — chosen to be evenly
divisible by common frame rates (30, 60 fps) and audio sample rates (44100, 48000 Hz).
"""

from __future__ import annotations

from fractions import Fraction

EDIT_RATE: int = 705_600_000
"""Ticks per second in Camtasia's timing system."""


def seconds_to_ticks(seconds: float) -> int:
    """Convert seconds to editRate ticks.

    Args:
        seconds: Duration in seconds.

    Returns:
        Integer tick count.
    """
    return round(seconds * EDIT_RATE)


def ticks_to_seconds(ticks: int) -> float:
    """Convert editRate ticks to seconds.

    Args:
        ticks: Tick count.

    Returns:
        Duration in seconds.
    """
    return ticks / EDIT_RATE


def format_duration(ticks: int) -> str:
    """Format a tick duration as 'M:SS.ff'.

    Args:
        ticks: Duration in editRate ticks.

    Returns:
        Formatted string like '2:15.30'.
    """
    total_seconds = ticks / EDIT_RATE
    sign = '-' if total_seconds < 0 else ''
    abs_seconds = abs(total_seconds)
    int_seconds = int(abs_seconds)
    fraction = abs_seconds - int_seconds
    cs = round(fraction * 100)
    if cs >= 100:
        cs = 0
        int_seconds += 1
    hours = int_seconds // 3600
    minutes = int_seconds % 3600 // 60
    seconds = int_seconds % 60
    if hours > 0:
        return f"{sign}{hours}:{minutes:02d}:{seconds:02d}.{cs:02d}"
    return f"{sign}{minutes}:{seconds:02d}.{cs:02d}"


def parse_scalar(value: int | float | str | Fraction) -> Fraction:
    """Parse a scalar value from Camtasia JSON into a Fraction.

    Camtasia stores speed scalars as integers (1), floats, or string
    fractions ('51/101').

    Args:
        value: Scalar as int, float, string fraction, or Fraction.

    Returns:
        Exact rational representation.
    """
    if isinstance(value, Fraction):
        return value
    if isinstance(value, str):
        try:
            return Fraction(value)
        except ZeroDivisionError:
            raise ValueError('Invalid scalar: division by zero')
    return Fraction(value).limit_denominator(10_000)


def scalar_to_string(scalar: Fraction) -> str | int:
    """Format a scalar Fraction for Camtasia JSON serialization.

    Args:
        scalar: Rational scalar value.

    Returns:
        Integer 1 if the scalar is exactly 1, otherwise 'numerator/denominator'.
    """
    if scalar == 1:
        return 1
    return f"{scalar.numerator}/{scalar.denominator}"


def speed_to_scalar(speed: float) -> Fraction:
    """Convert a human-readable speed multiplier to a Camtasia scalar.

    A scalar represents timeline_duration / source_duration. Faster playback
    (speed > 1) means less timeline per source, so scalar = 1/speed.

    Args:
        speed: Human speed multiplier (e.g. 2.0 for 2x playback).

    Returns:
        Rational scalar for Camtasia JSON.

    Raises:
        ValueError: If speed is zero.
    """
    if speed == 0:
        raise ValueError('Speed cannot be zero')
    if speed < 0:
        raise ValueError('Speed cannot be negative')
    return Fraction(1, 1) / Fraction(speed).limit_denominator(10_000)


def scalar_to_speed(scalar: Fraction) -> float:
    """Convert a Camtasia scalar to a human-readable speed multiplier.

    Args:
        scalar: Rational scalar from Camtasia JSON.

    Returns:
        Speed multiplier (e.g. 2.0 for 2x playback).

    Raises:
        ValueError: If scalar is zero.
    """
    if scalar == 0:
        raise ValueError('Scalar cannot be zero')
    if scalar < 0:
        raise ValueError('Scalar cannot be negative')
    return float(Fraction(1, 1) / scalar)
