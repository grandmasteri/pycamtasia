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

# Approximate speaking rate: ~150 words per minute → 2.5 words/sec
_WORDS_PER_SECOND = 2.5


def build_from_screenplay(
    project: Project,
    screenplay: Screenplay,
    audio_dir: str | Path,
    *,
    audio_track_name: str = 'Audio',
    default_pause: float = 1.0,
    vo_file_resolver: Callable[[VOBlock], str | Path | None] | None = None,
    section_pause: float | None = None,
    emit_scene_markers: bool = False,
    emit_captions: bool = False,
    validate_alignment: bool = True,
    screen_recording_path: Path | None = None,
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
        section_pause: Pause between sections (seconds). Defaults to
            *default_pause* when None.
        emit_scene_markers: When True, adds a timeline marker at the start
            of each section.
        emit_captions: When True, adds caption callouts from VO text lines.
        validate_alignment: When True, warns if VO audio duration differs
            from estimated text duration by more than 20%.
        screen_recording_path: When given, imports the screen recording as
            a ScreenVMFile on a separate track aligned with the voiceovers.

    Returns:
        Summary dict with counts.
    """
    from camtasia.builders.timeline_builder import TimelineBuilder
    from camtasia.timing import seconds_to_ticks

    builder = TimelineBuilder(project)
    audio_dir = Path(audio_dir)
    clips_placed = 0
    pauses_added = 0
    markers_added = 0
    captions_added = 0
    effective_section_pause = section_pause if section_pause is not None else default_pause

    for section_idx, section in enumerate(screenplay.sections):
        # Scene marker at start of section
        if emit_scene_markers:
            project.timeline.markers.add(
                section.title, seconds_to_ticks(builder.cursor),
            )
            markers_added += 1

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

            caption_start = builder.cursor

            if audio_path and Path(audio_path).exists():
                clip = builder.add_audio(audio_path, track_name=audio_track_name)
                clips_placed += 1
                vo_placed = True

                # Validate alignment: compare audio duration to estimated text duration
                if validate_alignment:
                    _validate_vo_alignment(vo, clip.duration_seconds)
            else:
                if audio_path:
                    warnings.warn(f'Audio file not found: {audio_path}', stacklevel=2)
                else:
                    warnings.warn(f'No audio file found for VO block {vo.id}', stacklevel=2)
                vo_placed = False

            # Emit caption from VO text
            if emit_captions:
                caption_dur = builder.cursor - caption_start if vo_placed else 2.0
                if _emit_captions_for_vo(project, vo, caption_start, caption_dur):
                    captions_added += 1

            # Insert interleaved explicit pauses that follow this VO block
            if has_explicit_pauses:
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

        # Add pause between sections
        if (effective_section_pause > 0
                and not has_explicit_pauses
                and section_idx < len(screenplay.sections) - 1):
            has_more_vo = any(s.vo_blocks for s in screenplay.sections[section_idx + 1:])
            if has_more_vo and clips_placed > 0:
                builder.add_pause(effective_section_pause)
                pauses_added += 1

    # Place screen recording aligned with voiceovers
    if screen_recording_path is not None:
        media = project.import_media(screen_recording_path)
        sr_track = project.timeline.get_or_create_track('Screen Recording')
        sr_dur = media.duration_seconds if media.duration_seconds else builder.cursor
        sr_track.add_clip(
            'ScreenVMFile', media.id,
            start=0,
            duration=seconds_to_ticks(min(sr_dur, builder.cursor) if builder.cursor > 0 else sr_dur),
            trackNumber=0,
        )

    result: ScreenplayBuildResult = {
        'clips_placed': clips_placed,
        'pauses_added': pauses_added,
        'total_duration': builder.cursor,
    }
    if emit_scene_markers:
        result['markers_added'] = markers_added
    if emit_captions:
        result['captions_added'] = captions_added
    return result


def _validate_vo_alignment(vo: VOBlock, audio_duration: float) -> None:
    """Warn if audio duration differs from estimated text duration by >20%.

    Estimated duration uses *_WORDS_PER_SECOND* (2.5 wps).
    """
    word_count = len(vo.text.split())
    if word_count == 0:
        return
    expected_dur = word_count / _WORDS_PER_SECOND
    if expected_dur > 0 and abs(audio_duration - expected_dur) / expected_dur > 0.2:
        warnings.warn(
            f'VO {vo.id}: audio duration {audio_duration:.1f}s '
            f'differs from estimated text duration '
            f'{expected_dur:.1f}s by >20%',
            stacklevel=3,
        )


def _emit_captions_for_vo(
    project: Project,
    vo: VOBlock,
    current_time: float,
    audio_duration: float,
) -> bool:
    """Add a caption for a VO block. Returns True if a caption was added."""
    if not vo.text:
        return False
    project.add_caption(text=vo.text, start_seconds=current_time, duration_seconds=audio_duration)
    return True


def _find_audio_file(audio_dir: Path, vo_id: str) -> Path | None:
    """Try to find an audio file matching a VO ID.

    Searches case-insensitively with fallback patterns:
    ``VO-{id}``, ``{id}-VO``, ``{id}``, and numbered prefix.
    """
    _EXTENSIONS = ('.wav', '.mp3', '.m4a', '.aac', '.flac')

    # Build a case-insensitive lookup of files in the directory
    try:
        dir_files = {f.name.lower(): f for f in audio_dir.iterdir() if f.is_file()}
    except OSError:
        return None

    # Try patterns in priority order: VO-{id}, {id}-VO, {id}
    for pattern in (f'VO-{vo_id}', f'{vo_id}-VO', vo_id):
        for ext in _EXTENSIONS:
            candidate = f'{pattern}{ext}'.lower()
            if candidate in dir_files:
                return dir_files[candidate]

    # Try numbered prefix using full VO ID: e.g. VO-1.1 -> 01-01-*.wav
    parts = [p for p in vo_id.split('.') if p]
    if len(parts) >= 2:
        try:
            prefix = '-'.join(f'{int(p):02d}' for p in parts) + '-'
        except ValueError:
            return None
        for ext in _EXTENSIONS:
            for f in sorted(audio_dir.glob(f'{prefix}*{ext}')):
                return f
    elif parts:  # pragma: no cover
        try:
            prefix = f'{int(parts[0]):02d}-'  # pragma: no cover
        except ValueError:
            return None
        for ext in _EXTENSIONS:  # pragma: no cover
            for f in sorted(audio_dir.glob(f'{prefix}*{ext}')):  # pragma: no cover
                return f  # pragma: no cover
    return None
