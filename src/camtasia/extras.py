"""Utilities and helper functions."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator

    from camtasia.media_bin import Media
    from camtasia.project import Project
    from camtasia.timeline.marker import Marker
    from camtasia.timeline.track import Track


def media_markers(project: Project) -> Iterator[tuple[Marker, Media, Track]]:
    """Get all media markers in a project.

    Args:
        project: The Project to fetch data from.

    Yields:
        Tuples of ``(Marker, Media, Track)`` for each media marker.
    """
    return (
        (marker, media, track)  # type: ignore[misc]
        for track in project.timeline.tracks
        for media in track.medias
        for marker in media.markers  # type: ignore[attr-defined]
    )
