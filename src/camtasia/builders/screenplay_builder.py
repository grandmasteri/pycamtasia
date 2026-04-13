"""Build a timeline from a parsed screenplay."""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from camtasia.project import Project
    from camtasia.screenplay import Screenplay, VOBlock

from camtasia.types import ScreenplayBuildResult


def build_from_screenplay(
    project: Project,
    screenplay: 'Screenplay',
    audio_dir: str | Path,
    *,
    audio_track_name: str = 'Audio',
    default_pause: float = 1.0,
    vo_file_resolver: Callable[['VOBlock'], str | Path | None] | None = None,
) -> ScreenplayBuildResult:
    """Build a timeline from a parsed screenplay.

    Places voiceover audio clips sequentially with pauses between them.
    Uses the TimelineBuilder cursor for automatic timing.

    Args:
        project: Target project.
        screenplay: Parsed Screenplay object.
        audio_dir: Directory containing VO audio files.
        audio_track_name: Name for the audio track.
        default_pause: Default pause between VO blocks (seconds).
        vo_file_resolver: Optional callback to resolve VO block to audio file path.
            If None, looks for files matching the VO ID pattern.

    Returns:
        Summary dict with counts.
    """
    from camtasia.builders.timeline_builder import TimelineBuilder

    builder = TimelineBuilder(project)
    audio_dir = Path(audio_dir)
    clips_placed = 0
    pauses_added = 0

    for section in screenplay.sections:
        for vo in section.vo_blocks:
            # Resolve audio file
            if vo_file_resolver:
                audio_path = vo_file_resolver(vo)
            else:
                # Default: look for files matching VO ID pattern
                # e.g. VO-1.1 -> try 01-*.wav, VO-1.1.wav, etc.
                audio_path = _find_audio_file(audio_dir, vo.id)

            if audio_path and Path(audio_path).exists():
                builder.add_audio(audio_path, track_name=audio_track_name)
                clips_placed += 1

        # Add pauses from the section
        for pause in section.pauses:
            builder.add_pause(pause.duration_seconds)
            pauses_added += 1

    return {
        'clips_placed': clips_placed,
        'pauses_added': pauses_added,
        'total_duration': builder.cursor,
    }


def _find_audio_file(audio_dir: Path, vo_id: str) -> Path | None:
    """Try to find an audio file matching a VO ID."""
    # Try exact match: VO-1.1.wav
    exact = audio_dir / f'{vo_id}.wav'
    if exact.exists():
        return exact
    # Try numbered prefix: 01-*.wav for VO-1.1
    parts = vo_id.replace('VO-', '').split('.')
    if parts:
        prefix = f'{int(parts[0]):02d}-'
        for f in sorted(audio_dir.glob(f'{prefix}*.wav')):
            return f
    return None
