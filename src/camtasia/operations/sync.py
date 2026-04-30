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
    from camtasia.audiate.project import AudiateProject
    from camtasia.audiate.transcript import Transcript, Word
    from camtasia.project import Project
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

    # Filter non-monotonic audio segments
    filtered_resolved: list[tuple[int, float]] = []
    prev_audio: float | None = None
    for v_ticks, a_time in resolved:
        if prev_audio is not None and a_time < prev_audio:
            import warnings
            warnings.warn(
                f'Non-monotonic audio timestamps in sync plan at video={v_ticks}; skipping segment',
                stacklevel=2,
            )
            continue
        filtered_resolved.append((v_ticks, a_time))
        prev_audio = a_time
    resolved = filtered_resolved

    if len(resolved) < 2:
        return []

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


def sync_audiate_edits_to_timeline(
    audiate_project: AudiateProject,
    camtasia_project: Project,
    *,
    mode: str = "edit_timeline",
) -> list[tuple[float, float]]:
    """Apply Audiate word-deletions to the Camtasia timeline.

    Compares the original transcript against the edited (fillers/pauses
    removed) version and creates ``ripple_delete_range`` calls for each
    deleted word's time span on every track.

    Args:
        audiate_project: Loaded AudiateProject with transcript.
        camtasia_project: Target Camtasia Project.
        mode: Operation mode (currently only ``'edit_timeline'``).

    Returns:
        List of ``(start, end)`` second pairs that were deleted.
    """
    original = audiate_project.transcript
    edits = audiate_project.apply_suggested_edits()
    edited: Transcript = edits["transcript"]

    edited_ids = {w.word_id for w in edited.words}
    deleted_spans: list[tuple[float, float]] = []
    for word in original.words:
        if word.word_id not in edited_ids and word.end is not None:
            deleted_spans.append((word.start, word.end))

    if mode == "edit_timeline":
        from camtasia.operations.layout import ripple_delete_range

        # Apply in reverse order so earlier deletions don't shift later spans
        for start, end in reversed(deleted_spans):
            for track in camtasia_project.timeline.tracks:
                ripple_delete_range(track, start, end)

    return deleted_spans


def send_media_to_audiate(
    project: Project,
    media_or_clip: object,
) -> dict:
    """Export audio from a Camtasia clip as an Audiate session stub.

    This is a stub — actual export requires the Audiate backend. Returns
    a dict describing the intended export.

    Args:
        project: Source Camtasia Project.
        media_or_clip: A clip or media entry to export.

    Returns:
        Dict with ``status`` and ``source`` keys describing the intent.
    """
    src_id = getattr(media_or_clip, "id", None) or getattr(
        media_or_clip, "_data", {},
    ).get("id")
    return {
        "status": "pending",
        "source": src_id,
        "format": ".audiate",
    }


def delete_words_from_timeline(
    audiate_project: AudiateProject,
    camtasia_project: Project,
    word_ids: list[str],
) -> list[tuple[float, float]]:
    """Delete specific words' time spans from the Camtasia timeline.

    Looks up each word by ID in the Audiate transcript and applies
    ``ripple_delete_range`` for words that have valid time spans.

    Args:
        audiate_project: Loaded AudiateProject with transcript.
        camtasia_project: Target Camtasia Project.
        word_ids: List of word IDs to delete.

    Returns:
        List of ``(start, end)`` second pairs that were deleted.
    """
    from camtasia.operations.layout import ripple_delete_range

    words_by_id = {w.word_id: w for w in audiate_project.transcript.words}
    spans: list[tuple[float, float]] = []
    for wid in word_ids:
        word = words_by_id.get(wid)
        if word is not None and word.end is not None:
            spans.append((word.start, word.end))

    for start, end in sorted(spans, reverse=True):
        for track in camtasia_project.timeline.tracks:
            ripple_delete_range(track, start, end)

    return spans


def apply_sync(
    group: Group,
    segments: list[SyncSegment],
) -> None:
    """Apply sync segments to a Group's internal track.

    Converts SyncSegment objects to the (source_start, source_end,
    timeline_duration) tuples expected by set_internal_segment_speeds.
    Subtracts the Group's mediaStart so positions are source-media offsets.
    """
    from camtasia.timing import parse_scalar, ticks_to_seconds
    group_start_ticks = int(Fraction(str(group._data.get('start', 0))))
    media_start_ticks = int(Fraction(str(group._data.get('mediaStart', 0))))
    group_scalar = parse_scalar(group._data.get('scalar', 1))
    if group_scalar == 0:
        raise ValueError('Group has scalar=0 (degenerate); cannot compute source offsets')
    tuples = []
    for seg in segments:
        tl_offset = seg.video_start_ticks - group_start_ticks
        tl_offset_end = seg.video_end_ticks - group_start_ticks
        src_offset = round(Fraction(tl_offset) / group_scalar)
        src_offset_end = round(Fraction(tl_offset_end) / group_scalar)
        tuples.append((
            ticks_to_seconds(src_offset + media_start_ticks),
            ticks_to_seconds(src_offset_end + media_start_ticks),
            seg.audio_end_seconds - seg.audio_start_seconds,
        ))
    group.set_internal_segment_speeds(tuples)
