"""REV-test_gaps-002: Caption index boundary errors are not tested.

timeline.py has three IndexError raises for caption index out of range
(lines 1355, 1374, 1403) plus a ValueError at 1407 and IndexError at 1453.
None of these are exercised by any test.
"""
import pytest

from camtasia import new_project


def test_edit_caption_index_out_of_range(tmp_path):
    """Accessing a caption by out-of-range index should raise IndexError."""
    proj_dir = tmp_path / "test.cmproj"
    proj = new_project(str(proj_dir))
    with pytest.raises(IndexError, match="Caption index"):
        proj.timeline.edit_caption(999, text="hello")


def test_remove_caption_index_out_of_range(tmp_path):
    """Removing a caption by out-of-range index should raise IndexError."""
    proj_dir = tmp_path / "test.cmproj"
    proj = new_project(str(proj_dir))
    with pytest.raises(IndexError, match="Caption index"):
        proj.timeline.remove_caption(999)


def test_split_caption_index_out_of_range(tmp_path):
    """Splitting a caption by out-of-range index should raise IndexError."""
    proj_dir = tmp_path / "test.cmproj"
    proj = new_project(str(proj_dir))
    with pytest.raises(IndexError, match="Caption index"):
        proj.timeline.split_caption(999, split_seconds=0.5)
