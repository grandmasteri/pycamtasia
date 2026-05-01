#!/usr/bin/env python3
"""REV-security-004: Subprocess calls with user-controlled file paths.

Multiple functions pass user-supplied file paths to subprocess calls
(ffprobe, ffmpeg, pkill). While list-form subprocess.run() is used
(not shell=True), the file paths are not validated or sanitized.

ffprobe/ffmpeg are generally safe with list-form args, but:
1. A filename starting with '-' could be interpreted as a flag
   (e.g., '-version' or '-loglevel')
2. app_validation.py passes project_path to subprocess.Popen which
   launches Camtasia with an attacker-controlled path argument

This is MEDIUM severity because list-form subprocess prevents shell
injection, but flag injection via filenames is still possible.
"""
import tempfile
from pathlib import Path


def demonstrate_dash_filename() -> None:
    """Show that a filename starting with '-' is passed unsanitized."""
    print("=== Flag injection via filename ===")
    print("If a media file is named '-version.mp4', the subprocess call becomes:")
    print("  ['ffprobe', '-v', 'quiet', ..., '-version.mp4']")
    print("ffprobe would interpret '-version.mp4' as a flag attempt.")
    print()
    print("Relevant code in media_bin.py line ~610:")
    print("  subprocess.run(['ffprobe', '-v', 'quiet', ..., str(file_path)], ...)")
    print()
    print("Mitigation: Prefix paths with './' to prevent flag interpretation,")
    print("or validate that filenames don't start with '-'.")


def demonstrate_app_validation_path() -> None:
    """Show that app_validation passes unvalidated path to Popen."""
    print("\n=== app_validation.py subprocess.Popen ===")
    print("camtasia_validate() passes project_path directly to Popen:")
    print("  subprocess.Popen([str(camtasia_path), str(project_path)], ...)")
    print()
    print("If project_path contains special characters or is a crafted path,")
    print("it's passed as an argument to the Camtasia binary.")
    print("This is lower risk since Camtasia is a GUI app, but the path")
    print("is not validated to be a real .cmproj directory.")


if __name__ == "__main__":
    demonstrate_dash_filename()
    demonstrate_app_validation_path()
