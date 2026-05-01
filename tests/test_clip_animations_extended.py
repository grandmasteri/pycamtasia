"""Tests for BaseClip animation axis-extensions and audio/trim helpers."""
from __future__ import annotations

from fractions import Fraction
from typing import Any

import pytest

from camtasia.timeline.clips import EDIT_RATE, BaseClip, clip_from_dict
from camtasia.timing import seconds_to_ticks


def _clip(duration_s: float = 10.0, _type: str = 'VMFile', **kw: Any) -> BaseClip:
    """Build a minimal clip dict and return a BaseClip."""
    d: dict[str, Any] = {
        'id': 1,
        '_type': _type,
        'src': 1,
        'start': 0,
        'duration': seconds_to_ticks(duration_s),
        'mediaStart': 0,
        'mediaDuration': seconds_to_ticks(duration_s),
        'scalar': 1,
        'parameters': {},
        'effects': [],
        'animationTracks': {},
    }
    d.update(kw)
    return clip_from_dict(d)


# ------------------------------------------------------------------
# set_skew_keyframes
# ------------------------------------------------------------------

class TestSetSkewKeyframes:
    def test_writes_geometry_skew_param(self) -> None:
        c = _clip()
        c.set_skew_keyframes([(0.0, 0.0), (5.0, 0.5)])
        param = c.parameters['geometrySkew']
        assert param['defaultValue'] == 0.5
        assert len(param['keyframes']) == 2

    def test_keyframe_timing(self) -> None:
        c = _clip()
        c.set_skew_keyframes([(1.0, 0.1), (3.0, 0.3)])
        kfs = c.parameters['geometrySkew']['keyframes']
        # Each keyframe is a point: endTime == time, duration == 0.
        # This matches Camtasia's own format (see techsmith_complex_asset.tscproj)
        # and is required — Camtasia rejects files where keyframes are spans.
        assert kfs[0]['time'] == seconds_to_ticks(1.0)
        assert kfs[0]['endTime'] == seconds_to_ticks(1.0)
        assert kfs[0]['duration'] == 0
        assert kfs[1]['time'] == seconds_to_ticks(3.0)
        assert kfs[1]['endTime'] == seconds_to_ticks(3.0)
        assert kfs[1]['duration'] == 0


# ------------------------------------------------------------------
# set_rotation_x_keyframes / set_rotation_y_keyframes
# ------------------------------------------------------------------

class TestRotationXYKeyframes:
    def test_rotation_x_writes_rotation0(self) -> None:
        c = _clip()
        c.set_rotation_x_keyframes([(0.0, 0.0), (2.0, 1.57)])
        assert 'rotation0' in c.parameters
        assert c.parameters['rotation0']['defaultValue'] == 1.57

    def test_rotation_y_writes_rotation1(self) -> None:
        c = _clip()
        c.set_rotation_y_keyframes([(0.0, 0.0), (2.0, 3.14)])
        assert 'rotation1' in c.parameters
        assert c.parameters['rotation1']['defaultValue'] == 3.14

    def test_creates_visual_tracks(self) -> None:
        c = _clip()
        c.set_rotation_x_keyframes([(0.0, 0.0), (2.0, 1.0)])
        assert len(c.visual_animations) > 0


# ------------------------------------------------------------------
# set_translation_z_keyframes
# ------------------------------------------------------------------

class TestTranslationZKeyframes:
    def test_writes_translation2(self) -> None:
        c = _clip()
        c.set_translation_z_keyframes([(0.0, 0.0), (5.0, 100.0)])
        assert c.parameters['translation2']['defaultValue'] == 100.0
        assert len(c.parameters['translation2']['keyframes']) == 2


# ------------------------------------------------------------------
# restore_animation
# ------------------------------------------------------------------

