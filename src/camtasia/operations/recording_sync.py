"""Synchronize screen recording speed to voiceover timing."""

from __future__ import annotations

from fractions import Fraction
from typing import TYPE_CHECKING, Any

from camtasia.timing import ticks_to_seconds

if TYPE_CHECKING:
    from camtasia.project import Project


def _find_clip_by_id(data: dict[str, Any], clip_id: int) -> dict[str, Any] | None:
    """Walk timeline to find a clip dict by id."""
    for track in data['timeline']['sceneTrack']['scenes'][0]['csml']['tracks']:
        for m in track.get('medias', []):
            if m.get('id') == clip_id:
                result: dict[str, Any] = m
                return result
            for t in m.get('tracks', []):
                for inner in t.get('medias', []):
                    if inner.get('id') == clip_id:
                        result = inner
                        return result
    return None


class ScreenRecordingSync:
    """Synchronize screen recording playback speed to match voiceover duration.

    Basic mode sets a single speed scalar. Advanced mode with markers
    creates per-segment speed adjustments via ``set_internal_segment_speeds``.

    Args:
        project: The Camtasia project to operate on.
    """

    def __init__(self, project: Project) -> None:
        self._project = project
        self._data = project._data

    def match_duration(
        self,
        screen_clip_id: int,
        voiceover_clip_id: int,
    ) -> Fraction:
        """Set screen recording speed so its duration matches the voiceover.

        Adjusts the screen clip's ``scalar`` and ``duration`` so that
        playback duration equals the voiceover clip's duration.

        Args:
            screen_clip_id: ID of the screen recording clip (or Group).
            voiceover_clip_id: ID of the voiceover/audio clip.

        Returns:
            The new scalar applied to the screen clip.

        Raises:
            KeyError: If either clip ID is not found.
            ValueError: If voiceover has zero duration.
        """
        screen = _find_clip_by_id(self._data, screen_clip_id)
        voice = _find_clip_by_id(self._data, voiceover_clip_id)
        if screen is None:
            raise KeyError(f'Screen clip {screen_clip_id} not found')
        if voice is None:
            raise KeyError(f'Voiceover clip {voiceover_clip_id} not found')

        voice_dur = int(Fraction(str(voice['duration'])))
        if voice_dur <= 0:
            raise ValueError('Voiceover clip has zero duration')

        # mediaDuration = source media length (what we're stretching)
        screen_media_dur = int(Fraction(str(screen.get('mediaDuration', screen['duration']))))
        if screen_media_dur <= 0:
            screen_media_dur = int(Fraction(str(screen['duration'])))

        # scalar = timeline_duration / media_duration
        new_scalar = Fraction(voice_dur, screen_media_dur)

        screen['duration'] = voice_dur
        screen['scalar'] = str(new_scalar) if new_scalar != 1 else 1
        screen['mediaDuration'] = int(Fraction(screen['duration']) / new_scalar)
        screen['metadata'] = screen.get('metadata', {})
        screen['metadata']['clipSpeedAttribute'] = {
            'type': 'bool',
            'value': new_scalar != 1,
        }

        # Propagate to UnifiedMedia children
        for key in ('video', 'audio'):
            child = screen.get(key)
            if isinstance(child, dict):
                child['duration'] = voice_dur
                child['scalar'] = screen['scalar']
                child['mediaDuration'] = screen['mediaDuration']
                child['mediaStart'] = screen.get('mediaStart', 0)
                child['metadata'] = child.get('metadata', {})
                child['metadata']['clipSpeedAttribute'] = {
                    'type': 'bool',
                    'value': new_scalar != 1,
                }

        return new_scalar

    def match_duration_with_markers(
        self,
        screen_clip_id: int,
        voiceover_clip_id: int,
        markers: list[tuple[int, int]],
    ) -> list[tuple[float, float, float]]:
        """Create per-segment speed adjustments using marker pairs.

        Each marker pair maps a screen recording position to a voiceover
        position. Segments between consecutive pairs get independent speeds.

        Args:
            screen_clip_id: ID of the screen recording Group clip.
            voiceover_clip_id: ID of the voiceover clip.
            markers: List of ``(screen_ticks, voiceover_ticks)`` pairs,
                sorted by screen position.

        Returns:
            List of ``(source_start_s, source_end_s, timeline_dur_s)``
            segment tuples that were applied.

        Raises:
            KeyError: If either clip ID is not found.
            ValueError: If fewer than 2 markers provided.
        """
        if len(markers) < 2:
            raise ValueError('Need at least 2 markers for segment sync')

        screen = _find_clip_by_id(self._data, screen_clip_id)
        voice = _find_clip_by_id(self._data, voiceover_clip_id)
        if screen is None:
            raise KeyError(f'Screen clip {screen_clip_id} not found')
        if voice is None:
            raise KeyError(f'Voiceover clip {voiceover_clip_id} not found')

        markers = sorted(markers, key=lambda m: m[0])

        segments: list[tuple[float, float, float]] = []
        for i in range(len(markers) - 1):
            src_start_ticks, vo_start_ticks = markers[i]
            src_end_ticks, vo_end_ticks = markers[i + 1]
            segments.append((
                ticks_to_seconds(src_start_ticks),
                ticks_to_seconds(src_end_ticks),
                ticks_to_seconds(vo_end_ticks - vo_start_ticks),
            ))

        # Apply via Group.set_internal_segment_speeds
        from camtasia.timeline.clips.group import Group
        for track in self._project.timeline.tracks:
            for clip in track.clips:
                if clip.id == screen_clip_id and isinstance(clip, Group):
                    clip.set_internal_segment_speeds(segments)
                    return segments

        raise KeyError(f'Screen clip {screen_clip_id} is not a Group on the timeline')
