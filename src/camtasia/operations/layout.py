from __future__ import annotations

from fractions import Fraction
from typing import TYPE_CHECKING, Any

from camtasia.timeline.track import _propagate_start_to_unified
from camtasia.timing import seconds_to_ticks

if TYPE_CHECKING:
    from camtasia.timeline.track import Track


def _to_ticks(v: Any) -> int:
    """Convert a tick value (int, str fraction like ``'705600000/2'``, etc.) to int."""
    return int(Fraction(str(v))) if v is not None else 0


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
    medias.sort(key=lambda m: _to_ticks(m.get('start', 0)))
    gap_ticks = seconds_to_ticks(gap_seconds)
    cursor = 0
    any_shifted = False
    for i, m in enumerate(medias):
        if _to_ticks(m.get('start', 0)) != cursor:
            any_shifted = True
        m['start'] = cursor
        _propagate_start_to_unified(m)
        cursor += _to_ticks(m.get('duration', 0))
        if i < len(medias) - 1:
            cursor += gap_ticks
    if any_shifted:
        track._data['transitions'] = []


def ripple_insert(track: Track, position_seconds: float, duration_seconds: float) -> None:
    """Shift all clips at or after position forward by duration.

    Creates a gap at the insertion point.
    """
    if position_seconds < 0:
        raise ValueError(f'position_seconds must be non-negative, got {position_seconds}')
    if duration_seconds < 0:
        raise ValueError(f'duration_seconds must be non-negative, got {duration_seconds}')
    pos_ticks = seconds_to_ticks(position_seconds)
    shift_ticks = seconds_to_ticks(duration_seconds)
    shifted = False
    for m in track._data.get('medias', []):
        if _to_ticks(m.get('start', 0)) >= pos_ticks:
            m['start'] = _to_ticks(m.get('start', 0)) + shift_ticks
            _propagate_start_to_unified(m)
            shifted = True
    if shifted:
        track._data['transitions'] = []


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
    gap = _to_ticks(target.get('duration', 0))
    target_start = _to_ticks(target.get('start', 0))
    medias.pop(target_idx)
    transitions = track._data.get('transitions', [])
    track._data['transitions'] = [
        t for t in transitions
        if t.get('leftMedia') != clip_id and t.get('rightMedia') != clip_id
    ]
    for m in medias:
        if _to_ticks(m.get('start', 0)) >= target_start + gap:
            m['start'] = _to_ticks(m.get('start', 0)) - gap
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
    shifted = False
    for m in track._data.get('medias', []):
        start = _to_ticks(m.get('start', 0))
        quotient, remainder = divmod(start, grid_ticks)
        if 2 * remainder >= grid_ticks:
            quotient += 1
        new_start = max(0, quotient * grid_ticks)
        if new_start != start:
            m['start'] = new_start
            _propagate_start_to_unified(m)
            shifted = True
    if shifted:
        track._data['transitions'] = []
