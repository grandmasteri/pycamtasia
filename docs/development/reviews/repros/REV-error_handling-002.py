"""Repro: _probe_media_ffprobe swallows all exceptions including unexpected ones.

Each of the three ffprobe subprocess calls catches `except Exception: pass`.
This means if subprocess.run raises an unexpected error (e.g. PermissionError,
MemoryError), it's silently swallowed. The function returns a dict with only
{'_backend': 'ffprobe'} — no metadata and no indication of failure.

Callers like import_media then use wrong defaults (e.g. 1920x1080 for an
audio file, 1-second duration for a video).
"""
from pathlib import Path
from unittest.mock import patch

from camtasia.project import _probe_media_ffprobe

# Simulate ffprobe raising PermissionError
with patch('camtasia.project._sp.run', side_effect=PermissionError("access denied")):
    result = _probe_media_ffprobe(Path("/tmp/any_file.mp4"))
    print(f"Result: {result}")
    assert result == {'_backend': 'ffprobe'}, f"Expected empty result, got {result}"
    print("BUG: PermissionError silently swallowed, returned empty metadata dict")
