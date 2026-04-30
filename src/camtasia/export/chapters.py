"""Export timeline markers as chapter files in various formats."""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from xml.etree.ElementTree import Element, SubElement, tostring

from camtasia.timing import ticks_to_seconds

if TYPE_CHECKING:
    from camtasia.project import Project

_VALID_FORMATS = frozenset({'webvtt', 'mp4', 'youtube'})


def _format_vtt_time(seconds: float) -> str:
    """Format seconds as HH:MM:SS.mmm for WebVTT."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f'{h:02d}:{m:02d}:{s:06.3f}'


def _format_youtube_time(seconds: float) -> str:
    """Format seconds as M:SS or H:MM:SS for YouTube chapter list."""
    total = int(seconds)
    h, remainder = divmod(total, 3600)
    m, s = divmod(remainder, 60)
    if h > 0:
        return f'{h}:{m:02d}:{s:02d}'
    return f'{m}:{s:02d}'


def _collect_sorted_markers(project: Project) -> list[tuple[str, float]]:
    """Return (name, seconds) pairs sorted by time."""
    markers = []
    for marker in project.timeline.markers:
        markers.append((marker.name, ticks_to_seconds(marker.time)))
    markers.sort(key=lambda m: m[1])
    return markers


def export_chapters(
    project: Project,
    path: Path,
    *,
    format: str = 'webvtt',
) -> Path:
    """Export timeline markers as chapter data.

    Args:
        project: The project to export.
        path: Output file path.
        format: One of 'webvtt', 'mp4', or 'youtube'.

    Returns:
        The output path.

    Raises:
        ValueError: If format is not recognized.
    """
    if format not in _VALID_FORMATS:
        raise ValueError(f'Unknown format {format!r}, expected one of {sorted(_VALID_FORMATS)}')

    path = Path(path)
    markers = _collect_sorted_markers(project)

    if format == 'webvtt':
        lines = ['WEBVTT', '']
        for i, (name, secs) in enumerate(markers):
            # End time: next marker start, or +1s for last marker
            end = markers[i + 1][1] if i + 1 < len(markers) else secs + 1.0
            lines.append(f'{i + 1}')
            lines.append(f'{_format_vtt_time(secs)} --> {_format_vtt_time(end)}')
            lines.append(name)
            lines.append('')
        path.write_text('\n'.join(lines))

    elif format == 'mp4':
        root = Element('Chapters')
        for name, secs in markers:
            atom = SubElement(root, 'ChapterAtom')
            SubElement(atom, 'ChapterTimeStart').text = _format_vtt_time(secs)
            SubElement(atom, 'ChapterString').text = name
        path.write_bytes(tostring(root, encoding='unicode').encode('utf-8'))

    else:  # youtube
        lines = [f'{_format_youtube_time(secs)} {name}' for name, secs in markers]
        path.write_text('\n'.join(lines))

    return path
