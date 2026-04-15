"""Utilities for cleaning up Camtasia projects."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from camtasia.project import Project

from camtasia.types import CompactResult


def _collect_source_ids(clip_data: dict) -> set[int]:
    ids = set()
    src = clip_data.get('src')
    if src is not None:
        ids.add(src)
    for track in clip_data.get('tracks', []):
        for media in track.get('medias', []):
            ids.update(_collect_source_ids(media))
            if 'video' in media:
                ids.update(_collect_source_ids(media['video']))
            if 'audio' in media:
                ids.update(_collect_source_ids(media['audio']))
    # StitchedMedia stores sub-clips in 'medias' directly
    for nested in clip_data.get('medias', []):
        ids.update(_collect_source_ids(nested))
    # UnifiedMedia stores sub-clips in 'video'/'audio'
    if 'video' in clip_data:
        ids.update(_collect_source_ids(clip_data['video']))
    if 'audio' in clip_data:
        ids.update(_collect_source_ids(clip_data['audio']))
    return ids


def remove_orphaned_media(project: Project) -> list[int]:
    """Remove media entries not referenced by any clip.

    Returns list of removed media IDs.
    """
    referenced_ids: set[int] = set()
    for track in project.timeline.tracks:
        for m in track._data.get('medias', []):
            referenced_ids.update(_collect_source_ids(m))

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


def compact_project(project: Project) -> CompactResult:
    """Run all cleanup operations on a project.

    Returns a summary dict with counts of items cleaned.
    """
    orphaned = remove_orphaned_media(project)
    empty = remove_empty_tracks(project)
    return {
        'orphaned_media_removed': len(orphaned),
        'empty_tracks_removed': empty,
    }
