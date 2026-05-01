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
from camtasia.operations.captions import (
    TrimRange,
    generate_captions_from_audio,
    sync_script_to_captions,
    trim_silences,
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
    ripple_replace_in_group,
    snap_to_clip_edge,
    snap_to_grid,
)
from camtasia.operations.merge import merge_tracks
from camtasia.operations.slide_markers import mark_slides_from_presentation
from camtasia.operations.speed import rescale_project, set_audio_speed
from camtasia.operations.stitch import auto_stitch_on_track
from camtasia.operations.sync import (
    SyncSegment,
    apply_sync,
    delete_words_from_timeline,
    match_marker_to_transcript,
    plan_sync,
    send_media_to_audiate,
    sync_audiate_edits_to_timeline,
)
from camtasia.operations.template import (
    TemplateManager,
    clone_project_structure,
    duplicate_project,
    export_camtemplate,
    install_camtemplate,
    list_installed_templates,
    new_from_template,
    new_project_from_template,
    replace_media_source,
    replace_placeholder,
    save_as_template,
)

__all__ = [
    "ProjectDiff",
    "SyncSegment",
    "TemplateManager",
    "TrimRange",
    "apply_sync",
    "apply_to_all_tracks",
    "apply_to_clips",
    "apply_to_track",
    "auto_stitch_on_track",
    "clone_project_structure",
    "compact_project",
    "delete_words_from_timeline",
    "diff_projects",
    "duplicate_project",
    "export_camtemplate",
    "fade_all",
    "generate_captions_from_audio",
    "install_camtemplate",
    "list_installed_templates",
    "mark_slides_from_presentation",
    "match_marker_to_transcript",
    "merge_tracks",
    "move_all",
    "new_from_template",
    "new_project_from_template",
    "pack_track",
    "plan_sync",
    "remove_empty_tracks",
    "remove_orphaned_media",
    "replace_media_source",
    "replace_placeholder",
    "rescale_project",
    "ripple_delete",
    "ripple_delete_range",
    "ripple_extend",
    "ripple_insert",
    "ripple_move",
    "ripple_move_multi",
    "ripple_replace_in_group",
    "save_as_template",
    "scale_all",
    "send_media_to_audiate",
    "set_audio_speed",
    "set_opacity_all",
    "snap_to_clip_edge",
    "snap_to_grid",
    "sync_audiate_edits_to_timeline",
    "sync_script_to_captions",
    "trim_silences",
]
