"""Presentation slide import — place a sequence of slide images on the timeline."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from camtasia.project import Project
    from camtasia.timeline.clips.base import BaseClip


def import_slide_images(
    project: Project,
    image_paths: list[Path | str],
    *,
    per_slide_seconds: float = 5.0,
    track_name: str = 'Slides',
    transition_seconds: float = 0.0,
) -> list[BaseClip]:
    """Place a sequence of pre-rendered slide images on a dedicated track.

    The intended workflow is:

    1. In PowerPoint (or Keynote/Google Slides), export slides as PNG/JPG
       images ("File → Export As Pictures" or similar).
    2. Call :func:`import_slide_images` with the ordered list of image paths.

    Each image is imported into the project's media bin and placed on a
    new track, one after another with the specified per-slide duration.

    Args:
        project: Target project.
        image_paths: Ordered list of slide image files.
        per_slide_seconds: Duration each slide is on screen.
        track_name: Name of the dedicated slides track.
        transition_seconds: When > 0, adjacent slide pairs overlap by this
            duration, producing a cross-fade effect (via the existing fade
            in/out machinery on each clip).

    Returns:
        List of placed image clips, in order.
    """
    track = project.timeline.get_or_create_track(track_name)
    placed: list[BaseClip] = []
    cursor = 0.0
    for i, path in enumerate(image_paths):
        media = project.import_media(path)
        clip = track.add_image(
            media.id,
            start_seconds=cursor,
            duration_seconds=per_slide_seconds,
        )
        if transition_seconds > 0:
            # Fade in all but the first; fade out all but the last
            if i > 0:
                clip.fade_in(transition_seconds)
            if i < len(image_paths) - 1:
                clip.fade_out(transition_seconds)
        placed.append(clip)
        cursor += per_slide_seconds - transition_seconds
    return placed
