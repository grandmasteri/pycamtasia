"""Export timeline data as CSV."""
from __future__ import annotations
import csv
from pathlib import Path
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from camtasia.project import Project


def export_csv(project: Project, output_path: str | Path) -> Path:
    """Export timeline clip data as CSV.
    
    Columns: track_name, track_index, clip_id, clip_type, start_seconds,
    duration_seconds, end_seconds, source_id, effect_count, effects
    """
    from camtasia.timing import ticks_to_seconds
    path = Path(output_path)
    with path.open('w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'track_name', 'track_index', 'clip_id', 'clip_type',
            'start_seconds', 'duration_seconds', 'end_seconds',
            'source_id', 'effect_count', 'effects',
        ])
        for track in project.timeline.tracks:
            for clip in track.clips:
                writer.writerow([
                    track.name,
                    track.index,
                    clip.id,
                    clip.clip_type,
                    f'{ticks_to_seconds(clip.start):.3f}',
                    f'{ticks_to_seconds(clip.duration):.3f}',
                    f'{clip.end_seconds:.3f}',
                    clip.source_id or '',
                    clip.effect_count,
                    '; '.join(clip.effect_names) if clip.has_effects else '',
                ])
    return path
