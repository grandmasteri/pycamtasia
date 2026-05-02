"""REV-fuzz-009: Missing 'timeline' key crashes validate() and save().

A .tscproj without a 'timeline' key loads successfully but both
validate() and save() crash with bare KeyError('timeline'). Since
validate() is supposed to detect structural problems, it should handle
missing required keys gracefully.
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
    del data["timeline"]
    (proj_dir / "project.tscproj").write_text(json.dumps(data))

    from camtasia.project import load_project

    p = load_project(proj_dir)  # loads OK
    print(f"Loaded project without timeline key, keys: {list(p._data.keys())}")

    try:
        p.validate()
    except KeyError as e:
        print(f"validate() CRASH: KeyError({e})")

    try:
        p.save()
    except KeyError as e:
        print(f"save() CRASH: KeyError({e})")
