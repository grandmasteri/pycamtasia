"""REV-typing-001: Public functions in shapes.py have no type annotations.

All three public factory functions (rectangle, ellipse, triangle) lack
parameter and return type annotations, making them invisible to type
checkers and breaking downstream typed code.

Repro: run `python -m mypy --strict` on this file or on shapes.py directly.
"""
from camtasia.annotations.shapes import rectangle

# mypy --strict reports: Function is missing a type annotation [no-untyped-def]
# for rectangle(), ellipse(), triangle()

# Downstream typed code cannot verify argument types:
result: dict[str, object] = rectangle(fill_color="not-a-color")  # no error raised by mypy
