"""Timeline — top-level container for tracks, markers, and scene data."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterator

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
    def end_seconds(self) -> float:
        """End time of the timeline in seconds."""
        return ticks_to_seconds(self.total_duration_ticks)

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
        """Collect all clips across all tracks.

        Returns:
            A flat list of every clip on the timeline.
        """
        return [clip for track in self.tracks for clip in track.clips]

    def find_track(self, name: str) -> Track | None:
        """Find a track by name, or return None."""
        for track in self.tracks:
            if track.name == name:
                return track
        return None

    @property
    def empty_tracks(self) -> list[Track]:
        """Return all tracks with no clips."""
        return [t for t in self.tracks if t.is_empty]

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
    def all_effects(self) -> list[tuple[Track, BaseClip, dict]]:
        """All effects across all tracks as (track, clip, effect_dict) tuples."""
        results = []
        for track in self.tracks:
            for clip in track.clips:
                for eff in clip._data.get('effects', []):
                    results.append((track, clip, eff))
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
        return self._data.get('gain', 1.0)

    @gain.setter
    def gain(self, value: float) -> None:
        self._data['gain'] = value

    @property
    def legacy_attenuate_audio_mix(self) -> bool:
        return self._data.get('legacyAttenuateAudioMix', True)

    @property
    def background_color(self) -> list[int]:
        return self._data.get('backgroundColor', [0, 0, 0, 255])

    @background_color.setter
    def background_color(self, value: list[int]) -> None:
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

        # Check 2: No duplicate clip IDs across all tracks
        all_ids: dict[int, str] = {}
        for track in self.tracks:
            for clip in track.clips:
                if clip.id in all_ids:
                    issues.append(
                        f'Duplicate clip ID {clip.id} on track {track.index} '
                        f'(also on {all_ids[clip.id]})'
                    )
                all_ids[clip.id] = f'track {track.index}'

        # Check 3: No stale transition references
        for track in self.tracks:
            clip_ids = {c.id for c in track.clips}
            for trans in track.transitions:
                if trans.left_media_id and trans.left_media_id not in clip_ids:
                    issues.append(
                        f'Track {track.index}: transition leftMedia={trans.left_media_id} '
                        f'not found in clips'
                    )
                if trans.right_media_id and trans.right_media_id not in clip_ids:
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
        next_id = self.next_clip_id()
        for track in self.tracks:
            if track.index == target_idx:
                continue
            for m in track._data.get('medias', []):
                new_clip = copy.deepcopy(m)
                new_clip['id'] = next_id
                next_id += 1
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
        attrs = self._data['trackAttributes']
        tracks.reverse()
        attrs.reverse()
        for i, t in enumerate(tracks):
            t['trackIndex'] = i

    def sort_tracks_by_name(self) -> None:
        """Sort tracks alphabetically by name."""
        tracks = self._data['sceneTrack']['scenes'][0]['csml']['tracks']
        attrs = self._data['trackAttributes']
        pairs = list(zip(tracks, attrs))
        pairs.sort(key=lambda p: p[1].get('ident', ''))
        for i, (t, a) in enumerate(pairs):
            t['trackIndex'] = i
        tracks[:] = [p[0] for p in pairs]
        attrs[:] = [p[1] for p in pairs]

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    @property
    def _track_list(self) -> list[dict[str, Any]]:
        """The raw tracks array: ``sceneTrack.scenes[0].csml.tracks``."""
        return self._data['sceneTrack']['scenes'][0]['csml']['tracks']


class _TrackAccessor:
    """Iterable/indexable accessor over timeline tracks."""

    def __init__(self, data: dict[str, Any]) -> None:
        self._data = data

    @property
    def _track_list(self) -> list[dict[str, Any]]:
        return self._data['sceneTrack']['scenes'][0]['csml']['tracks']

    @property
    def _attrs(self) -> list[dict[str, Any]]:
        return self._data.get('trackAttributes', [])

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
        new_attrs = [attrs[index_to_pos[idx]] for idx in order]
        tracks[:] = new_tracks
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
