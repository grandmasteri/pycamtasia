from __future__ import annotations
from pathlib import Path
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from camtasia.project import Project


def _format_srt_time(seconds: float) -> str:
    """Format seconds as SRT timecode HH:MM:SS,mmm."""
    seconds = max(0.0, seconds)
    total_ms = round(seconds * 1000)
    h = total_ms // 3600000
    total_ms %= 3600000
    m = total_ms // 60000
    total_ms %= 60000
    s = total_ms // 1000
    ms = total_ms % 1000
    return f'{h:02d}:{m:02d}:{s:02d},{ms:03d}'


def export_markers_as_srt(
    project: Project,
    output_path: str | Path,
    *,
    duration_seconds: float = 3.0,
) -> Path:
    """Export timeline markers as an SRT subtitle file."""
    path = Path(output_path)
    markers = list(project.timeline.markers)
    lines = []
    for i, marker in enumerate(markers, 1):
        start = marker.time_seconds
        end = start + duration_seconds
        if i < len(markers):
            next_start = markers[i].time_seconds
            if end > next_start:
                end = next_start
        lines.append(str(i))
        lines.append(f'{_format_srt_time(start)} --> {_format_srt_time(end)}')
        lines.append(marker.name)
        lines.append('')
    path.write_text('\n'.join(lines))
    return path