class TestRestoreAnimation:
    def test_clears_animations_and_resets_transforms(self) -> None:
        c = _clip()
        c.move_to(50, 50)
        c.scale_to(2.0)
        c.rotation = 1.5
        c.set_scale_keyframes([(0.0, 1.0), (5.0, 2.0)])
        c.restore_animation()
        assert c.translation == (0.0, 0.0)
        assert c.scale == (1.0, 1.0)
        assert c.rotation == 0.0
        assert not c.has_keyframes

    def test_returns_self(self) -> None:
        c = _clip()
        assert c.restore_animation() is c


# ------------------------------------------------------------------
# trim_head / trim_tail
# ------------------------------------------------------------------

class TestTrimHead:
    def test_advances_start_and_shrinks_duration(self) -> None:
        c = _clip(duration_s=10.0)
        orig_dur = c.duration
        c.trim_head(2.0)
        assert c.start == seconds_to_ticks(2.0)
        assert c.duration == orig_dur - seconds_to_ticks(2.0)

    def test_advances_media_start(self) -> None:
        c = _clip(duration_s=10.0)
        c.trim_head(3.0)
        assert float(Fraction(str(c.media_start))) == pytest.approx(seconds_to_ticks(3.0))

    def test_clamps_to_duration(self) -> None:
        c = _clip(duration_s=5.0)
        c.trim_head(999.0)
        assert c.duration == 0

    def test_returns_self(self) -> None:
        c = _clip()
        assert c.trim_head(1.0) is c


class TestTrimTail:
    def test_shrinks_duration(self) -> None:
        c = _clip(duration_s=10.0)
        orig_dur = c.duration
        c.trim_tail(3.0)
        assert c.duration == orig_dur - seconds_to_ticks(3.0)

    def test_start_unchanged(self) -> None:
        c = _clip(duration_s=10.0)
        c.trim_tail(2.0)
        assert c.start == 0

    def test_clamps_to_duration(self) -> None:
        c = _clip(duration_s=5.0)
        c.trim_tail(999.0)
        assert c.duration == 0

    def test_returns_self(self) -> None:
        c = _clip()
        assert c.trim_tail(1.0) is c


# ------------------------------------------------------------------
# silence_audio
# ------------------------------------------------------------------

class TestSilenceAudio:
    def test_creates_volume_keyframes(self) -> None:
        c = _clip()
        c.silence_audio(2.0, 5.0)
        vol = c.parameters['volume']
        assert isinstance(vol, dict)
        kfs = vol['keyframes']
        assert len(kfs) == 2
        assert kfs[0]['value'] == 0.0
        assert kfs[1]['value'] == 1.0

    def test_returns_self(self) -> None:
        c = _clip()
        assert c.silence_audio(1.0, 2.0) is c


# ------------------------------------------------------------------
# separate_video_and_audio
# ------------------------------------------------------------------

class TestSeparateVideoAndAudio:
    def test_vmfile_returns_amfile_dict(self) -> None:
        c = _clip(_type='VMFile')
        result = c.separate_video_and_audio()
        assert result is not None
        assert result['_type'] == 'AMFile'
        assert result['src'] == 1
        assert result['start'] == c.start
        assert result['duration'] == c.duration

    def test_unified_media_with_audio(self) -> None:
        audio_sub = {'_type': 'AMFile', 'id': 2, 'src': 1, 'start': 0,
                     'duration': EDIT_RATE * 10, 'mediaStart': 0,
                     'mediaDuration': EDIT_RATE * 10, 'scalar': 1}
        c = _clip(_type='UnifiedMedia', audio=audio_sub, video={'_type': 'VMFile'})
        result = c.separate_video_and_audio()
        assert result is not None
        assert result['_type'] == 'AMFile'

    def test_unified_media_no_audio(self) -> None:
        c = _clip(_type='UnifiedMedia', video={'_type': 'VMFile'})
        assert c.separate_video_and_audio() is None

    def test_audio_clip_returns_none(self) -> None:
        c = _clip(_type='AMFile')
        assert c.separate_video_and_audio() is None


# ------------------------------------------------------------------
# add_audio_fade_in / add_audio_fade_out
# ------------------------------------------------------------------

