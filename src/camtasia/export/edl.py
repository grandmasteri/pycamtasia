"""Export timeline as CMX 3600 EDL format."""
from __future__ import annotations

from fractions import Fraction
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from camtasia.project import Project


def _format_timecode(seconds: float, fps: int = 30) -> str:
    """Format seconds as SMPTE timecode HH:MM:SS:FF."""
    if seconds < 0:
        import warnings
        warnings.warn(f'Negative timecode {seconds}s clamped to 00:00:00:00', stacklevel=2)
        seconds = 0.0
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    f = int((seconds % 1) * fps)
    if f >= fps:  # pragma: no cover
        f = 0  # pragma: no cover
        s += 1  # pragma: no cover
    if s >= 60:  # pragma: no cover
        s -= 60  # pragma: no cover
        m += 1  # pragma: no cover
    if m >= 60:  # pragma: no cover
        m -= 60  # pragma: no cover
        h += 1  # pragma: no cover
    return f'{h:02d}:{m:02d}:{s:02d}:{f:02d}'


def export_edl(
    project: Project,
    output_path: str | Path,
    *,
    title: str = 'Untitled',
    fps: int = 30,
    include_nested: bool = True,
) -> Path:
    """Export timeline as a CMX 3600 EDL file.

    Maps each clip to an EDL event with source file, in/out points,
    and record in/out points.

    Args:
        project: The project to export.
        output_path: Path for the .edl file.
        title: EDL title.
        fps: Frame rate for timecode calculation.
        include_nested: When True (default), recurse into Groups/StitchedMedia
            and emit EDL events for their inner clips with timeline-absolute
            positions. EDL is inherently flat, so flattening is usually desired.

    Returns:
        The output path.
    """
    from camtasia.timing import ticks_to_seconds

    path = Path(output_path)
    lines = [
        f'TITLE: {title}',
        'FCM: NON-DROP FRAME',
        '',
    ]

    event_num = 1
    for _track, clip, effective_start in project.timeline.iter_clips_with_effective_start(
        include_nested=include_nested,
    ):
        start = ticks_to_seconds(effective_start)
        end = start + ticks_to_seconds(clip.duration)

        # Source name from media bin if available
        source = 'AX'
        if clip.clip_type == 'UnifiedMedia':
            src_id = clip._data.get('video', {}).get('src')
        else:
            src_id = clip.source_id
        if src_id is not None:
            try:
                media = project.media_bin[src_id]
                source = media.identity
            except KeyError:
                pass

        # Determine edit type
        is_unified = clip.clip_type == 'UnifiedMedia'
        video_types = ('VMFile', 'IMFile', 'ScreenVMFile', 'ScreenIMFile', 'PlaceholderMedia', 'Group', 'UnifiedMedia', 'Callout')
        if clip.clip_type == 'StitchedMedia':
            # Check sub-clips to determine if video or audio
            sub_types = {m.get('_type') for m in clip._data.get('medias', [])}  # pragma: no cover
            edit_type = 'V' if sub_types & {'VMFile', 'IMFile', 'ScreenVMFile', 'ScreenIMFile'} else 'A'  # pragma: no cover
        else:
            edit_type = 'V' if clip.clip_type in video_types else 'A'

        src_in_offset = ticks_to_seconds(round(Fraction(str(clip.media_start))))
        media_dur = ticks_to_seconds(round(Fraction(str(clip.media_duration))))
        src_in = _format_timecode(src_in_offset, fps)
        src_out = _format_timecode(src_in_offset + media_dur, fps)
        rec_in = _format_timecode(start, fps)
        rec_out = _format_timecode(end, fps)

        lines.append(
            f'{event_num:03d}  {source[:8]:<8s} {edit_type}     C        '
            f'{src_in} {src_out} {rec_in} {rec_out}'
        )
        event_num += 1

        if is_unified and 'audio' in clip._data:
            audio_data = clip._data.get('audio', {})
            audio_src = source
            audio_src_id = audio_data.get('src')
            if audio_src_id is not None:
                for m in project.media_bin:
                    if m.id == audio_src_id:
                        audio_src = m.identity
                        break
            audio_ms = ticks_to_seconds(round(Fraction(str(audio_data.get('mediaStart', 0)))))
            audio_md = ticks_to_seconds(round(Fraction(str(audio_data.get('mediaDuration', clip.media_duration)))))
            audio_src_in = _format_timecode(audio_ms, fps)
            audio_src_out = _format_timecode(audio_ms + audio_md, fps)
            lines.append(
                f'{event_num:03d}  {audio_src[:8]:<8s} A     C        '
                f'{audio_src_in} {audio_src_out} {rec_in} {rec_out}'
            )
            event_num += 1

    lines.append('')
    path.write_text('\n'.join(lines))
    return path
