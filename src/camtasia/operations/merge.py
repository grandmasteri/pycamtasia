"""Merge tracks from one project into another."""
from __future__ import annotations

import copy
from fractions import Fraction
from typing import TYPE_CHECKING

from camtasia.timeline.timeline import _remap_clip_ids_with_map
from camtasia.timeline.track import _propagate_start_to_unified

if TYPE_CHECKING:
    from camtasia.project import Project


def _remap_src_in_clip(clip_data: dict, src_map: dict[int, int]) -> None:
    """Recursively remap src references in a clip and its children."""
    if 'src' in clip_data and clip_data['src'] in src_map:
        clip_data['src'] = src_map[clip_data['src']]
    for key in ('video', 'audio'):
        if key in clip_data:
            _remap_src_in_clip(clip_data[key], src_map)
    for track in clip_data.get('tracks', []):
        for media in track.get('medias', []):
            _remap_src_in_clip(media, src_map)
    for media in clip_data.get('medias', []):
        _remap_src_in_clip(media, src_map)


def _remap_asset_properties(clip_data: dict, id_map: dict[int, int]) -> None:
    """Recursively remap assetProperties.objects references using a complete id_map."""
    for ap in clip_data.get('attributes', {}).get('assetProperties', []):
        if 'objects' in ap:
            new_objects = []
            for o in ap['objects']:
                if isinstance(o, dict):
                    new_o = dict(o)
                    if 'media' in new_o:
                        new_o['media'] = id_map.get(new_o['media'], new_o['media'])
                    new_objects.append(new_o)
                else:
                    new_objects.append(id_map.get(o, o))
            ap['objects'] = new_objects
    for key in ('video', 'audio'):
        if key in clip_data and isinstance(clip_data[key], dict):
            _remap_asset_properties(clip_data[key], id_map)
    for track in clip_data.get('tracks', []):
        for media in track.get('medias', []):
            _remap_asset_properties(media, id_map)
    for media in clip_data.get('medias', []):
        _remap_asset_properties(media, id_map)


def merge_tracks(
    source: Project,
    target: Project,
    *,
    offset_seconds: float = 0.0,
) -> int:
    """Copy all non-empty tracks from source into target.

    Clips are offset by offset_seconds on the target timeline.
    Media entries are copied to the target's source bin with new IDs.

    Args:
        source: Project to copy tracks from.
        target: Project to copy tracks into.
        offset_seconds: Time offset for all copied clips.

    Returns:
        Number of tracks copied.
    """
    from camtasia.timing import seconds_to_ticks

    offset_ticks = seconds_to_ticks(offset_seconds)

    # Build media ID mapping (source ID -> target ID)
    src_id_map: dict[int, int] = {}
    def _track_type(media_data: dict) -> str | None:
        tracks = media_data.get('sourceTracks', [])
        return tracks[0].get('type') if tracks else None

    for media in source.media_bin:
        existing = target.find_media_by_name(media.identity)
        if existing and _track_type(existing._data) == _track_type(media._data):
            src_id_map[media.id] = existing.id
        else:
            new_id = target.media_bin.next_id()
            entry = copy.deepcopy(media._data)
            entry['id'] = new_id
            target._data['sourceBin'].append(entry)
            src_id_map[media.id] = new_id

    # Copy non-empty tracks
    count = 0
    for track in source.timeline.tracks:
        if len(track) == 0:
            continue

        new_track = target.timeline.add_track(track.name)
        # Copy relevant attributes from source track
        for attr in ('audioMuted', 'videoHidden', 'solo', 'magnetic', 'matte'):
            if attr in track._data:
                new_track._data[attr] = track._data[attr]
        id_counter = [target.next_available_id]

        clip_id_map: dict[int, int] = {}
        new_clips: list[dict] = []
        for clip_data in track._data.get('medias', []):
            new_clip = copy.deepcopy(clip_data)
            _remap_clip_ids_with_map(new_clip, id_counter, clip_id_map)
            # Remap src references
            _remap_src_in_clip(new_clip, src_id_map)
            new_clip['start'] = int(Fraction(str(new_clip.get('start', 0)))) + offset_ticks
            _propagate_start_to_unified(new_clip)
            new_clips.append(new_clip)

        # Second pass: remap assetProperties with complete id_map
        for new_clip in new_clips:
            _remap_asset_properties(new_clip, clip_id_map)
            new_track._data.setdefault('medias', []).append(new_clip)

        count += 1

    return count
