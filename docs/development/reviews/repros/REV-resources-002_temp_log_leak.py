#!/usr/bin/env python3
"""REV-resources-002: Temp log file leaked in app_validation.py.

camtasia_validate() creates a NamedTemporaryFile with delete=False, writes
the path to log_path, then reads it later — but never deletes the file.
Each call leaves a .log file in the system temp directory.

The file is created at line 48:
    with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as log_file:
        log_path = Path(log_file.name)

And read at line 61:
    log_output = log_path.read_text()

But log_path.unlink() is never called.
"""

import tempfile
from pathlib import Path

def demonstrate():
    print("=== Demonstrating temp file leak pattern ===")
    # This is what app_validation.py does:
    with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as log_file:
        log_path = Path(log_file.name)

    print(f"Created temp file: {log_path}")
    print(f"File exists: {log_path.exists()}")
    print(f"File will persist until manual cleanup or reboot.")

    # Cleanup our demo file
    log_path.unlink()
    print(f"(Demo file cleaned up)")

    print("\n--- Issue ---")
    print("app_validation.py never calls log_path.unlink() after reading.")
    print("Each camtasia_validate() call leaks one .log file in /tmp/.")

if __name__ == '__main__':
    demonstrate()
