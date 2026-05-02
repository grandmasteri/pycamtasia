"""REV-fuzz-008: Negative trackIndex accepted without validation.

A .tscproj with trackIndex=-1 loads and is accessible. This creates
a track with index -1 which has no corresponding trackAttributes entry,
potentially causing index-out-of-bounds in operations that correlate
tracks with their attributes.
"""
import json
import shutil
import tempfile
from pathlib import Path

RESOURCES = Path(__file__).resolve().parents[4] / "src" / "camtasia" / "resources"

with tempfile.TemporaryDirectory() as tmp:
    proj_dir = Path(tmp) / "fuzz.cmproj"
    shutil.copytree(RESOURCES / "new.cmproj", proj_dir)
    data = json.loads((proj_dir / "project.tscproj").read_text())
    data["timeline"]["sceneTrack"]["scenes"][0]["csml"]["tracks"][0]["trackIndex"] = -1
    (proj_dir / "project.tscproj").write_text(json.dumps(data))

    from camtasia.project import load_project

    p = load_project(proj_dir)
    tracks = list(p.timeline.tracks)
    print(f"Track indices: {[t.index for t in tracks]}")
    # -1 is accepted — no validation catches this
    issues = p.validate()
    neg_issues = [i for i in issues if "index" in str(i).lower() or "negative" in str(i).lower()]
    print(f"Validation issues about negative index: {len(neg_issues)}")
