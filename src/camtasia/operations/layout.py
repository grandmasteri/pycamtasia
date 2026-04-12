from __future__ import annotations
from camtasia.timing import seconds_to_ticks, ticks_to_seconds
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from camtasia.timeline.track import Track


def pack_track(track: Track, gap_seconds: float = 0.0) -> None:
    """Remove gaps between clips, packing them end-to-end.
    
    Sorts clips by start time, then repositions each to start
    immediately after the previous clip (plus optional gap).
    """
    medias = track._data.get('medias', [])
    if not medias:
        return
    track._data['transitions'] = []
    medias.sort(key=lambda m: m.get('start', 0))
    gap_ticks = seconds_to_ticks(gap_seconds)
    cursor = 0
    for m in medias:
        m['start'] = cursor
        cursor += m.get('duration', 0) + gap_ticks


def ripple_insert(track: Track, position_seconds: float, duration_seconds: float) -> None:
    """Shift all clips at or after position forward by duration.
    
    Creates a gap at the insertion point.
    """
    pos_ticks = seconds_to_ticks(position_seconds)
    shift_ticks = seconds_to_ticks(duration_seconds)
    for m in track._data.get('medias', []):
        if m.get('start', 0) >= pos_ticks:
            m['start'] += shift_ticks


def ripple_delete(track: Track, clip_id: int) -> None:
    """Remove a clip and shift subsequent clips backward to close the gap."""
    medias = track._data.get('medias', [])
    target = None
    target_idx = None
    for i, m in enumerate(medias):
        if m.get('id') == clip_id:
            target = m
            target_idx = i
            break
    if target is None:
        raise KeyError(f'No clip with id={clip_id}')
    gap = target.get('duration', 0)
    target_start = target.get('start', 0)
    medias.pop(target_idx)
    transitions = track._data.get('transitions', [])
    track._data['transitions'] = [
        t for t in transitions
        if t.get('leftMedia') != clip_id and t.get('rightMedia') != clip_id
    ]
    for m in medias:
        if m.get('start', 0) > target_start:
            m['start'] -= gap


def snap_to_grid(track: Track, grid_seconds: float = 1.0) -> None:
    """Snap all clip start times to the nearest grid point."""
    grid_ticks = seconds_to_ticks(grid_seconds)
    if grid_ticks <= 0:
        raise ValueError(f'Grid must be positive, got {grid_seconds}')
    for m in track._data.get('medias', []):
        start = m.get('start', 0)
        m['start'] = round(start / grid_ticks) * grid_ticks
