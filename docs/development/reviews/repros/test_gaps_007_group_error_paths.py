"""REV-test_gaps-007: Group clip error paths not tested.

group.py has several untested error paths:
- line 98: 'Internal Group tracks do not support transitions'
- line 178: 'Group clips do not have a source ID'
- line 712: 'No internal track with UnifiedMedia found'
- line 759: 'segment src_end must be > src_start'
- line 989: 'Expected Library, got ...'
"""
import pytest

from camtasia import new_project
from camtasia.timing import seconds_to_ticks


def test_group_source_id_raises_type_error(tmp_path):
    """Accessing source_id on a Group clip should raise TypeError."""
    proj_dir = tmp_path / "test.cmproj"
    proj = new_project(str(proj_dir))
    track = proj.timeline.add_track("t")
    # Add two clips and group them
    proj.media_bin.import_media_by_id(1, "a.mp4", duration_ticks=seconds_to_ticks(5))
    proj.media_bin.import_media_by_id(2, "b.mp4", duration_ticks=seconds_to_ticks(5))
    track.add_clip("VMFile", 1, start_seconds=0, duration_seconds=5)
    track.add_clip("VMFile", 2, start_seconds=5, duration_seconds=5)
    clips = list(track.clips)
    group = track.group_clips([clips[0].id, clips[1].id])
    with pytest.raises(TypeError, match="Group clips do not have a source ID"):
        _ = group.source_id
