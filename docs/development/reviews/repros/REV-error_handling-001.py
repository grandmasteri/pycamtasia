"""Repro: _probe_media swallows all exceptions from pymediainfo.

If pymediainfo is installed but raises a non-ImportError (e.g. RuntimeError
from a corrupt file, or OSError from a permissions issue), the bare
`except Exception: pass` silently discards the error and falls through to
ffprobe. The caller never learns that pymediainfo was available but failed.

This means a corrupt media file that pymediainfo *could* diagnose gets
silently downgraded to ffprobe's best-effort output (or empty dict),
producing wrong metadata with no warning.
"""
from pathlib import Path
from unittest.mock import MagicMock, patch
import sys

# Simulate pymediainfo raising RuntimeError on parse
mock_mediainfo = MagicMock()
mock_mediainfo.MediaInfo.parse.side_effect = RuntimeError("corrupt file header")
sys.modules['pymediainfo'] = mock_mediainfo

try:
    # Import after mocking
    from camtasia.project import _probe_media

    # Create a dummy file
    tmp = Path("/tmp/repro_001_test.mp4")
    tmp.write_bytes(b"\x00" * 100)

    result = _probe_media(tmp)
    # Result silently falls through to ffprobe — no warning, no error logged
    print(f"Result: {result}")
    print("BUG: RuntimeError from pymediainfo was silently swallowed")
finally:
    del sys.modules['pymediainfo']
    Path("/tmp/repro_001_test.mp4").unlink(missing_ok=True)
