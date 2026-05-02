"""Repro: _parse_with_pymediainfo in media_bin.py swallows all exceptions.

The `except Exception: return None` on line 701 catches everything including
MemoryError, KeyboardInterrupt (in Python <3.11 via Exception subclass
patterns), and programming errors like AttributeError or TypeError.

When this returns None, import_media raises ValueError("Cannot determine
media type") — an unactionable message that hides the real cause.
"""
from pathlib import Path
from unittest.mock import MagicMock, patch
import sys

mock_mi = MagicMock()
mock_mi.MediaInfo.parse.side_effect = OSError("libmediainfo.so: cannot open shared object")
sys.modules['pymediainfo'] = mock_mi

try:
    from camtasia.media_bin.media_bin import _parse_with_pymediainfo

    result = _parse_with_pymediainfo(Path("/tmp/test.mp4"))
    print(f"Result: {result}")
    assert result is None
    print("BUG: OSError from pymediainfo silently returned as None")
    print("Caller will see: ValueError('Cannot determine media type')")
    print("Real cause (broken libmediainfo) is hidden")
finally:
    del sys.modules['pymediainfo']
