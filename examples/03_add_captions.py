#!/usr/bin/env python3
"""Load a fixture, add captions on a Subtitles track, save, and export as SRT.

Usage:
    python 03_add_captions.py
"""
from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from camtasia import load_project
from camtasia.export import export_captions_srt

FIXTURE = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "test_project_a.tscproj"


def main() -> None:
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)

        # Copy fixture into a .cmproj bundle so we can save
        bundle = td_path / "captions_demo.cmproj"
        bundle.mkdir()
        shutil.copy2(FIXTURE, bundle / "project.tscproj")

        project = load_project(bundle)

        # Add 3 captions
        project.add_caption("Hello, world!", 0.0, 3.0)
        project.add_caption("This is pycamtasia.", 3.5, 3.0)
        project.add_caption("Goodbye!", 7.0, 2.0)
        project.save()

        # Export as SRT
        srt_path = td_path / "captions.srt"
        export_captions_srt(project, srt_path)

        srt_text = srt_path.read_text()
        assert "Hello, world!" in srt_text
        assert "Goodbye!" in srt_text

    print("✓ 03_add_captions: added 3 captions and exported SRT")


if __name__ == "__main__":
    main()
