#!/usr/bin/env python3
"""REV-security-003: save() writes to whatever _project_file resolves to.

Project.save() writes to self._project_file which is derived from
self._file_path. If a project is loaded from a symlinked .cmproj directory,
save() follows the symlink and writes to the symlink target. There is no
check that the resolved path is within an expected directory.

Additionally, from_template() uses shutil.copytree with user-supplied
output_path and calls shutil.rmtree(dst) if it already exists — a
caller-controlled path could delete arbitrary directories.
"""
import json
import shutil
import tempfile
from pathlib import Path


def demonstrate_symlink_follow() -> None:
    """Show that save() follows symlinks."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)

        # Create a real project
        real_dir = tmp_path / "real.cmproj"
        real_dir.mkdir()
        real_tscproj = real_dir / "real.tscproj"
        real_tscproj.write_text(json.dumps({
            "sourceBin": [],
            "timeline": {"sceneTrack": {"scenes": [{"csml": {"tracks": []}}]}},
        }))

        # Create a symlink to it
        symlink_dir = tmp_path / "symlink.cmproj"
        symlink_dir.symlink_to(real_dir)

        from camtasia.project import Project
        proj = Project.load(str(symlink_dir))
        proj.title = "INJECTED"
        proj.save()

        # Verify the real file was modified through the symlink
        saved = json.loads(real_tscproj.read_text())
        assert saved.get("title") == "INJECTED", "Save followed symlink"
        print("CONFIRMED: save() follows symlinks to write to target location")


def demonstrate_from_template_rmtree() -> None:
    """Show that from_template() calls rmtree on caller-controlled path."""
    print("\nfrom_template() source code analysis:")
    print("  dst = Path(output_path)")
    print("  if dst.exists():")
    print("      shutil.rmtree(dst)  # <-- deletes whatever output_path points to")
    print("  shutil.copytree(src, dst)")
    print("\nA caller passing output_path='/' would attempt to delete the root filesystem.")
    print("While this is a caller-controlled API (not untrusted input),")
    print("the lack of any safety check is a defense-in-depth concern.")


if __name__ == "__main__":
    demonstrate_symlink_follow()
    demonstrate_from_template_rmtree()
