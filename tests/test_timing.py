from __future__ import annotations

from fractions import Fraction

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
    "seconds, expected_ticks",
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
    "ticks, expected_seconds",
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
    "ticks, expected_formatted",
    [
        (0, "0:00.00"),
        (seconds_to_ticks(90.5), "1:30.50"),
        (seconds_to_ticks(1.0), "0:01.00"),
        (seconds_to_ticks(59.99), "0:59.99"),
        (seconds_to_ticks(3600.0), "60:00.00"),
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
    "input_value, expected_fraction",
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
    "speed, expected_scalar",
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
    "scalar, expected_speed",
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
