#!/usr/bin/env python3
"""Create, save, and validate a new Camtasia project.

No external assets required — uses the bundled template.

Usage:
    python 00_hello_world.py
"""
from __future__ import annotations

import tempfile
from pathlib import Path

from camtasia import load_project, new_project


def main() -> None:
    with tempfile.TemporaryDirectory() as td:
        project_path = Path(td) / "hello.cmproj"
        new_project(project_path)
        project = load_project(project_path)
        project.save()

        issues = project.validate()
        errors = [i for i in issues if i.level == "error"]
        assert not errors, f"Validation errors: {errors}"

    print("✓ 00_hello_world: created, saved, and validated a project")


if __name__ == "__main__":
    main()
