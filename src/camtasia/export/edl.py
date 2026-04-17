"""Export timeline as CMX 3600 EDL format."""
from __future__ import annotations

from fractions import Fraction
from pathlib import Path
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from camtasia.project import Project


def _format_timecode(seconds: float, fps: int = 30) -> str:
    """Format seconds as SMPTE timecode HH:MM:SS:FF."""
    sign = '-' if seconds < 0 else ''
    seconds = abs(seconds)
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    f = round((seconds % 1) * fps)
    if f >= fps:
        f = 0
        s += 1
    if s >= 60:
        s -= 60
        m += 1
    if m >= 60:
        m -= 60
        h += 1
    return f'{sign}{h:02d}:{m:02d}:{s:02d}:{f:02d}'


def export_edl(
    project: Project,
    output_path: str | Path,
    *,
    title: str = 'Untitled',
    fps: int = 30,
) -> Path:
    """Export timeline as a CMX 3600 EDL file.

    Maps each clip to an EDL event with source file, in/out points,
    and record in/out points.

    Args:
        project: The project to export.
        output_path: Path for the .edl file.
        title: EDL title.
        fps: Frame rate for timecode calculation.

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
    for track in project.timeline.tracks:
        for clip in track.clips:
            start = ticks_to_seconds(clip.start)
            end = start + ticks_to_seconds(clip.duration)

            # Source name from media bin if available
            source = 'AX'
            if clip.source_id is not None:
                try:
                    media = project.media_bin[clip.source_id]
                    source = media.identity
                except KeyError:
                    pass

            # Determine edit type
            is_unified = clip.clip_type == 'UnifiedMedia'
            video_types = ('VMFile', 'IMFile', 'ScreenVMFile', 'ScreenIMFile', 'PlaceholderMedia', 'Group', 'UnifiedMedia', 'Callout')
            if clip.clip_type == 'StitchedMedia':
                # Check sub-clips to determine if video or audio
                sub_types = {m.get('_type') for m in clip._data.get('medias', [])} # pragma: no cover
                edit_type = 'V' if sub_types & {'VMFile', 'IMFile', 'ScreenVMFile', 'ScreenIMFile'} else 'A' # pragma: no cover
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

            if is_unified:
                audio_data = clip._data.get('audio', {})
                audio_ms = ticks_to_seconds(int(Fraction(str(audio_data.get('mediaStart', 0)))))
                audio_md = ticks_to_seconds(int(Fraction(str(audio_data.get('mediaDuration', clip.duration)))))
                audio_src_in = _format_timecode(audio_ms, fps)
                audio_src_out = _format_timecode(audio_ms + audio_md, fps)
                lines.append(
                    f'{event_num:03d}  {source[:8]:<8s} A     C        '
                    f'{audio_src_in} {audio_src_out} {rec_in} {rec_out}'
                )
                event_num += 1

    lines.append('')
    path.write_text('\n'.join(lines))
    return path