class TestAudioFadeIn:
    def test_creates_volume_keyframes_0_to_1(self) -> None:
        c = _clip()
        c.add_audio_fade_in(2.0)
        vol = c.parameters['volume']
        kfs = vol['keyframes']
        assert kfs[0]['value'] == 0.0
        assert kfs[1]['value'] == 1.0
        assert kfs[0]['time'] == 0

    def test_returns_self(self) -> None:
        c = _clip()
        assert c.add_audio_fade_in(1.0) is c


class TestAudioFadeOut:
    def test_creates_volume_keyframes_1_to_0(self) -> None:
        c = _clip(duration_s=10.0)
        c.add_audio_fade_out(3.0)
        vol = c.parameters['volume']
        kfs = vol['keyframes']
        assert kfs[0]['value'] == 1.0
        assert kfs[1]['value'] == 0.0
        assert kfs[1]['time'] == seconds_to_ticks(10.0)

    def test_returns_self(self) -> None:
        c = _clip()
        assert c.add_audio_fade_out(1.0) is c


# ------------------------------------------------------------------
# add_audio_point / remove_all_audio_points
# ------------------------------------------------------------------

class TestAddAudioPoint:
    def test_adds_volume_keyframe(self) -> None:
        c = _clip()
        c.add_audio_point(2.0, 0.5)
        vol = c.parameters['volume']
        assert isinstance(vol, dict)
        assert vol['keyframes'][0]['value'] == 0.5

    def test_returns_self(self) -> None:
        c = _clip()
        assert c.add_audio_point(1.0, 0.8) is c


class TestRemoveAllAudioPoints:
    def test_clears_volume_keyframes(self) -> None:
        c = _clip()
        c.add_audio_point(1.0, 0.5)
        c.add_audio_point(2.0, 0.8)
        c.remove_all_audio_points()
        vol = c.parameters.get('volume')
        if isinstance(vol, dict):
            assert 'keyframes' not in vol

    def test_returns_self(self) -> None:
        c = _clip()
        assert c.remove_all_audio_points() is c


# ------------------------------------------------------------------
# set_volume_keyframes
# ------------------------------------------------------------------

class TestSetVolumeKeyframes:
    def test_full_envelope(self) -> None:
        c = _clip()
        c.set_volume_keyframes([(0.0, 1.0), (3.0, 0.0), (6.0, 1.0)])
        vol = c.parameters['volume']
        assert len(vol['keyframes']) == 3
        assert vol['defaultValue'] == 1.0

    def test_no_visual_tracks_created(self) -> None:
        c = _clip()
        c.set_volume_keyframes([(0.0, 1.0), (5.0, 0.0)])
        assert len(c.visual_animations) == 0

    def test_returns_self(self) -> None:
        c = _clip()
        assert c.set_volume_keyframes([(0.0, 1.0)]) is c


# ------------------------------------------------------------------
# set_speed_by_duration
# ------------------------------------------------------------------

class TestSetSpeedByDuration:
    def test_doubles_speed_for_half_duration(self) -> None:
        c = _clip(duration_s=10.0)
        c.set_speed_by_duration(5.0)
        assert c.speed == pytest.approx(2.0, rel=0.01)

    def test_halves_speed_for_double_duration(self) -> None:
        c = _clip(duration_s=10.0)
        c.set_speed_by_duration(20.0)
        assert c.speed == pytest.approx(0.5, rel=0.01)

    def test_raises_on_zero(self) -> None:
        c = _clip()
        with pytest.raises(ValueError, match='must be > 0'):
            c.set_speed_by_duration(0.0)

    def test_raises_on_negative(self) -> None:
        c = _clip()
        with pytest.raises(ValueError, match='must be > 0'):
            c.set_speed_by_duration(-5.0)

    def test_returns_self(self) -> None:
        c = _clip(duration_s=10.0)
        assert c.set_speed_by_duration(5.0) is c
