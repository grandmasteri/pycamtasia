#!/usr/bin/env python3
"""REV-resources-001: subprocess.Popen without wait/kill in app_validation.py.

camtasia_validate() launches Camtasia via subprocess.Popen() but never calls
proc.wait(), proc.terminate(), or proc.kill() on the Popen object. It relies
on a subsequent `pkill -f Camtasia` to clean up, but:

1. The Popen object itself is leaked (Python's ResourceWarning).
2. If pkill fails (e.g., permission denied, race condition), the child
   process becomes orphaned.
3. The Popen object holds an open file descriptor for stderr_file.

Compare with integration_helpers.py which correctly calls proc.terminate()
and proc.wait(timeout=5) with a proc.kill() fallback.
"""

# Demonstration: show the code path
import ast
import textwrap
from pathlib import Path

SRC = Path(__file__).resolve().parents[4] / 'src' / 'camtasia' / 'app_validation.py'
HELPER = Path(__file__).resolve().parents[4] / 'tests' / 'integration_helpers.py'

def show_issue():
    print("=== app_validation.py: Popen WITHOUT wait/kill ===")
    lines = SRC.read_text().splitlines()
    for i, line in enumerate(lines, 1):
        if 'Popen' in line or 'pkill' in line or 'time.sleep' in line:
            print(f"  L{i}: {line.rstrip()}")

    print("\n=== integration_helpers.py: Popen WITH proper cleanup ===")
    lines = HELPER.read_text().splitlines()
    for i, line in enumerate(lines, 1):
        if any(kw in line for kw in ['Popen', 'terminate', 'wait', 'kill']):
            print(f"  L{i}: {line.rstrip()}")

    print("\n--- Issue ---")
    print("app_validation.py creates a Popen object but never stores it or")
    print("calls terminate/wait/kill. The process is only cleaned up via")
    print("pkill, which is unreliable. The Popen object leaks a file descriptor.")

if __name__ == '__main__':
    show_issue()
