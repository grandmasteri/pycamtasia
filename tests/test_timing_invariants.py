"""Tests for the CRITICAL timing invariant: duration = mediaDuration * scalar.

Every mutation method on BaseClip must preserve this relationship.
EDIT_RATE = 705,600,000 ticks/second. scalar = 1/speed.
"""
from __future__ import annotations

from fractions import Fraction

import pytest

from camtasia.timeline.clips import clip_from_dict
from camtasia.timing import parse_scalar, seconds_to_ticks

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _check_timing_invariant(clip_data: dict) -> None:
    scalar = parse_scalar(clip_data.get('scalar', 1))
    if scalar == 0:
        return
    if clip_data.get('_type') in ('IMFile', 'ScreenIMFile'):
        assert clip_data.get('mediaDuration') == 1
        return
    duration = Fraction(str(clip_data.get('duration', 0)))
    media_duration = Fraction(str(clip_data.get('mediaDuration', 0)))
    expected_md = duration / scalar
    assert media_duration == expected_md, (
        f'Invariant broken: {duration}/{scalar} = {expected_md}, got {media_duration}'
    )


# ---------------------------------------------------------------------------
# BaseClip mutation methods
# ---------------------------------------------------------------------------

class TestDurationSetter:
    """Setting duration must recalculate mediaDuration = duration / scalar."""

    def test_at_normal_speed(self, project):
        track = project.timeline.tracks[0]
        clip = track.add_video(0, 0.0, 5.0)
        clip.duration = seconds_to_ticks(10.0)
        _check_timing_invariant(clip._data)

    def test_at_double_speed(self, project):
        track = project.timeline.tracks[0]
        clip = track.add_video(0, 0.0, 5.0)
        clip.set_speed(2.0)
        clip.duration = seconds_to_ticks(8.0)
        _check_timing_invariant(clip._data)

    def test_at_half_speed(self, project):
        track = project.timeline.tracks[0]
        clip = track.add_video(0, 0.0, 5.0)
        clip.set_speed(0.5)
        clip.duration = seconds_to_ticks(3.0)
        _check_timing_invariant(clip._data)


class TestScalarSetter:
    """Setting scalar must recalculate mediaDuration = duration / scalar."""

    def test_set_scalar_half(self, project):
        track = project.timeline.tracks[0]
        clip = track.add_video(0, 0.0, 5.0)
        clip.scalar = Fraction(1, 2)
        _check_timing_invariant(clip._data)

    def test_set_scalar_third(self, project):
        track = project.timeline.tracks[0]
        clip = track.add_video(0, 0.0, 5.0)
        clip.scalar = Fraction(1, 3)
        _check_timing_invariant(clip._data)

    def test_set_scalar_back_to_one(self, project):
        track = project.timeline.tracks[0]
        clip = track.add_video(0, 0.0, 5.0)
        clip.scalar = Fraction(1, 2)
        clip.scalar = Fraction(1)
        _check_timing_invariant(clip._data)


class TestMediaDurationSetter:
    """Setting mediaDuration directly (no auto-recalc expected, just verify stored)."""

    def test_set_media_duration(self, project):
        track = project.timeline.tracks[0]
        clip = track.add_video(0, 0.0, 5.0)
        new_md = Fraction(seconds_to_ticks(5.0))
        clip.media_duration = new_md
        assert Fraction(str(clip._data['mediaDuration'])) == new_md


class TestSetSpeed:
    """set_speed() must maintain duration = mediaDuration * scalar."""

    def test_double_speed(self, project):
        track = project.timeline.tracks[0]
        clip = track.add_video(0, 0.0, 5.0)
        clip.set_speed(2.0)
        _check_timing_invariant(clip._data)

    def test_half_speed(self, project):
        track = project.timeline.tracks[0]
        clip = track.add_video(0, 0.0, 5.0)
        clip.set_speed(0.5)
        _check_timing_invariant(clip._data)

    def test_fractional_speed(self, project):
        track = project.timeline.tracks[0]
        clip = track.add_video(0, 0.0, 5.0)
        clip.set_speed(1.5)
        _check_timing_invariant(clip._data)

    def test_speed_then_speed(self, project):
        track = project.timeline.tracks[0]
        clip = track.add_video(0, 0.0, 5.0)
        clip.set_speed(2.0)
        clip.set_speed(0.75)
        _check_timing_invariant(clip._data)


