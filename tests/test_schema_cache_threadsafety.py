"""Test for REV-concurrency-001: _get_schema() must be thread-safe."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, wait
import threading

from camtasia import validation


def test_get_schema_concurrent_calls_return_same_object():
    """Multiple threads calling _get_schema() must all get the same dict."""
    # Clear any cached result so threads race on a cold cache.
    validation._CACHED_SCHEMA = None

    barrier = threading.Barrier(8)
    results: list[int] = []

    def _call() -> None:
        barrier.wait(timeout=5)
        schema = validation._get_schema()
        results.append(id(schema))

    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = [pool.submit(_call) for _ in range(8)]
        wait(futures, timeout=10)
        for f in futures:
            f.result()  # propagate exceptions

    # All threads must have received the exact same object.
    assert len(set(results)) == 1, (
        f"Expected 1 unique schema object, got {len(set(results))}"
    )
