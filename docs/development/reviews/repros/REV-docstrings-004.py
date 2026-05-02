"""Repro: Effect.duration return type annotation says float | None but
docstring says 'in ticks' — ticks are integers in this codebase.

The actual value from _data.get('duration') is typically int (ticks).
The type annotation should be int | None to match the docstring's 'ticks' claim.
"""
import inspect
from camtasia.effects.base import Effect

hints = Effect.duration.fget.__annotations__
print(f"Return annotation: {hints.get('return', 'not found')}")
# Shows: float | None

doc = Effect.duration.fget.__doc__
print(f"Docstring: {doc}")
# Shows: Effect duration in ticks, or ``None`` if not time-bounded.

# Ticks are integers (EDIT_RATE = 705600000 per second)
# The return type says float but the docstring says ticks
print("CONFIRMED: type annotation (float) disagrees with docstring (ticks = int)")
