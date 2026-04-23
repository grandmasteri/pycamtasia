"""Group (compound) clip."""
from __future__ import annotations

import copy
from fractions import Fraction
import sys
from typing import TYPE_CHECKING
import warnings

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Iterator

    from camtasia.timeline.transitions import TransitionList
    from camtasia.types import ClipType
if sys.version_info >= (3, 11):  # pragma: no cover
    from typing import Self
else:  # pragma: no cover
    from typing_extensions import Self
from typing import Any, NoReturn

from camtasia.timing import parse_scalar as _parse_scalar
from camtasia.timing import seconds_to_ticks, ticks_to_seconds, EDIT_RATE

from .base import BaseClip


def _scale_keyframes_and_tracks(data_dict: dict[str, Any], scalar: Fraction) -> None:
    """Scale parameters keyframes and animationTracks entries by scalar."""
    for _, pval in data_dict.get('parameters', {}).items():
        if isinstance(pval, dict) and 'keyframes' in pval:
            for kf in pval['keyframes']:
                for field in ('time', 'endTime'):
                    if field in kf:
                        kf[field] = round(Fraction(str(kf[field])) * scalar)
                if 'duration' in kf:
                    kf['duration'] = round(Fraction(str(kf['duration'])) * scalar)
    for track_entry in data_dict.get('animationTracks', {}).get('visual', []):
        for field in ('time', 'endTime', 'duration'):
            if field in track_entry:
                track_entry[field] = round(Fraction(str(track_entry[field])) * scalar)
        if 'range' in track_entry and isinstance(track_entry['range'], list) and len(track_entry['range']) == 2:
            track_entry['range'] = [
                round(Fraction(str(track_entry['range'][0])) * scalar),
                round(Fraction(str(track_entry['range'][1])) * scalar),
            ]