class TestSetTimeRange:
    """set_time_range() must maintain the invariant."""

    def test_basic(self, project):
        track = project.timeline.tracks[0]
        clip = track.add_video(0, 0.0, 5.0)
        clip.set_time_range(1.0, 3.0)
        _check_timing_invariant(clip._data)

    def test_after_speed_change(self, project):
        track = project.timeline.tracks[0]
        clip = track.add_video(0, 0.0, 5.0)
        clip.set_speed(2.0)
        clip.set_time_range(2.0, 4.0)
        _check_timing_invariant(clip._data)


class TestSetDurationSeconds:
    """set_duration_seconds() must maintain the invariant."""

    def test_basic(self, project):
        track = project.timeline.tracks[0]
        clip = track.add_video(0, 0.0, 5.0)
        clip.set_duration_seconds(10.0)
        _check_timing_invariant(clip._data)

    def test_after_speed_change(self, project):
        track = project.timeline.tracks[0]
        clip = track.add_video(0, 0.0, 5.0)
        clip.set_speed(3.0)
        clip.set_duration_seconds(7.0)
        _check_timing_invariant(clip._data)


class TestSetStartSeconds:
    """set_start_seconds() must NOT break the invariant (start is independent)."""

    def test_start_change_preserves_invariant(self, project):
        track = project.timeline.tracks[0]
        clip = track.add_video(0, 0.0, 5.0)
        _check_timing_invariant(clip._data)
        clip.set_start_seconds(10.0)
        _check_timing_invariant(clip._data)

    def test_start_change_after_speed(self, project):
        track = project.timeline.tracks[0]
        clip = track.add_video(0, 0.0, 5.0)
        clip.set_speed(2.0)
        clip.set_start_seconds(3.0)
        _check_timing_invariant(clip._data)


# ---------------------------------------------------------------------------
# IMFile / ScreenIMFile: mediaDuration must ALWAYS be 1
# ---------------------------------------------------------------------------

class TestIMFileInvariant:
    """Image clips always have mediaDuration == 1 regardless of mutations."""

    def test_imfile_after_duration_set(self, project):
        track = project.timeline.tracks[0]
        clip = track.add_image(0, 0.0, 5.0)
        clip.duration = seconds_to_ticks(10.0)
        assert clip._data['mediaDuration'] == 1

    def test_imfile_after_set_speed(self, project):
        track = project.timeline.tracks[0]
        clip = track.add_image(0, 0.0, 5.0)
        clip.set_speed(2.0)
        assert clip._data['mediaDuration'] == 1

    def test_imfile_after_scalar_set(self, project):
        track = project.timeline.tracks[0]
        clip = track.add_image(0, 0.0, 5.0)
        clip.scalar = Fraction(1, 2)
        assert clip._data['mediaDuration'] == 1

    def test_imfile_after_set_duration_seconds(self, project):
        track = project.timeline.tracks[0]
        clip = track.add_image(0, 0.0, 5.0)
        clip.set_duration_seconds(8.0)
        assert clip._data['mediaDuration'] == 1

    def test_imfile_after_set_time_range(self, project):
        track = project.timeline.tracks[0]
        clip = track.add_image(0, 0.0, 5.0)
        clip.set_time_range(1.0, 6.0)
        assert clip._data['mediaDuration'] == 1

    def test_screen_imfile_after_set_speed(self, project):
        track = project.timeline.tracks[0]
        clip = track.add_clip('ScreenIMFile', 0, 0, seconds_to_ticks(5.0),
                              media_duration=1, trimStartSum=0)
        clip.set_speed(2.0)
        assert clip._data['mediaDuration'] == 1


# ---------------------------------------------------------------------------
# UnifiedMedia: invariant on wrapper AND video/audio sub-clips
# ---------------------------------------------------------------------------

