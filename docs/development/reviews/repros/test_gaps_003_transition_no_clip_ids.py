"""REV-test_gaps-003: Transition add_transition with no clip IDs is not tested.

transitions.py line 136 raises ValueError when neither left_clip_id nor
right_clip_id is provided. No test triggers this path.
"""
import pytest

from camtasia import new_project


def test_add_transition_no_clip_ids(tmp_path):
    """add_transition with neither left nor right clip ID should raise ValueError."""
    proj_dir = tmp_path / "test.cmproj"
    proj = new_project(str(proj_dir))
    track = proj.timeline.add_track("t")
    with pytest.raises(ValueError, match="At least one of left_clip_id or right_clip_id"):
        track.add_transition(left_clip_id=None, right_clip_id=None)
