"""REV-edge_cases-001: format_duration with boundary tick values."""
from camtasia.timing import format_duration, EDIT_RATE

# Zero ticks
assert format_duration(0) == "0:00.00", f"Got {format_duration(0)}"

# Exactly one second
assert format_duration(EDIT_RATE) == "0:01.00", f"Got {format_duration(EDIT_RATE)}"

# Negative ticks
result = format_duration(-EDIT_RATE)
assert result.startswith('-'), f"Negative ticks should produce negative sign, got {result!r}"

# Very large ticks (overflow check) - 1 million hours
huge = EDIT_RATE * 3_600_000_000
try:
    r = format_duration(huge)
    print(f"Huge ticks: {r}")
except Exception as e:
    print(f"FAIL: format_duration with huge ticks raised {type(e).__name__}: {e}")

# Centisecond rounding boundary: 0.995 seconds -> cs rounds to 100, should carry
boundary_ticks = round(0.995 * EDIT_RATE)
r = format_duration(boundary_ticks)
print(f"0.995s boundary: {r}")
# Should be "0:01.00" (carry) not "0:00.100"
assert ".100" not in r, f"Centisecond overflow not handled: {r}"

# Float precision: 59.999... seconds
almost_60 = round(59.999 * EDIT_RATE)
r = format_duration(almost_60)
print(f"59.999s: {r}")

print("PASS: format_duration boundary tests")
