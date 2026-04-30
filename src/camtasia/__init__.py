"""pycamtasia — Python API for Camtasia project files."""

from __future__ import annotations

# Audiate
from camtasia.audiate import AudiateProject, Transcript, Word

# Builders
from camtasia.builders import TimelineBuilder, build_from_screenplay

# Color
from camtasia.color import RGBA, hex_rgb

# Effects
from camtasia.effects import (
    CursorMotionBlur,
    CursorPhysics,
    CursorShadow,
    DropShadow,
    Effect,
    Glow,
    LeftClickScaling,
    RoundCorners,
    SourceEffect,
    effect_from_dict,
)

# Export utilities
from camtasia.export import export_csv, export_edl, export_markers_as_srt

# Types / enums
from camtasia.history import ChangeHistory, ChangeRecord, with_undo

# Operations
from camtasia.operations import (
    SyncSegment,
    clone_project_structure,
    match_marker_to_transcript,
    plan_sync,
    replace_media_source,
    rescale_project,
    set_audio_speed,
)
from camtasia.project import Project, load_project, new_project, use_project

# Screenplay parsing
from camtasia.screenplay import parse_screenplay

# Project management
from camtasia.themes import Theme, apply_theme

# Timeline
from camtasia.timeline import (
    AMFile,
    BaseClip,
    Callout,
    Group,
    GroupTrack,
    IMFile,
    Marker,
    MarkerList,
    PlaceholderMedia,
    ScreenIMFile,
    ScreenVMFile,
    StitchedMedia,
    Timeline,
    Track,
    Transition,
    TransitionList,
    UnifiedMedia,
    VMFile,
    clip_from_dict,
)

# Callout builder (lives in timeline.clips.callout)
from camtasia.timeline.clips.callout import CalloutBuilder

# Timing
from camtasia.timing import (
    EDIT_RATE,
    format_duration,
    parse_scalar,
    scalar_to_speed,
    scalar_to_string,
    seconds_to_ticks,
    speed_to_scalar,
    ticks_to_seconds,
)
from camtasia.types import (
    BehaviorPreset,
    BlendMode,
    CalloutKind,
    CalloutShape,
    ClipType,
    EffectName,
    InterpolationType,
    MaskShape,
    MatteMode,
    MediaType,
    TransitionType,
    ValidationLevel,
)
from camtasia.validation import ValidationIssue, validate_all

__all__ = [
    # Timing
    "EDIT_RATE",
    # Color
    "RGBA",
    "AMFile",
    # Audiate
    "AudiateProject",
    "BaseClip",
    "BehaviorPreset",
    "BlendMode",
    "Callout",
    "CalloutBuilder",
    "CalloutKind",
    "CalloutShape",
    # History
    "ChangeHistory",
    "ChangeRecord",
    # Types / enums
    "ClipType",
    "CursorMotionBlur",
    "CursorPhysics",
    "CursorShadow",
    "DropShadow",
    # Effects
    "Effect",
    "EffectName",
    "Glow",
    "Group",
    "GroupTrack",
    "IMFile",
    "InterpolationType",
    "LeftClickScaling",
    "Marker",
    "MarkerList",
    "MaskShape",
    "MatteMode",
    "MediaType",
    "PlaceholderMedia",
    # Project
    "Project",
    "RoundCorners",
    "ScreenIMFile",
    "ScreenVMFile",
    "SourceEffect",
    "StitchedMedia",
    "SyncSegment",
    "Theme",
    # Timeline
    "Timeline",
    # Builders
    "TimelineBuilder",
    "Track",
    "Transcript",
    "Transition",
    "TransitionList",
    "TransitionType",
    "UnifiedMedia",
    "VMFile",
    "ValidationIssue",
    "ValidationLevel",
    "Word",
    "apply_theme",
    "build_from_screenplay",
    "clip_from_dict",
    "clone_project_structure",
    "effect_from_dict",
    "export_csv",
    # Export
    "export_edl",
    "export_markers_as_srt",
    "format_duration",
    "hex_rgb",
    "load_project",
    "match_marker_to_transcript",
    "new_project",
    "parse_scalar",
    # Screenplay
    "parse_screenplay",
    "plan_sync",
    "replace_media_source",
    # Operations
    "rescale_project",
    "scalar_to_speed",
    "scalar_to_string",
    "seconds_to_ticks",
    "set_audio_speed",
    "speed_to_scalar",
    "ticks_to_seconds",
    "use_project",
    "validate_all",
    "with_undo",
]
