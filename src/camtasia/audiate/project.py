"""Audiate project reader for .audiate files (same JSON schema as .tscproj)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

from camtasia.audiate.transcript import Transcript
from camtasia.timing import EDIT_RATE

if TYPE_CHECKING:
    from camtasia.media_bin.media_bin import Media
    from camtasia.project import Project


class AudiateProject:
    """Loads and exposes data from a TechSmith Audiate .audiate file.

    The .audiate format uses the same JSON schema as Camtasia .tscproj files.
    The transcript lives at ``tracks[0].parameters.transcription.keyframes``.

    Args:
        file_path: Path to the .audiate file or its containing directory.
    """

    def __init__(self, file_path: str | Path) -> None:
        path = Path(file_path).resolve()
        if path.is_dir():
            matches = list(path.glob("*.audiate"))
            if not matches:
                raise FileNotFoundError(f"No .audiate file found in {path}")
            path = matches[0]
        self._file_path = path
        self._data: dict = json.loads(path.read_text())

    @property
    def transcript(self) -> Transcript:
        """Word-level transcript parsed from the first track's transcription keyframes."""
        keyframes = (
            self._data["timeline"]["sceneTrack"]["scenes"][0]["csml"]
            ["tracks"][0]["parameters"]["transcription"]["keyframes"]
        )
        return Transcript.from_audiate_keyframes(keyframes)

    @property
    def language(self) -> str:
        """Project language code (e.g. 'en')."""
        return self._data["metadata"]["projectLanguage"]  # type: ignore[no-any-return]

    @language.setter
    def language(self, value: str) -> None:
        self._data["metadata"]["projectLanguage"] = value

    @property
    def session_id(self) -> str:
        """Camtasia linking UUID (caiCamtasiaSessionId)."""
        return self._data["metadata"]["caiCamtasiaSessionId"]  # type: ignore[no-any-return]

    @property
    def audio_duration(self) -> float:
        """Total audio duration in seconds, from the first track's first media clip."""
        track = (
            self._data["timeline"]["sceneTrack"]["scenes"][0]["csml"]["tracks"][0]
        )
        media = track["medias"][0]
        return float(media["duration"] / EDIT_RATE)

    @property
    def source_audio_path(self) -> Path:
        """Path to the source audio file (resolved relative to the .audiate file)."""
        src_id = (
            self._data["timeline"]["sceneTrack"]["scenes"][0]["csml"]
            ["tracks"][0]["medias"][0]["src"]
        )
        for entry in self._data.get("sourceBin", []):
            if entry["id"] == src_id:
                return (self._file_path.parent / entry["src"]).resolve()  # type: ignore[no-any-return]
        raise FileNotFoundError(f"Source with id={src_id} not found in sourceBin")

    def find_linked_media(self, project: Project) -> Media | None:
        """Find the Camtasia media entry linked to this Audiate session.

        Searches clips in the Camtasia project for one whose
        ``audiateLinkedSession`` matches this project's ``session_id``,
        then returns the corresponding ``Media`` from the source bin.

        Args:
            project: A loaded Camtasia Project.

        Returns:
            The linked Media, or None if no match is found.
        """
        sid = self.session_id
        for track in project.timeline.tracks:
            for clip in track.clips:
                linked = clip._data.get("audiateLinkedSession", "")
                if linked == sid:
                    src_id = clip._data.get("src")
                    if src_id is not None:
                        try:
                            return project.media_bin[int(src_id)]
                        except KeyError:
                            pass
        return None

    def __repr__(self) -> str:
        return f'AudiateProject(file_path="{self._file_path}")'
