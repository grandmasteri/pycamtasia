#!/usr/bin/env python3
"""Load a fixture project and print summary statistics and a markdown report.

Usage:
    python 01_inspect_project.py
"""
from __future__ import annotations

from pathlib import Path

from camtasia import load_project

FIXTURE = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "test_project_a.tscproj"


def main() -> None:
    project = load_project(FIXTURE)

    stats = project.statistics()
    print("=== Project Statistics ===")
    for key, value in stats.items():
        print(f"  {key}: {value}")

    print()
    print(project.to_markdown_report())

    print("✓ 01_inspect_project: loaded fixture and printed report")


if __name__ == "__main__":
    main()
