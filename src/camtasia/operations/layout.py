from __future__ import annotations
from camtasia.timing import seconds_to_ticks

from camtasia.timeline.track import _propagate_start_to_unified, ticks_to_seconds
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from camtasia.timeline.track import Track


def pack_track(track: Track, gap_seconds: float = 0.0) -> None:
    """Remove gaps between clips, packing them end-to-end.
    
    Sorts clips by start time, then repositions each to start
    immediately after the previous clip (plus optional gap).
    """
    if gap_seconds < 0:
        raise ValueError(f'gap_seconds must be non-negative, got {gap_seconds}')
    medias = track._data.get('medias', [])
    if not medias:
        return
    track._data['transitions'] = []
    medias.sort(key=lambda m: m.get('start', 0))
    gap_ticks = seconds_to_ticks(gap_seconds)
    cursor = 0
    for m in medias:
        m['start'] = cursor
        _propagate_start_to_unified(m)
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
            _propagate_start_to_unified(m)


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
        available = [m.get('id') for m in medias]
        raise KeyError(
            f"No clip with id={clip_id} on track index={track.index}. "
            f"Available clip IDs: {available}"
        )
    gap = target.get('duration', 0)
    target_start = target.get('start', 0)
    medias.pop(target_idx)
    transitions = track._data.get('transitions', [])
    track._data['transitions'] = [
        t for t in transitions
        if t.get('leftMedia') != clip_id and t.get('rightMedia') != clip_id
    ]
    for m in medias:
        if m.get('start', 0) >= target_start + gap:
            m['start'] -= gap
        _propagate_start_to_unified(m)


def snap_to_grid(track: Track, grid_seconds: float = 1.0) -> None:
    """Snap all clip start times to the nearest grid point.

    .. warning::
        Snapping can move two or more clips to the same grid point,
        creating overlapping clips on the track.  Callers should check
        ``track.overlaps()`` afterward and resolve any collisions
        (e.g. by calling :func:`pack_track`).
    """
    grid_ticks = seconds_to_ticks(grid_seconds)
    if grid_ticks <= 0:
        raise ValueError(f'Grid must be positive, got {grid_seconds}')
    for m in track._data.get('medias', []):
        start = m.get('start', 0)
        quotient, remainder = divmod(start, grid_ticks)
        if 2 * remainder > grid_ticks or (2 * remainder == grid_ticks and quotient % 2 == 1):
            quotient += 1
        m['start'] = max(0, quotient * grid_ticks)
        _propagate_start_to_unified(m)
    track._data['transitions'] = []
