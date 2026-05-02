"""REV-edge_cases-012: seconds_to_ticks with NaN, inf, and huge values."""
import math
from camtasia.timing import seconds_to_ticks, ticks_to_seconds, EDIT_RATE

# NaN
try:
    result = seconds_to_ticks(math.nan)
    print(f"UNEXPECTED: seconds_to_ticks(NaN) = {result}")
except (ValueError, Exception) as e:
    print(f"seconds_to_ticks(NaN) -> {type(e).__name__}: {e}")

# Infinity
try:
    result = seconds_to_ticks(math.inf)
    print(f"UNEXPECTED: seconds_to_ticks(inf) = {result}")
except (OverflowError, ValueError, Exception) as e:
    print(f"seconds_to_ticks(inf) -> {type(e).__name__}: {e}")

# Negative infinity
try:
    result = seconds_to_ticks(-math.inf)
    print(f"UNEXPECTED: seconds_to_ticks(-inf) = {result}")
except (OverflowError, ValueError, Exception) as e:
    print(f"seconds_to_ticks(-inf) -> {type(e).__name__}: {e}")

# Very large value that overflows int
try:
    result = seconds_to_ticks(1e300)
    print(f"seconds_to_ticks(1e300) = {result}")
    print(f"  type: {type(result)}")
except (OverflowError, Exception) as e:
    print(f"seconds_to_ticks(1e300) -> {type(e).__name__}: {e}")

# Negative seconds (valid for offsets)
result = seconds_to_ticks(-1.0)
print(f"seconds_to_ticks(-1.0) = {result}")
rt = ticks_to_seconds(result)
print(f"  roundtrip: {rt}")
