"""Media-bin operations: add media to track and remove media."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from camtasia.effects import Effect
    from camtasia.project import Project
    from camtasia.timeline.clips.base import BaseClip


_MEDIA_TYPE_TO_CLIP = {0: "VMFile", 1: "IMFile", 2: "AMFile"}


def add_media_to_track(
    proj: Project,
    track_index: int,
    media_id: int,
    start: int,
    duration: int | None = None,
    effects: list[Effect] | None = None,
) -> BaseClip:
    """Add a track reference to media-bin media.

    Args:
        proj: The Camtasia project.
        track_index: The index of the track to which to add media.
        media_id: The id of the media to be added to the track.
        start: The start position in ticks on the timeline.
        duration: The duration in ticks. Defaults to the source media range.
        effects: An optional sequence of Effect objects.

    Raises:
        KeyError: Specified track or media can't be found.
        ValueError: Media type is unknown.
    """
    track = proj.timeline.tracks[track_index]
    media = proj.media_bin[media_id]

    if duration is None:
        r = media.range
        duration = r[1] - r[0]

    media_type = media.type
    clip_type = _MEDIA_TYPE_TO_CLIP.get(media_type.value if media_type is not None else -1)
    if clip_type is None:
        raise ValueError(f"Unknown media type {media_type!r} for media {media_id}")

    effects_list = [e.data for e in effects] if effects else []
    return track.add_clip(clip_type, media_id, start, duration, effects=effects_list)


def remove_media(project: Project, media_id: int, clear_tracks: bool = False) -> None:
    """Remove a piece of media from the media-bin.

    By default, raises ``ValueError`` if references to the media exist on
    tracks.  Set *clear_tracks* to ``True`` to remove those references
    automatically before deleting the media.

    Args:
        project: The Camtasia project containing the media.
        media_id: The ID of the media bin media to remove.
        clear_tracks: Whether to remove references to the media from tracks.

    Raises:
        KeyError: The project has no media with the specified ID.
        ValueError: *clear_tracks* is ``False`` and references to the media
            exist on tracks.
    """
    for track in project.timeline.tracks:
        for mid in [tm.id for tm in track.medias if tm.source_id == media_id]:
            if not clear_tracks:
                raise ValueError("Attempt to remove media from media-bin while references exist on tracks")
            track.remove_clip(mid)

    del project.media_bin[media_id]
