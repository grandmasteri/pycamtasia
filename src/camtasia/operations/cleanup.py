"""Utilities for cleaning up Camtasia projects."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from camtasia.project import Project


def remove_orphaned_media(project: Project) -> list[int]:
    """Remove media entries not referenced by any clip.

    Returns list of removed media IDs.
    """
    referenced_ids: set[int] = set()
    for track in project.timeline.tracks:
        for clip in track.clips:
            src = clip.source_id
            if src is not None:
                referenced_ids.add(src)

    removed = []
    source_bin = project._data.get('sourceBin', [])
    to_keep = []
    for entry in source_bin:
        if entry['id'] in referenced_ids:
            to_keep.append(entry)
        else:
            removed.append(entry['id'])
    project._data['sourceBin'] = to_keep
    return removed


def remove_empty_tracks(project: Project) -> int:
    """Remove all empty tracks from the project.

    Returns count of tracks removed.
    """
    return project.timeline.remove_empty_tracks()


def compact_project(project: Project) -> dict[str, int]:
    """Run all cleanup operations on a project.

    Returns a summary dict with counts of items cleaned.
    """
    orphaned = remove_orphaned_media(project)
    empty = remove_empty_tracks(project)
    return {
        'orphaned_media_removed': len(orphaned),
        'empty_tracks_removed': empty,
    }
