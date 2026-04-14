from __future__ import annotations
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from camtasia.project import Project


def export_timeline_json(project: Project, output_path: str | Path) -> Path:
    """Export timeline structure as simplified JSON.
    
    Useful for documentation, debugging, and comparing timelines
    without the full Camtasia project overhead.
    """
    path = Path(output_path)
    data = _build_timeline_data(project)
    path.write_text(json.dumps(data, indent=2))
    return path


def _build_timeline_data(project: Project) -> dict[str, Any]:
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
            clips.append(clip_data)
        tracks.append({
            'index': track.index,
            'name': track.name,
            'clips': clips,
        })
    
    markers = []
    for marker in project.timeline.markers:
        markers.append({
            'name': marker.name,
            'time_seconds': round(marker.time_seconds, 3),
        })
    
    return {
        'version': '1.0',
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
