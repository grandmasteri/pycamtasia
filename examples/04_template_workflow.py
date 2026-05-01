#!/usr/bin/env python3
"""Save a project as a template, instantiate a new project from it, and verify.

Usage:
    python 04_template_workflow.py
"""
from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from camtasia import load_project
from camtasia.operations.template import new_from_template, save_as_template

FIXTURE = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "test_project_a.tscproj"


def main() -> None:
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)

        # Create a source project with a placeholder
        bundle = td_path / "source.cmproj"
        bundle.mkdir()
        shutil.copy2(FIXTURE, bundle / "project.tscproj")
        source = load_project(bundle)

        track = source.timeline.get_or_create_track("Placeholders")
        track.add_placeholder(0.0, 5.0, title="Intro Shot", note="Replace me")
        source.save()

        # Save as template
        template_path = td_path / "demo.camtemplate"
        save_as_template(source, "Demo Template", template_path)
        assert template_path.exists()

        # Instantiate new project from template
        new_bundle = td_path / "from_template.cmproj"
        new_project = new_from_template(template_path, new_bundle)

        # Verify the project loaded and has tracks
        assert new_project.timeline.track_count > 0

    print("✓ 04_template_workflow: saved template and instantiated new project")


if __name__ == "__main__":
    main()
