"""REV-fuzz-001: Project accepts non-dict timeline without validation.

Setting timeline to a string in the JSON creates a Project that loads
successfully but crashes on any timeline operation with an unhelpful
TypeError ('string indices must be integers').
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
    data["timeline"] = "not a dict"
    (proj_dir / "project.tscproj").write_text(json.dumps(data))

    from camtasia.project import load_project

    p = load_project(proj_dir)  # loads without error
    tl = p.timeline  # returns Timeline wrapping a string
    print(f"Timeline type: {type(tl)}, internal data type: {type(tl._data)}")

    try:
        list(tl.tracks)  # crashes here
    except TypeError as e:
        print(f"CRASH: {e}")
        # Expected: "string indices must be integers, not 'str'"

    try:
        p.save()  # also crashes
    except (TypeError, KeyError) as e:
        print(f"Save CRASH: {e}")
