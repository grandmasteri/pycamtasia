"""Export audio timeline metadata as CSV or JSON.

Since pycamtasia cannot render actual audio, these functions emit
**metadata** describing the audio mix — clip sources, timing, volume,
gain, and applied effects.  The output is intended for documentation,
external mixing tools, or DAW import preparation.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from camtasia.project import Project


def _collect_audio_clips(
    project: Project,
    *,
    solo_track: str | None = None,
) -> list[dict[str, Any]]:
    """Collect audio clip metadata from the timeline.

    Yields metadata for clips that carry audio: ``AMFile`` clips and
    ``UnifiedMedia`` clips with an ``audio`` sub-clip.
    """
    from camtasia.timing import ticks_to_seconds

    rows: list[dict[str, Any]] = []
    for track, clip, effective_start in project.timeline.iter_clips_with_effective_start():
        if solo_track is not None and track.name != solo_track:
            continue

        # Determine if this clip carries audio
        if clip.clip_type == 'AMFile':
            pass  # always audio
        elif clip.clip_type == 'UnifiedMedia' and clip._data.get('audio') is not None:
            pass  # has audio sub-clip
        else:
            continue

        start_s = round(ticks_to_seconds(effective_start), 3)
        dur_s = round(ticks_to_seconds(clip.duration), 3)

        row: dict[str, Any] = {
            'track_name': track.name,
            'track_index': track.index,
            'clip_id': clip.id,
            'clip_type': clip.clip_type,
            'start_seconds': start_s,
            'duration_seconds': dur_s,
            'end_seconds': round(start_s + dur_s, 3),
            'source_id': clip.source_id if clip.source_id is not None else '',
            'volume': clip.volume,
            'gain': clip.gain,
            'effects': list(clip.effect_names) if clip.has_effects else [],
        }
        rows.append(row)
    return rows


_CSV_COLUMNS = [
    'track_name', 'track_index', 'clip_id', 'clip_type',
    'start_seconds', 'duration_seconds', 'end_seconds',
    'source_id', 'volume', 'gain', 'effects',
]


def export_audio(
    project: Project,
    out_path: str | Path,
    *,
    format: str = 'csv',
    solo_track: str | None = None,
) -> Path:
    """Export audio timeline metadata to a file.

    This does **not** render audio — it writes metadata describing the
    audio mix (clip sources, timing, volume, gain, effects) for use by
    external tools or documentation.

    Args:
        project: The project to export.
        out_path: Destination file path.
        format: ``'csv'`` (default) or ``'json'``.
        solo_track: When set, only include clips from the named track.

    Returns:
        The written path.

    Raises:
        ValueError: If *format* is not ``'csv'`` or ``'json'``.
    """
    if format not in ('csv', 'json'):
        raise ValueError(f"format must be 'csv' or 'json', got {format!r}")

    path = Path(out_path)
    rows = _collect_audio_clips(project, solo_track=solo_track)

    if format == 'csv':
        with path.open('w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=_CSV_COLUMNS)
            writer.writeheader()
            for row in rows:
                csv_row = dict(row)
                csv_row['effects'] = '; '.join(row['effects'])
                writer.writerow(csv_row)
    else:
        path.write_text(json.dumps(rows, indent=2))

    return path


def export_audio_clips(
    project: Project,
    out_dir: str | Path,
    *,
    solo_track: str | None = None,
) -> list[Path]:
    """Export per-clip audio metadata files for external mixing tools.

    Writes one JSON file per audio clip into *out_dir*, named
    ``clip_<clip_id>.json``.  Each file contains the clip's timing,
    volume, gain, and effects — enough for an external tool to
    reconstruct the mix.

    Args:
        project: The project to export.
        out_dir: Destination directory (created if missing).
        solo_track: When set, only include clips from the named track.

    Returns:
        List of written file paths.
    """
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    rows = _collect_audio_clips(project, solo_track=solo_track)
    paths: list[Path] = []
    for row in rows:
        p = out / f"clip_{row['clip_id']}.json"
        p.write_text(json.dumps(row, indent=2))
        paths.append(p)
    return paths
