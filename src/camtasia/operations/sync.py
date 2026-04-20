"""Audio-video sync from transcript and timeline markers.

Implements the V3 labeled-markers workflow: given markers on a screen
recording and a word-level transcript, calculate per-segment speed
adjustments to align video with audio.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import re
import string
from typing import TYPE_CHECKING

from camtasia.timing import EDIT_RATE

if TYPE_CHECKING:
    from camtasia.audiate.transcript import Word
    from camtasia.timeline.clips.group import Group


@dataclass
class SyncSegment:
    """A segment between two sync points with its speed adjustment.

    Attributes:
        video_start_ticks: Segment start on the video timeline (ticks).
        video_end_ticks: Segment end on the video timeline (ticks).
        audio_start_seconds: Corresponding audio start (seconds).
        audio_end_seconds: Corresponding audio end (seconds).
        scalar: Camtasia scalar (video_duration / audio_duration in ticks).
    """

    video_start_ticks: int
    video_end_ticks: int
    audio_start_seconds: float
    audio_end_seconds: float
    scalar: Fraction


def match_marker_to_transcript(
    label: str,
    words: list[Word],
) -> float | None:
    """Fuzzy-match a marker label to words in a transcript.

    Uses simple case-insensitive substring matching. Checks each word
    in the label against the running text of the transcript.

    Args:
        label: Marker label text (e.g. "Selecting a recent batch run").
        words: List of Word objects with .text, .start, .end attributes.

    Returns:
        Start timestamp (seconds) of the best match, or None.
    """
    label_lower = [w for w in (re.sub(r'[^\w\s]', '', w) for w in label.lower().split()) if w]
    if not label_lower or not words:
        return None

    # Build running text for substring search
    texts = []
    text_to_word_idx = []
    for wi, w in enumerate(words):
        cleaned = re.sub(r'[^\w\s]', '', w.text.lower()).strip()
        for sub_word in cleaned.split():
            if sub_word:
                texts.append(sub_word)
                text_to_word_idx.append(wi)
    full = " ".join(texts)
    target = " ".join(label_lower)

    idx = full.find(target)
    while idx != -1:
        at_start = idx == 0 or full[idx - 1] == ' '
        at_end = idx + len(target) >= len(full) or full[idx + len(target)] == ' '
        if at_start and at_end:
            break
        idx = full.find(target, idx + 1)
    if idx != -1:
        # Count words before the match to find the word index
        word_idx = full[:idx].count(" ")
        return words[text_to_word_idx[min(word_idx, len(text_to_word_idx) - 1)]].start

    # Fallback: match first word of label
    # Additional guard: if multi-word label, require phrase match
    if len(label_lower) > 1:
        # Try full multi-word match across all words
        for i in range(len(words) - len(label_lower) + 1):
            match = all(
                words[i + j].text.lower().strip(string.punctuation) == label_lower[j]
                for j in range(len(label_lower))
            )
            if match:
                return words[i].start  # pragma: no cover  # defensive: primary match typically catches this case first
        # Fallback to 2-word match if full match fails
        for i in range(len(words) - 1):
            if (words[i].text.lower().strip(string.punctuation) == label_lower[0] and
                words[i+1].text.lower().strip(string.punctuation) == label_lower[1]):
                return words[i].start
        return None
    # Single-word label, fall back to exact first-word match
    first = label_lower[0]
    for w in words:
        if first == w.text.lower().strip(string.punctuation):
            return w.start  # pragma: no cover  # primary match catches exact word matches first

    return None


def plan_sync(
    markers: list[tuple[str, int]],
    transcript_words: list[Word],
    edit_rate: int = EDIT_RATE,
) -> list[SyncSegment]:
    """Calculate per-segment speed adjustments to sync video with audio.

    For each pair of consecutive markers, finds the corresponding audio
    timestamps via transcript matching and computes the scalar needed to
    align the video segment duration with the audio segment duration.

    Args:
        markers: List of ``(label, video_time_ticks)`` from
            ``timeline.parameters.toc`` keyframes.
        transcript_words: List of dicts with ``word``, ``start``, ``end``
            keys (from WhisperX or Audiate).
        edit_rate: Ticks per second (default 705,600,000).

    Returns:
        List of SyncSegments, one per gap between consecutive markers.
    """
    if len(markers) < 2:
        return []

    # Resolve audio timestamps for each marker
    resolved: list[tuple[int, float]] = []
    for label, video_ticks in markers:
        audio_time = match_marker_to_transcript(label, transcript_words)
        if audio_time is not None:
            resolved.append((video_ticks, audio_time))

    if len(resolved) < 2:
        return []

    resolved.sort(key=lambda x: x[0])

    segments: list[SyncSegment] = []
    for i in range(len(resolved) - 1):
        v_start, a_start = resolved[i]
        v_end, a_end = resolved[i + 1]

        video_dur_ticks = v_end - v_start
        audio_dur_ticks = round(float(a_end - a_start) * edit_rate)

        if audio_dur_ticks <= 0 or video_dur_ticks <= 0:
            continue

        scalar = Fraction(video_dur_ticks, audio_dur_ticks)

        segments.append(SyncSegment(
            video_start_ticks=v_start,
            video_end_ticks=v_end,
            audio_start_seconds=a_start,
            audio_end_seconds=a_end,
            scalar=scalar,
        ))

    return segments


def apply_sync(
    group: Group,
    segments: list[SyncSegment],
) -> None:
    """Apply sync segments to a Group's internal track.

    Converts SyncSegment objects to the (source_start, source_end,
    timeline_duration) tuples expected by set_internal_segment_speeds.
    Subtracts the Group's mediaStart so positions are source-media offsets.
    """
    from camtasia.timing import ticks_to_seconds
    media_start_ticks = int(Fraction(str(group._data.get('mediaStart', 0))))
    tuples = []
    for seg in segments:
        tuples.append((
            ticks_to_seconds(seg.video_start_ticks - media_start_ticks),
            ticks_to_seconds(seg.video_end_ticks - media_start_ticks),
            seg.audio_end_seconds - seg.audio_start_seconds,
        ))
    group.set_internal_segment_speeds(tuples)
