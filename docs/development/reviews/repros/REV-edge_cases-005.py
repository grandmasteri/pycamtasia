"""REV-edge_cases-005: parse_scalar with edge case inputs."""
from camtasia.timing import parse_scalar, speed_to_scalar
from fractions import Fraction

# Empty string
try:
    result = parse_scalar("")
    print(f"UNEXPECTED: parse_scalar('') = {result}")
except (ValueError, ZeroDivisionError) as e:
    print(f"OK: parse_scalar('') -> {type(e).__name__}: {e}")

# String "0/0"
try:
    result = parse_scalar("0/0")
    print(f"UNEXPECTED: parse_scalar('0/0') = {result}")
except (ValueError, ZeroDivisionError) as e:
    print(f"OK: parse_scalar('0/0') -> {type(e).__name__}: {e}")

# String "1/0"
try:
    result = parse_scalar("1/0")
    print(f"UNEXPECTED: parse_scalar('1/0') = {result}")
except ValueError as e:
    print(f"OK: parse_scalar('1/0') -> ValueError: {e}")

# Negative scalar
result = parse_scalar("-1/2")
print(f"parse_scalar('-1/2') = {result}")

# Very small float near zero
result = parse_scalar(1e-15)
print(f"parse_scalar(1e-15) = {result}")

# NaN
import math
try:
    result = parse_scalar(math.nan)
    print(f"UNEXPECTED: parse_scalar(NaN) = {result}")
except (ValueError, Exception) as e:
    print(f"parse_scalar(NaN) -> {type(e).__name__}: {e}")

# Infinity
try:
    result = parse_scalar(math.inf)
    print(f"UNEXPECTED: parse_scalar(inf) = {result}")
except (ValueError, OverflowError, Exception) as e:
    print(f"parse_scalar(inf) -> {type(e).__name__}: {e}")

# speed_to_scalar with very small speed
try:
    result = speed_to_scalar(1e-300)
    print(f"speed_to_scalar(1e-300) = {result}")
except Exception as e:
    print(f"speed_to_scalar(1e-300) -> {type(e).__name__}: {e}")

# Non-numeric string
try:
    result = parse_scalar("hello")
    print(f"UNEXPECTED: parse_scalar('hello') = {result}")
except ValueError as e:
    print(f"OK: parse_scalar('hello') -> ValueError: {e}")
