#!/usr/bin/env python3
"""Repro for REV-user_docs-001: new_project() does not accept a `title` parameter.

Expected: TypeError at runtime because new_project() only accepts file_path.
"""
import tempfile
from pathlib import Path

from camtasia import new_project

with tempfile.TemporaryDirectory() as td:
    path = Path(td) / "test.cmproj"
    # This line from the cookbook will raise TypeError:
    # new_project("my-video.cmproj", title="My Video")
    try:
        new_project(path, title="My Video")  # type: ignore[call-arg]
        print("FAIL: no TypeError raised")
    except TypeError as e:
        print(f"PASS: TypeError raised as expected: {e}")
