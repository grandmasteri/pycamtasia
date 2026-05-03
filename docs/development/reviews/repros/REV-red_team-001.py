"""REV-red_team-001: Deeply nested groups cause RecursionError.

The fuzz fix (REV-fuzz-001/002/009) added structural validation for
top-level keys but does NOT limit nesting depth. A crafted .tscproj
with ~500 levels of nested Group clips loads successfully (json.loads
uses C code) but crashes on save() or validate() with RecursionError.

This bypasses the file-size limit (the file is only ~100 KB) and the
structural validation (timeline and sourceBin are present and correct).
"""
import os
import shutil
import sys
import tempfile


def build_nested_json(depth: int) -> str:
    """Build a valid .tscproj JSON string with deeply nested groups."""
    leaf = (
        '{"id":0,"_type":"AMFile","start":0,"duration":100,"src":0,'
        '"mediaStart":0,"mediaDuration":100,"scalar":1,'
        '"metadata":{},"animationTracks":{},"parameters":{},"effects":[]}'
    )
    current = leaf
    for i in range(1, depth + 1):
        current = (
            f'{{"id":{i},"_type":"Group","start":0,"duration":100,'
            f'"mediaStart":0,"mediaDuration":100,"scalar":1,'
            f'"metadata":{{}},"animationTracks":{{}},"parameters":{{}},"effects":[],'
            f'"tracks":[{{"trackIndex":0,"medias":[{current}]}}]}}'
        )
    return (
        f'{{"timeline":{{"sceneTrack":{{"scenes":[{{"csml":{{"tracks":['
        f'{{"trackIndex":0,"medias":[{current}]}}]}}}}]}},"parameters":{{}}}},'
        f'"sourceBin":[]}}'
    )


tmpdir = tempfile.mkdtemp(suffix=".cmproj")
try:
    json_str = build_nested_json(500)
    with open(os.path.join(tmpdir, "project.tscproj"), "w") as f:
        f.write(json_str)

    print(f"File size: {len(json_str)} bytes (well under 100MB limit)")
    print(f"Recursion limit: {sys.getrecursionlimit()}")

    from camtasia.project import Project

    proj = Project.load(tmpdir)
    print("load() succeeded (json.loads uses C code, no Python recursion)")

    try:
        proj.save()
        print("save() succeeded — BUG NOT TRIGGERED")
    except RecursionError:
        print("CONFIRMED: RecursionError on save() — json.dumps hits Python recursion limit")

    try:
        issues = proj.validate()
        print(f"validate() succeeded — {len(issues)} issues")
    except RecursionError:
        print("CONFIRMED: RecursionError on validate() — Python recursion in validation code")

except RecursionError:
    print("CONFIRMED: RecursionError on load()")
except ValueError as e:
    print(f"Caught ValueError (good — validation caught it): {e}")
finally:
    sys.setrecursionlimit(10000)
    shutil.rmtree(tmpdir)
