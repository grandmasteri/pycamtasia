"""Group (compound) clip."""
from __future__ import annotations

import copy
import sys
import warnings
from fractions import Fraction
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from camtasia.timeline.transitions import TransitionList
if sys.version_info >= (3, 11):  # pragma: no cover
    from typing import Self
else:  # pragma: no cover
    from typing_extensions import Self
from typing import Any, Iterator, NoReturn

from camtasia.timing import EDIT_RATE, parse_scalar as _parse_scalar, seconds_to_ticks, ticks_to_seconds
from camtasia.types import ClipType

from .base import BaseClip


class GroupTrack:
    """A track inside a Group clip.

    Args:
        data: The raw track dict from the Group's ``tracks`` array.
    """

    def __init__(self, data: dict[str, Any]) -> None:
        self._data = data

    @property
    def track_index(self) -> int:
        """Track index within the group."""
        return int(self._data.get('trackIndex', 0))

    @property
    def clips(self) -> list[BaseClip]:
        """Clips on this group track.

        Returns:
            List of typed clip instances created via ``clip_from_dict``.
        """
        from . import clip_from_dict
        return [clip_from_dict(m) for m in self._data.get('medias', [])]

    @property
    def parameters(self) -> dict[str, Any]:
        """Track parameters dict."""
        return self._data.get('parameters', {})  # type: ignore[no-any-return]

    @property
    def transitions(self) -> 'TransitionList':
        """Transitions are not supported on internal Group tracks."""
        raise AttributeError('Internal Group tracks do not support transitions')

    def add_clip(
        self,
        clip_type: str,
        source_id: int | None,
        start_ticks: int,
        duration_ticks: int,
        *,
        next_id: int | None = None,
        **extra_fields: Any,
    ) -> BaseClip:
        """Add a clip to this internal group track.

        Args:
            clip_type: The ``_type`` value (e.g. ``'AMFile'``, ``'VMFile'``).
            source_id: Source bin ID, or ``None`` for callouts/groups.
            start_ticks: Timeline position in ticks (group-relative).
            duration_ticks: Playback duration in ticks.
            next_id: Explicit clip ID to use.  Pass
                ``project.next_available_id`` for global uniqueness.
                If ``None``, uses local max+1 (unique within this track only).
            **extra_fields: Additional fields merged into the clip dict.

        Returns:
            The newly created typed clip object.
        """
        if next_id is None:
            next_id = max(
                (int(m.get('id', 0)) for m in self._data.get('medias', [])),
                default=0,
            ) + 1
            warnings.warn(
                'GroupTrack.add_clip auto-generated locally-unique ID; '
                'pass next_id for global uniqueness',
                stacklevel=2,
            )
        clip_data: dict[str, Any] = {
            '_type': clip_type,
            'id': next_id,
            'start': start_ticks,
            'duration': duration_ticks,
            'mediaStart': 0,
            'mediaDuration': duration_ticks,
            'scalar': 1,
            'attributes': {},
            'parameters': {},
            'effects': [],
            'metadata': {},
            'animationTracks': {},
            **extra_fields,
        }
        if clip_type in ('IMFile', 'ScreenIMFile'):
            clip_data['mediaDuration'] = 1
        if source_id is not None:
            clip_data['src'] = source_id
        self._data.setdefault('medias', []).append(clip_data)
        from camtasia.timeline.clips import clip_from_dict
        return clip_from_dict(clip_data)

    def __len__(self) -> int:
        """Number of clips in this group track."""
        return len(self._data.get('medias', []))

    def __iter__(self) -> Iterator[BaseClip]:
        """Iterate over clips in this group track."""
        return iter(self.clips)

    def __repr__(self) -> str:
        return f"GroupTrack(index={self.track_index}, clips={len(self)})"


