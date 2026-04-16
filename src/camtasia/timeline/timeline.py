"""Timeline — top-level container for tracks, markers, and scene data."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterator, TYPE_CHECKING

if TYPE_CHECKING:
    from camtasia.timeline.captions import CaptionAttributes
    from camtasia.timeline.clips.group import Group

from camtasia.timeline.clips import BaseClip
from camtasia.timeline.markers import Marker, MarkerList
from camtasia.timeline.track import Track
from camtasia.timing import seconds_to_ticks, ticks_to_seconds
from camtasia.types import TimelineSummary


@dataclass
class ZoomPanKeyframe:
    """A zoom/pan keyframe on the timeline."""
    time_seconds: float
    scale: float = 1.0
    center_x: float = 0.5  # 0.0-1.0 normalized
    center_y: float = 0.5  # 0.0-1.0 normalized

    def __repr__(self) -> str:
        return (f'ZoomPanKeyframe(t={self.time_seconds:.2f}s, '
                f'scale={self.scale:.2f}, center=({self.center_x:.2f}, {self.center_y:.2f}))')


def _remap_clip_ids_recursive(clip_data: dict, id_counter: list[int]) -> None:
    """Recursively remap all 'id' fields in a clip and its nested children."""
    if 'id' in clip_data:
        clip_data['id'] = id_counter[0]
        id_counter[0] += 1
    for key in ('video', 'audio'):
        if key in clip_data and isinstance(clip_data[key], dict):
            _remap_clip_ids_recursive(clip_data[key], id_counter)
    for track in clip_data.get('tracks', []):
        for media in track.get('medias', []):
            _remap_clip_ids_recursive(media, id_counter)
    for media in clip_data.get('medias', []):
        _remap_clip_ids_recursive(media, id_counter) # pragma: no cover


def _remap_clip_ids_with_map(clip_data: dict, id_counter: list[int], id_map: dict[int, int]) -> None:
    """Recursively remap 'id' fields, recording old→new in id_map."""
    if 'id' in clip_data:
        old_id = clip_data['id']
        clip_data['id'] = id_counter[0]
        id_map[old_id] = id_counter[0]
        id_counter[0] += 1
    for key in ('video', 'audio'):
        if key in clip_data and isinstance(clip_data[key], dict):
            _remap_clip_ids_with_map(clip_data[key], id_counter, id_map)
    for track in clip_data.get('tracks', []):
        for media in track.get('medias', []):
            _remap_clip_ids_with_map(media, id_counter, id_map)
    for media in clip_data.get('medias', []):
        _remap_clip_ids_with_map(media, id_counter, id_map) # pragma: no cover


class Timeline:
    """Represents the timeline of a Camtasia project.

    Args:
        timeline_data: The ``timeline`` sub-dict from the project JSON.
    """

    def __init__(self, timeline_data: dict[str, Any]) -> None:
        self._data = timeline_data

    def __repr__(self) -> str:
        return f'Timeline(tracks={self.track_count})'

    def __len__(self) -> int:
        return self.track_count

    # ------------------------------------------------------------------
    # Tracks
    # ------------------------------------------------------------------

    @property
    def tracks(self) -> _TrackAccessor:
        """Iterable accessor over Track objects."""
        return _TrackAccessor(self._data)

    @property
    def track_count(self) -> int:
        """Number of tracks on the timeline."""
        return len(self._track_list)

    @property
    def total_clip_count(self) -> int:
        """Total number of clips across all tracks."""
        return sum(len(track) for track in self.tracks)

    @property
    def has_clips(self) -> bool:
        """Whether any track has clips."""
        return self.total_clip_count > 0

    @property
    def total_transition_count(self) -> int:
        """Total number of transitions across all tracks."""
        return sum(track.transition_count for track in self.tracks)

    def add_track(self, name: str = '') -> Track:
        """Append a new empty track.

        Args:
            name: Display name for the track.

        Returns:
            The newly created Track.
        """
        index = len(self._track_list)
        return self.tracks.insert_track(index, name)

    def remove_track(self, index: int) -> None:
        """Remove a track by its index and re-number remaining tracks.

        Args:
            index: The track index to remove.

        Raises:
            KeyError: No track with the given index.
        """
        del self.tracks[index]

    def remove_tracks_by_name(self, name: str) -> int:
        """Remove all tracks with the given name. Returns count removed."""
        indices = [t.index for t in self.tracks if t.name == name]
        for idx in reversed(indices):
            self.remove_track(idx)
        return len(indices)

    def next_clip_id(self) -> int:
        """Return the next available clip ID across ALL tracks.

        Scans every track — including nested group tracks and
        UnifiedMedia sub-clips — for the maximum clip ID and returns
        ``max + 1``.  Returns ``1`` for an empty project.
        """
        from camtasia.timeline.track import _max_clip_id
        return _max_clip_id(self._track_list) + 1

    def duplicate_track(self, source_track_index: int) -> Track:
        """Duplicate a track and all its clips. Returns the new track."""
        import copy
        source_track_data: dict[str, Any] = self._track_list[source_track_index]
        source_attrs: dict[str, Any] = self._data['trackAttributes'][source_track_index]

        duplicated_track_data: dict[str, Any] = copy.deepcopy(source_track_data)
        duplicated_attrs: dict[str, Any] = copy.deepcopy(source_attrs)
        duplicated_attrs['ident'] = f"{duplicated_attrs.get('ident', '')} (copy)"

        # Remap clip IDs to avoid collisions (recursively, including nested clips)
        next_id: int = self.next_clip_id()
        id_counter: list[int] = [next_id]
        clip_id_map: dict[int, int] = {}
        for media_dict in duplicated_track_data.get('medias', []):
            _remap_clip_ids_with_map(media_dict, id_counter, clip_id_map)

        # Remap transition leftMedia/rightMedia references
        for trans in duplicated_track_data.get('transitions', []):
            old_left = trans.get('leftMedia')
            if old_left in clip_id_map:
                trans['leftMedia'] = clip_id_map[old_left]
            old_right = trans.get('rightMedia')
            if old_right in clip_id_map:
                trans['rightMedia'] = clip_id_map[old_right]

        # Insert after source
        insert_index: int = source_track_index + 1
        self._track_list.insert(insert_index, duplicated_track_data)
        self._data['trackAttributes'].insert(insert_index, duplicated_attrs)

        # Fix track indices
        for track_index, track_data in enumerate(self._track_list):
            track_data['trackIndex'] = track_index

        return Track(duplicated_attrs, duplicated_track_data)

    def move_track(self, from_index: int, to_index: int) -> None:
        """Move a track from one array position to another.

        Args:
            from_index: Current array position.
            to_index: Desired array position.
        """
        self.tracks.move_track(from_index, to_index)

    def move_track_to_back(self, track_index: int) -> None:
        """Move a track to position 0 (behind all other tracks)."""
        self.move_track(track_index, 0)

    def move_track_to_front(self, track_index: int) -> None:
        """Move a track to the last position (in front of all other tracks)."""
        self.move_track(track_index, len(self) - 1)

    def find_clip(self, clip_id: int) -> tuple | None:
        """Find a clip by ID across all tracks.

        Returns (track, clip) tuple, or None.
        """
        for track in self.tracks:
            result = track.find_clip(clip_id)
            if result is not None:
                return (track, result)
        return None

    def reorder_tracks(self, order: list[int]) -> None:
        """Reorder tracks by providing current trackIndex values in desired order.

        Args:
            order: List of current ``trackIndex`` values in the new order.
        """
        self.tracks.reorder_tracks(order)

    # ------------------------------------------------------------------
    # Markers
    # ------------------------------------------------------------------

    @property
    def markers(self) -> _TimelineMarkers:
        """Timeline-level markers (from ``parameters.toc``)."""
        return _TimelineMarkers(self._data)

    # ------------------------------------------------------------------
    # L2 convenience methods
    # ------------------------------------------------------------------

    @property
    def total_duration_ticks(self) -> int:
        """Maximum end time across all tracks, in ticks.

        Returns:
            The tick position of the latest clip end, or 0 if empty.
        """
        return max(
            (track.end_time_ticks() for track in self.tracks),
            default=0,
        )

    def total_duration_seconds(self) -> float:
        """Maximum end time across all tracks, in seconds.

        Returns:
            Duration in seconds, or 0.0 if the timeline is empty.
        """
        return ticks_to_seconds(self.total_duration_ticks)

    @property
    def duration_seconds(self) -> float:
        """Total timeline duration in seconds."""
        return self.total_duration_seconds()

    @property
    def total_duration_formatted(self) -> str:
        """Total timeline duration as HH:MM:SS or MM:SS string."""
        total_seconds: float = self.total_duration_seconds()
        hours: int = int(total_seconds // 3600)
        minutes: int = int((total_seconds % 3600) // 60)
        remaining_seconds: int = int(total_seconds % 60)
        if hours > 0:
            return f'{hours}:{minutes:02d}:{remaining_seconds:02d}'
        return f'{minutes}:{remaining_seconds:02d}'

    def summary(self) -> str:
        """Human-readable timeline summary."""
        lines: list[str] = [
            f'Timeline: {self.total_duration_formatted}',
            f'Tracks: {len(list(self.tracks))}',
            f'Total clips: {sum(len(t) for t in self.tracks)}',
            f'Clip density: {self.clip_density:.2f}',
        ]
        groups = self.groups
        if groups:
            lines.append(f'Groups: {len(groups)}')
        return '\n'.join(lines)

    @property
    def end_seconds(self) -> float:
        """End time of the timeline in seconds."""
        return ticks_to_seconds(self.total_duration_ticks)

    @property
    def track_summary(self) -> list[dict[str, Any]]:
        """Summary of each track as a list of dicts."""
        return [
            {
                'name': track.name,
                'index': track.index,
                'clip_count': len(track),
                'duration_seconds': track.total_duration_seconds,
                'is_empty': track.is_empty,
            }
            for track in self.tracks
        ]

    def describe(self) -> str:
        """Human-readable timeline description."""
        lines = [
            f'Timeline: {self.track_count} tracks, {self.total_clip_count} clips, {self.total_duration_seconds():.1f}s',
            '',
        ]
        for track in self.tracks:
            lines.append(track.describe())
            lines.append('')
        return '\n'.join(lines)

    def get_or_create_track(self, name: str) -> Track:
        """Find a track by name, or create a new one if it doesn't exist.

        Args:
            name: Display name to search for (exact match).

        Returns:
            The existing or newly created Track.
        """
        for track in self.tracks:
            if track.name == name:
                return track
        return self.add_track(name)

    def all_clips(self) -> list[BaseClip]:
        """All clips across all tracks, including nested clips inside Groups/StitchedMedia/UnifiedMedia."""
        from typing import Iterable
        result: list[BaseClip] = []

        def _collect(clips: Iterable[BaseClip]) -> None:
            for clip in clips:
                result.append(clip)
                if clip.clip_type == 'Group':
                    from camtasia.timeline.clips.group import Group
                    if isinstance(clip, Group):
                        for gt in clip.tracks:
                            _collect(gt.clips)
                elif clip.clip_type == 'StitchedMedia':
                    from camtasia.timeline.clips import clip_from_dict
                    for nested in clip._data.get('medias', []):
                        result.append(clip_from_dict(nested))
                elif clip.clip_type == 'UnifiedMedia':
                    from camtasia.timeline.clips import clip_from_dict
                    if 'video' in clip._data:
                        result.append(clip_from_dict(clip._data['video']))
                    if 'audio' in clip._data:
                        result.append(clip_from_dict(clip._data['audio']))

        for track in self.tracks:
            _collect(track.clips)
        return result

    @property
    def groups(self) -> list[Group]:
        """All Group clips across all tracks, including nested groups."""
        from camtasia.timeline.clips.group import Group
        return [clip for clip in self.all_clips() if isinstance(clip, Group)]

    @property
    def empty_tracks(self) -> list[Track]:
        """Return all tracks with no clips."""
        return [t for t in self.tracks if t.is_empty]

    def find_track_by_name(self, track_name: str) -> Track | None:
        """Find the first track with the given name, or None.

        Args:
            track_name: Exact track name to search for.

        Returns:
            The first matching Track, or None if no track has that name.
        """
        for track in self.tracks:
            if track.name == track_name:
                return track
        return None

    @property
    def tracks_with_clips(self) -> list[Track]:
        """Return only tracks that have clips."""
        return [t for t in self.tracks if not t.is_empty]

    @property
    def track_names(self) -> list[str]:
        """Names of all tracks."""
        return [t.name for t in self.tracks]

    def to_dict(self) -> TimelineSummary:
        """Return a summary dict of the timeline structure."""
        return {
            'track_count': self.track_count,
            'total_clip_count': self.total_clip_count,
            'duration_seconds': self.total_duration_seconds(),
            'has_clips': self.has_clips,
            'track_names': self.track_names,
        }

    @property
    def all_clip_ids(self) -> set[int]:
        """Set of all clip IDs across all tracks."""
        return {c.id for c in self.all_clips()}

    @property
    def all_effects(self) -> list[tuple[Track, BaseClip, dict]]:
        """All effects across all tracks as (track, clip, effect_dict) tuples."""
        from typing import Iterable
        results: list[tuple[Track, BaseClip, dict]] = []

        def _collect(track: Track, clips: Iterable[BaseClip]) -> None:
            for clip in clips:
                for eff in clip._data.get('effects', []):
                    results.append((track, clip, eff))
                if clip.clip_type == 'Group':
                    from camtasia.timeline.clips.group import Group
                    if isinstance(clip, Group):
                        for gt in clip.tracks:
                            _collect(track, gt.clips)
                elif clip.clip_type == 'StitchedMedia':
                    from camtasia.timeline.clips import clip_from_dict
                    for nested in clip._data.get('medias', []):
                        nc = clip_from_dict(nested)
                        for eff in nc._data.get('effects', []):
                            results.append((track, nc, eff))
                elif clip.clip_type == 'UnifiedMedia':
                    from camtasia.timeline.clips import clip_from_dict
                    for key in ('video', 'audio'):
                        if key in clip._data:
                            nc = clip_from_dict(clip._data[key])
                            for eff in nc._data.get('effects', []):
                                results.append((track, nc, eff))

        for track in self.tracks:
            _collect(track, track.clips)
        return results

    def remove_all_transitions(self) -> int:
        """Remove all transitions from all tracks. Returns count removed."""
        count = 0
        for track in self.tracks:
            transitions = track._data.get('transitions', [])
            count += len(transitions)
            track._data['transitions'] = []
        return count

    def remove_empty_tracks(self) -> int:
        """Remove all empty tracks. Returns count removed."""
        empty_indices = [t.index for t in self.tracks if t.is_empty]
        for idx in reversed(empty_indices):
            self.remove_track(idx)
        return len(empty_indices)

    def pack_all_tracks(self) -> int:
        """Pack every track, removing intra-track gaps between clips.

        Calls :func:`camtasia.operations.layout.pack_track` on each track
        so clips are repositioned end-to-end with no gaps.

        Returns:
            Number of tracks packed (tracks with at least one clip).
        """
        from camtasia.operations.layout import pack_track

        packed_count: int = 0
        for track in self.tracks:
            if not track.is_empty:
                pack_track(track)
                packed_count += 1
        return packed_count

    def remove_short_clips_all_tracks(self, minimum_duration_seconds: float) -> int:
        """Remove short clips from all tracks. Returns total count removed."""
        total_removed: int = 0
        for track in self.tracks:
            total_removed += track.remove_short_clips(minimum_duration_seconds)
        return total_removed

    def clear_all(self) -> None:
        """Clear all clips and transitions from all tracks."""
        for track in self.tracks:
            track.clear()

    def add_marker(self, label: str, time_seconds: float) -> Marker:
        """Add a timeline marker at the given time.

        Args:
            label: Display label for the marker.
            time_seconds: Position in seconds.

        Returns:
            The newly created Marker.
        """
        return self.markers.add(label, seconds_to_ticks(time_seconds))

    # ------------------------------------------------------------------
    # Search & filter
    # ------------------------------------------------------------------

    def clips_in_range(
        self,
        start_seconds: float,
        end_seconds: float,
    ) -> list[tuple[Track, BaseClip]]:
        """Find all clips that overlap with a time range.

        Returns (track, clip) tuples for clips whose time span
        overlaps [start_seconds, end_seconds].
        """
        start_ticks = seconds_to_ticks(start_seconds)
        end_ticks = seconds_to_ticks(end_seconds)
        results = []
        for track in self.tracks:
            for clip in track.clips:
                clip_start = clip.start
                clip_end = clip_start + clip.duration
                if clip_start < end_ticks and clip_end > start_ticks:
                    results.append((track, clip))
        return results

    def find_all_clips_at(self, time_seconds: float) -> list[tuple[Track, BaseClip]]:
        """Find all clips at a time point across all tracks."""
        results = []
        for track in self.tracks:
            for clip in track.clips_at(time_seconds):
                results.append((track, clip))
        return results

    def clips_of_type(self, clip_type: str) -> list[tuple[Track, BaseClip]]:
        """Find all clips of a specific type across all tracks.

        Args:
            clip_type: Clip type string (e.g. 'AMFile', 'IMFile', 'Group').

        Returns:
            List of (track, clip) tuples.
        """
        results = []
        for track in self.tracks:
            for clip in track.clips:
                if clip.clip_type == clip_type:
                    results.append((track, clip))
        return results

    @property
    def audio_clips(self) -> list[tuple[Track, BaseClip]]:
        """All audio clips across all tracks."""
        return self.clips_of_type('AMFile')

    @property
    def image_clips(self) -> list[tuple[Track, BaseClip]]:
        """All image clips across all tracks."""
        return self.clips_of_type('IMFile')

    @property
    def video_clips(self) -> list[tuple[Track, BaseClip]]:
        """All video clips across all tracks."""
        return self.clips_of_type('VMFile')

    # ------------------------------------------------------------------
    # Zoom & Pan
    # ------------------------------------------------------------------

    @property
    def zoom_pan_keyframes(self) -> list[ZoomPanKeyframe]:
        """Get zoom/pan keyframes from the timeline."""
        return [
            ZoomPanKeyframe(
                time_seconds=ticks_to_seconds(kf.get('time', 0)),
                scale=kf.get('scale', 1.0),
                center_x=kf.get('centerX', 0.5),
                center_y=kf.get('centerY', 0.5),
            )
            for kf in self._data.get('zoomNPan', [])
        ]

    def add_zoom_pan(
        self,
        time_seconds: float,
        *,
        scale: float = 1.0,
        center_x: float = 0.5,
        center_y: float = 0.5,
    ) -> ZoomPanKeyframe:
        """Add a zoom/pan keyframe to the timeline.

        Args:
            time_seconds: Timeline position.
            scale: Zoom level (1.0 = 100%, 2.0 = 200%).
            center_x: Horizontal center 0.0-1.0 (0.5 = center).
            center_y: Vertical center 0.0-1.0 (0.5 = center).
        """
        if scale <= 0:
            raise ValueError(f'Scale must be positive, got {scale}')
        self._data.setdefault('zoomNPan', []).append({
            'time': seconds_to_ticks(time_seconds),
            'scale': scale,
            'centerX': center_x,
            'centerY': center_y,
        })
        return ZoomPanKeyframe(time_seconds, scale, center_x, center_y)

    def clear_zoom_pan(self) -> None:
        """Remove all zoom/pan keyframes."""
        self._data['zoomNPan'] = []

    # ------------------------------------------------------------------
    # Audio / visual top-level properties
    # ------------------------------------------------------------------

    @property
    def gain(self) -> float:
        """Audio gain level for the timeline."""
        return float(self._data.get('gain', 1.0))

    @gain.setter
    def gain(self, value: float) -> None:
        """Set the audio gain level for the timeline."""
        self._data['gain'] = value

    @property
    def legacy_attenuate_audio_mix(self) -> bool:
        """Whether legacy audio attenuation mixing is enabled."""
        return bool(self._data.get('legacyAttenuateAudioMix', True))

    @property
    def background_color(self) -> list[int]:
        """Background color as an RGBA list."""
        return self._data.get('backgroundColor', [0, 0, 0, 255])  # type: ignore[no-any-return]

    @background_color.setter
    def background_color(self, value: list[int]) -> None:
        """Set the background color as an RGBA list."""
        self._data['backgroundColor'] = value

    # ------------------------------------------------------------------
    # Caption attributes
    # ------------------------------------------------------------------

    @property
    def caption_attributes(self) -> CaptionAttributes:
        """Caption styling configuration."""
        from camtasia.timeline.captions import CaptionAttributes
        return CaptionAttributes(self._data.setdefault('captionAttributes', {}))

    # ------------------------------------------------------------------
    # Structural validation
    # ------------------------------------------------------------------

    def validate_structure(self) -> list[str]:
        """Check timeline structural invariants.

        Returns a list of issue descriptions (empty = valid).
        """
        issues = []

        # Check 1: trackIndex matches array position
        for i, track in enumerate(self.tracks):
            if track.index != i:
                issues.append(f'Track array[{i}] has trackIndex={track.index}')

        # Check 2: No duplicate clip IDs across all tracks (recursive)
        all_ids: dict[int, str] = {}
        for clip in self.all_clips():
            if clip.id in all_ids:
                issues.append(
                    f'Duplicate clip ID {clip.id} '
                    f'(also on {all_ids[clip.id]})'
                )
            all_ids[clip.id] = 'timeline'

        # Check 3: No stale transition references (per-track clip IDs)
        for track in self.tracks:
            track_clip_ids = {c.id for c in track.clips}
            for trans in track.transitions:
                if trans.left_media_id and trans.left_media_id not in track_clip_ids:
                    issues.append(
                        f'Track {track.index}: transition leftMedia={trans.left_media_id} '
                        f'not found in clips'
                    )
                if trans.right_media_id and trans.right_media_id not in track_clip_ids:
                    issues.append(
                        f'Track {track.index}: transition rightMedia={trans.right_media_id} '
                        f'not found in clips'
                    )

        # Check 4: No overlapping clips on the same track
        for track in self.tracks:
            for a_id, b_id in track.overlaps():
                issues.append(
                    f'Track {track.index}: clips {a_id} and {b_id} overlap'
                )

        return issues

    def flatten_to_track(self, target_track_name: str = 'Flattened') -> Track:
        """Copy all clips from all tracks onto a single target track.

        Creates a new track and copies all clips to it. Original tracks
        are not modified. Clips keep their original timing.

        Args:
            target_track_name: Name for the target track.

        Returns:
            The target track with all clips.
        """
        import copy
        target = self.add_track(target_track_name)
        target_idx = target.index
        next_id = [self.next_clip_id()]
        for track in self.tracks:
            if track.index == target_idx:
                continue
            for m in track._data.get('medias', []):
                new_clip = copy.deepcopy(m)
                _remap_clip_ids_recursive(new_clip, next_id)
                target._data.setdefault('medias', []).append(new_clip)
        return target

    def shift_all(self, seconds: float) -> None:
        """Shift all clips on all tracks by the given number of seconds.

        Positive values move clips forward, negative moves backward.
        Clips are clamped to not go before time 0.
        """
        offset = seconds_to_ticks(seconds)
        for track in self.tracks:
            for m in track._data.get('medias', []):
                new_start = m.get('start', 0) + offset
                m['start'] = max(0, new_start)

    def apply_to_all_clips(self, fn) -> int:
        """Apply a function to every clip on every track. Returns count."""
        count = 0
        for track in self.tracks:
            count += track.apply_to_all(fn)
        return count

    def reverse_track_order(self) -> None:
        """Reverse the order of all tracks."""
        tracks = self._data['sceneTrack']['scenes'][0]['csml']['tracks']
        attrs = self._data.get('trackAttributes', [])
        tracks.reverse()
        if attrs:
            attrs.reverse()
        for i, t in enumerate(tracks):
            t['trackIndex'] = i

    def sort_tracks_by_name(self) -> None:
        """Sort tracks alphabetically by name."""
        tracks = self._data['sceneTrack']['scenes'][0]['csml']['tracks']
        attrs = self._data.get('trackAttributes', [])
        # Pad attrs to match tracks length so no data is dropped
        while len(attrs) < len(tracks):
            attrs.append({})
        pairs = list(zip(tracks, attrs))
        pairs.sort(key=lambda p: p[1].get('ident', ''))
        for i, (t, a) in enumerate(pairs):
            t['trackIndex'] = i
        tracks[:] = [p[0] for p in pairs]
        attrs[:] = [p[1] for p in pairs]

    # ------------------------------------------------------------------
    # Gap manipulation
    # ------------------------------------------------------------------

    def insert_gap(self, position_seconds: float, gap_duration_seconds: float) -> None:
        """Insert a gap at a position across ALL tracks, shifting subsequent clips."""
        from camtasia.timing import seconds_to_ticks
        gap_ticks: int = seconds_to_ticks(gap_duration_seconds)
        position_ticks: int = seconds_to_ticks(position_seconds)
        for track in self.tracks:
            for media_dict in track._data.get('medias', []):
                clip_start: int = media_dict.get('start', 0)
                if clip_start >= position_ticks:
                    media_dict['start'] = clip_start + gap_ticks

    def remove_gap(self, position_seconds: float, gap_duration_seconds: float) -> None:
        """Remove a gap at a position across ALL tracks, pulling subsequent clips back."""
        from camtasia.timing import seconds_to_ticks
        gap_ticks: int = seconds_to_ticks(gap_duration_seconds)
        position_ticks: int = seconds_to_ticks(position_seconds)
        for track in self.tracks:
            for media_dict in track._data.get('medias', []):
                clip_start: int = media_dict.get('start', 0)
                if clip_start >= position_ticks:
                    media_dict['start'] = max(position_ticks, clip_start - gap_ticks)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    @property
    def _track_list(self) -> list[dict[str, Any]]:
        """The raw tracks array: ``sceneTrack.scenes[0].csml.tracks``."""
        return self._data['sceneTrack']['scenes'][0]['csml']['tracks']  # type: ignore[no-any-return]

    @property
    def longest_track(self) -> Track | None:
        """The track with the greatest end time, or None if empty."""
        all_tracks = list(self.tracks)
        if not all_tracks:
            return None
        return max(all_tracks, key=lambda track: track.end_time_ticks())

    def normalize_all_tracks(self) -> None:
        """Normalize timing on all tracks so each starts at time 0."""
        for track in self.tracks:
            track.normalize_timing()

    @property
    def clip_density(self) -> float:
        """Ratio of total clip duration to timeline duration (0.0-1.0+)."""
        timeline_duration: float = self.total_duration_seconds()
        if timeline_duration == 0:
            return 0.0
        total_clip_duration: float = sum(
            track.total_duration_seconds for track in self.tracks
        )
        return total_clip_duration / timeline_duration

    def group_clips_across_tracks(
        self,
        clip_ids: list[int],
        target_track_index: int,
        group_name: str = '',
    ) -> Group:
        """Group clips from multiple tracks into a single Group clip.

        Clips are removed from their original tracks and placed inside
        a new Group on the target track. Each source track becomes an
        internal track in the Group. Empty source tracks are preserved.

        Args:
            clip_ids: IDs of clips to group (can be on different tracks).
            target_track_index: Index of the track to place the Group on.
            group_name: Display name for the Group.

        Returns:
            The newly created Group clip.
        """
        import copy
        from camtasia.timeline.clips.group import Group

        clip_id_set = set(clip_ids)

        # Collect clips from all tracks, grouped by source track
        clips_by_track: dict[int, list[dict]] = {}
        for track in self.tracks:
            for media in track._data.get('medias', []):
                if media.get('id') in clip_id_set:
                    clips_by_track.setdefault(track.index, []).append(media)

        # Validate all clips found
        found_ids: set[int] = set()
        for clips in clips_by_track.values():
            for c in clips:
                found_ids.add(c['id'])
        missing = clip_id_set - found_ids
        if missing:
            raise KeyError(f'Clips not found: {sorted(missing)}')

        # Compute Group bounds
        all_clips_list = [c for clips in clips_by_track.values() for c in clips]
        earliest_start = min(int(c.get('start', 0)) for c in all_clips_list)
        latest_end = max(
            int(c.get('start', 0)) + int(c.get('duration', 0))
            for c in all_clips_list
        )
        group_duration = latest_end - earliest_start

        # Build internal tracks (one per source track)
        internal_tracks: list[dict] = []
        id_counter = [self.next_clip_id()]
        for track_idx in sorted(clips_by_track.keys()):
            internal_medias: list[dict] = []
            for clip_data in clips_by_track[track_idx]:
                cloned = copy.deepcopy(clip_data)
                cloned['start'] = int(cloned.get('start', 0)) - earliest_start
                _remap_clip_ids_recursive(cloned, id_counter)
                internal_medias.append(cloned)
            internal_tracks.append({
                'trackIndex': len(internal_tracks),
                'medias': internal_medias,
                'parameters': {},
                'ident': '',
                'audioMuted': False,
                'videoHidden': False,
                'magnetic': False,
                'matte': 0,
                'solo': False,
            })

        # Remove clips from their original tracks (preserve empty tracks)
        for track in self.tracks:
            medias = track._data.get('medias', [])
            track._data['medias'] = [
                m for m in medias if m.get('id') not in clip_id_set
            ]
            transitions = track._data.get('transitions', [])
            track._data['transitions'] = [
                t for t in transitions
                if t.get('leftMedia') not in clip_id_set
                and t.get('rightMedia') not in clip_id_set
            ]

        # Create the Group on the target track directly with tick values
        # to avoid ticks→seconds→ticks roundtrip
        from camtasia.timeline.clips import clip_from_dict
        from typing import cast
        target_track = self.tracks[target_track_index]
        group_record: dict[str, Any] = {
            'id': self.next_clip_id(),
            '_type': 'Group',
            'start': earliest_start,
            'duration': group_duration,
            'mediaStart': 0,
            'mediaDuration': group_duration,
            'scalar': 1,
            'metadata': {
                'audiateLinkedSession': '',
                'clipSpeedAttribute': {'type': 'bool', 'value': False},
                'colorAttribute': {'type': 'color', 'value': [0, 0, 0, 0]},
                'effectApplied': 'none',
            },
            'animationTracks': {},
            'parameters': {},
            'effects': [],
            'attributes': {
                'ident': group_name,
                'widthAttr': float(self._data.get('width', 1920)),
                'heightAttr': float(self._data.get('height', 1080)),
                'maxDurationAttr': 0,
                'gain': 1.0,
                'mixToMono': False,
                'assetProperties': [],
            },
            'tracks': internal_tracks,
        }
        target_track._data.setdefault('medias', []).append(group_record)
        group = cast(Group, clip_from_dict(group_record))

        return group


class _TrackAccessor:
    """Iterable/indexable accessor over timeline tracks."""

    def __init__(self, data: dict[str, Any]) -> None:
        self._data = data

    @property
    def _track_list(self) -> list[dict[str, Any]]:
        return self._data['sceneTrack']['scenes'][0]['csml']['tracks']  # type: ignore[no-any-return]

    @property
    def _attrs(self) -> list[dict[str, Any]]:
        return self._data.get('trackAttributes', [])  # type: ignore[no-any-return]

    def __len__(self) -> int:
        return len(self._track_list)

    def __iter__(self) -> Iterator[Track]:
        for i, track_data in enumerate(self._track_list):
            attrs = self._attrs[i] if i < len(self._attrs) else {}
            yield Track(attrs, track_data, _all_tracks=self._track_list)

    def __getitem__(self, track_index: int) -> Track:
        """Get a track by its ``trackIndex``.

        Args:
            track_index: The track index.

        Raises:
            KeyError: No track with the given index.
        """
        for i, t in enumerate(self._track_list):
            if t['trackIndex'] == track_index:
                attrs = self._attrs[i] if i < len(self._attrs) else {}
                return Track(attrs, t, _all_tracks=self._track_list)
        raise KeyError(
            f"No track with index={track_index}. "
            f"Timeline has {len(self)} tracks (indices 0\u2013{len(self)-1})"
        )

    def __delitem__(self, track_index: int) -> None:
        """Remove a track by its ``trackIndex``.

        Args:
            track_index: The track index to remove.

        Raises:
            KeyError: No track with the given index.
        """
        tracks = self._track_list
        attrs = self._data.get('trackAttributes', [])

        for i, t in enumerate(tracks):
            if t['trackIndex'] == track_index:
                tracks.pop(i)
                if i < len(attrs):
                    attrs.pop(i)
                for j, t2 in enumerate(tracks):
                    t2['trackIndex'] = j
                return

        raise KeyError(f'No track with index={track_index}')

    def insert_track(self, index: int, name: str) -> Track:
        """Insert a new empty track at the given index.

        Updates ``trackIndex`` on all tracks after insertion.

        Args:
            index: Position to insert the track.
            name: Display name for the track.

        Returns:
            The newly created Track.
        """
        record: dict[str, Any] = {
            'trackIndex': index,
            'medias': [],
            'parameters': {},
        }

        attrs_record: dict[str, Any] = {
            'ident': name,
            'audioMuted': False,
            'videoHidden': False,
            'magnetic': False,
            'matte': 0,
            'solo': False,
            'metadata': {'IsLocked': 'False', 'trackHeight': '33'},
        }

        self._track_list.insert(index, record)
        self._data.setdefault('trackAttributes', []).insert(index, attrs_record)

        # Re-number all tracks since Camtasia uses index as ID
        for j, t in enumerate(self._track_list):
            t['trackIndex'] = j

        return self[index]

    def move_track(self, from_index: int, to_index: int) -> None:
        """Move a track from one array position to another.

        Args:
            from_index: Current array position of the track.
            to_index: Desired array position.

        Raises:
            IndexError: If either index is out of range.
        """
        tracks = self._track_list
        attrs = self._data.get('trackAttributes', [])
        n = len(tracks)
        if not (0 <= from_index < n) or not (0 <= to_index < n):
            raise IndexError(
                f'Track index out of range: from_index={from_index}, '
                f'to_index={to_index}, num_tracks={n}'
            )
        track = tracks.pop(from_index)
        attr = attrs.pop(from_index) if from_index < len(attrs) else {}
        tracks.insert(to_index, track)
        attrs.insert(to_index, attr)
        for j, t in enumerate(tracks):
            t['trackIndex'] = j

    def reorder_tracks(self, order: list[int]) -> None:
        """Reorder tracks by providing current trackIndex values in desired order.

        Args:
            order: List of current ``trackIndex`` values in the new order.

        Raises:
            ValueError: If ``order`` doesn't contain exactly all current indices.
        """
        tracks = self._track_list
        attrs = self._data.get('trackAttributes', [])
        current_indices = {t['trackIndex'] for t in tracks}
        if set(order) != current_indices or len(order) != len(tracks):
            raise ValueError(
                f'order must contain exactly all current trackIndex values: '
                f'{sorted(current_indices)}'
            )
        index_to_pos = {t['trackIndex']: i for i, t in enumerate(tracks)}
        new_tracks = [tracks[index_to_pos[idx]] for idx in order]
        tracks[:] = new_tracks
        if attrs and len(attrs) >= len(tracks):
            new_attrs = [attrs[index_to_pos[idx]] for idx in order]
            attrs[:] = new_attrs
        for j, t in enumerate(tracks):
            t['trackIndex'] = j


class _TimelineMarkers:
    """Timeline markers yielding ``marker.Marker`` instances for backward compat.

    Delegates add/remove to ``MarkerList``.
    """

    def __init__(self, data: dict[str, Any]) -> None:
        self._data = data
        self._inner = MarkerList(data)

    def __iter__(self) -> Iterator[Marker]:
        for m in self._inner:
            yield Marker(name=m.name, time=m.time)

    def __len__(self) -> int:
        return len(self._inner)

    def add(self, name: str, time_ticks: int) -> Marker:
        """Add a marker at the given time."""
        self._inner.add(name, time_ticks)
        return Marker(name=name, time=time_ticks)

    def remove_at(self, time: int) -> None:
        """Remove all markers at the given time."""
        self._inner.remove_at(time)

    def clear(self) -> None:
        """Remove all markers."""
        self._inner.clear()

    def replace(self, markers: list[tuple[str, int]]) -> None:
        """Replace all markers with a new set."""
        self._inner.replace(markers)
