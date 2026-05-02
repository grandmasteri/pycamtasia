"""REV-edge_cases-009: RGBA.from_floats crashes with inf instead of clamping."""
import math
from camtasia.color import RGBA

# Positive infinity - should clamp to 255 but raises OverflowError
try:
    result = RGBA.from_floats(math.inf, 0.5, 0.5, 1.0)
    print(f"UNEXPECTED: from_floats(inf, ...) = {result}")
except OverflowError as e:
    print(f"CONFIRMED: RGBA.from_floats(inf, 0.5, 0.5, 1.0) -> OverflowError: {e}")

# Negative infinity - should clamp to 0 but raises OverflowError
try:
    result = RGBA.from_floats(-math.inf, 0.5, 0.5, 1.0)
    print(f"UNEXPECTED: from_floats(-inf, ...) = {result}")
except OverflowError as e:
    print(f"CONFIRMED: RGBA.from_floats(-inf, 0.5, 0.5, 1.0) -> OverflowError: {e}")

# NaN - round(NaN * 255) raises ValueError
try:
    result = RGBA.from_floats(math.nan, 0.5, 0.5, 1.0)
    print(f"UNEXPECTED: from_floats(NaN, ...) = {result}")
except ValueError as e:
    print(f"CONFIRMED: RGBA.from_floats(NaN, 0.5, 0.5, 1.0) -> ValueError: {e}")

# The _clamp function uses max(0, min(255, round(channel * 255)))
# but round(inf * 255) overflows before max/min can clamp it
print("\nRoot cause: _clamp does round() before max/min, but round(inf*255) overflows")
print("Fix: check for inf/nan before round(), or use try/except in _clamp")
