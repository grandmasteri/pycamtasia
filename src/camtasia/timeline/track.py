"""Track on the timeline — wraps a single track dict and its attributes."""
from __future__ import annotations

from typing import Any, Iterator

from camtasia.annotations import callouts
from camtasia.timeline.clips import AMFile, BaseClip, Callout, IMFile, VMFile, clip_from_dict
from camtasia.timeline.transitions import Transition, TransitionList
from camtasia.timeline.markers import MarkerList
from camtasia.timeline.marker import Marker
from camtasia.timing import seconds_to_ticks, ticks_to_seconds


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
            'trackNumber': 0,
            'start': start,
            'duration': duration,
            'mediaStart': kwargs.pop('media_start', 0),
            'mediaDuration': kwargs.pop('media_duration', duration),
            'scalar': kwargs.pop('scalar', 1),
            'metadata': {
                'audiateLinkedSession': '',
                'clipSpeedAttribute': {'type': 'bool', 'value': False},
                'colorAttribute': {'type': 'color', 'value': [0, 0, 0, 0]},
                'effectApplied': 'none',
                **kwargs.pop('metadata', {}),
            },
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

    # ------------------------------------------------------------------
    # L2 convenience methods — typed, seconds-based clip creation
    # ------------------------------------------------------------------

    def add_image(
        self,
        source_id: int,
        start_seconds: float,
        duration_seconds: float,
        **kwargs: Any,
    ) -> IMFile:
        """Add an image clip (IMFile) to the track.

        Args:
            source_id: Source bin ID for the image.
            start_seconds: Timeline position in seconds.
            duration_seconds: Playback duration in seconds.
            **kwargs: Additional fields merged into the clip dict.

        Returns:
            The newly created IMFile clip.
        """
        clip = self.add_clip(
            'IMFile', source_id,
            seconds_to_ticks(start_seconds),
            seconds_to_ticks(duration_seconds),
            media_duration=1,
            trimStartSum=1,
            **kwargs,
        )
        return clip  # type: ignore[return-value]

    def add_audio(
        self,
        source_id: int,
        start_seconds: float,
        duration_seconds: float,
        **kwargs: Any,
    ) -> AMFile:
        """Add an audio clip (AMFile) to the track.

        Args:
            source_id: Source bin ID for the audio.
            start_seconds: Timeline position in seconds.
            duration_seconds: Playback duration in seconds.
            **kwargs: Additional fields merged into the clip dict.

        Returns:
            The newly created AMFile clip.
        """
        clip = self.add_clip(
            'AMFile', source_id,
            seconds_to_ticks(start_seconds),
            seconds_to_ticks(duration_seconds),
            attributes={'ident': '', 'gain': 1.0, 'mixToMono': False,
                        'loudnessNormalization': True, 'sourceFileOffset': 0},
            channelNumber='0',
            **kwargs,
        )
        return clip  # type: ignore[return-value]

    def add_video(
        self,
        source_id: int,
        start_seconds: float,
        duration_seconds: float,
        **kwargs: Any,
    ) -> VMFile:
        """Add a video clip (VMFile) to the track.

        Args:
            source_id: Source bin ID for the video.
            start_seconds: Timeline position in seconds.
            duration_seconds: Playback duration in seconds.
            **kwargs: Additional fields merged into the clip dict.

        Returns:
            The newly created VMFile clip.
        """
        clip = self.add_clip(
            'VMFile', source_id,
            seconds_to_ticks(start_seconds),
            seconds_to_ticks(duration_seconds),
            **kwargs,
        )
        return clip  # type: ignore[return-value]

    def add_callout(
        self,
        text: str,
        start_seconds: float,
        duration_seconds: float,
        font_name: str = 'Arial',
        font_weight: str = 'Normal',
        font_size: float = 96.0,
        **kwargs: Any,
    ) -> Callout:
        """Add a text callout clip to the track.

        Args:
            text: The callout text content.
            start_seconds: Timeline position in seconds.
            duration_seconds: Playback duration in seconds.
            font_name: Font family name.
            font_weight: Font weight (e.g. ``'Regular'``, ``'Bold'``).
            font_size: Font size in points.
            **kwargs: Additional fields merged into the clip dict.

        Returns:
            The newly created Callout clip.
        """
        callout_def = callouts.text(text, font_name, font_weight, font_size)
        clip = self.add_clip(
            'Callout', None,
            seconds_to_ticks(start_seconds),
            seconds_to_ticks(duration_seconds),
            **{'def': callout_def, **kwargs},
        )
        return clip  # type: ignore[return-value]

    def add_transition(
        self,
        name: str,
        left_clip: BaseClip,
        right_clip: BaseClip,
        duration_seconds: float = 0.5,
    ) -> Transition:
        """Add a named transition between two clips on this track.

        Args:
            name: Transition type name (e.g. ``'FadeThroughBlack'``).
            left_clip: The clip on the left side.
            right_clip: The clip on the right side.
            duration_seconds: Transition duration in seconds.

        Returns:
            The newly created Transition.
        """
        return self.transitions.add(
            name, left_clip.id, right_clip.id,
            seconds_to_ticks(duration_seconds),
        )

    def add_fade_through_black(
        self,
        left_clip: BaseClip,
        right_clip: BaseClip,
        duration_seconds: float = 0.5,
    ) -> Transition:
        """Add a FadeThroughBlack transition between two clips.

        Args:
            left_clip: The clip on the left side.
            right_clip: The clip on the right side.
            duration_seconds: Transition duration in seconds.

        Returns:
            The newly created Transition.
        """
        return self.transitions.add_fade_through_black(
            left_clip.id, right_clip.id,
            seconds_to_ticks(duration_seconds),
        )

    def add_image_sequence(
        self,
        source_ids: list[int],
        start_seconds: float,
        duration_per_image_seconds: float,
        transition_seconds: float = 0.0,
        transition_name: str = 'FadeThroughBlack',
    ) -> list[IMFile]:
        """Add a sequence of image clips, optionally with transitions.

        Args:
            source_ids: Source bin IDs for each image.
            start_seconds: Timeline position of the first image.
            duration_per_image_seconds: Duration of each image clip.
            transition_seconds: Transition duration between images (0 = none).
            transition_name: Transition type name.

        Returns:
            List of created IMFile clips.
        """
        clips: list[IMFile] = []
        offset = start_seconds
        for src_id in source_ids:
            clip = self.add_image(src_id, offset, duration_per_image_seconds)
            clips.append(clip)
            offset += duration_per_image_seconds

        if transition_seconds > 0 and len(clips) > 1:
            for i in range(len(clips) - 1):
                self.transitions.add_fade_through_black(
                    clips[i].id, clips[i + 1].id,
                    seconds_to_ticks(transition_seconds),
                )

        return clips

    def end_time_seconds(self) -> float:
        """Return the end time of the last clip on this track in seconds.

        Returns:
            Maximum ``start + duration`` across all clips, in seconds.
            Returns ``0.0`` if the track has no clips.
        """
        max_ticks = max(
            (clip.start + clip.duration for clip in self.clips),
            default=0,
        )
        return ticks_to_seconds(max_ticks)

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
