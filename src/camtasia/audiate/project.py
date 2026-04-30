"""Audiate project reader for .audiate files (same JSON schema as .tscproj)."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import TYPE_CHECKING

from camtasia.audiate.transcript import Transcript
from camtasia.timing import EDIT_RATE

if TYPE_CHECKING:
    from camtasia.media_bin.media_bin import Media
    from camtasia.project import Project

SUPPORTED_TRANSLATION_LANGUAGES: list[str] = [
    "en", "de", "fr", "es", "it", "ja", "zh", "pt", "ko", "ru", "nl", "sv", "pl", "ar",
]
"""ISO 639-1 language codes supported for translation scaffolding."""


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

    @property
    def smart_scenes(self) -> list[dict]:
        """Scene segmentation dicts from project metadata.

        Returns an empty list if no scene data is present.
        """
        return self._data.get("metadata", {}).get("smartScenes", [])

    def apply_suggested_edits(
        self,
        *,
        remove_fillers: bool = True,
        remove_pauses: bool = True,
    ) -> dict:
        """Apply suggested transcript edits (filler removal and pause shortening).

        Chains ``Transcript.remove_filler_words`` and ``shorten_pauses`` to
        produce a cleaned transcript. Returns a dict describing the changes
        rather than mutating the project in place.

        Args:
            remove_fillers: Remove filler words (um, uh, ah, like).
            remove_pauses: Shorten long pauses to 0.2 s.

        Returns:
            Dict with keys ``fillers_removed`` (int), ``pauses_shortened`` (int),
            and ``transcript`` (the resulting Transcript).
        """
        transcript = self.transcript
        fillers_removed = 0
        pauses_shortened = 0

        if remove_fillers:
            fillers = transcript.detect_filler_words()
            fillers_removed = len(fillers)
            transcript = transcript.remove_filler_words()

        if remove_pauses:
            pauses = transcript.detect_pauses()
            pauses_shortened = len(pauses)
            transcript = transcript.shorten_pauses()

        return {
            "fillers_removed": fillers_removed,
            "pauses_shortened": pauses_shortened,
            "transcript": transcript,
        }

    def translate_script(self, target_language: str) -> Transcript:
        """Return a placeholder-translated transcript.

        This is scaffolding — real translation would require an external API.
        Each word's text is replaced with ``[{target_language}:{original}]``.

        Args:
            target_language: ISO 639-1 language code (e.g. ``'de'``).

        Returns:
            A new Transcript with placeholder-translated words.

        Raises:
            ValueError: If *target_language* is not in
                ``SUPPORTED_TRANSLATION_LANGUAGES``.
        """
        if target_language not in SUPPORTED_TRANSLATION_LANGUAGES:
            raise ValueError(
                f"Unsupported language '{target_language}'. "
                f"Supported: {SUPPORTED_TRANSLATION_LANGUAGES}"
            )
        from camtasia.audiate.transcript import Word

        words = self.transcript.words
        translated = [
            Word(
                text=f"[{target_language}:{w.text}]",
                start=w.start,
                end=w.end,
                word_id=w.word_id,
            )
            for w in words
        ]
        return Transcript(translated)

    def generate_audio(
        self,
        voice: str,
        *,
        apply_to_entire_project: bool = True,
    ) -> None:
        """Record TTS generation intent in project metadata.

        This is a stub — actual audio generation requires the Audiate backend.
        Stores the request as ``metadata.pendingTTS``.

        Args:
            voice: Voice identifier (e.g. ``'en-US-Neural2-F'``).
            apply_to_entire_project: Whether TTS covers the full project.
        """
        self._data.setdefault("metadata", {})["pendingTTS"] = {
            "voice": voice,
            "language": self.language,
            "applyToEntireProject": apply_to_entire_project,
        }

    def generate_avatar(self, avatar_id: str) -> None:
        """Record avatar generation intent in project metadata.

        This is a stub — actual avatar rendering requires the Audiate backend.

        Args:
            avatar_id: Identifier for the avatar to generate.
        """
        self._data.setdefault("metadata", {})["pendingAvatar"] = {
            "avatarId": avatar_id,
        }

    def save_as_translation(self, language_code: str, dest_path: Path) -> None:
        """Write a translated copy of this Audiate project to *dest_path*.

        Creates a deep copy of the project data, sets the language, replaces
        transcript word texts with placeholder markers, and writes the result.

        Args:
            language_code: ISO 639-1 code for the target language.
            dest_path: Destination file path.

        Raises:
            ValueError: If *language_code* is not in
                ``SUPPORTED_TRANSLATION_LANGUAGES``.
        """
        if language_code not in SUPPORTED_TRANSLATION_LANGUAGES:
            raise ValueError(
                f"Unsupported language '{language_code}'. "
                f"Supported: {SUPPORTED_TRANSLATION_LANGUAGES}"
            )
        data = copy.deepcopy(self._data)
        data["metadata"]["projectLanguage"] = language_code

        keyframes = (
            data["timeline"]["sceneTrack"]["scenes"][0]["csml"]
            ["tracks"][0]["parameters"]["transcription"]["keyframes"]
        )
        for kf in keyframes:
            parsed = json.loads(kf["value"])
            parsed["text"] = f"[{language_code}:{parsed['text']}]"
            kf["value"] = json.dumps(parsed)

        dest_path = Path(dest_path)
        dest_path.write_text(json.dumps(data, indent=2))

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