class TestUnifiedMediaInvariant:
    """UnifiedMedia must maintain invariant on wrapper and both sub-clips."""

    def _add_unified(self, project, duration_seconds=5.0):
        track = project.timeline.tracks[0]
        group = track.add_screen_recording(0, 0.0, duration_seconds)
        # The UnifiedMedia is inside the group's internal tracks
        for inner_track in group._data.get('tracks', []):
            for media in inner_track.get('medias', []):
                if media.get('_type') == 'UnifiedMedia':
                    return clip_from_dict(media)
        pytest.skip('No UnifiedMedia found in screen recording group')

    def test_set_speed_wrapper(self, project):
        clip = self._add_unified(project)
        clip.set_speed(2.0)
        _check_timing_invariant(clip._data)

    def test_set_speed_video_sub(self, project):
        clip = self._add_unified(project)
        clip.set_speed(2.0)
        _check_timing_invariant(clip._data['video'])

    def test_set_speed_audio_sub(self, project):
        clip = self._add_unified(project)
        clip.set_speed(2.0)
        _check_timing_invariant(clip._data['audio'])

    def test_duration_setter_wrapper(self, project):
        clip = self._add_unified(project)
        clip.duration = seconds_to_ticks(10.0)
        _check_timing_invariant(clip._data)

    def test_duration_setter_subs(self, project):
        clip = self._add_unified(project)
        clip.duration = seconds_to_ticks(10.0)
        _check_timing_invariant(clip._data['video'])
        _check_timing_invariant(clip._data['audio'])

    def test_scalar_setter_subs(self, project):
        clip = self._add_unified(project)
        clip.scalar = Fraction(1, 3)
        _check_timing_invariant(clip._data)
        _check_timing_invariant(clip._data['video'])
        _check_timing_invariant(clip._data['audio'])

    def test_set_time_range_subs(self, project):
        clip = self._add_unified(project)
        clip.set_time_range(1.0, 3.0)
        _check_timing_invariant(clip._data)
        _check_timing_invariant(clip._data['video'])
        _check_timing_invariant(clip._data['audio'])

    def test_set_duration_seconds_subs(self, project):
        clip = self._add_unified(project)
        clip.set_duration_seconds(8.0)
        _check_timing_invariant(clip._data)
        _check_timing_invariant(clip._data['video'])
        _check_timing_invariant(clip._data['audio'])


# ---------------------------------------------------------------------------
# StitchedMedia: children must have same scalar as wrapper after set_speed
# ---------------------------------------------------------------------------

class TestStitchedMediaInvariant:
    """StitchedMedia children must share the wrapper's scalar after set_speed."""

    def _add_stitched(self, project, duration_seconds=5.0):
        track = project.timeline.tracks[0]
        dur = seconds_to_ticks(duration_seconds)
        child = {
            'id': 900,
            '_type': 'VMFile',
            'src': 0,
            'trackNumber': 0,
            'attributes': {'ident': ''},
            'start': 0,
            'duration': dur,
            'mediaStart': 0,
            'mediaDuration': dur,
            'scalar': 1,
            'metadata': {},
            'animationTracks': {},
            'parameters': {},
            'effects': [],
        }
        clip = track.add_clip(
            'StitchedMedia', None, 0, dur,
            medias=[child],
            attributes={'ident': ''},
        )
        return clip

    def test_set_speed_wrapper(self, project):
        clip = self._add_stitched(project)
        clip.set_speed(2.0)
        _check_timing_invariant(clip._data)

    def test_set_speed_children_scalar(self, project):
        clip = self._add_stitched(project)
        clip.set_speed(2.0)
        wrapper_scalar = clip._data.get('scalar', 1)
        for child in clip._data.get('medias', []):
            assert child['scalar'] == wrapper_scalar, (
                f'Child scalar {child["scalar"]} != wrapper {wrapper_scalar}'
            )

    def test_set_speed_children_invariant(self, project):
        clip = self._add_stitched(project)
        clip.set_speed(2.0)
        for child in clip._data.get('medias', []):
            _check_timing_invariant(child)


# ---------------------------------------------------------------------------
# Group: wrapper timing must be consistent after set_speed
# ---------------------------------------------------------------------------

class TestGroupInvariant:
    """Group wrapper timing must be consistent after set_speed."""

    def test_set_speed(self, project):
        track = project.timeline.tracks[0]
        group = track.add_group(0.0, 5.0)
        group.set_speed(2.0)
        _check_timing_invariant(group._data)

    def test_set_speed_then_duration(self, project):
        track = project.timeline.tracks[0]
        group = track.add_group(0.0, 5.0)
        group.set_speed(2.0)
        group.duration = seconds_to_ticks(8.0)
        _check_timing_invariant(group._data)

    def test_scalar_setter(self, project):
        track = project.timeline.tracks[0]
        group = track.add_group(0.0, 5.0)
        group.scalar = Fraction(1, 4)
        _check_timing_invariant(group._data)
