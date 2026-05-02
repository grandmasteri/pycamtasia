"""REV-fuzz-002: Empty JSON object loads but crashes on timeline/validate/save.

An empty JSON object `{}` is accepted by load_project. Accessing
.timeline, .validate(), or .save() raises bare KeyError('timeline')
with no guidance about what's wrong with the file.
"""
import json
import shutil
import tempfile
from pathlib import Path

RESOURCES = Path(__file__).resolve().parents[4] / "src" / "camtasia" / "resources"

with tempfile.TemporaryDirectory() as tmp:
    proj_dir = Path(tmp) / "fuzz.cmproj"
    shutil.copytree(RESOURCES / "new.cmproj", proj_dir)
    (proj_dir / "project.tscproj").write_text("{}")

    from camtasia.project import load_project

    p = load_project(proj_dir)  # loads without error
    print(f"Loaded empty JSON project, _data keys: {list(p._data.keys())}")

    for attr in ["timeline", "validate", "save"]:
        try:
            if attr == "timeline":
                _ = p.timeline
            elif attr == "validate":
                p.validate()
            else:
                p.save()
            print(f"  {attr}: OK")
        except KeyError as e:
            print(f"  {attr}: KeyError({e}) — no helpful message")
