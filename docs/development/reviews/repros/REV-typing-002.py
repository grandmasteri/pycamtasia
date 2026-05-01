"""REV-typing-002: Public functions text() and square() in callouts.py have no type annotations.

These are high-level public API functions used to create callout annotations.
Without annotations, mypy cannot check callers and IDE autocompletion is degraded.

Repro: run `python -m mypy --strict` on callouts.py.
"""
from camtasia.annotations.callouts import text, square

# mypy --strict reports: Function is missing a type annotation [no-untyped-def]
# for text() at line 113 and square() at line 175

# Downstream typed code gets no checking:
result: dict[str, object] = text(123, 456, 789)  # wrong types, no mypy error
