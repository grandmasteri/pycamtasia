#!/usr/bin/env python3
"""Create a project, add a track with a placeholder clip, and save.

Demonstrates the multi-step API: new_project → load → add track →
add clip → save. No external assets required.

Usage:
    python 02_add_clips.py
"""
from __future__ import annotations

import tempfile
from pathlib import Path

from camtasia import load_project, new_project


def main() -> None:
    with tempfile.TemporaryDirectory() as td:
        project_path = Path(td) / "clips_demo.cmproj"
        new_project(project_path)
        project = load_project(project_path)

        track = project.timeline.add_track("Demo Track")
        track.add_placeholder(0.0, 5.0, title="Placeholder", note="5-second silent clip")

        project.save()

        # Verify the clip was added
        reloaded = load_project(project_path)
        demo_track = reloaded.timeline.find_track_by_name("Demo Track")
        assert demo_track is not None
        clips = list(demo_track.clips)
        assert len(clips) == 1
        assert clips[0].clip_type == "PlaceholderMedia"

    print("✓ 02_add_clips: created project with a placeholder clip")


if __name__ == "__main__":
    main()
