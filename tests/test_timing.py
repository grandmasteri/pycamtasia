from __future__ import annotations

from fractions import Fraction

from hypothesis import given, settings
from hypothesis import strategies as st
import pytest

from camtasia.timing import (
    EDIT_RATE,
    format_duration,
    parse_scalar,
    scalar_to_speed,
    scalar_to_string,
    seconds_to_ticks,
    speed_to_scalar,
    ticks_to_seconds,
)

# ------------------------------------------------------------------
# seconds_to_ticks / ticks_to_seconds round-trip
# ------------------------------------------------------------------

@pytest.mark.parametrize(
    ("seconds", "expected_ticks"),
    [
        (0.0, 0),
        (1.0, EDIT_RATE),
        (0.5, EDIT_RATE // 2),
        (2.5, round(2.5 * EDIT_RATE)),
    ],
    ids=["zero", "one-second", "half-second", "two-and-half"],
)
def test_seconds_to_ticks(seconds: float, expected_ticks: int) -> None:
    actual_ticks = seconds_to_ticks(seconds)
    assert actual_ticks == expected_ticks


@pytest.mark.parametrize(
    ("ticks", "expected_seconds"),
    [
        (0, 0.0),
        (EDIT_RATE, 1.0),
        (EDIT_RATE // 2, 0.5),
    ],
    ids=["zero", "one-second", "half-second"],
)
def test_ticks_to_seconds(ticks: int, expected_seconds: float) -> None:
    actual_seconds = ticks_to_seconds(ticks)
    assert actual_seconds == expected_seconds


@pytest.mark.parametrize(
    "seconds",
    [0.0, 1.0, 0.5, 2.5, 90.5, 0.001],
    ids=["zero", "one", "half", "two-half", "ninety-half", "milli"],
)
def test_round_trip(seconds: float) -> None:
    actual_seconds = ticks_to_seconds(seconds_to_ticks(seconds))
    assert actual_seconds == pytest.approx(seconds)


# ------------------------------------------------------------------
# format_duration
# ------------------------------------------------------------------

@pytest.mark.parametrize(
    ("ticks", "expected_formatted"),
    [
        (0, "0:00.00"),
        (seconds_to_ticks(90.5), "1:30.50"),
        (seconds_to_ticks(1.0), "0:01.00"),
        (seconds_to_ticks(59.99), "0:59.99"),
        (seconds_to_ticks(3600.0), "1:00:00.00"),
    ],
    ids=["zero", "ninety-half", "one-second", "just-under-minute", "one-hour"],
)
def test_format_duration(ticks: int, expected_formatted: str) -> None:
    actual_formatted = format_duration(ticks)
    assert actual_formatted == expected_formatted


# ------------------------------------------------------------------
# parse_scalar
# ------------------------------------------------------------------

@pytest.mark.parametrize(
    ("input_value", "expected_fraction"),
    [
        (1, Fraction(1)),
        (0.5, Fraction(1, 2)),
        ("51/101", Fraction(51, 101)),
        (Fraction(3, 4), Fraction(3, 4)),
    ],
    ids=["int", "float", "string-fraction", "fraction-passthrough"],
)
def test_parse_scalar(input_value: int | float | str | Fraction, expected_fraction: Fraction) -> None:
    actual_scalar = parse_scalar(input_value)
    assert actual_scalar == expected_fraction


# ------------------------------------------------------------------
# scalar_to_string
# ------------------------------------------------------------------

def test_scalar_to_string_returns_int_for_unity() -> None:
    actual_result = scalar_to_string(Fraction(1))
    assert actual_result == 1


def test_scalar_to_string_returns_fraction_string() -> None:
    actual_result = scalar_to_string(Fraction(51, 101))
    assert actual_result == "51/101"


# ------------------------------------------------------------------
# speed_to_scalar / scalar_to_speed
# ------------------------------------------------------------------

@pytest.mark.parametrize(
    ("speed", "expected_scalar"),
    [
        (1.0, Fraction(1)),
        (2.0, Fraction(1, 2)),
        (0.5, Fraction(2)),
    ],
    ids=["normal", "double", "half"],
)
def test_speed_to_scalar(speed: float, expected_scalar: Fraction) -> None:
    actual_scalar = speed_to_scalar(speed)
    assert actual_scalar == expected_scalar


@pytest.mark.parametrize(
    ("scalar", "expected_speed"),
    [
        (Fraction(1), 1.0),
        (Fraction(1, 2), 2.0),
        (Fraction(2), 0.5),
    ],
    ids=["normal", "double", "half"],
)
def test_scalar_to_speed(scalar: Fraction, expected_speed: float) -> None:
    actual_speed = scalar_to_speed(scalar)
    assert actual_speed == expected_speed


def test_speed_scalar_round_trip() -> None:
    """speed_to_scalar and scalar_to_speed are inverses."""
    original_speed = 2.0
    actual_speed = scalar_to_speed(speed_to_scalar(original_speed))
    assert actual_speed == original_speed


# ------------------------------------------------------------------
# Edge cases
# ------------------------------------------------------------------

def test_seconds_to_ticks_negative() -> None:
    actual_ticks = seconds_to_ticks(-1.0)
    assert actual_ticks == -EDIT_RATE


def test_seconds_to_ticks_very_large() -> None:
    actual_ticks = seconds_to_ticks(100_000.0)
    assert actual_ticks == round(100_000.0 * EDIT_RATE)


def test_parse_scalar_zero() -> None:
    actual_scalar = parse_scalar(0)
    assert actual_scalar == Fraction(0)


# ── Merged from test_coverage_misc.py ────────────────────────────────


class TestFormatDurationHours:
    def test_hours_format(self):
        result = format_duration(seconds_to_ticks(3661.5))
        assert result.startswith('1:01:01')

    def test_negative_duration(self):
        result = format_duration(-seconds_to_ticks(5.0))
        assert result.startswith('-')

    def test_centisecond_carry(self):
        result = format_duration(seconds_to_ticks(59.999))
        assert ':' in result



class TestParseScalarEdgeCases:
    def test_zero_division_string(self):
        with pytest.raises(ValueError, match='division by zero'):
            parse_scalar('1/0')




class TestSpeedScalarConversions:
    def test_speed_zero_raises(self):
        with pytest.raises(ValueError, match='zero'):
            speed_to_scalar(0)

    def test_speed_negative_raises(self):
        with pytest.raises(ValueError, match='negative'):
            speed_to_scalar(-1.0)

    def test_scalar_zero_raises(self):
        with pytest.raises(ValueError, match='zero'):
            scalar_to_speed(Fraction(0))

    def test_scalar_negative_raises(self):
        with pytest.raises(ValueError, match='negative'):
            scalar_to_speed(Fraction(-1))


# ------------------------------------------------------------------
# REV-test_gaps-001: Property-based timing roundtrip
# ------------------------------------------------------------------


@given(seconds=st.floats(min_value=0, max_value=86400, allow_nan=False, allow_infinity=False))
@settings(max_examples=200)
def test_seconds_roundtrip_property(seconds: float) -> None:
    """seconds_to_ticks(x) → ticks_to_seconds → should be within 1/EDIT_RATE of x."""
    ticks = seconds_to_ticks(seconds)
    recovered = ticks_to_seconds(ticks)
    assert abs(recovered - seconds) <= 1.0 / EDIT_RATE


@given(ticks=st.integers(min_value=0, max_value=86400 * EDIT_RATE))
@settings(max_examples=200)
def test_ticks_roundtrip_property(ticks: int) -> None:
    """ticks_to_seconds(t) → seconds_to_ticks should recover t exactly."""
    seconds = ticks_to_seconds(ticks)
    recovered = seconds_to_ticks(seconds)
    assert recovered == ticks


# REV-red_team-002: parse_scalar string DoS prevention


def test_parse_scalar_rejects_oversized_string_fraction() -> None:
    """Extremely long fraction strings are rejected as potential DoS.

    Regression for REV-red_team-002: parse_scalar previously accepted
    arbitrary-precision string fractions (e.g. "1/999...999" with 4000+
    digits) without bounds, enabling CPU-based DoS via slow Fraction
    arithmetic downstream.
    """
    import pytest

    from camtasia.timing import parse_scalar
    big = "1/" + "9" * 300
    with pytest.raises(ValueError, match="too long"):
        parse_scalar(big)


def test_parse_scalar_accepts_reasonable_string_fraction() -> None:
    """Normal-length string fractions still work."""
    from camtasia.timing import parse_scalar
    result = parse_scalar("2520000000/705600000")
    assert result is not None
