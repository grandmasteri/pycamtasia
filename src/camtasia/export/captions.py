"""Caption extract/reimport for translation workflows."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from camtasia.project import Project


@dataclass
class CaptionEntry:
    """A single caption/subtitle entry.

    Attributes:
        start_seconds: Start time in seconds.
        duration_seconds: Duration in seconds.
        text: Caption text.
    """

    start_seconds: float
    duration_seconds: float
    text: str


def export_captions(
    project: Project,
    output_path: str | Path,
    *,
    track_name: str = 'Subtitles',
) -> Path:
    """Extract caption entries from a subtitle/caption track to a JSON file.

    Useful for external translation workflows: export → translate → import.

    Args:
        project: Source project.
        output_path: Destination JSON file.
        track_name: Name of the track carrying caption callouts.

    Returns:
        The written path.

    Raises:
        KeyError: If no track with the given name exists.
    """
    from camtasia.timing import ticks_to_seconds
    path = Path(output_path)
    track = project.timeline.find_track_by_name(track_name)
    if track is None:
        raise KeyError(f'No track named {track_name!r}')
    entries: list[CaptionEntry] = []
    for clip in track.clips:
        if clip.clip_type != 'Callout':
            continue
        callout_def: dict = clip._data.get('def', {}) or {}  # type: ignore[assignment]
        text: str = callout_def.get('text', '')
        entries.append(CaptionEntry(
            start_seconds=round(ticks_to_seconds(clip.start), 3),
            duration_seconds=round(ticks_to_seconds(clip.duration), 3),
            text=text,
        ))
    path.write_text(json.dumps([asdict(e) for e in entries], indent=2, ensure_ascii=False))
    return path


def import_captions(
    project: Project,
    input_path: str | Path,
    *,
    track_name: str = 'Subtitles',
    overwrite: bool = True,
) -> int:
    """Import caption entries from a JSON file, updating text on existing
    clips with matching timing.

    Args:
        project: Target project.
        input_path: JSON file produced by :func:`export_captions`.
        track_name: Name of the caption track.
        overwrite: When True, update the text of existing clips whose
            start/duration match an entry. When False, raise if entry count
            differs from existing clip count.

    Returns:
        Number of caption entries updated.

    Raises:
        KeyError: No track with the given name exists.
        ValueError: overwrite=False and counts mismatch.
    """
    from camtasia.timing import ticks_to_seconds
    track = project.timeline.find_track_by_name(track_name)
    if track is None:
        raise KeyError(f'No track named {track_name!r}')
    raw = json.loads(Path(input_path).read_text())
    entries = [CaptionEntry(**e) for e in raw]
    callouts = [c for c in track.clips if c.clip_type == 'Callout']
    if not overwrite and len(entries) != len(callouts):
        raise ValueError(
            f'overwrite=False but entries={len(entries)} differs from '
            f'existing callouts={len(callouts)}'
        )
    # Match by (start_seconds, duration_seconds) tuple rounded to 0.001s
    by_key = {
        (round(ticks_to_seconds(c.start), 3), round(ticks_to_seconds(c.duration), 3)): c
        for c in callouts
    }
    updated = 0
    for entry in entries:
        key = (entry.start_seconds, entry.duration_seconds)
        match = by_key.get(key)
        if match is None:
            continue
        match._data.setdefault('def', {})['text'] = entry.text  # type: ignore[typeddict-item]
        updated += 1
    return updated
