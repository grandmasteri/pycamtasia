"""REV-edge_cases-010: speed_to_scalar with very small float raises ZeroDivisionError."""
from camtasia.timing import speed_to_scalar
from fractions import Fraction

# Very small float that limit_denominator rounds to 0
# Fraction(1e-300).limit_denominator(10_000) == Fraction(0, 1)
small = 1e-300
frac = Fraction(small).limit_denominator(10_000)
print(f"Fraction({small}).limit_denominator(10_000) = {frac}")

try:
    result = speed_to_scalar(small)
    print(f"UNEXPECTED: speed_to_scalar({small}) = {result}")
except ZeroDivisionError as e:
    print(f"CONFIRMED: speed_to_scalar({small}) -> ZeroDivisionError: {e}")
    print("Root cause: speed > 0 check passes, but limit_denominator rounds to 0/1")
    print("Then Fraction(1,1) / Fraction(0,1) raises ZeroDivisionError")

# Also test with a slightly larger value that still rounds to 0
small2 = 1e-10
frac2 = Fraction(small2).limit_denominator(10_000)
print(f"\nFraction({small2}).limit_denominator(10_000) = {frac2}")
try:
    result = speed_to_scalar(small2)
    print(f"speed_to_scalar({small2}) = {result}")
except ZeroDivisionError as e:
    print(f"CONFIRMED: speed_to_scalar({small2}) -> ZeroDivisionError")

# Threshold: what's the smallest speed that works?
for exp in range(-1, -20, -1):
    val = 10.0 ** exp
    frac = Fraction(val).limit_denominator(10_000)
    if frac == 0:
        print(f"\nFirst zero: 10^{exp} = {val}, Fraction = {frac}")
        break
