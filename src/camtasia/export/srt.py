from __future__ import annotations
from pathlib import Path
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from camtasia.project import Project


def _format_srt_time(seconds: float) -> str:
    """Format seconds as SRT timecode HH:MM:SS,mmm."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
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
        lines.append(str(i))
        lines.append(f'{_format_srt_time(start)} --> {_format_srt_time(end)}')
        lines.append(marker.name)
        lines.append('')
    path.write_text('\n'.join(lines))
    return path
