"""pycamtasia — Python API for Camtasia project files."""

from __future__ import annotations

# Project management
from camtasia.project import Project, load_project, use_project, new_project
from camtasia.validation import ValidationIssue

# Timeline
from camtasia.timeline import (
    Timeline,
    Track,
    BaseClip,
    AMFile,
    VMFile,
    IMFile,
    ScreenVMFile,
    ScreenIMFile,
    StitchedMedia,
    Group,
    Callout,
    clip_from_dict,
    Transition,
    TransitionList,
    Marker,
    MarkerList,
)

# Effects
from camtasia.effects import (
    Effect,
    effect_from_dict,
    Glow,
    RoundCorners,
    DropShadow,
    CursorMotionBlur,
    CursorPhysics,
    CursorShadow,
    LeftClickScaling,
    SourceEffect,
)

# Audiate
from camtasia.audiate import AudiateProject, Transcript, Word

# Timing
from camtasia.timing import (
    EDIT_RATE,
    seconds_to_ticks,
    ticks_to_seconds,
    format_duration,
    parse_scalar,
    scalar_to_string,
    speed_to_scalar,
    scalar_to_speed,
)

# Operations
from camtasia.operations import (
    rescale_project,
    set_audio_speed,
    SyncSegment,
    match_marker_to_transcript,
    plan_sync,
    clone_project_structure,
    replace_media_source,
)

__all__ = [
    # Project
    "Project",
    "ValidationIssue",
    "load_project",
    "use_project",
    "new_project",
    # Timeline
    "Timeline",
    "Track",
    "BaseClip",
    "AMFile",
    "VMFile",
    "IMFile",
    "ScreenVMFile",
    "ScreenIMFile",
    "StitchedMedia",
    "Group",
    "Callout",
    "clip_from_dict",
    "Transition",
    "TransitionList",
    "Marker",
    "MarkerList",
    # Effects
    "Effect",
    "effect_from_dict",
    "Glow",
    "RoundCorners",
    "DropShadow",
    "CursorMotionBlur",
    "CursorPhysics",
    "CursorShadow",
    "LeftClickScaling",
    "SourceEffect",
    # Audiate
    "AudiateProject",
    "Transcript",
    "Word",
    # Timing
    "EDIT_RATE",
    "seconds_to_ticks",
    "ticks_to_seconds",
    "format_duration",
    "parse_scalar",
    "scalar_to_string",
    "speed_to_scalar",
    "scalar_to_speed",
    # Operations
    "rescale_project",
    "set_audio_speed",
    "SyncSegment",
    "match_marker_to_transcript",
    "plan_sync",
    "clone_project_structure",
    "replace_media_source",
]
