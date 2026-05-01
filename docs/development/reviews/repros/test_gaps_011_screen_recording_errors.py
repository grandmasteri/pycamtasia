"""REV-test_gaps-011: screen_recording.py error paths for cursor editing not fully tested.

screen_recording.py has several error paths:
- line 36: 'Cannot change source on screen recording video clips'
- line 234: 'Cannot change source on cursor overlay clips'
- line 444: 'No cursor keyframe at {time_seconds}s'
- line 595: 'scope must be one of ...'
These should have dedicated negative tests.
"""
import pytest

from camtasia.timeline.clips.screen_recording import ScreenVMFile, ScreenIMFile


def test_screen_vmfile_set_source_raises(tmp_path):
    """Setting source on ScreenVMFile should raise TypeError."""
    data = {
        "_type": "ScreenVMFile",
        "id": 1,
        "start": 0,
        "duration": 705600000,
        "mediaStart": 0,
        "mediaDuration": 705600000,
        "scalar": 1,
        "src": 1,
        "effects": [],
        "parameters": {"gestureData": []},
    }
    clip = ScreenVMFile(data)
    with pytest.raises(TypeError, match="Cannot change source on screen recording"):
        clip.set_source(99)


def test_screen_imfile_set_source_raises(tmp_path):
    """Setting source on ScreenIMFile cursor overlay should raise TypeError."""
    data = {
        "_type": "ScreenIMFile",
        "id": 2,
        "start": 0,
        "duration": 705600000,
        "mediaStart": 0,
        "mediaDuration": 705600000,
        "scalar": 1,
        "src": 1,
        "effects": [],
        "parameters": {"cursorData": {"keyframes": []}},
    }
    clip = ScreenIMFile(data)
    with pytest.raises(TypeError, match="Cannot change source on cursor overlay"):
        clip.set_source(99)
