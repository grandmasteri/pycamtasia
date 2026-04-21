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
    ) -> BaseClip:
        """Add a title card at the cursor position.

        Does NOT advance the cursor.
        """
        track = self._project.timeline.get_or_create_track(track_name)
        return track.add_title(text, start_seconds=self._cursor, duration_seconds=duration)

    def add_background_image(
        self,
        file_path: str | Path,
        *,
        track_name: str = 'Background',
        duration: float | None = None,
    ) -> BaseClip:
        """Import and place an image on a dedicated background track.

        The image starts at time 0 and fills the given duration. If
        ``duration`` is None, the image is placed for the entire current
        timeline (project.total_duration_seconds()).

        Args:
            file_path: Path to the background image.
            track_name: Name for the dedicated background track.
            duration: Duration in seconds. Defaults to the current
                project total duration.

        Returns:
            The placed image clip.
        """
        media = self._project.import_media(Path(file_path))
        track = self._project.timeline.get_or_create_track(track_name)
        effective_duration = duration if duration is not None else self._project.total_duration_seconds()
        return track.add_image(media.id, start_seconds=0.0, duration_seconds=effective_duration)

    def add_background_video(
        self,
        file_path: str | Path,
        *,
        track_name: str = 'Background',
        duration: float | None = None,
        mute: bool = True,
    ) -> BaseClip:
        """Import and place a video on a dedicated background track for
        an animated/dynamic background.

        Args:
            file_path: Path to the background video.
            track_name: Name for the dedicated background track.
            duration: Duration in seconds. Defaults to the video's
                native duration if known, else the current project total.
            mute: When True (default), the background video's audio is
                muted so it doesn't compete with voiceover/music.

        Returns:
            The placed video clip.
        """
        media = self._project.import_media(Path(file_path))
        track = self._project.timeline.get_or_create_track(track_name)
        if duration is None:
            # Use native video duration if available via the media entry,
            # otherwise fall back to the project total duration.
            native = getattr(media, 'duration_seconds', None)
            duration = float(native) if native else self._project.total_duration_seconds()
        clip = track.add_clip(
            'VMFile', media.id, start=0, duration=int(duration * 705600000),
        )
        if mute:
            # BaseClip.mute handles Group/StitchedMedia/UnifiedMedia dispatch too
            clip.mute()
        return clip
