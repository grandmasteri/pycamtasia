"""REV-fuzz-006: speed_to_scalar raises OverflowError instead of ValueError for inf.

speed_to_scalar validates zero and negative but not inf/NaN. Passing
float('inf') raises OverflowError from Fraction internals instead of
a clean ValueError. parse_scalar has the same issue with inf.
"""
from camtasia.timing import speed_to_scalar, parse_scalar

# speed_to_scalar: inf → OverflowError (should be ValueError)
for label, val in [("inf", float("inf")), ("-inf", float("-inf"))]:
    try:
        speed_to_scalar(val)
    except OverflowError as e:
        print(f"speed_to_scalar({label}): OverflowError: {e}")
    except ValueError as e:
        print(f"speed_to_scalar({label}): ValueError: {e}")

# parse_scalar: inf → OverflowError (should be ValueError)
for label, val in [("inf", float("inf")), ("-inf", float("-inf"))]:
    try:
        parse_scalar(val)
    except OverflowError as e:
        print(f"parse_scalar({label}): OverflowError: {e}")
    except ValueError as e:
        print(f"parse_scalar({label}): ValueError: {e}")
