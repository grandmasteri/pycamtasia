"""Export table-of-contents from timeline markers."""
from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING
from xml.etree.ElementTree import Element, SubElement, tostring

from camtasia.timing import ticks_to_seconds

if TYPE_CHECKING:
    from camtasia.project import Project

_VALID_FORMATS = frozenset({'smartplayer', 'xml', 'json'})


def _seconds_to_hms(seconds: float) -> str:
    """Format seconds as HH:MM:SS.mmm."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f'{h:02d}:{m:02d}:{s:06.3f}'


def _collect_chapters(project: Project) -> list[dict]:
    """Collect marker data as chapter dicts."""
    chapters = []
    for marker in project.timeline.markers:
        secs = ticks_to_seconds(marker.time)
        chapters.append({
            'title': marker.name,
            'time_seconds': secs,
            'time_ticks': marker.time,
        })
    chapters.sort(key=lambda c: c['time_seconds'])
    return chapters


def export_toc(
    project: Project,
    path: Path,
    *,
    format: str = 'smartplayer',
) -> Path:
    """Export timeline markers as a table-of-contents file.

    Args:
        project: The project to export.
        path: Output file path.
        format: One of 'smartplayer', 'xml', or 'json'.

    Returns:
        The output path.

    Raises:
        ValueError: If format is not recognized.
    """
    if format not in _VALID_FORMATS:
        raise ValueError(f'Unknown format {format!r}, expected one of {sorted(_VALID_FORMATS)}')

    path = Path(path)
    chapters = _collect_chapters(project)

    if format == 'json':
        path.write_text(json.dumps({'chapters': chapters}, indent=2))
    elif format == 'xml':
        root = Element('chapters')
        for ch in chapters:
            el = SubElement(root, 'chapter')
            el.set('title', ch['title'])
            el.set('time', _seconds_to_hms(ch['time_seconds']))
        path.write_bytes(tostring(root, encoding='unicode').encode('utf-8'))
    else:  # smartplayer
        root = Element('SmartPlayerTOC')
        for ch in chapters:
            entry = SubElement(root, 'Entry')
            SubElement(entry, 'Title').text = ch['title']
            SubElement(entry, 'Time').text = _seconds_to_hms(ch['time_seconds'])
            SubElement(entry, 'Thumbnail').text = ''
        path.write_bytes(tostring(root, encoding='unicode').encode('utf-8'))

    return path
