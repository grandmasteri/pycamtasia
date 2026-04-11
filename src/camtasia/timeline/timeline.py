"""Timeline — top-level container for tracks, markers, and scene data."""
from __future__ import annotations

from typing import Any, Iterator

from camtasia.timeline.clips import BaseClip
from camtasia.timeline.markers import Marker, MarkerList
from camtasia.timeline.track import Track
from camtasia.timing import ticks_to_seconds


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

    def total_duration_ticks(self) -> int:
        """Maximum end time across all tracks, in ticks.

        Returns:
            The tick position of the latest clip end, or 0 if empty.
        """
        max_end = 0
        for track in self.tracks:
            for clip in track.clips:
                end = clip.start + clip.duration
                if end > max_end:
                    max_end = end
        return max_end

    def total_duration_seconds(self) -> float:
        """Maximum end time across all tracks, in seconds.

        Returns:
            Duration in seconds, or 0.0 if the timeline is empty.
        """
        return ticks_to_seconds(self.total_duration_ticks())

    @property
    def duration_seconds(self) -> float:
        """Total timeline duration in seconds."""
        return self.total_duration_seconds()

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

    def remove_empty_tracks(self) -> int:
        """Remove all empty tracks. Returns count removed."""
        empty_indices = [t.index for t in self.tracks if t.is_empty]
        for idx in reversed(empty_indices):
            self.remove_track(idx)
        return len(empty_indices)

    def add_marker(self, label: str, time_seconds: float) -> Marker:
        """Add a timeline marker at the given time.

        Args:
            label: Display label for the marker.
            time_seconds: Position in seconds.

        Returns:
            The newly created Marker.
        """
        from camtasia.timing import seconds_to_ticks
        return self.markers.add(label, seconds_to_ticks(time_seconds))

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
        raise KeyError(f'No track with index={track_index}')

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
