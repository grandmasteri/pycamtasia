"""REV-red_team-002: parse_scalar string fractions bypass limit_denominator.

parse_scalar() applies limit_denominator(10_000) to float inputs but
passes string fractions directly to Fraction() without any cap. A
crafted scalar like "1/999...999" (4000 digits, under Python's 4300
int-string limit) creates an arbitrarily large Fraction.
"""
from camtasia.timing import parse_scalar, scalar_to_string

# Use 4000 digits — under Python 3.12's 4300-digit int-string limit
big_denom = "9" * 4000
adversarial_scalar = f"1/{big_denom}"

result = parse_scalar(adversarial_scalar)
denom_digits = len(str(result.denominator))
print(f"Denominator digits: {denom_digits}")
print(f"Expected (if limit_denominator applied): ≤4 digits")
print(f"Actual: {denom_digits} digits")

serialized = scalar_to_string(result)
print(f"Serialized length: {len(str(serialized))} chars")
print()
if denom_digits > 5:
    print("CONFIRMED: String fractions bypass limit_denominator cap")
else:
    print("NOT CONFIRMED")
