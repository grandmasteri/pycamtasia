"""Device frame overlay builder — wrap a clip with a phone/laptop bezel image."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from camtasia.project import Project
    from camtasia.timeline.clips.base import BaseClip


def add_device_frame(
    project: Project,
    frame_image_path: str | Path,
    wrapped_clip: BaseClip,
    *,
    track_name: str = 'Device Frame',
    scale: float = 1.0,
) -> BaseClip:
    """Overlay a device bezel image (phone, laptop, tablet, etc.) on top of a clip.

    The frame image is imported as media and placed on a new track above
    the wrapped clip's track, matching its start and duration. Users
    should supply a PNG with a transparent cutout where the video shows through.

    Args:
        project: Target project.
        frame_image_path: Path to the bezel PNG (should have a transparent cutout).
        wrapped_clip: The clip (typically a screen recording or video) to
            wrap. The frame inherits its start and duration.
        track_name: Name for the new track hosting the frame overlay.
            Will be placed above the wrapped clip's track.
        scale: Uniform scale factor applied to the frame clip.

    Returns:
        The placed frame clip (IMFile).
    """
    from camtasia.timing import ticks_to_seconds
    media = project.import_media(frame_image_path)
    track = project.timeline.get_or_create_track(track_name)
    frame_clip = track.add_image(
        media.id,
        start_seconds=ticks_to_seconds(wrapped_clip.start),
        duration_seconds=ticks_to_seconds(wrapped_clip.duration),
    )
    frame_clip.scale = (scale, scale)
    return frame_clip


def remove_device_frame(
    project: Project,
    track_name: str = 'Device Frame',
) -> None:
    """Remove the device frame track created by :func:`add_device_frame`.

    Finds the track by name and removes it from the timeline.

    Args:
        project: Target project.
        track_name: Name of the device frame track to remove.

    Raises:
        ValueError: If no track with the given name exists.
    """
    removed = project.timeline.remove_tracks_by_name(track_name)
    if removed == 0:
        raise ValueError(f'No track named {track_name!r} found')
