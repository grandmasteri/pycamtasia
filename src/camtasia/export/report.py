from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from camtasia.project import Project
    from camtasia.types import ReportFormat


def export_project_report(
    project: Project,
    output_path: str | Path,
    *,
    format: ReportFormat = 'markdown',
    include_nested: bool = True,
) -> Path:
    """Export a detailed project report.

    Args:
        project: The project to export.
        output_path: Destination file path.
        format: ``'markdown'`` (default) or ``'json'``.
        include_nested: When True (default), include clips nested inside
            Groups/StitchedMedia. Inner clip positions are shown in
            timeline-absolute coordinates.
    """
    path = Path(output_path)
    if format == 'json':
        json_report = _build_json_report(project, include_nested=include_nested)
        path.write_text(json.dumps(json_report, indent=2))
    else:
        md_report = _build_markdown_report(project, include_nested=include_nested)
        path.write_text(md_report)
    return path


def _build_json_report(project: Project, *, include_nested: bool = True) -> dict:
    from camtasia.timing import ticks_to_seconds
    # Collect clips grouped by track index, using effective timeline positions
    tracks_by_index: dict[int, list[dict]] = {}
    for track, clip, effective_start in project.timeline.iter_clips_with_effective_start(
        include_nested=include_nested,
    ):
        tracks_by_index.setdefault(track.index, []).append({
            'id': clip.id,
            'type': clip.clip_type,
            'start_seconds': round(ticks_to_seconds(effective_start), 3),
            'duration_seconds': round(ticks_to_seconds(clip.duration), 3),
        })
    tracks = []
    for track in project.timeline.tracks:
        clips = tracks_by_index.get(track.index, [])
        tracks.append({
            'index': track.index,
            'name': track.name,
            'clip_count': len(clips),
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
        'duration_seconds': round(project.total_duration_seconds(), 3),
        'track_count': project.timeline.track_count,
        'tracks': tracks,
        'media_count': len(project.media_bin),
        'media': media,
    }


def _build_markdown_report(project: Project, *, include_nested: bool = True) -> str:
    lines = [
        f'# Project Report: {project.file_path.name}',
        '',
        f'**Canvas:** {project.width}x{project.height}',
        f'**Duration:** {project.total_duration_seconds():.1f}s',
        f'**Tracks:** {project.timeline.track_count}',
        f'**Media:** {len(project.media_bin)} items',
        '',
        '## Tracks',
        '',
    ]
    # Collect clips (including nested) grouped by track index
    clips_by_track: dict[int, list] = {}
    for track, clip, _effective in project.timeline.iter_clips_with_effective_start(
        include_nested=include_nested,
    ):
        clips_by_track.setdefault(track.index, []).append(clip)
    for track in project.timeline.tracks:
        track_clips = clips_by_track.get(track.index, [])
        clip_count = len(track_clips)
        if clip_count > 0:
            types = sorted({c.clip_type for c in track_clips})
            type_str = ', '.join(types)
        else:
            type_str = '(empty)'
        lines.append(f'### Track {track.index}: {track.name or "(unnamed)"}')
        clip_word = 'clip' if clip_count == 1 else 'clips'
        lines.append(f'- {clip_count} {clip_word}: {type_str}')
        lines.append('')
    lines.append('## Media Bin')
    lines.append('')
    for m in project.media_bin:
        type_name = m.type.name if m.type is not None and hasattr(m.type, 'name') else str(m.type)
        lines.append(f'- [{m.id}] {m.identity} ({type_name})')
    lines.append('')
    return '\n'.join(lines)
