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


def pack_track(track: Track, gap_seconds: float = 0.0, *, preserve_groups: bool = False) -> None:
    """Remove gaps between clips, packing them end-to-end.

    Sorts clips by start time, then repositions each to start
    immediately after the previous clip (plus optional gap).

    Args:
        track: Track to pack.
        gap_seconds: Optional gap between clips in seconds.
        preserve_groups: When ``True``, Group clips keep their original
            spacing relative to their neighbors (they are not moved).
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
        if preserve_groups and m.get('_type') == 'Group':
            # Groups keep their position; advance cursor past them
            group_end = _to_ticks(m.get('start', 0)) + _to_ticks(m.get('duration', 0))
            cursor = max(cursor, group_end)
            if i < len(medias) - 1:
                cursor += gap_ticks
            continue
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


def ripple_extend(track: Track, clip_id: int, extend_seconds: float) -> None:
    """Extend a clip's duration and push all following clips forward.

    Args:
        track: Track containing the clip.
        clip_id: ID of the clip to extend.
        extend_seconds: Seconds to add (positive) or remove (negative) from duration.

    Raises:
        KeyError: If no clip with the given ID exists on the track.
        ValueError: If the resulting duration would be negative.
    """
    medias = track._data.get('medias', [])
    target = None
    for m in medias:
        if m.get('id') == clip_id:
            target = m
            break
    if target is None:
        available = [m.get('id') for m in medias]
        raise KeyError(
            f"No clip with id={clip_id} on track index={track.index}. "
            f"Available clip IDs: {available}"
        )
    old_duration = _to_ticks(target.get('duration', 0))
    extend_ticks = seconds_to_ticks(extend_seconds)
    new_duration = old_duration + extend_ticks
    if new_duration < 0:
        raise ValueError(
            f"Resulting duration would be negative: {old_duration} + {extend_ticks} = {new_duration}"
        )
    target['duration'] = new_duration
    _propagate_start_to_unified(target)
    target_end = _to_ticks(target.get('start', 0)) + old_duration
    shifted = False
    for m in medias:
        if m is not target and _to_ticks(m.get('start', 0)) >= target_end:
            m['start'] = _to_ticks(m.get('start', 0)) + extend_ticks
            _propagate_start_to_unified(m)
            shifted = True
    if shifted or extend_ticks != 0:
        track._data['transitions'] = []


def ripple_delete_range(track: Track, start_seconds: float, end_seconds: float) -> None:
    """Delete all clips (or parts) within a time range, then close the gap.

    Clips fully inside the range are removed. Clips partially overlapping
    are trimmed. All clips after the range shift backward by the range width.

    Args:
        track: Track to operate on.
        start_seconds: Start of the range in seconds.
        end_seconds: End of the range in seconds.

    Raises:
        ValueError: If start_seconds >= end_seconds or either is negative.
    """
    if start_seconds < 0:
        raise ValueError(f'start_seconds must be non-negative, got {start_seconds}')
    if end_seconds <= start_seconds:
        raise ValueError('end_seconds must be greater than start_seconds')
    range_start = seconds_to_ticks(start_seconds)
    range_end = seconds_to_ticks(end_seconds)
    range_width = range_end - range_start
    medias = track._data.get('medias', [])
    removed_ids: set[int] = set()
    to_remove: list[int] = []
    for i, m in enumerate(medias):
        clip_start = _to_ticks(m.get('start', 0))
        clip_dur = _to_ticks(m.get('duration', 0))
        clip_end = clip_start + clip_dur
        if clip_start >= range_start and clip_end <= range_end:
            # Fully inside — remove
            to_remove.append(i)
            removed_ids.add(m.get('id'))
        elif clip_start < range_start and clip_end > range_end:
            # Clip spans the entire range — trim out the middle portion
            m['duration'] = clip_dur - range_width
            _propagate_start_to_unified(m)
        elif clip_start < range_start < clip_end <= range_end:
            # Clip starts before range, ends inside — trim end
            m['duration'] = range_start - clip_start
            _propagate_start_to_unified(m)
        elif range_start <= clip_start < range_end < clip_end:
            # Clip starts inside range, ends after — trim start and shift
            trim = range_end - clip_start
            m['start'] = range_start
            m['duration'] = clip_dur - trim
            _propagate_start_to_unified(m)
    # Remove fully-contained clips (reverse order to preserve indices)
    for i in reversed(to_remove):
        medias.pop(i)
    # Shift clips after the range backward
    for m in medias:
        clip_start = _to_ticks(m.get('start', 0))
        if clip_start >= range_end:
            m['start'] = clip_start - range_width
            _propagate_start_to_unified(m)
    # Clean transitions referencing removed clips
    if removed_ids:
        transitions = track._data.get('transitions', [])
        track._data['transitions'] = [
            t for t in transitions
            if t.get('leftMedia') not in removed_ids and t.get('rightMedia') not in removed_ids
        ]


def ripple_move(track: Track, clip_id: int, delta_seconds: float) -> None:
    """Shift a clip and all clips to its right by delta_seconds.

    Args:
        track: Track containing the clip.
        clip_id: ID of the clip to move.
        delta_seconds: Seconds to shift (positive = right, negative = left).

    Raises:
        KeyError: If no clip with the given ID exists on the track.
        ValueError: If any clip would be shifted to a negative start time.
    """
    medias = track._data.get('medias', [])
    target = None
    for m in medias:
        if m.get('id') == clip_id:
            target = m
            break
    if target is None:
        available = [m.get('id') for m in medias]
        raise KeyError(
            f"No clip with id={clip_id} on track index={track.index}. "
            f"Available clip IDs: {available}"
        )
    delta_ticks = seconds_to_ticks(delta_seconds)
    target_start = _to_ticks(target.get('start', 0))
    # Shift target and all clips at or after target's start
    for m in medias:
        if _to_ticks(m.get('start', 0)) >= target_start:
            new_start = _to_ticks(m.get('start', 0)) + delta_ticks
            if new_start < 0:
                raise ValueError(
                    f"Clip id={m.get('id')} would have negative start time: {new_start}"
                )
            m['start'] = new_start
            _propagate_start_to_unified(m)
    track._data['transitions'] = []


def ripple_move_multi(
    tracks: list[Track],
    clip_ids_per_track: list[list[int]],
    delta_seconds: float,
) -> None:
    """Multi-track ripple move: shift specified clips and all to their right.

    Args:
        tracks: List of tracks to operate on.
        clip_ids_per_track: For each track, the list of clip IDs to move.
            Each inner list should contain at least one clip ID.
        delta_seconds: Seconds to shift (positive = right, negative = left).

    Raises:
        ValueError: If tracks and clip_ids_per_track have different lengths,
            or if any clip would be shifted to a negative start time.
        KeyError: If a clip ID is not found on its track.
    """
    if len(tracks) != len(clip_ids_per_track):
        raise ValueError(
            f"tracks and clip_ids_per_track must have same length, "
            f"got {len(tracks)} and {len(clip_ids_per_track)}"
        )
    for track, clip_ids in zip(tracks, clip_ids_per_track):
        for clip_id in clip_ids:
            ripple_move(track, clip_id, delta_seconds)


def snap_to_clip_edge(track: Track, tolerance_seconds: float = 0.05) -> None:
    """Snap clip starts/ends to nearest neighboring clip boundary within tolerance.

    For each clip, checks if its start or end is within tolerance of any
    other clip's start or end. If so, snaps to that boundary.

    Args:
        track: Track to operate on.
        tolerance_seconds: Maximum distance in seconds to snap.

    Raises:
        ValueError: If tolerance_seconds is negative.
    """
    if tolerance_seconds < 0:
        raise ValueError(f'tolerance_seconds must be non-negative, got {tolerance_seconds}')
    medias = track._data.get('medias', [])
    if len(medias) < 2:
        return
    tolerance_ticks = seconds_to_ticks(tolerance_seconds)
    # Collect all edges (start and end of each clip)
    edges: list[int] = []
    for m in medias:
        s = _to_ticks(m.get('start', 0))
        d = _to_ticks(m.get('duration', 0))
        edges.append(s)
        edges.append(s + d)
    shifted = False
    for m in medias:
        clip_start = _to_ticks(m.get('start', 0))
        clip_dur = _to_ticks(m.get('duration', 0))
        clip_end = clip_start + clip_dur
        # Find nearest edge for start (excluding own start and own end)
        best_start_dist = tolerance_ticks + 1
        best_start_edge = clip_start
        for e in edges:
            if e in (clip_start, clip_end):
                continue
            dist = abs(clip_start - e)
            if dist <= tolerance_ticks and dist < best_start_dist:
                best_start_dist = dist
                best_start_edge = e
        # Find nearest edge for end (excluding own start and own end)
        best_end_dist = tolerance_ticks + 1
        best_end_edge = clip_end
        for e in edges:
            if e in (clip_start, clip_end):
                continue
            dist = abs(clip_end - e)
            if dist <= tolerance_ticks and dist < best_end_dist:
                best_end_dist = dist
                best_end_edge = e
        # Apply snaps
        new_start = best_start_edge if best_start_dist <= tolerance_ticks else clip_start
        new_end = best_end_edge if best_end_dist <= tolerance_ticks else clip_end
        new_dur = new_end - new_start
        if new_dur > 0 and (new_start != clip_start or new_dur != clip_dur):
            m['start'] = new_start
            m['duration'] = new_dur
            _propagate_start_to_unified(m)
            shifted = True
    if shifted:
        track._data['transitions'] = []


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


def ripple_replace_in_group(
    group: Any,
    clip_id: int,
    new_media: dict[str, Any],
) -> bool:
    """Replace a clip inside a Group's internal tracks, rippling timing.

    Recurses into nested Group clips. Returns ``True`` if the clip was
    found and replaced, ``False`` otherwise.

    Args:
        group: A Group clip (or any object with a ``_data`` dict
            containing ``tracks``).
        clip_id: ID of the clip to replace.
        new_media: Dict describing the replacement media.

    Returns:
        ``True`` if the replacement was made.
    """
    import copy as _copy

    for inner_track in group._data.get('tracks', []):
        medias = inner_track.get('medias', [])
        for i, m in enumerate(medias):
            if m.get('id') == clip_id:
                old_duration = m.get('duration', 0)
                replacement = _copy.deepcopy(new_media)
                replacement['start'] = m.get('start', 0)
                new_duration = replacement.get('duration', old_duration)
                delta = new_duration - old_duration
                replacement['id'] = clip_id
                _propagate_start_to_unified(replacement)
                medias[i] = replacement
                if delta != 0:
                    for other in medias:
                        if other is not replacement and other.get('start', 0) > replacement['start']:
                            other['start'] = other.get('start', 0) + delta
                            _propagate_start_to_unified(other)
                return True
            # Recurse into nested Groups
            if m.get('_type') == 'Group':
                from camtasia.timeline.clips import clip_from_dict
                nested = clip_from_dict(m)
                if ripple_replace_in_group(nested, clip_id, new_media):
                    return True
    return False
