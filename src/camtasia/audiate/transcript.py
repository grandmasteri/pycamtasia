"""Word-level transcript with timestamps, parsed from Audiate keyframes or WhisperX."""

from __future__ import annotations

from dataclasses import dataclass
import json
import re

from camtasia.timing import EDIT_RATE


@dataclass
class Word:
    """A single transcribed word with timing information.

    Attributes:
        text: The word text.
        start: Start time in seconds.
        end: End time in seconds, or None if unavailable.
        word_id: Unique identifier for this word.
    """

    text: str
    start: float
    end: float | None
    word_id: str


class Transcript:
    """Word-level transcript with search and range queries.

    Args:
        words: List of Word objects comprising the transcript.
    """

    def __init__(self, words: list[Word]) -> None:
        self._words = words

    @property
    def words(self) -> list[Word]:
        """All words in the transcript."""
        return self._words

    @property
    def full_text(self) -> str:
        """All words joined by spaces."""
        return " ".join(w.text for w in self._words)

    @property
    def duration(self) -> float:
        """Time of the last word's end (or start if end is None)."""
        if not self._words:
            return 0.0
        last = self._words[-1]
        return last.end if last.end is not None else last.start

    def find_phrase(self, phrase: str) -> Word | None:
        """Find the first word matching the start of a phrase.

        Args:
            phrase: Phrase to search for (case-insensitive).

        Returns:
            The first Word where the phrase begins, or None.
        """
        phrase_lower = phrase.lower()
        text_words = phrase_lower.split()
        if not text_words:
            return None
        def _normalize(s: str) -> str:
            return re.sub(r"[^\w\s]", "", s).strip()

        for i, word in enumerate(self._words):
            if _normalize(word.text.lower()) == _normalize(text_words[0]):
                if len(text_words) == 1:
                    return word
                remaining = text_words[1:]
                if i + len(remaining) < len(self._words) and all(
                    _normalize(self._words[i + 1 + j].text.lower()) == _normalize(remaining[j])
                    for j in range(len(remaining))
                ):
                    return word
        return None

    def words_in_range(self, start_seconds: float, end_seconds: float) -> list[Word]:
        """Return words whose start time falls within [start, end].

        Args:
            start_seconds: Range start in seconds.
            end_seconds: Range end in seconds.

        Returns:
            List of words in the time range.
        """
        return [w for w in self._words if start_seconds <= w.start <= end_seconds]

    @classmethod
    def from_audiate_keyframes(cls, keyframes: list[dict]) -> Transcript:
        """Parse Audiate transcription keyframes into a Transcript.

        Each keyframe has a ``time`` in editRate ticks and a JSON-encoded
        ``value`` containing ``id`` and ``text`` fields.

        Args:
            keyframes: Raw keyframe dicts from
                ``tracks[0].parameters.transcription.keyframes``.

        Returns:
            A Transcript instance.
        """
        words: list[Word] = []
        for i, kf in enumerate(keyframes):
            parsed = json.loads(kf["value"])
            start = kf["time"] / EDIT_RATE
            # Use next keyframe's time as end, if available
            end = keyframes[i + 1]["time"] / EDIT_RATE if i + 1 < len(keyframes) else None
            words.append(Word(
                text=parsed["text"],
                start=start,
                end=end,
                word_id=parsed["id"],
            ))
        return cls(words)

    @classmethod
    def from_whisperx_result(cls, result: dict) -> Transcript:
        """Parse a WhisperX alignment result into a Transcript.

        Expected format::

            result['segments'][*]['words'][*] = {
                'word': str, 'start': float, 'end': float
            }

        Args:
            result: WhisperX result dict with ``segments``.

        Returns:
            A Transcript instance.
        """
        words: list[Word] = []
        for seg in result.get("segments", []):
            for _i, w in enumerate(seg.get("words", [])):
                words.append(Word(
                    text=w["word"],
                    start=w.get("start", 0.0),
                    end=w.get("end"),
                    word_id=f"wx-{len(words)}",
                ))
        return cls(words)