def _collect_all_ids(clip_data: dict[str, Any]) -> set[int]:
    """Recursively collect all 'id' fields from a clip and its nested structures."""
    ids: set[int] = set()
    if 'id' in clip_data:
        ids.add(clip_data['id'])
    for key in ('video', 'audio'):
        sub = clip_data.get(key)
        if isinstance(sub, dict):
            ids.update(_collect_all_ids(sub))
    for track in clip_data.get('tracks', []):
        for media in track.get('medias', []):
            ids.update(_collect_all_ids(media))
    for media in clip_data.get('medias', []):
        ids.update(_collect_all_ids(media))
    return ids


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
    def transitions(self) -> TransitionList:
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
        group_scalar = _parse_scalar(self._data.get('scalar', 1))
        extracted_clips: list[BaseClip] = []
        for group_track in self.tracks:
            for clip in group_track.clips:
                cloned_data: dict[str, Any] = copy.deepcopy(dict(clip._data))
                if group_scalar != 1:
                    orig_start = Fraction(str(cloned_data.get('start', 0)))
                    orig_dur = Fraction(str(cloned_data.get('duration', 0)))
                    new_start = orig_start * group_scalar
                    new_dur = orig_dur * group_scalar
                    cloned_data['start'] = round(new_start)
                    cloned_data['duration'] = round(new_dur)
                    orig_scalar = _parse_scalar(cloned_data.get('scalar', 1))
                    composed = group_scalar * orig_scalar
                    cloned_data['scalar'] = int(composed) if composed == int(composed) else str(composed)
                    # Scale effect start/duration
                    for effect in cloned_data.get('effects', []):
                        if 'start' in effect:
                            orig_eff_start = Fraction(str(effect['start']))
                            new_eff_start = orig_eff_start * group_scalar
                            effect['start'] = round(new_eff_start)
                        if 'duration' in effect:
                            orig_eff_dur = Fraction(str(effect['duration']))
                            new_eff_dur = orig_eff_dur * group_scalar
                            effect['duration'] = round(new_eff_dur)
                    # Also scale effects on UnifiedMedia sub-clips
                    if cloned_data.get('_type') == 'UnifiedMedia':
                        for sub_key in ('video', 'audio'):
                            sub = cloned_data.get(sub_key)
                            if sub is not None:
                                for effect in sub.get('effects', []):
                                    if 'start' in effect:
                                        orig_start = Fraction(str(effect['start']))
                                        effect['start'] = round(orig_start * group_scalar)
                                    if 'duration' in effect:
                                        orig_dur = Fraction(str(effect['duration']))
                                        effect['duration'] = round(orig_dur * group_scalar)
                    # Scale parameters keyframes and animationTracks
                    _scale_keyframes_and_tracks(cloned_data, group_scalar)
                    if cloned_data.get('_type') == 'UnifiedMedia':
                        for sub_key in ('video', 'audio'):
                            sub = cloned_data.get(sub_key)
                            if sub is not None:
                                _scale_keyframes_and_tracks(sub, group_scalar)
                    if cloned_data.get('_type') == 'StitchedMedia':
                        for inner in cloned_data.get('medias', []):
                            _scale_keyframes_and_tracks(inner, group_scalar)
                    if cloned_data.get('_type') == 'StitchedMedia' and group_scalar != 1:
                        for inner in cloned_data.get('medias', []):
                            inner_orig_scalar = _parse_scalar(inner.get('scalar', 1))
                            composed_inner = group_scalar * inner_orig_scalar
                            inner['scalar'] = int(composed_inner) if composed_inner == int(composed_inner) else str(composed_inner)
                            inner_md = Fraction(str(inner.get('mediaDuration', 0)))
                            new_inner_dur = inner_md * composed_inner
                            inner['duration'] = round(new_inner_dur)
                            # Scale effects on inner segments
                            for effect in inner.get('effects', []):
                                if 'start' in effect:
                                    orig_eff_start = Fraction(str(effect['start']))
                                    effect['start'] = round(orig_eff_start * group_scalar)
                                if 'duration' in effect:
                                    orig_eff_dur = Fraction(str(effect['duration']))
                                    effect['duration'] = round(orig_eff_dur * group_scalar)
                            # Propagate to UnifiedMedia segments
                            if inner.get('_type') == 'UnifiedMedia':
                                for sub_key in ('video', 'audio'):
                                    sub = inner.get(sub_key)
                                    if sub is not None:
                                        sub['scalar'] = inner['scalar']
                                        sub['duration'] = inner['duration']
                                        sub['start'] = inner['start']
                                        if 'mediaDuration' in inner:
                                            sub['mediaDuration'] = inner['mediaDuration']
                                        # Scale effects on sub-clips
                                        for effect in sub.get('effects', []):
                                            if 'start' in effect:
                                                orig = Fraction(str(effect['start']))
                                                effect['start'] = round(orig * group_scalar)
                                            if 'duration' in effect:
                                                orig = Fraction(str(effect['duration']))
                                                effect['duration'] = round(orig * group_scalar)
                        cursor = 0
                        for inner in cloned_data.get('medias', []):
                            inner['start'] = cursor
                            cursor += round(Fraction(str(inner['duration'])))
                        # Adjust last segment to close rounding gap
                        wrapper_dur = round(Fraction(str(cloned_data['duration'])))
                        total_inner = sum(round(Fraction(str(inner['duration']))) for inner in cloned_data.get('medias', []))
                        if total_inner != wrapper_dur and cloned_data.get('medias'):
                            last = cloned_data['medias'][-1]
                            old_dur = round(Fraction(str(last['duration'])))
                            adjusted_dur = old_dur + (wrapper_dur - total_inner)
                            last['duration'] = adjusted_dur
                            last_scalar = _parse_scalar(last.get('scalar', 1))
                            if last_scalar != 0:
                                new_md = Fraction(adjusted_dur) / last_scalar
                                last['mediaDuration'] = int(new_md) if new_md == int(new_md) else str(new_md)
                            if last.get('_type') == 'UnifiedMedia':
                                for sub_key in ('video', 'audio'):
                                    sub = last.get(sub_key)
                                    if sub is not None:
                                        sub['duration'] = adjusted_dur
                                        if 'mediaDuration' in last:
                                            sub['mediaDuration'] = last['mediaDuration']
                    if cloned_data.get('_type') == 'Group' and group_scalar != 1:
                        for inner_track in cloned_data.get('tracks', []):
                            for nested_clip in inner_track.get('medias', []):
                                orig_n_start = Fraction(str(nested_clip.get('start', 0)))
                                orig_n_dur = Fraction(str(nested_clip.get('duration', 0)))
                                nested_clip['start'] = round(orig_n_start * group_scalar)
                                nested_clip['duration'] = round(orig_n_dur * group_scalar)
                                nested_scalar = _parse_scalar(nested_clip.get('scalar', 1))
                                composed = nested_scalar * group_scalar
                                nested_clip['scalar'] = 1 if composed == 1 else str(composed)
                                # Bug 5: recalc mediaDuration for non-image, non-compound inner clips
                                if nested_clip.get('_type') not in ('IMFile', 'ScreenIMFile', 'StitchedMedia', 'Group', 'UnifiedMedia'):
                                    if composed != 0:
                                        nested_md = Fraction(nested_clip['duration']) / composed
                                        nested_clip['mediaDuration'] = int(nested_md) if nested_md == int(nested_md) else str(nested_md)
                                elif nested_clip.get('_type') in ('IMFile', 'ScreenIMFile'):
                                    nested_clip['mediaDuration'] = 1
                                # Scale effects (Bug 5)
                                for effect in nested_clip.get('effects', []):
                                    if 'start' in effect:
                                        effect['start'] = round(Fraction(str(effect['start'])) * group_scalar)
                                    if 'duration' in effect:
                                        effect['duration'] = round(Fraction(str(effect['duration'])) * group_scalar)
                                # Bug 6: scale keyframes and tracks on nested clips
                                _scale_keyframes_and_tracks(nested_clip, group_scalar)
                                if nested_clip.get('_type') == 'UnifiedMedia':
                                    for sub_key in ('video', 'audio'):
                                        sub = nested_clip.get(sub_key)
                                        if sub is not None:
                                            _scale_keyframes_and_tracks(sub, group_scalar)
                                # Propagate to UnifiedMedia sub-clips (Bug 6)
                                from camtasia.timeline.track import _propagate_start_to_unified
                                _propagate_start_to_unified(nested_clip)
                                # Handle StitchedMedia inner segments (Bug 7)
                                if nested_clip.get('_type') == 'StitchedMedia':
                                    for inner_seg in nested_clip.get('medias', []):
                                        seg_scalar = _parse_scalar(inner_seg.get('scalar', 1))
                                        seg_composed = seg_scalar * group_scalar
                                        inner_seg['scalar'] = 1 if seg_composed == 1 else str(seg_composed)
                                        seg_dur = Fraction(str(inner_seg.get('duration', 0)))
                                        inner_seg['duration'] = round(seg_dur * group_scalar)
                                        # Scale effects on inner segments (Bug 4)
                                        for effect in inner_seg.get('effects', []):
                                            if 'start' in effect:
                                                effect['start'] = round(Fraction(str(effect['start'])) * group_scalar)
                                            if 'duration' in effect:
                                                effect['duration'] = round(Fraction(str(effect['duration'])) * group_scalar)
                                        # Bug 7: scale keyframes on inner segments
                                        _scale_keyframes_and_tracks(inner_seg, group_scalar)
                                        # Propagate to UnifiedMedia sub-clips (Bug 5)
                                        if inner_seg.get('_type') == 'UnifiedMedia':
                                            for sub_key in ('video', 'audio'):
                                                sub = inner_seg.get(sub_key)
                                                if sub is not None:
                                                    sub['scalar'] = inner_seg['scalar']
                                                    sub['duration'] = inner_seg['duration']
                                                    _scale_keyframes_and_tracks(sub, group_scalar)
                                                    for effect in sub.get('effects', []):
                                                        if 'start' in effect:
                                                            effect['start'] = round(Fraction(str(effect['start'])) * group_scalar)
                                                        if 'duration' in effect:
                                                            effect['duration'] = round(Fraction(str(effect['duration'])) * group_scalar)
                                    # Re-layout starts
                                    cursor = 0
                                    for inner_seg in nested_clip.get('medias', []):
                                        inner_seg['start'] = cursor
                                        cursor += round(Fraction(str(inner_seg.get('duration', 0))))
                                        # Bug 8: propagate start to UnifiedMedia sub-clips
                                        if inner_seg.get('_type') == 'UnifiedMedia':
                                            for sub_key in ('video', 'audio'):
                                                sub = inner_seg.get(sub_key)
                                                if sub is not None:
                                                    sub['start'] = inner_seg['start']
                        # Recalculate nested Group's own mediaDuration after rounding
                        nested_grp_scalar = _parse_scalar(cloned_data.get('scalar', 1))
                        if nested_grp_scalar != 0:
                            nested_md = Fraction(cloned_data['duration']) / nested_grp_scalar
                            cloned_data['mediaDuration'] = int(nested_md) if nested_md == int(nested_md) else str(nested_md)
                cloned_start = Fraction(str(cloned_data.get('start', 0)))
                new_start = cloned_start + group_start
                cloned_data['start'] = round(new_start)
                from camtasia.timeline.track import _propagate_start_to_unified
                _propagate_start_to_unified(cloned_data)
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
                if media.get('_type') == 'ScreenVMFile':
                    return True
                if media.get('_type') == 'UnifiedMedia':
                    video = media.get('video', {})
                    if video.get('_type') == 'ScreenVMFile':
                        return True
                if media.get('_type') == 'StitchedMedia':
                    for seg in media.get('medias', []):
                        if seg.get('_type') == 'ScreenVMFile':
                            return True
                        if seg.get('_type') == 'UnifiedMedia' and seg.get('video', {}).get('_type') == 'ScreenVMFile':
                                return True
        return False

    @property
    def internal_media_src(self) -> int | None:
        """Return the source ID of the internal screen recording media, or None."""
        for track in self._data.get('tracks', []):
            for media in track.get('medias', []):
                if media.get('_type') == 'ScreenVMFile':
                    src = media.get('src')
                    return int(src) if src is not None else None
                if media.get('_type') == 'UnifiedMedia':
                    video = media.get('video', {})
                    if video.get('_type') == 'ScreenVMFile':
                        src = video.get('src')
                        return int(src) if src is not None else None
                if media.get('_type') == 'StitchedMedia':
                    for seg in media.get('medias', []):
                        if seg.get('_type') == 'ScreenVMFile':
                            src = seg.get('src')
                            return int(src) if src is not None else None
                        if seg.get('_type') == 'UnifiedMedia':
                            video = seg.get('video', {})
                            if video.get('_type') == 'ScreenVMFile':
                                src = video.get('src')
                                return int(src) if src is not None else None
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
        for clip in self.all_internal_clips:
            if clip.clip_type == 'UnifiedMedia':
                if clip.has_audio:  # type: ignore[attr-defined]
                    return True
            elif clip.is_audio:
                return True
        return False

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
        tracks_snapshot = list(self.tracks)
        if len(tracks_snapshot) <= 1:
            return tracks_snapshot[0]
        target_track: GroupTrack = tracks_snapshot[0]
        # Collect existing IDs (including nested) to detect collisions
        from camtasia.timeline.timeline import _remap_clip_ids_with_map
        existing_ids: set[int] = set()
        for m in target_track._data.get('medias', []):
            existing_ids.update(_collect_all_ids(m))
        max_id = max(existing_ids) if existing_ids else 0
        id_counter = [max_id + 1]
        for source_track in tracks_snapshot[1:]:
            for media_dict in source_track._data.get('medias', []):
                clip_ids = _collect_all_ids(media_dict)
                if clip_ids & existing_ids:
                    id_map: dict[int, int] = {}
                    _remap_clip_ids_with_map(media_dict, id_counter, id_map)
                else:
                    max_nested = max(clip_ids) if clip_ids else 0
                    if max_nested >= id_counter[0]:
                        id_counter[0] = max_nested + 1
                existing_ids.update(_collect_all_ids(media_dict))
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
        """Replace the internal track's media with per-segment ScreenVMFile clips.

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
        if not segments:
            raise ValueError('segments list must not be empty')
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
            track_number = video.get('trackNumber', 0)
        else:
            template_medias = template_media.get('medias') or [{}]
            src = template_medias[0].get('src', template_media.get('src', 0)) if template_medias else template_media.get('src', 0)
            ident = template_media.get('attributes', {}).get('ident', '')
            video_params = {}
            video_effects = []
            track_number = template_media.get('trackNumber', 0)

        # Build clips for each segment.
        # Following v2 Track 1 pattern: use bare ScreenVMFile clips with
        # scalar and clipSpeedAttribute for speed-changed segments.
        new_medias = []
        cursor_ticks = Fraction(0)

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
            all_ids: set[int] = set()
            for track in self._data.get('tracks', []):
                for m in track.get('medias', []):
                    all_ids.update(_collect_all_ids(m))
            next_id = (max(all_ids) if all_ids else 0) + 1
        cid = next_id

        for src_start, src_end, tl_dur in segments:
            if src_end <= src_start:
                raise ValueError(f'segment src_end ({src_end}) must be > src_start ({src_start})')
            src_dur = src_end - src_start
            scalar = (Fraction(tl_dur) / Fraction(src_dur)).limit_denominator(100000)

            start_ticks = int(cursor_ticks)
            dur_ticks = int(Fraction(tl_dur) * EDIT_RATE)
            ms_ticks = int(Fraction(src_start) * EDIT_RATE)
            media_dur_ticks = int(Fraction(src_dur) * EDIT_RATE)

            clip = {
                'id': cid,
                '_type': 'ScreenVMFile',
                'src': src,
                'trackNumber': track_number,
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
                        'value': scalar != 1,
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
                        f'Source aspect ratio ({source_w}x{source_h}) differs from canvas '
                        f'({canvas_width}x{canvas_height}): scale0={sv:.4f}, scale1={sv2:.4f}. '
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
            cursor_ticks += Fraction(tl_dur) * EDIT_RATE
            cid += 1

        # Replace the internal track's medias
        media_track['medias'] = new_medias

        # Remove transitions key — internal Group tracks should not have it
        # per the format reference §8
        media_track.pop('transitions', None)

        # Update Group duration and mediaDuration to match total timeline
        total_tl = int(cursor_ticks)
        self._data['duration'] = total_tl
        self._data['mediaDuration'] = total_tl
        self._data['mediaStart'] = 0
        self._data['scalar'] = 1

        # Keep VMFile on other tracks but extend to cover full source
        for track in self._data.get('tracks', []):
            if track is media_track:
                continue
            first_seg_src_start = segments[0][0] if segments else 0
            last_seg_src_end = segments[-1][1] if segments else 0
            first_seg_src_start_ticks = int(Fraction(first_seg_src_start) * EDIT_RATE)
            total_src_span = int(Fraction(last_seg_src_end - first_seg_src_start) * EDIT_RATE)
            for m in track.get('medias', []):
                if m.get('_type') in ('VMFile', 'ScreenVMFile', 'AMFile'):
                    m['start'] = 0
                    m['duration'] = total_tl
                    m['mediaDuration'] = total_src_span
                    m['mediaStart'] = first_seg_src_start_ticks
                    ratio = Fraction(total_tl) / Fraction(total_src_span) if total_src_span != 0 else Fraction(1)
                    m['scalar'] = int(ratio) if ratio == int(ratio) else str(ratio)
                elif m.get('_type') == 'UnifiedMedia':
                    m['start'] = 0
                    m['duration'] = total_tl
                    m['mediaDuration'] = total_src_span
                    m['mediaStart'] = first_seg_src_start_ticks
                    ratio = Fraction(total_tl) / Fraction(total_src_span) if total_src_span != 0 else Fraction(1)
                    m['scalar'] = int(ratio) if ratio == int(ratio) else str(ratio)
                    for sub_key in ('video', 'audio'):
                        sub = m.get(sub_key)
                        if sub is not None:
                            sub['duration'] = m['duration']
                            sub['mediaDuration'] = m['mediaDuration']
                            sub['mediaStart'] = m['mediaStart']
                            sub['scalar'] = m['scalar']

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
                clip_start = m.get('start', 0)
                clip_end = clip_start + m.get('duration', 0)
                if clip_end > group_dur:
                    m['duration'] = max(0, group_dur - clip_start)
                    if m['duration'] == 0:
                        if m.get('_type') in ('IMFile', 'ScreenIMFile'):
                            m['mediaDuration'] = 1
                        else:
                            m['mediaDuration'] = 0
                        from camtasia.timeline.track import _propagate_start_to_unified as _psu0
                        _psu0(m)
                        continue
                    if m.get('_type') in ('IMFile', 'ScreenIMFile'):
                        m['mediaDuration'] = 1
                    else:
                        scalar = _parse_scalar(m.get('scalar', 1))
                        if scalar != 0:
                            md = Fraction(m['duration']) / scalar
                            m['mediaDuration'] = int(md) if md == int(md) else str(md)
                    if m.get('_type') == 'StitchedMedia':
                        new_dur = round(Fraction(str(m.get('duration', 0))))
                        segments_to_keep: list[dict[str, Any]] = []
                        for seg in m.get('medias', []):
                            seg_start = round(Fraction(str(seg.get('start', 0))))
                            seg_dur = round(Fraction(str(seg.get('duration', 0))))
                            if seg_start >= new_dur:
                                continue
                            seg_end = seg_start + seg_dur
                            if seg_end > new_dur:
                                seg['duration'] = new_dur - seg_start
                                # Recalculate mediaDuration for speed-changed segments
                                seg_scalar = _parse_scalar(seg.get('scalar', 1))
                                if seg_scalar != 0 and seg.get('_type') not in ('IMFile', 'ScreenIMFile'):
                                    new_md = Fraction(seg['duration']) / seg_scalar
                                    seg['mediaDuration'] = int(new_md) if new_md == int(new_md) else str(new_md)
                            segments_to_keep.append(seg)
                        m['medias'] = segments_to_keep
                        for seg in m.get('medias', []):
                            if seg.get('_type') == 'UnifiedMedia':
                                for sub_key in ('video', 'audio'):
                                    sub = seg.get(sub_key)
                                    if sub is not None:
                                        sub['duration'] = seg['duration']
                                        if 'mediaDuration' in seg:
                                            sub['mediaDuration'] = seg['mediaDuration']
                                        sub['scalar'] = seg.get('scalar', 1)
                                        sub['mediaStart'] = seg.get('mediaStart', 0)
                                        sub['start'] = seg.get('start', 0)
                    from camtasia.timeline.track import _propagate_start_to_unified as _psu
                    _psu(m)
        return self
