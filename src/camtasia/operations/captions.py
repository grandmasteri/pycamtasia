"""Caption generation and audio-sync stubs.

These functions are stubs for workflows that require external tools
(Audiate, audio analysis) not available in the pure-Python library.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from camtasia.project import Project
    from camtasia.timeline.clips.base import BaseClip
    from camtasia.timeline.track import Track


@dataclass
class TrimRange:
    """A suggested silence trim range.

    Attributes:
        start_seconds: Start of the silence in seconds.
        end_seconds: End of the silence in seconds.
    """

    start_seconds: float
    end_seconds: float


def generate_captions_from_audio(
    project: Project,
    clip_or_track: BaseClip | Track,
) -> list[BaseClip]:
    """Generate caption clips from word-level timings in a linked AudiateProject.

    This is a stub — a real implementation would extract word-level timings
    from the linked AudiateProject and emit Caption clips on the timeline.

    Args:
        project: The Camtasia project.
        clip_or_track: The audio clip or track to generate captions from.

    Returns:
        Empty list (stub).

    Raises:
        NotImplementedError: Always — this is a stub.
    """
    raise NotImplementedError(
        'generate_captions_from_audio requires Audiate integration'
    )


def sync_script_to_captions(
    project: Project,
    script_text: str,
    timings: list[tuple[float, float]],
) -> int:
    """Sync script text to caption clips using provided timings.

    This is a Windows workflow stub — a real implementation would split
    the script into segments and place them as caption clips aligned
    to the given timing windows.

    Args:
        project: The Camtasia project.
        script_text: Full script text to split into captions.
        timings: List of (start_seconds, end_seconds) windows.

    Returns:
        0 (stub — no captions created).

    Raises:
        NotImplementedError: Always — this is a stub.
    """
    raise NotImplementedError(
        'sync_script_to_captions requires Windows Camtasia integration'
    )


def trim_silences(
    clip: BaseClip,
    threshold_db: float = -50,
    min_silence_ms: int = 300,
) -> list[TrimRange]:
    """Identify silence regions in an audio clip and return suggested trim ranges.

    This is a stub — a real implementation would analyze the audio waveform
    and return regions below the threshold.

    Args:
        clip: The audio clip to analyze.
        threshold_db: Volume threshold in dB below which audio is silence.
        min_silence_ms: Minimum silence duration in milliseconds to report.

    Returns:
        Empty list (stub).

    Raises:
        NotImplementedError: Always — this is a stub.
    """
    raise NotImplementedError(
        'trim_silences requires audio analysis libraries'
    )