class Group(BaseClip):
    """Compound clip containing its own internal tracks.

    Args:
        data: The raw clip dict.
    """

    def set_source(self, source_id: int) -> NoReturn:
        raise TypeError('Group clips do not have a source ID')

    @property
    def tracks(self) -> list[GroupTrack]:
        """Internal tracks, each with their own clips."""
        return [GroupTrack(t) for t in self._data.get('tracks', [])]

    @property
    def clip_count(self) -> int:
        """Total number of clips across all internal tracks."""
        return sum(len(group_track) for group_track in self.tracks)

    def add_internal_track(self) -> GroupTrack:
        """Add a new empty internal track to this Group.

        Returns:
            The newly created GroupTrack.
        """
        track_index: int = len(self._data.get('tracks', []))
        new_track_data: dict[str, Any] = {
            'trackIndex': track_index,
            'medias': [],
            'parameters': {},
            'ident': '',
            'audioMuted': False,
            'videoHidden': False,
            'magnetic': False,
            'matte': 0,
            'solo': False,
        }
        self._data.setdefault('tracks', []).append(new_track_data)
        return GroupTrack(new_track_data)

    def ungroup(self) -> list[BaseClip]:
        """Extract all internal clips as a flat list.

        Returns the clips with their start times adjusted to be relative
        to the Group's position on the timeline.  Internal clip data is
        deep-copied so the Group's own state is never mutated.

        Returns:
            List of clips with timeline-absolute start positions.
        """
        group_start: int = self.start
        extracted_clips: list[BaseClip] = []
        for group_track in self.tracks:
            for clip in group_track.clips:
                cloned_data: dict[str, Any] = copy.deepcopy(dict(clip._data))
                cloned_data['start'] = cloned_data.get('start', 0) + group_start
                from camtasia.timeline.clips import clip_from_dict
                extracted_clips.append(clip_from_dict(cloned_data))
        return extracted_clips

    @property
    def attributes(self) -> dict[str, Any]:
        """Group attributes dict (ident, widthAttr, heightAttr)."""
        return self._data.get('attributes', {})

    @property
    def ident(self) -> str:
        """Group name / identifier."""
        return str(self.attributes.get('ident', ''))

    @property
    def width(self) -> float:
        """Group width."""
        return float(self.attributes.get('widthAttr', 0.0))

    @property
    def height(self) -> float:
        """Group height."""
        return float(self.attributes.get('heightAttr', 0.0))

    @property
    def is_screen_recording(self) -> bool:
        """Return True if this group contains screen recording media."""
        for track in self._data.get('tracks', []):
            for media in track.get('medias', []):
                if media.get('_type') in ('UnifiedMedia', 'ScreenVMFile'):
                    return True
        return False

    @property
    def internal_media_src(self) -> int | None:
        """Return the source ID of the internal screen recording media, or None."""
        for track in self._data.get('tracks', []):
            for media in track.get('medias', []):
                if media.get('_type') == 'UnifiedMedia':
                    return media.get('video', {}).get('src')  # type: ignore[no-any-return]
                if media.get('_type') == 'ScreenVMFile':
                    return media.get('src')  # type: ignore[no-any-return]
        return None

    def find_internal_clip(self, clip_type: str) -> BaseClip | None:
        """Find the first internal clip matching the given type string."""
        for track in self.tracks:
            for clip in track.clips:
                if clip.clip_type == clip_type:
                    return clip
        return None

    @property
    def all_internal_clips(self) -> list[BaseClip]:
        """All clips across all internal tracks (flat list)."""
        all_clips: list[BaseClip] = []
        for group_track in self.tracks:
            all_clips.extend(group_track.clips)
        return all_clips

    @property
    def internal_clip_types(self) -> set[str]:
        """Set of unique clip types across all internal tracks."""
        return {clip.clip_type for clip in self.all_internal_clips}

    @property
    def has_audio(self) -> bool:
        """Whether any internal clip is an audio clip."""
        return any(clip.is_audio for clip in self.all_internal_clips)

    @property
    def has_video(self) -> bool:
        """Whether any internal clip is a video clip."""
        return any(clip.is_video for clip in self.all_internal_clips)

    @property
    def internal_duration_seconds(self) -> float:
        """Duration of the longest internal track in seconds."""
        if not self.tracks:
            return 0.0
        max_end: int = 0
        for group_track in self.tracks:
            for clip in group_track.clips:
                clip_end: int = clip.start + clip.duration
                if clip_end > max_end:
                    max_end = clip_end
        return float(ticks_to_seconds(max_end))

    def find_internal_clips_by_type(self, clip_type: str | ClipType) -> list[BaseClip]:
        """Find all internal clips of a specific type.

        Args:
            clip_type: Clip type string or ClipType enum value.

        Returns:
            List of matching clips across all internal tracks.
        """
        return [clip for clip in self.all_internal_clips if clip.clip_type == clip_type]

    def remove_internal_clip(self, clip_id: int) -> None:
        """Remove a clip from any internal track by ID.

        Args:
            clip_id: The ``id`` of the internal clip to remove.

        Raises:
            KeyError: If no internal clip with the given ID exists.
        """
        for group_track in self.tracks:
            medias: list[dict[str, Any]] = group_track._data.get('medias', [])
            for i, media_dict in enumerate(medias):
                if media_dict.get('id') == clip_id:
                    medias.pop(i)
                    return
        raise KeyError(f'No internal clip with id={clip_id}')

    def clear_all_internal_clips(self) -> int:
        """Remove all clips from all internal tracks.

        Returns:
            The total number of clips removed.
        """
        total_removed: int = 0
        for group_track in self.tracks:
            medias: list[dict[str, Any]] = group_track._data.get('medias', [])
            total_removed += len(medias)
            medias.clear()
        return total_removed

    def set_dimensions(self, width_pixels: float, height_pixels: float) -> Self:
        """Set the Group's width and height attributes.

        Args:
            width_pixels: New width value.
            height_pixels: New height value.

        Returns:
            ``self`` for fluent chaining.
        """
        self._data.setdefault('attributes', {})['widthAttr'] = width_pixels
        self._data['attributes']['heightAttr'] = height_pixels
        return self

    def rename(self, new_name: str) -> Self:
        """Rename this Group.

        Args:
            new_name: The new identifier for this Group.

        Returns:
            ``self`` for fluent chaining.
        """
        self._data.setdefault('attributes', {})['ident'] = new_name
        return self

    def merge_internal_tracks(self) -> GroupTrack:
        """Merge all internal tracks into a single track.

        Moves every clip from tracks[1:] into tracks[0], then removes
        the extra tracks.  If the group has no tracks, a new empty one
        is created.

        Returns:
            The surviving (first) GroupTrack containing all clips.
        """
        if not self.tracks:
            return self.add_internal_track()
        target_track: GroupTrack = self.tracks[0]
        for source_track in self.tracks[1:]:
            for media_dict in source_track._data.get('medias', []):
                target_track._data.setdefault('medias', []).append(media_dict)
        # Remove all tracks except the first
        self._data['tracks'] = [self._data['tracks'][0]]
        self._data['tracks'][0]['trackIndex'] = 0
        return target_track

    def describe(self) -> str:
        """Human-readable Group description."""
        lines: list[str] = [
            f'Group(id={self.id}, ident={self.ident!r})',
            f'  Tracks: {len(self.tracks)}',
            f'  Total clips: {self.clip_count}',
            f'  Types: {", ".join(sorted(str(t) for t in self.internal_clip_types)) or "none"}',
            f'  Duration: {self.duration_seconds:.2f}s',
        ]
        if self.is_screen_recording:
            lines.append('  Screen recording: yes')
        return '\n'.join(lines)

    # ------------------------------------------------------------------
    # Per-segment speed via StitchedMedia (v2 reverse-engineered format)
    # ------------------------------------------------------------------

    def set_internal_segment_speeds(
        self,
        segments: list[tuple[float, float, float]],
        *,
        next_id: int | None = None,
        canvas_width: float | None = None,
        canvas_height: float | None = None,
        source_width: float | None = None,
        source_height: float | None = None,
        source_bin: list[dict] | None = None,
    ) -> None:
        """Replace the internal track's media with per-segment StitchedMedia clips.

        Each segment maps a slice of the source recording to a timeline
        duration, allowing different playback speeds per segment.

        Uses the Camtasia StitchedMedia format reverse-engineered from
        v2 projects: each StitchedMedia clip on the Group's internal
        track has its own ``scalar``, ``mediaStart``, and nested
        ScreenVMFile + ScreenIMFile children.

        Args:
            segments: List of ``(source_start_s, source_end_s,
                timeline_duration_s)`` tuples.
            next_id: Starting ID for generated clips. If ``None``,
                auto-detects from existing internal clip IDs.
            canvas_width: Optional width to set on each created
                ScreenVMFile clip.  When provided, overrides the source
                recording's native width so the clip fits the project
                canvas (e.g. 1920 for a Retina recording).
            canvas_height: Optional height to set on each created
                ScreenVMFile clip.

        Warning:
            Camtasia may throw a "Collision exception" when loading
            projects with more than ~8 ScreenVMFile segments inside a
            Group.  If you need more segments, consider merging adjacent
            segments with similar speeds to stay under the limit.
        """
        if len(segments) > 8:
            import warnings
            warnings.warn(
                f'{len(segments)} segments requested; Camtasia may fail to '
                f'load Groups with >8 internal ScreenVMFile clips. '
                f'Consider merging adjacent segments.',
                UserWarning, stacklevel=2,
            )
        # Find the internal track containing UnifiedMedia or existing media
        media_track = None
        template_media = None
        for track in self._data.get('tracks', []):
            for m in track.get('medias', []):
                if m['_type'] in ('UnifiedMedia', 'StitchedMedia', 'ScreenVMFile'):
                    media_track = track
                    template_media = m
                    break
            if media_track is not None:
                break
        if media_track is None:
            raise ValueError('No internal track with UnifiedMedia found')
        assert template_media is not None  # guaranteed by media_track check

        # Extract template info from UnifiedMedia or first StitchedMedia
        if template_media['_type'] == 'UnifiedMedia':
            video = template_media['video']
            src = video['src']
            ident = video['attributes'].get('ident', '')
            video_params = copy.deepcopy(video.get('parameters', {}))
            video_effects = copy.deepcopy(video.get('effects', []))
        else:
            src = template_media.get('src', 0)
            ident = template_media.get('attributes', {}).get('ident', '')
            video_params = {}
            video_effects = []

        # Build clips for each segment.
        # Following v2 Track 1 pattern: use bare ScreenVMFile clips with
        # scalar and clipSpeedAttribute for speed-changed segments.
        new_medias = []
        cursor_ticks: int = 0

        # Auto-resolve source dimensions from sourceBin if not provided
        if (canvas_width is not None or canvas_height is not None) and source_width is None and source_height is None and source_bin is not None:
            for entry in source_bin:
                if entry.get('id') == src:
                    for st in entry.get('sourceTracks', []):
                        rect = st.get('trackRect', [0, 0, 0, 0])
                        if rect[2] > 0 and rect[3] > 0:
                            source_width = float(rect[2])
                            source_height = float(rect[3])
                            break
                    break

        if next_id is None:
            max_id = 0
            for track in self._data.get('tracks', []):
                for m in track.get('medias', []):
                    max_id = max(max_id, m.get('id', 0))
            next_id = max_id + 1
        cid = next_id

        for src_start, src_end, tl_dur in segments:
            src_dur = src_end - src_start
            scalar = Fraction(tl_dur).limit_denominator(100000) / Fraction(src_dur).limit_denominator(100000)

            start_ticks = cursor_ticks
            dur_ticks = seconds_to_ticks(tl_dur)
            ms_ticks = seconds_to_ticks(src_start)
            media_dur_ticks = seconds_to_ticks(src_dur)

            clip = {
                'id': cid,
                '_type': 'ScreenVMFile',
                'src': src,
                'trackNumber': 0,
                'attributes': {'ident': ident},
                'parameters': copy.deepcopy(video_params),
                'effects': copy.deepcopy(video_effects),
                'start': start_ticks,
                'duration': dur_ticks,
                'mediaStart': ms_ticks,
                'mediaDuration': media_dur_ticks,
                'scalar': str(scalar) if scalar != 1 else 1,
                'metadata': {
                    'audiateLinkedSession': '',
                    'clipSpeedAttribute': {
                        'type': 'bool',
                        'value': True,
                    },
                    'colorAttribute': {
                        'type': 'color',
                        'value': [0, 0, 0, 0],
                    },
                    'effectApplied': 'none',
                },
                'animationTracks': {},
            }
            new_medias.append(clip)
            if canvas_width is not None and canvas_height is not None:
                source_w = source_width if source_width is not None else self._data.get('attributes', {}).get('widthAttr', canvas_width)
                source_h = source_height if source_height is not None else self._data.get('attributes', {}).get('heightAttr', canvas_height)
                sv = canvas_width / source_w if source_w else 1.0
                sv2 = canvas_height / source_h if source_h else 1.0
                if abs(sv - sv2) > 0.01:
                    import warnings
                    warnings.warn(
                        f'Source aspect ratio ({source_w}×{source_h}) differs from canvas '
                        f'({canvas_width}×{canvas_height}): scale0={sv:.4f}, scale1={sv2:.4f}. '
                        f'Using uniform scale {min(sv, sv2):.4f} (best fit).',
                        UserWarning, stacklevel=2,
                    )
                    sv = sv2 = min(sv, sv2)
                clip['parameters']['scale0'] = {'type': 'double', 'defaultValue': sv, 'interp': 'eioe'}
                clip['parameters']['scale1'] = {'type': 'double', 'defaultValue': sv2, 'interp': 'eioe'}
            elif canvas_width is not None:
                source_w = source_width if source_width is not None else self._data.get('attributes', {}).get('widthAttr', canvas_width)
                sv = canvas_width / source_w if source_w else 1.0
                clip['parameters']['scale0'] = {'type': 'double', 'defaultValue': sv, 'interp': 'eioe'}
            elif canvas_height is not None:
                source_h = source_height if source_height is not None else self._data.get('attributes', {}).get('heightAttr', canvas_height)
                sv2 = canvas_height / source_h if source_h else 1.0
                clip['parameters']['scale1'] = {'type': 'double', 'defaultValue': sv2, 'interp': 'eioe'}
            cursor_ticks += dur_ticks
            cid += 1

        # Replace the internal track's medias
        media_track['medias'] = new_medias

        # Remove transitions key — internal Group tracks should not have it
        # per the format reference §8
        media_track.pop('transitions', None)

        # Update Group duration and mediaDuration to match total timeline
        total_tl = cursor_ticks
        self._data['duration'] = total_tl
        self._data['mediaDuration'] = total_tl
        self._data['mediaStart'] = 0
        self._data['scalar'] = 1

        # Keep VMFile on other tracks but extend to cover full source
        for track in self._data.get('tracks', []):
            if track is media_track:
                continue
            for m in track.get('medias', []):
                if m.get('_type') in ('VMFile', 'ScreenVMFile'):
                    m['duration'] = total_tl
                    m['mediaDuration'] = total_tl

    def sync_internal_durations(self) -> Self:
        """Trim all internal clips to match the Group's duration.

        Call this after trimming a Group's duration so that internal
        clips don't extend beyond the visible portion.  This ensures
        fade-out animations placed at the Group's end are visible.

        Returns:
            ``self`` for chaining.
        """
        group_dur = self._data.get('duration', 0)
        for track in self._data.get('tracks', []):
            for m in track.get('medias', []):
                if m.get('duration', 0) > group_dur:
                    m['duration'] = group_dur
                    if m.get('_type') in ('IMFile', 'ScreenIMFile'):
                        m['mediaDuration'] = 1
                    else:
                        scalar = _parse_scalar(m.get('scalar', 1))
                        if scalar != 0:
                            md = Fraction(m['duration']) / scalar
                            m['mediaDuration'] = int(md) if md == int(md) else str(md)
        return self
