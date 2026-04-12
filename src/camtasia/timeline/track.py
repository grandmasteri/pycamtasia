"""Track on the timeline — wraps a single track dict and its attributes."""
from __future__ import annotations

import copy
import json
from typing import Any, Iterator

from camtasia.annotations import callouts
from camtasia.timeline.clips import AMFile, BaseClip, Callout, Group, IMFile, VMFile, clip_from_dict
from camtasia.timeline.transitions import Transition, TransitionList
from camtasia.timeline.markers import MarkerList
from camtasia.timeline.marker import Marker
from camtasia.timing import seconds_to_ticks, ticks_to_seconds


_VALID_CLIP_TYPES = frozenset({
    'AMFile', 'VMFile', 'IMFile', 'Callout', 'Group',
    'ScreenVMFile', 'ScreenIMFile', 'StitchedMedia', 'UnifiedMedia',
})


class Track:
    """A track on the timeline.

    Wraps both the track data dict (from ``csml.tracks``) and the
    corresponding entry in ``trackAttributes``.

    Args:
        attributes: The ``trackAttributes`` record for this track.
        data: The track dict from ``csml.tracks``.
    """

    def __init__(
        self,
        attributes: dict[str, Any],
        data: dict[str, Any],
        _all_tracks: list[dict[str, Any]] | None = None,
    ) -> None:
        self._attributes = attributes
        self._data = data
        self._all_tracks = _all_tracks

    # ------------------------------------------------------------------
    # Identity / display properties
    # ------------------------------------------------------------------

    @property
    def name(self) -> str:
        """Track name from trackAttributes ``ident``."""
        return self._attributes.get('ident', '')

    @name.setter
    def name(self, value: str) -> None:
        """Set the track name."""
        self._attributes['ident'] = value

    @property
    def index(self) -> int:
        """Track index (position in the track list)."""
        return self._data['trackIndex']

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Track):
            return NotImplemented
        return self._data is other._data or self.index == other.index

    def __hash__(self) -> int:
        return hash(self.index)

    def __len__(self) -> int:
        """Number of clips on this track."""
        return len(self._data.get('medias', []))

    @property
    def clip_count(self) -> int:
        """Number of clips on this track."""
        return len(self)

    def find_clip(self, clip_id: int) -> BaseClip | None:
        """Find a clip by ID, or return None."""
        try:
            return self.clips[clip_id]
        except KeyError:
            return None

    # ------------------------------------------------------------------
    # Track attribute flags
    # ------------------------------------------------------------------

    @property
    def audio_muted(self) -> bool:
        """Whether the track's audio is muted."""
        return self._attributes.get('audioMuted', False)

    @audio_muted.setter
    def audio_muted(self, value: bool) -> None:
        """Set whether the track's audio is muted."""
        self._attributes['audioMuted'] = value

    @property
    def video_hidden(self) -> bool:
        """Whether the track's video is hidden."""
        return self._attributes.get('videoHidden', False)

    @video_hidden.setter
    def video_hidden(self, value: bool) -> None:
        """Set whether the track's video is hidden."""
        self._attributes['videoHidden'] = value

    @property
    def magnetic(self) -> bool:
        """Whether the track has magnetic clip snapping enabled."""
        return self._attributes.get('magnetic', False)

    @magnetic.setter
    def magnetic(self, value: bool) -> None:
        """Set whether magnetic clip snapping is enabled."""
        self._attributes['magnetic'] = value

    @property
    def solo(self) -> bool:
        """Whether the track is soloed for exclusive playback."""
        return self._attributes.get('solo', False)

    @solo.setter
    def solo(self, value: bool) -> None:
        """Set whether the track is soloed."""
        self._attributes['solo'] = value

    def mute(self) -> None:
        """Mute this track's audio."""
        self.audio_muted = True

    def unmute(self) -> None:
        """Unmute this track's audio."""
        self.audio_muted = False

    def hide(self) -> None:
        """Hide this track's video."""
        self.video_hidden = True

    def show(self) -> None:
        """Show this track's video."""
        self.video_hidden = False

    @property
    def is_locked(self) -> bool:
        """Whether the track is locked against editing."""
        return self._attributes.get('metadata', {}).get('IsLocked', 'False') == 'True'

    @is_locked.setter
    def is_locked(self, value: bool) -> None:
        """Set whether the track is locked against editing."""
        self._attributes.setdefault('metadata', {})['IsLocked'] = str(value)

    # ------------------------------------------------------------------
    # Clips
    # ------------------------------------------------------------------

    def clear(self) -> None:
        """Remove all clips and transitions from this track."""
        self._data['medias'] = []
        self._data['transitions'] = []

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
        if clip_type not in _VALID_CLIP_TYPES:
            raise ValueError(f'Unknown clip type {clip_type!r}. Valid: {sorted(_VALID_CLIP_TYPES)}')

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
                transitions = self._data.get('transitions', [])
                self._data['transitions'] = [
                    t for t in transitions
                    if t.get('leftMedia') != clip_id and t.get('rightMedia') != clip_id
                ]
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

    def add_callout_from_builder(
        self,
        builder: 'CalloutBuilder',
        start_seconds: float,
        duration_seconds: float,
    ) -> Callout:
        """Add a callout using a CalloutBuilder configuration."""
        clip = self.add_callout(
            builder.text, start_seconds, duration_seconds,
            font_name=builder._font_name,
            font_weight=builder._font_weight,
            font_size=builder._font_size,
        )
        clip.move_to(builder._x, builder._y)
        if builder._width and builder._height:
            clip.resize(builder._width, builder._height)
        if builder._fill_color:
            clip.fill_color = builder._fill_color
        if builder._font_color:
            clip.set_colors(font_color=builder._font_color)
        if builder._stroke_color:
            clip.stroke_color = builder._stroke_color
        clip.set_alignment(builder._alignment, 'center')
        return clip

    def add_title(
        self,
        text: str,
        start_seconds: float,
        duration_seconds: float,
        preset: str = 'centered',
        **kwargs: Any,
    ) -> Callout:
        """Add a title callout with preset styling.

        Args:
            text: The title text content.
            start_seconds: Timeline position in seconds.
            duration_seconds: Playback duration in seconds.
            preset: Preset name. Currently only ``'centered'`` is supported.
            **kwargs: Additional fields merged into the clip dict.

        Returns:
            The newly created Callout clip for further customization.

        Raises:
            ValueError: If the preset name is not recognized.
        """
        if preset != 'centered':
            raise ValueError(f'Unknown title preset: {preset!r}')

        clip = self.add_callout(
            text, start_seconds, duration_seconds,
            font_name='Montserrat', font_weight='Regular', font_size=64.0,
            **kwargs,
        )
        clip.set_colors(font_color=(1.0, 1.0, 1.0))
        clip.set_alignment('center', 'center')
        clip.set_size(934.5, 253.9)
        clip.position(-416.6, -274.8)
        return clip

    def add_lower_third(
        self,
        title: str,
        subtitle: str,
        start_seconds: float,
        duration_seconds: float,
        title_color: tuple[int, int, int, int] | None = None,
        accent_color: tuple[float, float, float] | None = None,
        *,
        font_weight: int = 900,
        scale: float | None = None,
        template_ident: str = 'Right Angle Lower Third',
    ) -> Group:
        """Add a Right Angle Lower Third title template to the track.

        Args:
            title: Main heading text (replaces 'Your Name Here').
            subtitle: Body text (replaces 'Lorem ipsum...').
            start_seconds: Timeline position in seconds.
            duration_seconds: Playback duration in seconds.
            title_color: Optional RGBA tuple ``(r, g, b, a)`` 0-255 for the
                title text ``fgColor``.
            accent_color: Optional ``(r, g, b)`` floats 0.0-1.0 for the
                accent line fill color.
            font_weight: Font weight for the title text (default 900).
            scale: Uniform scale for the outer Group (default ``None``
                leaves the template scale unchanged).
            template_ident: Identity string for the outer Group
                (default ``'Right Angle Lower Third'``).

        Returns:
            The newly created Group clip.
        """
        from camtasia.templates.lower_third import LOWER_THIRD_TEMPLATE

        tpl = copy.deepcopy(LOWER_THIRD_TEMPLATE)

        # --- Assign fresh sequential IDs ---
        base_id = self._next_clip_id()
        # Map old IDs to new ones: outer=83, text_group=84, subtitle=85,
        # title=86, shape=87, line=88
        old_ids = [83, 84, 85, 86, 87, 88]
        id_map = {old: base_id + i for i, old in enumerate(old_ids)}

        tpl['id'] = id_map[83]

        # Walk inner tracks and reassign IDs
        for track in tpl['tracks']:
            for media in track.get('medias', []):
                media['id'] = id_map[media['id']]
                # Recurse into nested group tracks (text group)
                for inner_track in media.get('tracks', []):
                    for inner_media in inner_track.get('medias', []):
                        inner_media['id'] = id_map[inner_media['id']]

        # Update assetProperties object references
        for ap in tpl.get('attributes', {}).get('assetProperties', []):
            ap['objects'] = [id_map[o] for o in ap['objects']]
        # Inner text group assetProperties
        text_group = tpl['tracks'][0]['medias'][0]
        for ap in text_group.get('attributes', {}).get('assetProperties', []):
            ap['objects'] = [id_map[o] for o in ap['objects']]

        # --- Set timing ---
        start_ticks = seconds_to_ticks(start_seconds)
        dur_ticks = seconds_to_ticks(duration_seconds)
        tpl['start'] = start_ticks
        tpl['duration'] = dur_ticks
        tpl['mediaDuration'] = float(dur_ticks)

        # --- Replace text ---
        # Title is clip id_map[86] on tracks[0].medias[0].tracks[1].medias[0]
        title_clip = text_group['tracks'][1]['medias'][0]
        title_clip['def']['text'] = title
        # Update textAttributes rangeEnd to match new text length
        for kf in title_clip['def'].get('textAttributes', {}).get('keyframes', []):
            for attr in kf.get('value', []):
                attr['rangeEnd'] = len(title)

        # Subtitle is clip id_map[85] on tracks[0].medias[0].tracks[0].medias[0]
        subtitle_clip = text_group['tracks'][0]['medias'][0]
        subtitle_clip['def']['text'] = subtitle
        for kf in subtitle_clip['def'].get('textAttributes', {}).get('keyframes', []):
            for attr in kf.get('value', []):
                attr['rangeEnd'] = len(subtitle)

        # --- Optional color overrides ---
        if title_color is not None:
            r, g, b, a = title_color
            color_str = f'({r},{g},{b},{a})'
            for kf in title_clip['def']['textAttributes']['keyframes']:
                for attr in kf['value']:
                    if attr['name'] == 'fgColor':
                        attr['value'] = color_str

        if accent_color is not None:
            line_clip = tpl['tracks'][2]['medias'][0]
            for channel, val in zip(
                ('fill-color-red', 'fill-color-green', 'fill-color-blue'),
                accent_color,
            ):
                line_clip['def'][channel]['defaultValue'] = val
                for kf in line_clip['def'][channel].get('keyframes', []):
                    kf['value'] = val

        # --- font_weight override ---
        for kf in title_clip['def']['textAttributes']['keyframes']:
            for attr in kf['value']:
                if attr['name'] == 'fontWeight':
                    attr['value'] = font_weight

        # --- scale override ---
        if scale is not None:
            tpl['parameters']['scale0'] = scale
            tpl['parameters']['scale1'] = scale

        # --- template_ident override ---
        tpl['attributes']['ident'] = template_ident

        # --- Insert into track ---
        self._data.setdefault('medias', []).append(tpl)
        return clip_from_dict(tpl)  # type: ignore[return-value]

    def add_group(
        self,
        start_seconds: float,
        duration_seconds: float,
        internal_tracks: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> Group:
        """Add a Group clip to the track.

        Args:
            start_seconds: Timeline position in seconds.
            duration_seconds: Playback duration in seconds.
            internal_tracks: List of internal track dicts. If ``None``, an
                empty ``tracks`` list is created.
            **kwargs: Additional fields merged into the clip dict.

        Returns:
            The newly created Group clip.
        """
        clip = self.add_clip(
            'Group', None,
            seconds_to_ticks(start_seconds),
            seconds_to_ticks(duration_seconds),
            tracks=internal_tracks or [],
            attributes=kwargs.pop('attributes', {
                'ident': '', 'gain': 1.0, 'mixToMono': False,
            }),
            **kwargs,
        )
        return clip  # type: ignore[return-value]

    def add_screen_recording(
        self,
        source_id: int,
        start_seconds: float,
        duration_seconds: float,
        background_source_id: int = 1,
    ) -> Group:
        """Add a Camtasia Rev screen recording Group to the track.

        Creates a Group with the standard Rev structure:

        - Track 0: VMFile shader background
        - Track 1: UnifiedMedia with ScreenVMFile video + AMFile audio

        Args:
            source_id: Source bin ID for the .trec media entry.
            start_seconds: Timeline position in seconds.
            duration_seconds: Playback duration in seconds.
            background_source_id: Source bin ID for the background shader
                (defaults to 1).

        Returns:
            The newly created Group clip.
        """
        dur_ticks = seconds_to_ticks(duration_seconds)
        next_id = self._next_clip_id()

        bg_media = {
            'id': next_id + 1,
            '_type': 'VMFile',
            'src': background_source_id,
            'trackNumber': 0,
            'attributes': {'ident': ''},
            'parameters': {},
            'effects': [],
            'start': 0,
            'duration': dur_ticks,
            'mediaStart': 0,
            'mediaDuration': dur_ticks,
            'scalar': 1,
            'metadata': {},
            'animationTracks': {},
        }

        unified_media = {
            'id': next_id + 2,
            '_type': 'UnifiedMedia',
            'video': {
                'id': next_id + 3,
                '_type': 'ScreenVMFile',
                'src': source_id,
                'trackNumber': 0,
                'attributes': {'ident': ''},
                'parameters': {},
                'effects': [],
                'start': 0,
                'duration': dur_ticks,
                'mediaStart': 0,
                'mediaDuration': dur_ticks,
                'scalar': 1,
                'animationTracks': {},
            },
            'audio': {
                'id': next_id + 4,
                '_type': 'AMFile',
                'src': source_id,
                'trackNumber': 1,
                'attributes': {
                    'ident': '', 'gain': 1.0, 'mixToMono': False,
                    'loudnessNormalization': True, 'sourceFileOffset': 0,
                },
                'channelNumber': '0',
                'parameters': {},
                'effects': [],
            },
            'effects': [],
            'start': 0,
            'duration': dur_ticks,
            'mediaStart': 0,
            'mediaDuration': dur_ticks,
            'scalar': 1,
        }

        internal_tracks = [
            {'trackIndex': 0, 'medias': [bg_media]},
            {'trackIndex': 1, 'medias': [unified_media]},
        ]

        return self.add_group(
            start_seconds, duration_seconds,
            internal_tracks=internal_tracks,
            attributes={
                'ident': '', 'gain': 1.0, 'mixToMono': False,
            },
        )

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

    def sort_clips(self) -> None:
        """Sort clips by start time."""
        self._data.get('medias', []).sort(key=lambda m: m.get('start', 0))

    @property
    def first_clip(self) -> BaseClip | None:
        """First clip by start time, or None if track is empty."""
        medias = self._data.get('medias', [])
        if not medias:
            return None
        return clip_from_dict(min(medias, key=lambda m: m.get('start', 0)))

    @property
    def last_clip(self) -> BaseClip | None:
        """Last clip by end time, or None if track is empty."""
        medias = self._data.get('medias', [])
        if not medias:
            return None
        return clip_from_dict(max(medias, key=lambda m: m.get('start', 0) + m.get('duration', 0)))

    @property
    def is_empty(self) -> bool:
        """True if this track has no clips."""
        return len(self) == 0

    def end_time_ticks(self) -> int:
        """End time of the last clip on this track, in ticks."""
        max_end = 0
        for m in self._data.get('medias', []):
            end = m.get('start', 0) + m.get('duration', 0)
            max_end = max(max_end, end)
        return max_end

    def end_time_seconds(self) -> float:
        """Return the end time of the last clip on this track in seconds.

        Returns:
            Maximum ``start + duration`` across all clips, in seconds.
            Returns ``0.0`` if the track has no clips.
        """
        return ticks_to_seconds(self.end_time_ticks())

    def set_segment_speeds(
        self,
        clip_id: int,
        segments: list[tuple[float, float]],
    ) -> list:
        """Split a clip into segments with per-segment playback speeds.

        Splits the clip at the boundaries defined by each segment's
        timeline duration, then sets the appropriate scalar on each
        piece so it plays at the requested speed.

        Internally handles the Camtasia-specific scalar formula,
        ``mediaStart`` accumulation, VMFile scalar compensation,
        and ``clipSpeedAttribute`` metadata.

        Args:
            clip_id: ID of the clip to split and speed-adjust.
            segments: List of ``(timeline_duration_seconds, speed)``
                tuples.  *speed* is a multiplier where ``1.0`` means
                the clip's original playback rate, ``2.0`` means twice
                as fast, ``0.5`` means half speed, etc.  The sum of
                all *timeline_duration_seconds* must equal the clip's
                current duration.

        Returns:
            List of the resulting clip objects (one per segment).
        """
        from fractions import Fraction as _Frac

        # Find the clip
        clip = None
        for c in self.clips:
            if c.id == clip_id:
                clip = c
                break
        if clip is None:
            raise KeyError(f'No clip with id={clip_id} on this track')

        total_dur = ticks_to_seconds(clip.duration)
        md = clip._data.get('mediaDuration', clip.duration)
        source_dur = ticks_to_seconds(int(md))
        original_scalar = _Frac(source_dur / total_dur).limit_denominator(100000)
        vmfile_scalar = (_Frac(1) / original_scalar).limit_denominator(100000)

        # Split right-to-left at segment boundaries
        split_points = []
        clip_start = ticks_to_seconds(clip.start)
        t = clip_start
        for dur_s, _ in segments[:-1]:
            t += dur_s
            split_points.append(t)

        current = clip
        for sp in reversed(split_points):
            left, right = self.split_clip(current.id, sp)
            current = left

        # Collect the split pieces in order
        pieces = sorted(
            [c for c in self.clips if c.start >= clip.start],
            key=lambda c: c.start,
        )[:len(segments)]

        # Apply scalars using reverse-engineered Camtasia formula:
        #   scalar = original_scalar / user_speed
        #   mediaStart[i+1] = mediaStart[i] + dur[i] * (original_scalar / scalar[i])
        #   VMFile scalar = 1 / original_scalar
        cumulative_ms = 0.0
        for piece, (dur_s, speed) in zip(pieces, segments):
            seg_scalar = (
                original_scalar / _Frac(speed).limit_denominator(100000)
            ).limit_denominator(100000)
            piece.scalar = seg_scalar
            piece.duration = seconds_to_ticks(dur_s)
            piece._data['mediaStart'] = int(cumulative_ms)
            piece._data.setdefault('metadata', {})['clipSpeedAttribute'] = {
                'type': 'bool', 'value': True,
            }
            # Adjust internal VMFile scalar to compensate for Group speed
            for itrack in piece._data.get('tracks', []):
                for imedia in itrack.get('medias', []):
                    if imedia.get('_type') == 'VMFile':
                        imedia['scalar'] = str(vmfile_scalar)

            advance = seconds_to_ticks(dur_s) * float(original_scalar / seg_scalar)
            cumulative_ms += advance

        return pieces

    def duplicate_clip(self, clip_id: int, *, offset_seconds: float = 0.0) -> BaseClip:
        """Duplicate a clip on this track.

        Creates a deep copy of the clip with a new ID, placed immediately
        after the original (or offset by offset_seconds).

        Args:
            clip_id: ID of the clip to duplicate.
            offset_seconds: Time offset from the original's end (default 0).

        Returns:
            The new clip.
        """
        source = None
        for m in self._data.get('medias', []):
            if m.get('id') == clip_id:
                source = m
                break
        if source is None:
            raise KeyError(f'No clip with id={clip_id}')

        new_data = copy.deepcopy(source)
        new_id = self._next_clip_id()
        new_data['id'] = new_id

        def _remap_ids(obj, base_id):
            cid = base_id
            if isinstance(obj, dict):
                if 'id' in obj and obj is not new_data:
                    cid += 1
                    obj['id'] = cid
                for v in obj.values():
                    cid = _remap_ids(v, cid)
            elif isinstance(obj, list):
                for item in obj:
                    cid = _remap_ids(item, cid)
            return cid
        _remap_ids(new_data, new_id)

        new_data['start'] = source['start'] + source.get('duration', 0) + seconds_to_ticks(offset_seconds)

        self._data.setdefault('medias', []).append(new_data)
        return clip_from_dict(new_data)

    def move_clip(self, clip_id: int, new_start_seconds: float) -> None:
        """Move a clip to a new timeline position.

        Args:
            clip_id: ID of the clip to move.
            new_start_seconds: New start position in seconds.
        """
        for m in self._data.get('medias', []):
            if m.get('id') == clip_id:
                m['start'] = seconds_to_ticks(new_start_seconds)
                # Remove transitions referencing the moved clip
                transitions = self._data.get('transitions', [])
                self._data['transitions'] = [
                    t for t in transitions
                    if t.get('leftMedia') != clip_id and t.get('rightMedia') != clip_id
                ]
                return
        raise KeyError(f'No clip with id={clip_id}')

    def split_clip(self, clip_id: int, split_at_seconds: float) -> tuple:
        """Split a clip into two halves at a timeline position.

        The left half keeps the original clip dict (mutated in place).
        The right half is a deep copy inserted immediately after.

        For Group clips, internal tracks are deep-copied unchanged —
        the Group's ``mediaStart``/``mediaDuration`` act as a viewing
        window into the internal timeline.

        Args:
            clip_id: ID of the clip to split.
            split_at_seconds: Absolute timeline position in seconds.

        Returns:
            Tuple of ``(left_clip, right_clip)`` as typed clip objects.

        Raises:
            KeyError: No clip with the given ID on this track.
            ValueError: Split point is outside the clip's time range.
        """
        import copy

        medias = self._data.get('medias', [])
        left_data = None
        left_idx = None
        for i, m in enumerate(medias):
            if m['id'] == clip_id:
                left_data = m
                left_idx = i
                break
        if left_data is None:
            raise KeyError(f'No clip with id={clip_id} on track {self.index}')

        split_point = seconds_to_ticks(split_at_seconds)
        orig_start = left_data['start']
        orig_duration = left_data['duration']

        if split_point <= orig_start or split_point >= orig_start + orig_duration:
            start_sec = ticks_to_seconds(orig_start)
            end_sec = ticks_to_seconds(orig_start + orig_duration)
            raise ValueError(
                f"Split point {split_at_seconds}s is outside clip range "
                f"({start_sec:.3f}s\u2013{end_sec:.3f}s) for clip id={clip_id}"
            )

        split_offset = split_point - orig_start

        # Deep copy for right half
        right_data = copy.deepcopy(left_data)

        # Mutate left half
        left_data['duration'] = split_offset
        left_data['mediaDuration'] = split_offset

        # Mutate right half
        right_data['start'] = orig_start + split_offset
        right_data['duration'] = orig_duration - split_offset
        right_data['mediaStart'] = split_offset
        right_data['mediaDuration'] = orig_duration - split_offset

        # Assign new sequential IDs to right half
        next_id = self._next_clip_id()
        right_data['id'] = next_id
        next_id += 1

        # Re-ID internal tracks for Group clips
        if right_data.get('_type') == 'Group':
            for track in right_data.get('tracks', []):
                for media in track.get('medias', []):
                    media['id'] = next_id
                    next_id += 1
                    # Handle UnifiedMedia with nested video/audio
                    if 'video' in media:
                        media['video']['id'] = next_id
                        next_id += 1
                    if 'audio' in media:
                        media['audio']['id'] = next_id
                        next_id += 1

        # Insert right half after left half
        medias.insert(left_idx + 1, right_data)

        # Cascade: remove transitions referencing the split clip
        transitions = self._data.get('transitions', [])
        self._data['transitions'] = [
            t for t in transitions
            if t.get('leftMedia') != clip_id and t.get('rightMedia') != clip_id
        ]

        return (clip_from_dict(left_data), clip_from_dict(right_data))

    def _next_clip_id(self) -> int:
        """Scan all medias for the max ID and increment.

        When ``_all_tracks`` is set, scans every track in the project
        (including nested group tracks and UnifiedMedia sub-clips) to
        avoid ID collisions across tracks.  Falls back to scanning only
        this track when ``_all_tracks`` is not available.
        """
        sources = self._all_tracks if self._all_tracks is not None else [self._data]
        return _max_clip_id(sources) + 1

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


def _max_clip_id(tracks: list[dict[str, Any]]) -> int:
    """Return the maximum clip ID across a list of track dicts, recursively."""
    best = 0
    for track in tracks:
        for m in track.get('medias', []):
            best = max(best, m.get('id', 0))
            if 'video' in m:
                best = max(best, m['video'].get('id', 0))
            if 'audio' in m:
                best = max(best, m['audio'].get('id', 0))
            # Recurse into Group internal tracks
            inner_tracks = m.get('tracks', [])
            if inner_tracks:
                best = max(best, _max_clip_id(inner_tracks))
    return best