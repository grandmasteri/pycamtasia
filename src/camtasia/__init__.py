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
    PlaceholderMedia,
    Group,
    GroupTrack,
    Callout,
    UnifiedMedia,
    clip_from_dict,
    Transition,
    TransitionList,
    Marker,
    MarkerList,
)

# Callout builder (lives in timeline.clips.callout)
from camtasia.timeline.clips.callout import CalloutBuilder

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

# Types / enums
from camtasia.history import ChangeHistory, ChangeRecord, with_undo
from camtasia.types import (
    ClipType,
    EffectName,
    TransitionType,
    BehaviorPreset,
    BlendMode,
    CalloutKind,
    CalloutShape,
    MaskShape,
    InterpolationType,
    ValidationLevel,
    MediaType,
)

# Color
from camtasia.color import RGBA, hex_rgb

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

# Builders
from camtasia.builders import TimelineBuilder, build_from_screenplay

# Screenplay parsing
from camtasia.screenplay import parse_screenplay

# Export utilities
from camtasia.export import export_edl, export_csv, export_markers_as_srt

__all__ = [
    # Project
    "Project",
    "load_project",
    "use_project",
    "new_project",
    "ValidationIssue",
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
    "PlaceholderMedia",
    "Group",
    "GroupTrack",
    "Callout",
    "UnifiedMedia",
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
    # Types / enums
    "ClipType",
    "EffectName",
    "TransitionType",
    "BehaviorPreset",
    "BlendMode",
    "CalloutKind",
    "CalloutShape",
    "MaskShape",
    "InterpolationType",
    "ValidationLevel",
    "MediaType",
    # History
    "ChangeHistory",
    "ChangeRecord",
    "with_undo",
    # Color
    "RGBA",
    "hex_rgb",
    # Operations
    "rescale_project",
    "set_audio_speed",
    "SyncSegment",
    "match_marker_to_transcript",
    "plan_sync",
    "clone_project_structure",
    "replace_media_source",
    # Builders
    "TimelineBuilder",
    "CalloutBuilder",
    "build_from_screenplay",
    # Screenplay
    "parse_screenplay",
    # Export
    "export_edl",
    "export_csv",
    "export_markers_as_srt",
]
