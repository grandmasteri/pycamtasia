"""REV-fuzz-003: Deeply nested JSON causes RecursionError in save().

A project with ~500 levels of nesting loads fine but crashes in save()
due to copy.deepcopy hitting Python's recursion limit. This is a
denial-of-service vector for any pipeline that loads untrusted .tscproj
files and attempts to save them.
"""
import copy
import json
import shutil
import tempfile
from pathlib import Path

RESOURCES = Path(__file__).resolve().parents[4] / "src" / "camtasia" / "resources"

with tempfile.TemporaryDirectory() as tmp:
    proj_dir = Path(tmp) / "fuzz.cmproj"
    shutil.copytree(RESOURCES / "new.cmproj", proj_dir)
    data = json.loads((proj_dir / "project.tscproj").read_text())

    # Build 500-deep nesting
    nested = "leaf"
    for _ in range(500):
        nested = {"a": nested}
    data["metadata"]["deep"] = nested
    (proj_dir / "project.tscproj").write_text(json.dumps(data))

    from camtasia.project import load_project

    p = load_project(proj_dir)  # loads OK
    print("Loaded project with 500-deep nesting")

    try:
        p.save()  # crashes
        print("Save succeeded (unexpected)")
    except RecursionError:
        print("CRASH: RecursionError in save() — copy.deepcopy overflow")
