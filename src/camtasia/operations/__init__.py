"""High-level operations that coordinate across multiple clips and tracks."""

from __future__ import annotations

from camtasia.operations.layout import pack_track, ripple_delete, ripple_insert, snap_to_grid
from camtasia.operations.speed import rescale_project, set_audio_speed
from camtasia.operations.sync import SyncSegment, match_marker_to_transcript, plan_sync
from camtasia.operations.template import clone_project_structure, replace_media_source

__all__ = [
    "pack_track",
    "rescale_project",
    "ripple_delete",
    "ripple_insert",
    "set_audio_speed",
    "snap_to_grid",
    "SyncSegment",
    "match_marker_to_transcript",
    "plan_sync",
    "clone_project_structure",
    "replace_media_source",
]
