"""REV-test_gaps-004: Crop negative value and target_duration_seconds <= 0 not tested.

base.py line 1741 raises ValueError for negative crop values.
base.py line 2678 raises ValueError for target_duration_seconds <= 0.
Neither is exercised by any test.
"""
import json
import pytest

from camtasia import new_project
from camtasia.timing import seconds_to_ticks


def _add_video_clip(proj):
    """Helper to add a video clip to the project."""
    mid = proj.media_bin.import_media_by_id(1, "video.mp4", duration_ticks=seconds_to_ticks(10))
    track = proj.timeline.add_track("t")
    track.add_clip("VMFile", mid, start_seconds=0, duration_seconds=10)
    return list(track.clips)[0]


def test_crop_negative_value_raises(tmp_path):
    """Setting a negative crop value should raise ValueError."""
    proj_dir = tmp_path / "test.cmproj"
    proj = new_project(str(proj_dir))
    clip = _add_video_clip(proj)
    with pytest.raises(ValueError, match="must be non-negative"):
        clip.set_crop(left=-0.1)


def test_fit_to_duration_zero_raises(tmp_path):
    """fit_to_duration with target_duration_seconds=0 should raise ValueError."""
    proj_dir = tmp_path / "test.cmproj"
    proj = new_project(str(proj_dir))
    clip = _add_video_clip(proj)
    with pytest.raises(ValueError, match="target_duration_seconds must be > 0"):
        clip.fit_to_duration(target_duration_seconds=0)
