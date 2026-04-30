"""Word-level transcript with timestamps, parsed from Audiate keyframes or WhisperX."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re

from camtasia.timing import EDIT_RATE

_DEFAULT_FILLERS: set[str] = {"um", "uh", "ah", "like"}


def _format_srt_time(seconds: float) -> str:
    """Format seconds as SRT timecode ``HH:MM:SS,mmm``."""
    seconds = max(0.0, seconds)
    total_ms = round(seconds * 1000)
    h = total_ms // 3_600_000
    total_ms %= 3_600_000
    m = total_ms // 60_000
    total_ms %= 60_000
    s = total_ms // 1000
    ms = total_ms % 1000
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


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

    def to_srt(self, path: Path | None = None) -> str:
        """Serialize transcript words into SRT subtitle format.

        Each word becomes one SRT cue. Words without an end time use
        the next word's start (or ``start + 0.5`` for the last word).

        Args:
            path: If given, also write the SRT string to this file.

        Returns:
            The SRT-formatted string.
        """
        lines: list[str] = []
        for i, word in enumerate(self._words):
            end = word.end
            if end is None:
                end = (
                    self._words[i + 1].start
                    if i + 1 < len(self._words)
                    else word.start + 0.5
                )
            lines.append(str(i + 1))
            lines.append(f"{_format_srt_time(word.start)} --> {_format_srt_time(end)}")
            lines.append(word.text)
            lines.append("")
        result = "\n".join(lines)
        if path is not None:
            Path(path).write_text(result)
        return result

    def detect_filler_words(
        self, fillers: set[str] = _DEFAULT_FILLERS,
    ) -> list[Word]:
        """Return words whose text matches a filler word (case-insensitive).

        Args:
            fillers: Set of filler words to detect.

        Returns:
            List of matching Word objects.
        """
        lower_fillers = {f.lower() for f in fillers}
        return [w for w in self._words if w.text.lower() in lower_fillers]

    def remove_filler_words(
        self, fillers: set[str] = _DEFAULT_FILLERS,
    ) -> Transcript:
        """Return a new Transcript with filler words removed.

        Args:
            fillers: Set of filler words to remove.

        Returns:
            A new Transcript without the filler words.
        """
        lower_fillers = {f.lower() for f in fillers}
        return Transcript([w for w in self._words if w.text.lower() not in lower_fillers])

    def detect_pauses(self, min_gap_seconds: float = 0.5) -> list[tuple[float, float]]:
        """Detect gaps between consecutive words.

        A pause is a gap where the previous word's end time is before the
        next word's start time by at least *min_gap_seconds*.

        Args:
            min_gap_seconds: Minimum gap duration to report.

        Returns:
            List of ``(gap_start, gap_end)`` tuples.
        """
        pauses: list[tuple[float, float]] = []
        for i in range(len(self._words) - 1):
            end = self._words[i].end
            if end is None:
                continue
            next_start = self._words[i + 1].start
            if next_start - end >= min_gap_seconds:
                pauses.append((end, next_start))
        return pauses

    def shorten_pauses(
        self,
        min_gap_seconds: float = 0.5,
        target_gap_seconds: float = 0.2,
    ) -> Transcript:
        """Return a new Transcript with long pauses shortened.

        Words after each detected pause are shifted earlier so the gap
        equals *target_gap_seconds*.

        Args:
            min_gap_seconds: Minimum gap to consider a pause.
            target_gap_seconds: Desired gap duration after shortening.

        Returns:
            A new Transcript with adjusted timings.
        """
        if not self._words:
            return Transcript([])
        new_words: list[Word] = []
        shift = 0.0
        for i, word in enumerate(self._words):
            if i > 0:
                prev = self._words[i - 1]
                if prev.end is not None:
                    gap = word.start - prev.end
                    if gap >= min_gap_seconds:
                        shift += gap - target_gap_seconds
            new_end = word.end - shift if word.end is not None else None
            new_words.append(Word(
                text=word.text,
                start=word.start - shift,
                end=new_end,
                word_id=word.word_id,
            ))
        return Transcript(new_words)

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
