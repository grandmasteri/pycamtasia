"""REV-fuzz-010: parse_scalar leaks OverflowError for inf inputs.

parse_scalar(float('inf')) raises OverflowError from Fraction internals
instead of ValueError. Callers catching ValueError (the documented
exception) will miss this. Same for float('-inf').
"""
from camtasia.timing import parse_scalar

for val in [float("inf"), float("-inf")]:
    try:
        parse_scalar(val)
    except OverflowError as e:
        print(f"parse_scalar({val}): OverflowError (should be ValueError): {e}")
    except ValueError:
        print(f"parse_scalar({val}): ValueError (correct)")
