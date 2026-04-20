"""Tests for Project.add_background_music()."""
from __future__ import annotations

from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / 'fixtures'
EMPTY_WAV = FIXTURES / 'empty.wav'


@pytest.mark.parametrize("path", [EMPTY_WAV, str(EMPTY_WAV)], ids=["Path", "str"])
def test_returns_base_clip(project, path):
    clip = project.add_background_music(path)
    assert clip.start == 0
    assert clip.volume == 0.3


def test_custom_volume(project):
    clip = project.add_background_music(EMPTY_WAV, volume=0.5)
    assert clip.volume == 0.5


def test_default_track_name(project):
    project.add_background_music(EMPTY_WAV)
    track = project.timeline.get_or_create_track('Background Music')
    clips = list(track.clips)
    assert len(clips) == 1
    assert clips[0].volume == 0.3


def test_custom_track_name(project):
    project.add_background_music(EMPTY_WAV, track_name='BGM')
    track = project.timeline.get_or_create_track('BGM')
    clips = list(track.clips)
    assert len(clips) == 1
    assert clips[0].start == 0


def test_empty_project_uses_fallback_duration(project):
    assert project.duration_seconds == 0
    clip = project.add_background_music(EMPTY_WAV)
    assert clip.duration_seconds == pytest.approx(60.0)


def test_no_fade_in(project):
    clip = project.add_background_music(EMPTY_WAV, fade_in_seconds=0)
    # Only fade-out should be present (default 3.0s)
    assert clip.volume == 0.3


def test_no_fade_out(project):
    clip = project.add_background_music(EMPTY_WAV, fade_out_seconds=0)
    # Only fade-in should be present (default 2.0s)
    assert clip.volume == 0.3


def test_no_fades(project):
    clip = project.add_background_music(EMPTY_WAV, fade_in_seconds=0, fade_out_seconds=0)
    assert 'opacity' not in clip._data.get('parameters', {})


def test_media_imported_to_bin(project):
    before = project.media_count
    project.add_background_music(EMPTY_WAV)
    assert project.media_count == before + 1


def test_custom_fade_values(project):
    clip = project.add_background_music(EMPTY_WAV, fade_in_seconds=1.0, fade_out_seconds=5.0)
    volume = clip._data.get('parameters', {}).get('volume')
    assert isinstance(volume, dict)
    assert len(volume['keyframes']) >= 2


def test_fade_in_only_has_sustain_keyframe(project):
    """Bug 3: when fade_in > 0 and fade_out == 0, a sustain keyframe must hold volume."""
    clip = project.add_background_music(EMPTY_WAV, fade_in_seconds=2.0, fade_out_seconds=0)
    volume_param = clip._data.get('parameters', {}).get('volume', {})
    keyframes = volume_param.get('keyframes', [])
    # Should have 3 keyframes: start at 0, ramp to volume, sustain to end
    assert len(keyframes) == 3
    # Last keyframe should hold the target volume until end of clip
    assert keyframes[-1]['value'] == 0.3
    assert keyframes[-1]['endTime'] > keyframes[1]['endTime']


def test_overlapping_fades_clamped(project):
    """Bug 1: fade_in + fade_out > total should not produce negative hold duration."""
    clip = project.add_background_music(
        EMPTY_WAV, fade_in_seconds=50.0, fade_out_seconds=50.0,
    )
    volume_param = clip._data.get('parameters', {}).get('volume', {})
    keyframes = volume_param.get('keyframes', [])
    # All keyframe durations must be non-negative
    for kf in keyframes:
        assert kf.get('duration', 0) >= 0, f"Negative duration in keyframe: {kf}"


def test_fade_out_applied_when_total_equals_fades(project):
    """Bug 6: fade-out should be applied when total_ticks == fade_in_ticks + fade_out_ticks."""
    # Use a short clip where total exactly equals fade_in + fade_out
    clip = project.add_background_music(
        EMPTY_WAV, fade_in_seconds=0.5, fade_out_seconds=0.5,
    )
    volume_param = clip._data.get('parameters', {}).get('volume', {})
    keyframes = volume_param.get('keyframes', [])
    # Should have fade-out keyframes (value going to 0.0 at end)
    last_kf = keyframes[-1]
    assert last_kf['value'] == 0.0, "Fade-out should produce a final keyframe with value 0.0"


def test_no_duplicate_keyframe_fade_out_only(project):
    """Bug 3: fade_in=0, fade_out>0 should not produce duplicate keyframes at t=0."""
    clip = project.add_background_music(
        EMPTY_WAV, fade_in_seconds=0, fade_out_seconds=3.0,
    )
    volume_param = clip._data.get('parameters', {}).get('volume', {})
    keyframes = volume_param.get('keyframes', [])
    # Collect all keyframes at time=0 with endTime=0
    zero_kfs = [kf for kf in keyframes if kf.get('endTime') == 0 and kf.get('time') == 0]
    assert len(zero_kfs) <= 1, f"Duplicate keyframes at t=0: {zero_kfs}"
    # Should have 3 keyframes: initial anchor, sustain, then fade-out
    assert len(keyframes) == 3
    assert keyframes[-1]['value'] == 0.0


def test_fade_out_only_has_initial_anchor_keyframe(project):
    """Bug 1: fade_in=0, fade_out>0 must have an initial anchor keyframe at target volume."""
    clip = project.add_background_music(
        EMPTY_WAV, fade_in_seconds=0, fade_out_seconds=3.0, volume=0.5,
    )
    volume_param = clip._data.get('parameters', {}).get('volume', {})
    keyframes = volume_param.get('keyframes', [])
    # First keyframe should be the anchor at volume (not 0.0)
    assert keyframes[0]['endTime'] == 0
    assert keyframes[0]['value'] == 0.5
    # Last keyframe should fade to 0.0
    assert keyframes[-1]['value'] == 0.0
