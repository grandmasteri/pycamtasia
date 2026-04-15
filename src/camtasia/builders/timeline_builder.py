from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from camtasia.project import Project
    from camtasia.timeline.clips.base import BaseClip


class TimelineBuilder:
    """High-level builder for assembling Camtasia timelines.

    Provides a cursor-based API for sequentially placing clips
    with automatic timing management.

    Usage:
        builder = TimelineBuilder(project)
        builder.add_audio_sequence(['intro.wav', 'main.wav'], pause=1.0)
        builder.add_background_image('bg.png')
        builder.add_title('My Video', duration=5.0)
    """

    def __init__(self, project: Project) -> None:
        self._project = project
        self._cursor: float = 0.0

    @property
    def cursor(self) -> float:
        """Current timeline position in seconds."""
        return self._cursor

    @cursor.setter
    def cursor(self, value: float) -> None:
        """Set the current cursor position in seconds."""
        if value < 0:
            raise ValueError(f'Cursor must be non-negative, got {value}')
        self._cursor = value

    def advance(self, seconds: float) -> TimelineBuilder:
        """Move cursor forward by seconds."""
        self._cursor += seconds
        return self

    def seek(self, seconds: float) -> TimelineBuilder:
        """Set cursor to an absolute position."""
        self.cursor = seconds
        return self

    def add_audio(
        self,
        file_path: str | Path,
        *,
        track_name: str = 'Audio',
        duration: float | None = None,
    ) -> BaseClip:
        """Import and place an audio file at the cursor position.

        Advances the cursor by the clip duration.
        """
        media = self._project.import_media(Path(file_path))
        track = self._project.timeline.get_or_create_track(track_name)
        dur = duration if duration is not None else (media.duration_seconds if media.duration_seconds is not None else 5.0)
        clip = track.add_audio(media.id, start_seconds=self._cursor, duration_seconds=dur)
        self._cursor += dur
        return clip

    def add_pause(self, seconds: float) -> TimelineBuilder:
        """Add a pause (advance cursor without placing a clip)."""
        self._cursor += seconds
        return self

    def add_image(
        self,
        file_path: str | Path,
        *,
        track_name: str = 'Content',
        duration: float = 5.0,
    ) -> BaseClip:
        """Import and place an image at the cursor position.

        Does NOT advance the cursor (images are visual overlays).
        """
        media = self._project.import_media(Path(file_path))
        track = self._project.timeline.get_or_create_track(track_name)
        return track.add_image(media.id, start_seconds=self._cursor, duration_seconds=duration)

    def add_title(
        self,
        text: str,
        *,
        track_name: str = 'Titles',
        duration: float = 5.0,
        subtitle: str = '',
    ) -> BaseClip:
        """Add a title card at the cursor position.

        Does NOT advance the cursor.
        """
        track = self._project.timeline.get_or_create_track(track_name)
        return track.add_title(text, start_seconds=self._cursor, duration_seconds=duration)
