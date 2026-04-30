"""Create timeline markers from presentation slide data."""
from __future__ import annotations

from typing import TYPE_CHECKING

from camtasia.timing import seconds_to_ticks

if TYPE_CHECKING:
    from camtasia.project import Project
    from camtasia.timeline.markers import MarkerList
    from camtasia.timeline.timeline import _TimelineMarkers


def mark_slides_from_presentation(
    project: Project,
    slides: list[dict],
    *,
    track_name: str | None = None,
) -> int:
    """Create timeline markers from slide timing data.

    Each slide dict must have ``time_seconds`` (float) and ``title`` (str).
    If *track_name* is given, markers are placed on that track's media
    markers; otherwise they are placed on the timeline-level markers.

    Args:
        project: The project to modify.
        slides: List of dicts with 'time_seconds' and 'title' keys.
        track_name: Optional track name for per-track markers.

    Returns:
        Number of markers created.

    Raises:
        KeyError: If *track_name* is given but no matching track exists.
    """
    marker_list: MarkerList | _TimelineMarkers
    if track_name is not None:
        track = project.timeline.find_track_by_name(track_name)
        if track is None:
            raise KeyError(f'No track named {track_name!r}')
        marker_list = track.markers
    else:
        marker_list = project.timeline.markers

    count = 0
    for slide in slides:
        time_ticks = seconds_to_ticks(slide['time_seconds'])
        marker_list.add(slide['title'], time_ticks)
        count += 1
    return count
