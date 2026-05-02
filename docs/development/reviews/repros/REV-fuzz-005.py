"""REV-fuzz-005: add_clip accepts negative duration and negative start.

Track.add_clip() does not validate that start >= 0 or duration > 0.
Negative durations create clips that Camtasia cannot render. The clip
persists through save/reload. validate() only warns, doesn't prevent.
"""
import json
import shutil
import tempfile
from pathlib import Path

RESOURCES = Path(__file__).resolve().parents[4] / "src" / "camtasia" / "resources"

with tempfile.TemporaryDirectory() as tmp:
    proj_dir = Path(tmp) / "fuzz.cmproj"
    shutil.copytree(RESOURCES / "new.cmproj", proj_dir)

    from camtasia.project import load_project

    p = load_project(proj_dir)
    track = list(p.timeline.tracks)[0]

    # Negative duration — accepted
    c1 = track.add_clip("AMFile", 0, 0, -705600000)
    print(f"Negative duration clip: start={c1.start}, duration={c1.duration}")

    # Negative start — accepted
    c2 = track.add_clip("AMFile", 0, -705600000, 705600000)
    print(f"Negative start clip: start={c2.start}, duration={c2.duration}")

    # Zero duration — accepted
    c3 = track.add_clip("AMFile", 0, 0, 0)
    print(f"Zero duration clip: start={c3.start}, duration={c3.duration}")

    # Validate only warns
    issues = p.validate()
    for i in issues:
        if "duration" in str(i).lower() or "negative" in str(i).lower():
            print(f"Validation: {i}")
