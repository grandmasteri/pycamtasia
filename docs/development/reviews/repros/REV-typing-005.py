"""REV-typing-005: `with_undo` decorator return type is bare `Callable`.

history.py:215 declares `-> Callable` without type arguments. This erases
the decorated function's signature for callers, defeating type checking.

Repro: run `python -m mypy --strict src/camtasia/history.py`.
"""
from typing import Callable

# The current signature:
#   def with_undo(description: str) -> Callable:
#
# Should be:
#   def with_undo(description: str) -> Callable[[Callable[..., T]], Callable[..., T]]:
#
# or use ParamSpec for full signature preservation.
