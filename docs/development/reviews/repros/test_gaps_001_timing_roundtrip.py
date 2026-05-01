"""REV-test_gaps-001: Property-based test for ticks_to_seconds / seconds_to_ticks roundtrip.

The existing test uses only 4 parametrized values. A property-based test would
catch floating-point precision issues across the full domain.
"""
from hypothesis import given, settings
from hypothesis import strategies as st

from camtasia.timing import EDIT_RATE, seconds_to_ticks, ticks_to_seconds


@given(st.floats(min_value=0.0, max_value=86400.0, allow_nan=False, allow_infinity=False))
@settings(max_examples=500)
def test_seconds_roundtrip_property(seconds: float) -> None:
    """seconds_to_ticks(ticks_to_seconds(x)) should be close to identity."""
    ticks = seconds_to_ticks(seconds)
    recovered = ticks_to_seconds(ticks)
    # round() in seconds_to_ticks introduces at most 0.5 tick of error
    assert abs(recovered - seconds) < 1.0 / EDIT_RATE + 1e-12


@given(st.integers(min_value=0, max_value=86400 * EDIT_RATE))
@settings(max_examples=500)
def test_ticks_roundtrip_property(ticks: int) -> None:
    """ticks_to_seconds then seconds_to_ticks should recover the original ticks."""
    seconds = ticks_to_seconds(ticks)
    recovered = seconds_to_ticks(seconds)
    assert recovered == ticks
