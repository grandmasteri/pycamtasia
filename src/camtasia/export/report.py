from __future__ import annotations
import json
from pathlib import Path
from typing import TYPE_CHECKING
from camtasia.types import ReportFormat
if TYPE_CHECKING:
    from camtasia.project import Project


def export_project_report(
    project: Project,
    output_path: str | Path,
    *,
    format: ReportFormat = 'markdown',
) -> Path:
    """Export a detailed project report."""
    path = Path(output_path)
    if format == 'json':
        json_report = _build_json_report(project)
        path.write_text(json.dumps(json_report, indent=2))
    else:
        md_report = _build_markdown_report(project)
        path.write_text(md_report)
    return path


def _build_json_report(project: Project) -> dict:
    tracks = []
    for track in project.timeline.tracks:
        clips = []
        for clip in track.clips:
            clips.append({
                'id': clip.id,
                'type': clip.clip_type,
                'start_seconds': clip.start_seconds,
                'duration_seconds': clip.duration_seconds,
            })
        tracks.append({
            'index': track.index,
            'name': track.name,
            'clip_count': len(track),
            'clips': clips,
        })
    media = []
    for m in project.media_bin:
        media.append({
            'id': m.id,
            'identity': m.identity,
            'type': m.type.name if m.type is not None and hasattr(m.type, 'name') else str(m.type),
        })
    return {
        'project': str(project.file_path.name),
        'canvas': {'width': project.width, 'height': project.height},
        'duration_seconds': project.total_duration_seconds(),
        'track_count': project.timeline.track_count,
        'tracks': tracks,
        'media_count': len(project.media_bin),
        'media': media,
    }


def _build_markdown_report(project: Project) -> str:
    lines = [
        f'# Project Report: {project.file_path.name}',
        '',
        f'**Canvas:** {project.width}×{project.height}',
        f'**Duration:** {project.total_duration_seconds():.1f}s',
        f'**Tracks:** {project.timeline.track_count}',
        f'**Media:** {len(project.media_bin)} items',
        '',
        '## Tracks',
        '',
    ]
    for track in project.timeline.tracks:
        clip_count = len(track)
        if clip_count > 0:
            types = sorted({c.clip_type for c in track.clips})
            lines.append(f'### Track {track.index}: {track.name or "(unnamed)"}')
            lines.append(f'- {clip_count} clips: {", ".join(types)}')
            lines.append('')
    lines.append('## Media Bin')
    lines.append('')
    for m in project.media_bin:
        type_name = m.type.name if m.type is not None and hasattr(m.type, 'name') else str(m.type)
        lines.append(f'- [{m.id}] {m.identity} ({type_name})')
    lines.append('')
    return '\n'.join(lines)
