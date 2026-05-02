"""REV-fuzz-007: validate() crashes with TypeError on corrupted tracks.

If a loaded project has tracks set to None (possible from a corrupted
.tscproj), validate() raises TypeError('NoneType object is not iterable')
instead of reporting a validation issue. validate() should be robust
against malformed data — that's its entire purpose.
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
    # Simulate corrupted tracks (could come from malformed .tscproj)
    p._data["timeline"]["sceneTrack"]["scenes"][0]["csml"]["tracks"] = None

    try:
        issues = p.validate()
        print(f"Validate returned {len(issues)} issues")
    except TypeError as e:
        print(f"CRASH: validate() raised TypeError: {e}")
        print("validate() should catch this and report it as a validation issue")
