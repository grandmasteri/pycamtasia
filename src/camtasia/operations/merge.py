"""Merge tracks from one project into another."""
from __future__ import annotations

import copy
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from camtasia.project import Project


def merge_tracks(
    source: Project,
    target: Project,
    *,
    offset_seconds: float = 0.0,
) -> int:
    """Copy all non-empty tracks from source into target.

    Clips are offset by offset_seconds on the target timeline.
    Media entries are copied to the target's source bin with new IDs.

    Args:
        source: Project to copy tracks from.
        target: Project to copy tracks into.
        offset_seconds: Time offset for all copied clips.

    Returns:
        Number of tracks copied.
    """
    from camtasia.timing import seconds_to_ticks

    offset_ticks = seconds_to_ticks(offset_seconds)

    # Build media ID mapping (source ID -> target ID)
    id_map: dict[int, int] = {}
    for media in source.media_bin:
        existing = target.find_media_by_name(media.identity)
        if existing:
            id_map[media.id] = existing.id
        else:
            new_id = target.media_bin.next_id()
            entry = copy.deepcopy(media._data)
            entry['id'] = new_id
            target._data['sourceBin'].append(entry)
            id_map[media.id] = new_id

    # Copy non-empty tracks
    count = 0
    for track in source.timeline.tracks:
        if len(track) == 0:
            continue

        new_track = target.timeline.add_track(track.name)
        base_id = target.timeline.next_clip_id()

        for clip_data in track._data.get('medias', []):
            new_clip = copy.deepcopy(clip_data)
            new_clip['id'] = base_id
            base_id += 1
            new_clip['start'] = new_clip.get('start', 0) + offset_ticks
            if 'src' in new_clip and new_clip['src'] in id_map:
                new_clip['src'] = id_map[new_clip['src']]
            new_track._data.setdefault('medias', []).append(new_clip)

        count += 1

    return count
