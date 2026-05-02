"""Repro for REV-concurrency-002: Popen handle leaked in app_validation.py.

Demonstrates that subprocess.Popen() without storing the handle produces
a ResourceWarning (zombie process) and that pkill-based cleanup is racy.

Run: python -W all docs/development/reviews/repros/REV-concurrency-002.py
Expected: ResourceWarning about subprocess, demonstrating the leak.
"""
from __future__ import annotations

import subprocess
import warnings


def camtasia_validate_leak_demo() -> None:
    """Simulates the leak pattern from app_validation.py.

    The Popen object is created but never assigned to a variable,
    so it cannot be properly terminated/waited on.
    """
    # This mirrors the pattern in app_validation.py lines 51-53:
    #   subprocess.Popen(
    #       [str(camtasia_path), str(project_path)],
    #       stderr=stderr_file,
    #   )
    # Note: no variable captures the return value.

    # We use 'sleep 10' as a stand-in for Camtasia to avoid requiring
    # the actual application.
    proc = subprocess.Popen(
        ["sleep", "10"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # Simulate what app_validation.py does: drop the reference
    # In the real code, the Popen() return value is never assigned at all.
    # Here we explicitly delete to trigger the same ResourceWarning.
    del proc  # <-- triggers ResourceWarning: subprocess is still running

    # The real code then does:
    #   subprocess.run(['pkill', '-f', 'Camtasia'], ...)
    # which is racy and may kill unrelated processes.


def main() -> None:
    # Enable all warnings so ResourceWarning is visible
    warnings.simplefilter("always")

    print("Demonstrating Popen handle leak (expect ResourceWarning):")
    print("-" * 60)
    camtasia_validate_leak_demo()

    # Clean up the orphaned sleep process
    import time
    time.sleep(0.5)
    subprocess.run(["pkill", "-f", "sleep 10"], capture_output=True)

    print("-" * 60)
    print(
        "If you see 'ResourceWarning: subprocess ... is still running',\n"
        "that confirms the leak. The process was orphaned because the\n"
        "Popen handle was never stored or waited on."
    )


if __name__ == "__main__":
    main()
