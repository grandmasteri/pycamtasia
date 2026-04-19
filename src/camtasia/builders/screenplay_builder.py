"""Build a timeline from a parsed screenplay."""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
import warnings

if TYPE_CHECKING:
    from collections.abc import Callable

    from camtasia.project import Project
    from camtasia.screenplay import Screenplay, VOBlock
    from camtasia.types import ScreenplayBuildResult



def build_from_screenplay(
    project: Project,
    screenplay: Screenplay,
    audio_dir: str | Path,
    *,
    audio_track_name: str = 'Audio',
    default_pause: float = 1.0,
    vo_file_resolver: Callable[[VOBlock], str | Path | None] | None = None,
) -> ScreenplayBuildResult:
    """Build a timeline from a parsed screenplay.

    Places voiceover audio clips sequentially with pauses interleaved
    at their original positions from the screenplay text.

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
        has_explicit_pauses = bool(section.pauses)
        # Build a map of pauses keyed by the VO index they follow
        pauses_after: dict[int, list[float]] = {}
        trailing_pauses: list[float] = []
        if has_explicit_pauses:
            for p in section.pauses:
                if p.after_vo_index is not None:
                    pauses_after.setdefault(p.after_vo_index, []).append(p.duration_seconds)
                else:
                    trailing_pauses.append(p.duration_seconds)

        vo_blocks = section.vo_blocks
        for vi, vo in enumerate(vo_blocks):
            # Resolve audio file
            if vo_file_resolver:
                audio_path = vo_file_resolver(vo)
            else:
                audio_path = _find_audio_file(audio_dir, vo.id)

            if audio_path and Path(audio_path).exists():
                builder.add_audio(audio_path, track_name=audio_track_name)
                clips_placed += 1
                vo_placed = True
            else:
                if audio_path:
                    warnings.warn(f'Audio file not found: {audio_path}', stacklevel=2)
                else:
                    warnings.warn(f'No audio file found for VO block {vo.id}', stacklevel=2)
                vo_placed = False

            # Insert interleaved explicit pauses that follow this VO block
            if has_explicit_pauses:
                if vo_placed:
                    for dur in pauses_after.get(vi, []):
                        builder.add_pause(dur)
                        pauses_added += 1
            elif default_pause > 0 and vi < len(vo_blocks) - 1 and vo_placed:
                builder.add_pause(default_pause)
                pauses_added += 1

        # Add any trailing pauses (before any VO or unpositioned)
        for dur in trailing_pauses:
            builder.add_pause(dur)
            pauses_added += 1

    return {
        'clips_placed': clips_placed,
        'pauses_added': pauses_added,
        'total_duration': builder.cursor,
    }


def _find_audio_file(audio_dir: Path, vo_id: str) -> Path | None:
    """Try to find an audio file matching a VO ID."""
    _EXTENSIONS = ('.wav', '.mp3', '.m4a', '.aac', '.flac')
    # Try exact match: VO-1.1.wav, .mp3, etc.
    for ext in _EXTENSIONS:
        exact = audio_dir / f'VO-{vo_id}{ext}'
        if exact.exists():
            return exact
    # Fallback: try without VO- prefix
    for ext in _EXTENSIONS:
        exact = audio_dir / f'{vo_id}{ext}'
        if exact.exists():
            return exact
    # Try numbered prefix using full VO ID: e.g. VO-1.1 -> 01-01-*.wav
    parts = [p for p in vo_id.split('.') if p]
    if len(parts) >= 2:
        try:
            prefix = f'{int(parts[0]):02d}-{int(parts[1]):02d}-'
        except ValueError:
            return None
        for ext in _EXTENSIONS:
            for f in sorted(audio_dir.glob(f'{prefix}*{ext}')):
                return f
    elif parts: # pragma: no cover
        try:
            prefix = f'{int(parts[0]):02d}-' # pragma: no cover
        except ValueError:
            return None
        for ext in _EXTENSIONS: # pragma: no cover
            for f in sorted(audio_dir.glob(f'{prefix}*{ext}')): # pragma: no cover
                return f # pragma: no cover
    return None
