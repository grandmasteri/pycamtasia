"""REV-test_gaps-008: Library 'No libraries exist' and 'Library not found' not tested.

library.py line 247 raises RuntimeError('No libraries exist') and
line 267 raises KeyError('Library not found'). Neither is tested.
"""
import pytest

from camtasia.library.library import Libraries


def test_no_libraries_exist_raises(tmp_path):
    """Accessing default library when none exist should raise RuntimeError."""
    libs = Libraries(tmp_path)
    with pytest.raises(RuntimeError, match="No libraries exist"):
        libs.default


def test_library_not_found_raises(tmp_path):
    """Accessing a non-existent library by name should raise KeyError."""
    libs = Libraries(tmp_path)
    with pytest.raises(KeyError, match="Library.*not found"):
        libs["nonexistent"]
