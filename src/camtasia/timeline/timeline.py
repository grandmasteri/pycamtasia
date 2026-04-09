"""Timeline — top-level container for tracks, markers, and scene data."""
from __future__ import annotations

from typing import Any, Iterator

from camtasia.timeline.markers import MarkerList
from camtasia.timeline.marker import Marker
from camtasia.timeline.track import Track


class Timeline:
    """Represents the timeline of a Camtasia project.

    Args:
        timeline_data: The ``timeline`` sub-dict from the project JSON.
    """

    def __init__(self, timeline_data: dict[str, Any]) -> None:
        self._data = timeline_data

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

    # ------------------------------------------------------------------
    # Markers
    # ------------------------------------------------------------------

    @property
    def markers(self) -> _TimelineMarkers:
        """Timeline-level markers (from ``parameters.toc``)."""
        return _TimelineMarkers(self._data)

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
            yield Track(attrs, track_data)

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
                return Track(attrs, t)
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
        }

        attrs_record: dict[str, Any] = {
            'ident': name,
            'audioMuted': False,
            'videoHidden': False,
            'magnetic': False,
            'metadata': {'IsLocked': 'False', 'trackHeight': '33'},
        }

        self._track_list.insert(index, record)
        self._data.setdefault('trackAttributes', []).insert(index, attrs_record)

        # Re-number all tracks since Camtasia uses index as ID
        for j, t in enumerate(self._track_list):
            t['trackIndex'] = j

        return self[index]


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
