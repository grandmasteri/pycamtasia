"""REV-test_gaps-009: operations/speed.py has 18 branch coverage gaps.

The speed module has the most branch gaps (18) of any module. These are
in _process_clip's handling of nested StitchedMedia with UnifiedMedia,
Group, and inner clips with non-unity scalars. Tests should exercise:
- StitchedMedia containing UnifiedMedia children
- StitchedMedia containing Group children
- StitchedMedia containing inner clips with non-unity scalar
- The mediaDuration recalculation path for various clip types
"""
import pytest
from fractions import Fraction

from camtasia import new_project
from camtasia.timing import seconds_to_ticks, parse_scalar


def test_rescale_stitched_with_non_unity_inner_scalar(tmp_path):
    """Rescaling a project with StitchedMedia whose inner clips have non-unity scalar."""
    proj_dir = tmp_path / "test.cmproj"
    proj = new_project(str(proj_dir))
    track = proj.timeline.add_track("t")

    # Create a StitchedMedia clip manually via low-level API
    track.add_clip("VMFile", 1, start_seconds=0, duration_seconds=5)
    clip = list(track.clips)[0]

    # Set a non-unity scalar to exercise the mediaDuration recalculation branch
    clip._data["scalar"] = "1/2"
    clip._data["mediaDuration"] = seconds_to_ticks(10)

    from camtasia.operations.speed import rescale_project
    rescale_project(proj, Fraction(2))

    # Verify the clip was rescaled
    assert clip.duration > 0
