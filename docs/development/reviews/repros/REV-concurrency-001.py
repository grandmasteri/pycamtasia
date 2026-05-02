"""Repro for REV-concurrency-001: _CACHED_SCHEMA race condition.

Demonstrates that two threads can both enter the `if _CACHED_SCHEMA is None`
branch simultaneously, causing redundant schema loads. While the final value
is correct in CPython (GIL prevents dict corruption), the double-load is
observable and the pattern is unsafe on nogil/PyPy STM.

Run: python docs/development/reviews/repros/REV-concurrency-001.py
Expected: "RACE DETECTED" printed if both threads enter the None branch.
"""
from __future__ import annotations

import threading
import time
from unittest.mock import patch

# Simulate the pattern from validation.py
_CACHED_SCHEMA: dict | None = None
_load_count = 0
_load_count_lock = threading.Lock()
_barrier = threading.Barrier(2)


def _get_schema_racy() -> dict:
    """Reproduction of the racy _get_schema() pattern."""
    global _CACHED_SCHEMA, _load_count

    if _CACHED_SCHEMA is None:
        # Both threads can reach here before either assigns
        _barrier.wait(timeout=2)  # Force both threads into the branch
        time.sleep(0.01)  # Simulate I/O delay of reading schema file

        with _load_count_lock:
            _load_count += 1

        _CACHED_SCHEMA = {"type": "object"}  # Simulated schema

    return _CACHED_SCHEMA


def main() -> None:
    global _CACHED_SCHEMA, _load_count
    _CACHED_SCHEMA = None
    _load_count = 0

    threads = [threading.Thread(target=_get_schema_racy) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=5)

    if _load_count > 1:
        print(f"RACE DETECTED: schema loaded {_load_count} times (expected 1)")
    else:
        print(f"No race observed this run (loaded {_load_count} time)")
        print("Note: race is timing-dependent; barrier forces it in this repro")


if __name__ == "__main__":
    main()
