"""Track on the timeline — wraps a single track dict and its attributes."""
from __future__ import annotations

from typing import Any, Iterator

from camtasia.timeline.clips import BaseClip, clip_from_dict
from camtasia.timeline.transitions import TransitionList
from camtasia.timeline.markers import MarkerList
from camtasia.timeline.marker import Marker


class Track:
    """A track on the timeline.

    Wraps both the track data dict (from ``csml.tracks``) and the
    corresponding entry in ``trackAttributes``.

    Args:
        attributes: The ``trackAttributes`` record for this track.
        data: The track dict from ``csml.tracks``.
    """

    def __init__(self, attributes: dict[str, Any], data: dict[str, Any]) -> None:
        self._attributes = attributes
        self._data = data

    # ------------------------------------------------------------------
    # Identity / display properties
    # ------------------------------------------------------------------

    @property
    def name(self) -> str:
        """Track name from trackAttributes ``ident``."""
        return self._attributes.get('ident', '')

    @name.setter
    def name(self, value: str) -> None:
        self._attributes['ident'] = value

    @property
    def index(self) -> int:
        """Track index (position in the track list)."""
        return self._data['trackIndex']

    # ------------------------------------------------------------------
    # Track attribute flags
    # ------------------------------------------------------------------

    @property
    def audio_muted(self) -> bool:
        return self._attributes.get('audioMuted', False)

    @audio_muted.setter
    def audio_muted(self, value: bool) -> None:
        self._attributes['audioMuted'] = value

    @property
    def video_hidden(self) -> bool:
        return self._attributes.get('videoHidden', False)

    @video_hidden.setter
    def video_hidden(self, value: bool) -> None:
        self._attributes['videoHidden'] = value

    @property
    def magnetic(self) -> bool:
        return self._attributes.get('magnetic', False)

    @magnetic.setter
    def magnetic(self, value: bool) -> None:
        self._attributes['magnetic'] = value

    @property
    def solo(self) -> bool:
        return self._attributes.get('solo', False)

    @solo.setter
    def solo(self, value: bool) -> None:
        self._attributes['solo'] = value

    @property
    def is_locked(self) -> bool:
        return self._attributes.get('metadata', {}).get('IsLocked', 'False') == 'True'

    @is_locked.setter
    def is_locked(self, value: bool) -> None:
        self._attributes.setdefault('metadata', {})['IsLocked'] = str(value)

    # ------------------------------------------------------------------
    # Clips
    # ------------------------------------------------------------------

    @property
    def clips(self) -> _ClipAccessor:
        """Iterable accessor over typed clip objects on this track."""
        return _ClipAccessor(self._data)

    @property
    def medias(self) -> _ClipAccessor:
        """Alias for ``clips`` (backward compatibility)."""
        return self.clips

    # ------------------------------------------------------------------
    # Transitions & markers
    # ------------------------------------------------------------------

    @property
    def transitions(self) -> TransitionList:
        """Track-level transitions between clips."""
        return TransitionList(self._data)

    @property
    def markers(self) -> MarkerList:
        """Per-media markers (TOC keyframes in track parameters)."""
        return MarkerList(self._data)

    # ------------------------------------------------------------------
    # Clip mutation helpers
    # ------------------------------------------------------------------

    def add_clip(
        self,
        clip_type: str,
        source_id: int | None,
        start: int,
        duration: int,
        **kwargs: Any,
    ) -> BaseClip:
        """Create a clip dict and append it to this track.

        Args:
            clip_type: The ``_type`` value (e.g. ``'AMFile'``, ``'IMFile'``).
            source_id: Source bin ID, or ``None`` for callouts/groups.
            start: Timeline position in ticks.
            duration: Playback duration in ticks.
            **kwargs: Additional fields merged into the clip dict.

        Returns:
            The newly created typed clip object.
        """
        record: dict[str, Any] = {
            'id': self._next_clip_id(),
            '_type': clip_type,
            'start': start,
            'duration': duration,
            'mediaStart': kwargs.pop('media_start', 0),
            'mediaDuration': kwargs.pop('media_duration', duration),
            'scalar': kwargs.pop('scalar', 1),
            'metadata': kwargs.pop('metadata', {}),
            'animationTracks': kwargs.pop('animation_tracks', {}),
            'parameters': kwargs.pop('parameters', {}),
            'effects': kwargs.pop('effects', []),
        }
        if source_id is not None:
            record['src'] = source_id
        record.update(kwargs)

        self._data.setdefault('medias', []).append(record)
        return clip_from_dict(record)

    def remove_clip(self, clip_id: int) -> None:
        """Remove a clip by its ID.

        Args:
            clip_id: The unique clip ID to remove.

        Raises:
            KeyError: No clip with the given ID exists on this track.
        """
        medias = self._data.get('medias', [])
        for i, m in enumerate(medias):
            if m['id'] == clip_id:
                medias.pop(i)
                return
        raise KeyError(f'No clip with id={clip_id} on track {self.index}')

    def _next_clip_id(self) -> int:
        """Scan all medias on this track for the max ID and increment."""
        max_id = max((m['id'] for m in self._data.get('medias', [])), default=0)
        return max_id + 1

    def __repr__(self) -> str:
        return f'Track(name={self.name!r}, index={self.index})'


class _ClipAccessor:
    """Lightweight iterable/indexable accessor over a track's clips."""

    def __init__(self, data: dict[str, Any]) -> None:
        self._data = data

    @property
    def _medias(self) -> list[dict[str, Any]]:
        return self._data.get('medias', [])

    def __len__(self) -> int:
        return len(self._medias)

    def __iter__(self) -> Iterator[BaseClip]:
        for m in self._medias:
            clip = clip_from_dict(m)
            clip.markers = _PerMediaMarkers(m)
            yield clip

    def __getitem__(self, clip_id: int) -> BaseClip:
        """Get a clip by its ID.

        Args:
            clip_id: The unique clip ID.

        Raises:
            KeyError: No clip with the given ID.
        """
        for m in self._medias:
            if m['id'] == clip_id:
                clip = clip_from_dict(m)
                clip.markers = _PerMediaMarkers(m)
                return clip
        raise KeyError(f'No clip with id={clip_id}')


class _PerMediaMarkers:
    """Per-media markers with timeline-adjusted times.

    Marker timestamps in the JSON are relative to the source media.
    This class adjusts them to timeline-relative positions:
    ``start + (marker_time - media_start)``.
    """

    def __init__(self, media_data: dict[str, Any]) -> None:
        self._data = media_data

    def __iter__(self) -> Iterator[Marker]:
        keyframes = (
            self._data
            .get('parameters', {})
            .get('toc', {})
            .get('keyframes', [])
        )
        start = self._data.get('start', 0)
        media_start = self._data.get('mediaStart', 0)
        for kf in keyframes:
            yield Marker(
                name=kf['value'],
                time=start + (kf['time'] - media_start),
            )

    def __len__(self) -> int:
        return len(
            self._data
            .get('parameters', {})
            .get('toc', {})
            .get('keyframes', [])
        )
