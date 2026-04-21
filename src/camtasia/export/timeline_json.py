from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from camtasia.project import Project


def export_timeline_json(
    project: Project,
    output_path: str | Path,
    *,
    include_effects: bool = True,
    include_transitions: bool = True,
    include_metadata: bool = True,
) -> Path:
    """Export timeline structure as simplified JSON.

    Useful for documentation, debugging, and comparing timelines
    without the full Camtasia project overhead.

    Args:
        project: Source project.
        output_path: Destination file path.
        include_effects: Include each clip's effect names and count.
        include_transitions: Include each track's transitions (name, leftMedia, rightMedia, duration).
        include_metadata: Include per-clip metadata (mediaStart, mediaDuration, scalar).

    Returns:
        The written path.
    """
    path = Path(output_path)
    data = _build_timeline_data(
        project,
        include_effects=include_effects,
        include_transitions=include_transitions,
        include_metadata=include_metadata,
    )
    path.write_text(json.dumps(data, indent=2))
    return path


def _build_timeline_data(
    project: Project,
    *,
    include_effects: bool = True,
    include_transitions: bool = True,
    include_metadata: bool = True,
) -> dict[str, Any]:
    from camtasia.timing import ticks_to_seconds
    tracks = []
    for track in project.timeline.tracks:
        clips = []
        for clip in track.clips:
            clip_data: dict[str, Any] = {
                'id': clip.id,
                'type': clip.clip_type,
                'start_seconds': round(ticks_to_seconds(clip.start), 3),
                'duration_seconds': round(ticks_to_seconds(clip.duration), 3),
            }
            if hasattr(clip, 'source_id') and clip.source_id is not None:
                clip_data['source_id'] = clip.source_id
            if include_effects and clip.effect_count > 0:
                clip_data['effects'] = list(clip.effect_names)
            if include_metadata:
                md = clip._data.get('mediaDuration')
                ms = clip._data.get('mediaStart')
                sc = clip._data.get('scalar')
                if md is not None:
                    clip_data['mediaDuration'] = md
                if ms is not None:
                    clip_data['mediaStart'] = ms
                if sc is not None and sc not in (1, 1.0, '1', '1/1'):
                    clip_data['scalar'] = sc
            clips.append(clip_data)
        track_entry: dict[str, Any] = {
            'index': track.index,
            'name': track.name,
            'clips': clips,
        }
        if include_transitions:
            transitions = []
            for t in track._data.get('transitions', []):
                transitions.append({
                    'name': t.get('name', ''),
                    'leftMedia': t.get('leftMedia'),
                    'rightMedia': t.get('rightMedia'),
                    'duration': t.get('duration', 0),
                })
            if transitions:
                track_entry['transitions'] = transitions
        tracks.append(track_entry)

    markers = []
    for marker in project.timeline.markers:
        markers.append({
            'name': marker.name,
            'time_seconds': round(marker.time_seconds, 3),
        })

    return {
        'version': '1.1',
        'canvas': {'width': project.width, 'height': project.height},
        'duration_seconds': round(project.total_duration_seconds(), 3),
        'tracks': tracks,
        'markers': markers,
    }


def load_timeline_json(path: str | Path) -> dict[str, Any]:
    """Load a timeline JSON file.

    Returns the parsed dict. Useful for comparing timelines
    or generating reports.
    """
    return json.loads(Path(path).read_text())  # type: ignore[no-any-return]
