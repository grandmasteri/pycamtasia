"""REV-edge_cases-004: hex_rgb with non-hex characters, empty string, unicode."""
from camtasia.color import hex_rgb, RGBA

# Empty string after stripping #
try:
    result = hex_rgb("#")
    print(f"UNEXPECTED: hex_rgb('#') = {result}")
except ValueError as e:
    print(f"OK: hex_rgb('#') -> ValueError: {e}")

# Empty string
try:
    result = hex_rgb("")
    print(f"UNEXPECTED: hex_rgb('') = {result}")
except ValueError as e:
    print(f"OK: hex_rgb('') -> ValueError: {e}")

# Non-hex characters
try:
    result = hex_rgb("#GGHHII")
    print(f"UNEXPECTED: hex_rgb('#GGHHII') = {result}")
except ValueError as e:
    print(f"OK: hex_rgb('#GGHHII') -> ValueError: {e}")

# 5-digit hex (invalid length)
try:
    result = hex_rgb("#12345")
    print(f"UNEXPECTED: hex_rgb('#12345') = {result}")
except ValueError as e:
    print(f"OK: hex_rgb('#12345') -> ValueError: {e}")

# Unicode characters that look like hex
try:
    result = hex_rgb("#\uff10\uff10\uff10\uff10\uff10\uff10")  # fullwidth 0s
    print(f"UNEXPECTED: hex_rgb with fullwidth digits = {result}")
except (ValueError, Exception) as e:
    print(f"OK: hex_rgb with fullwidth digits -> {type(e).__name__}: {e}")

# RGBA.from_floats with NaN
import math
try:
    result = RGBA.from_floats(math.nan, 0.0, 0.0, 1.0)
    print(f"UNEXPECTED: RGBA.from_floats(NaN, ...) = {result}")
except (ValueError, TypeError) as e:
    print(f"OK: RGBA.from_floats(NaN, ...) -> {type(e).__name__}: {e}")

# RGBA.from_floats with inf
try:
    result = RGBA.from_floats(math.inf, 0.0, 0.0, 1.0)
    print(f"RGBA.from_floats(inf, ...) = {result}")
    print(f"  red={result.red}")  # Should be clamped to 255
except Exception as e:
    print(f"RGBA.from_floats(inf, ...) -> {type(e).__name__}: {e}")

# RGBA.from_floats with negative infinity
try:
    result = RGBA.from_floats(-math.inf, 0.0, 0.0, 1.0)
    print(f"RGBA.from_floats(-inf, ...) = {result}")
    print(f"  red={result.red}")  # Should be clamped to 0
except Exception as e:
    print(f"RGBA.from_floats(-inf, ...) -> {type(e).__name__}: {e}")
