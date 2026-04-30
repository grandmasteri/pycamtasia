"""High-level operations that coordinate across multiple clips and tracks."""

from __future__ import annotations

from camtasia.operations.batch import (
    apply_to_all_tracks,
    apply_to_clips,
    apply_to_track,
    fade_all,
    move_all,
    scale_all,
    set_opacity_all,
)
from camtasia.operations.cleanup import compact_project, remove_empty_tracks, remove_orphaned_media
from camtasia.operations.diff import ProjectDiff, diff_projects
from camtasia.operations.layout import (
    pack_track,
    ripple_delete,
    ripple_delete_range,
    ripple_extend,
    ripple_insert,
    ripple_move,
    ripple_move_multi,
    snap_to_clip_edge,
    snap_to_grid,
)
from camtasia.operations.merge import merge_tracks
from camtasia.operations.speed import rescale_project, set_audio_speed
from camtasia.operations.sync import SyncSegment, apply_sync, match_marker_to_transcript, plan_sync
from camtasia.operations.template import clone_project_structure, duplicate_project, replace_media_source

__all__ = [
    "ProjectDiff",
    "SyncSegment",
    "apply_sync",
    "apply_to_all_tracks",
    "apply_to_clips",
    "apply_to_track",
    "clone_project_structure",
    "compact_project",
    "diff_projects",
    "duplicate_project",
    "fade_all",
    "match_marker_to_transcript",
    "merge_tracks",
    "move_all",
    "pack_track",
    "plan_sync",
    "remove_empty_tracks",
    "remove_orphaned_media",
    "replace_media_source",
    "rescale_project",
    "ripple_delete",
    "ripple_delete_range",
    "ripple_extend",
    "ripple_insert",
    "ripple_move",
    "ripple_move_multi",
    "scale_all",
    "set_audio_speed",
    "set_opacity_all",
    "snap_to_clip_edge",
    "snap_to_grid",
]
