"""Batch operations — apply the same transformation to multiple clips at once."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Iterable

if TYPE_CHECKING:
    from camtasia.timeline.clips.base import BaseClip
    from camtasia.timeline.track import Track
    from camtasia.timeline.timeline import Timeline


def apply_to_clips(
    clips: Iterable[BaseClip],
    fn: Callable[[BaseClip], Any],
) -> int:
    """Apply a function to each clip. Returns count of clips processed."""
    count = 0
    for clip in clips:
        fn(clip)
        count += 1
    return count


def apply_to_track(
    track: Track,
    fn: Callable[[BaseClip], Any],
) -> int:
    """Apply a function to every clip on a track."""
    return apply_to_clips(track.clips, fn)


def apply_to_all_tracks(
    timeline: Timeline,
    fn: Callable[[BaseClip], Any],
) -> int:
    """Apply a function to every clip on every track."""
    count = 0
    for track in timeline.tracks:
        count += apply_to_track(track, fn)
    return count


def set_opacity_all(clips: Iterable[BaseClip], opacity: float) -> int:
    """Set opacity on all clips."""
    return apply_to_clips(clips, lambda c: c.set_opacity(opacity))


def fade_all(
    clips: Iterable[BaseClip],
    fade_in: float = 0.5,
    fade_out: float = 0.5,
) -> int:
    """Apply fade-in and fade-out to all clips."""
    return apply_to_clips(clips, lambda c: c.fade(fade_in, fade_out))


def scale_all(clips: Iterable[BaseClip], factor: float) -> int:
    """Set uniform scale on all clips."""
    return apply_to_clips(clips, lambda c: c.scale_to(factor))


def move_all(
    clips: Iterable[BaseClip],
    dx: float = 0.0,
    dy: float = 0.0,
) -> int:
    """Offset all clips by (dx, dy) from their current position."""
    def _offset(clip: BaseClip) -> None:
        x, y = clip.translation
        clip.move_to(x + dx, y + dy)
    return apply_to_clips(clips, _offset)
