#!/usr/bin/env python3
"""REV-resources-003: tempfile.mkdtemp() without cleanup in ~30 test locations.

Multiple test files use tempfile.mkdtemp() to create temporary directories
but never clean them up with shutil.rmtree(). Each test run accumulates
orphaned directories containing .cmproj bundles in the system temp dir.

Affected files (non-exhaustive):
- test_caption_accessibility.py (5 locations)
- test_themes.py (5 locations)
- test_invariants_property.py (4 locations)
- test_themes_extended.py (3 locations)
- test_captions_export.py (2 locations)
- test_timeline_operations.py (2 locations)
- test_invariants.py (1 location)
- test_slide_import.py (1 location)
- test_device_frame.py (1 location)
- test_captions_import_export.py (1 location)
- test_export_campackage.py (1 location)
- test_slide_import_extended.py (1 location)

These tests should use pytest's tmp_path fixture (which auto-cleans)
or tempfile.TemporaryDirectory() context manager instead.
"""

import os
import tempfile
from pathlib import Path

def demonstrate():
    print("=== Demonstrating mkdtemp leak ===")
    # This is the pattern used in ~30 test locations:
    td = tempfile.mkdtemp()
    print(f"Created: {td}")
    print(f"Exists: {Path(td).exists()}")
    print("No cleanup code follows in the test functions.")

    # Count how many orphaned dirs might exist
    tmp_root = Path(tempfile.gettempdir())
    orphans = list(tmp_root.glob('tmp*'))
    print(f"\nCurrent temp dirs in {tmp_root}: {len(orphans)}")

    # Clean up our demo
    os.rmdir(td)

    print("\n--- Fix ---")
    print("Replace: tmp = Path(tempfile.mkdtemp()) / 'test.cmproj'")
    print("With:    pytest's tmp_path fixture or tempfile.TemporaryDirectory()")

if __name__ == '__main__':
    demonstrate()
