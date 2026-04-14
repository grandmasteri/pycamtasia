"""Group (compound) clip."""
from __future__ import annotations

import copy
from fractions import Fraction
from typing import Any, Iterator

from camtasia.timing import EDIT_RATE, seconds_to_ticks

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

    @property
    def tracks(self) -> list[GroupTrack]:
        """Internal tracks, each with their own clips."""
        return [GroupTrack(t) for t in self._data.get('tracks', [])]

    @property
    def attributes(self) -> dict[str, Any]:
        """Group attributes dict (ident, widthAttr, heightAttr)."""
        return self._data.get('attributes', {})  # type: ignore[no-any-return]

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

    # ------------------------------------------------------------------
    # Per-segment speed via StitchedMedia (v2 reverse-engineered format)
    # ------------------------------------------------------------------

    def set_internal_segment_speeds(
        self,
        segments: list[tuple[float, float, float]],
        *,
        next_id: int | None = None,
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
        """
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
        timeline_cursor: float = 0

        if next_id is None:
            max_id = 0
            for track in self._data.get('tracks', []):
                for m in track.get('medias', []):
                    max_id = max(max_id, m.get('id', 0))
            next_id = max_id + 1
        cid = next_id

        for src_start, src_end, tl_dur in segments:
            src_dur = src_end - src_start
            scalar = Fraction(src_dur / tl_dur).limit_denominator(100000)

            start_ticks = seconds_to_ticks(timeline_cursor)
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
            timeline_cursor += tl_dur
            cid += 1

        # Replace the internal track's medias
        media_track['medias'] = new_medias
        media_track['transitions'] = []

        # Update Group duration and mediaDuration to match total timeline
        total_tl = seconds_to_ticks(timeline_cursor)
        self._data['duration'] = total_tl
        self._data['mediaDuration'] = total_tl
        self._data['scalar'] = 1

        # Keep VMFile on other tracks but extend to cover full source
        for track in self._data.get('tracks', []):
            if track is media_track:
                continue
            for m in track.get('medias', []):
                if m.get('_type') in ('VMFile', 'ScreenVMFile'):
                    m['duration'] = total_tl
                    m['mediaDuration'] = total_tl
