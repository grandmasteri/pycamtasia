"""REV-fuzz-004: NaN in numeric fields silently replaced with 0.0 on save.

When a .tscproj contains NaN (e.g. from a corrupted upstream tool),
load_project reads it as float('nan'). On save(), the NaN is silently
replaced with 0.0 — changing project dimensions from NaN to 0x0.
A warning is emitted but the data corruption proceeds.
"""
import json
import shutil
import tempfile
import warnings
from pathlib import Path

RESOURCES = Path(__file__).resolve().parents[4] / "src" / "camtasia" / "resources"

with tempfile.TemporaryDirectory() as tmp:
    proj_dir = Path(tmp) / "fuzz.cmproj"
    shutil.copytree(RESOURCES / "new.cmproj", proj_dir)
    data = json.loads((proj_dir / "project.tscproj").read_text())
    data["width"] = float("nan")
    (proj_dir / "project.tscproj").write_text(json.dumps(data, allow_nan=True))

    from camtasia.project import load_project

    p = load_project(proj_dir)
    print(f"Before save: width={p._data['width']}")  # nan

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        p.save()
        print(f"Warnings: {[str(x.message) for x in w]}")

    p2 = load_project(proj_dir)
    print(f"After save: width={p2._data['width']}")  # 0.0 — silent corruption
