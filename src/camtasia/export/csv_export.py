"""Export timeline data as CSV."""
from __future__ import annotations

import csv
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from camtasia.project import Project


def export_csv(project: Project, output_path: str | Path, *, include_nested: bool = True) -> Path:
    """Export timeline clip data as CSV.

    Columns: track_name, track_index, clip_id, clip_type, start_seconds,
    duration_seconds, end_seconds, source_id, effect_count, effects, nested_depth.

    Args:
        project: The project to export.
        output_path: Destination .csv path.
        include_nested: When True (default), recurse into Groups/StitchedMedia
            and include inner clips with their effective timeline-absolute start
            positions. When False, only top-level clips are emitted.

    Returns:
        The written path.
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
        for track, clip, effective_start in project.timeline.iter_clips_with_effective_start(
            include_nested=include_nested,
        ):
            start_s = ticks_to_seconds(effective_start)
            dur_s = ticks_to_seconds(clip.duration)
            writer.writerow([
                track.name,
                track.index,
                clip.id,
                clip.clip_type,
                f'{start_s:.3f}',
                f'{dur_s:.3f}',
                f'{start_s + dur_s:.3f}',
                clip.source_id if clip.source_id is not None else '',
                clip.effect_count,
                '; '.join(clip.effect_names) if clip.has_effects else '',
            ])
    return path
