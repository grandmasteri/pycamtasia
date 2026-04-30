"""Audiate file support: project loading and word-level transcripts."""

from __future__ import annotations

from camtasia.audiate.project import SUPPORTED_TRANSLATION_LANGUAGES, AudiateProject
from camtasia.audiate.transcript import Transcript, TranscriptGap, Word

__all__ = ["SUPPORTED_TRANSLATION_LANGUAGES", "AudiateProject", "Transcript", "TranscriptGap", "Word"]
