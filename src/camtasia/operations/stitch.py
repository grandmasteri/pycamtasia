"""Auto-stitch adjacent same-source clips on a track.

This is an explicit post-split operation — users call it after cutting
clips to re-join adjacent segments that share the same media source.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from camtasia.timeline.clips.base import BaseClip
    from camtasia.timeline.track import Track


def auto_stitch_on_track(track: Track) -> list[BaseClip]:
    """Scan a track for adjacent same-source clips and stitch them.

    Two clips are considered adjacent when the first clip's end tick
    equals the second clip's start tick and both reference the same
    ``src`` media ID.

    Args:
        track: The track to scan.

    Returns:
        List of stitched clips produced (one per group of adjacent
        same-source clips).  Returns an empty list if nothing was
        stitched.
    """
    clips = sorted(track.clips, key=lambda c: c.start)
    if len(clips) < 2:
        return []

    groups: list[list[int]] = []
    current_group: list[int] = [clips[0].id]
    for i in range(1, len(clips)):
        prev = clips[i - 1]
        curr = clips[i]
        prev_end = prev.start + prev.duration
        same_source = (
            prev.source_id is not None
            and prev.source_id == curr.source_id
        )
        if same_source and prev_end == curr.start:
            current_group.append(curr.id)
        else:
            if len(current_group) >= 2:
                groups.append(current_group)
            current_group = [curr.id]
    if len(current_group) >= 2:
        groups.append(current_group)

    results: list[BaseClip] = []
    for group_ids in groups:
        stitched = track.stitch_adjacent(group_ids)
        results.append(stitched)
    return results
