"""High-level operations that coordinate across multiple clips and tracks."""

from __future__ import annotations

from camtasia.operations.speed import rescale_project, set_audio_speed
from camtasia.operations.sync import SyncSegment, match_marker_to_transcript, plan_sync
from camtasia.operations.template import clone_project_structure, replace_media_source

__all__ = [
    "rescale_project",
    "set_audio_speed",
    "SyncSegment",
    "match_marker_to_transcript",
    "plan_sync",
    "clone_project_structure",
    "replace_media_source",
]
