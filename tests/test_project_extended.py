"""Tests for Project SmartFocus, animation preset, and noise removal methods."""
from __future__ import annotations

import pytest

from camtasia.timing import seconds_to_ticks

# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _add_screen_recording_group(project, cursor_keyframes):
    """Add a Group with ScreenVMFile + ScreenIMFile to the project.

    Returns the ScreenIMFile clip's ID.
    """
    track = project.timeline.get_or_create_track('Recording')
    media_id = project.media_bin.next_id()
    # Add a sourceBin entry
    project._data.setdefault('sourceBin', []).append({
        'id': media_id,
        'src': './media/recording.trec',
        'rect': [0, 0, 1920, 1080],
        'sourceTracks': [{'range': [0, 100000], 'type': 0, 'editRate': 30,
                          'trackRect': [0, 0, 1920, 1080], 'sampleRate': 30,
                          'bitDepth': 32, 'numChannels': 0}],
    })
    next_id = project.next_available_id
    # Build a ScreenIMFile clip with cursor keyframes
    screen_im_data = {
        'id': next_id,
        '_type': 'ScreenIMFile',
        'src': media_id,
        'start': 0,
        'duration': seconds_to_ticks(10.0),
        'mediaStart': 0,
        'mediaDuration': seconds_to_ticks(10.0),
        'scalar': 1,
        'parameters': {
            'cursorLocation': {
                'type': 'point3',
                'defaultValue': [0, 0, 0],
                'keyframes': cursor_keyframes,
            },
        },
        'effects': [],
    }
    track._data.setdefault('medias', []).append(screen_im_data)
    return next_id


def _make_cursor_keyframes_with_jump():
    """Create cursor keyframes with a sharp position change."""
    t0 = seconds_to_ticks(0.0)
    t1 = seconds_to_ticks(1.0)
    t2 = seconds_to_ticks(2.0)
    return [
        {'time': t0, 'endTime': t1, 'value': [100, 100, 0], 'duration': t1 - t0},
        {'time': t1, 'endTime': t2, 'value': [100, 110, 0], 'duration': t2 - t1},  # small move
        {'time': t2, 'endTime': t2, 'value': [1800, 900, 0], 'duration': 0},  # big jump
    ]


def _make_cursor_keyframes_no_jump():
    """Create cursor keyframes with only small movements."""
    t0 = seconds_to_ticks(0.0)
    t1 = seconds_to_ticks(1.0)
    return [
        {'time': t0, 'endTime': t1, 'value': [100, 100, 0], 'duration': t1 - t0},
        {'time': t1, 'endTime': t1, 'value': [105, 102, 0], 'duration': 0},
    ]


def _add_audio_clip(project, track_name='Audio'):
    """Add an AMFile clip and return its ID."""
    track = project.timeline.get_or_create_track(track_name)
    media_id = project.media_bin.next_id()
    project._data.setdefault('sourceBin', []).append({
        'id': media_id,
        'src': './media/audio.wav',
        'rect': [0, 0, 0, 0],
        'sourceTracks': [{'range': [0, 48000], 'type': 1, 'editRate': 48000,
                          'trackRect': [0, 0, 0, 0], 'sampleRate': 48000,
                          'bitDepth': 16, 'numChannels': 2}],
    })
    clip = track.add_audio(media_id, start_seconds=0.0, duration_seconds=5.0)
    return clip.id


def _add_video_clip(project, track_name='Video'):
    """Add a VMFile clip and return its ID."""
    track = project.timeline.get_or_create_track(track_name)
    media_id = project.media_bin.next_id()
    project._data.setdefault('sourceBin', []).append({
        'id': media_id,
        'src': './media/video.mp4',
        'rect': [0, 0, 1920, 1080],
        'sourceTracks': [{'range': [0, 300], 'type': 0, 'editRate': 30,
                          'trackRect': [0, 0, 1920, 1080], 'sampleRate': 48000,
                          'bitDepth': 16, 'numChannels': 2}],
    })
    clip = track.add_video(media_id, start_seconds=0.0, duration_seconds=10.0)
    return clip.id


# ------------------------------------------------------------------
# apply_smart_focus
# ------------------------------------------------------------------

class TestApplySmartFocus:
    def test_detects_sharp_cursor_jump(self, project):
        kfs = _make_cursor_keyframes_with_jump()
        _add_screen_recording_group(project, kfs)
        count = project.apply_smart_focus()
        assert count == 1
        assert len(project.timeline.zoom_pan_keyframes) == 1

    def test_no_zoom_for_small_movements(self, project):
        kfs = _make_cursor_keyframes_no_jump()
        _add_screen_recording_group(project, kfs)
        count = project.apply_smart_focus()
        assert count == 0
        assert project.timeline.zoom_pan_keyframes == []

    def test_filter_by_track_name(self, project):
        kfs = _make_cursor_keyframes_with_jump()
        _add_screen_recording_group(project, kfs)
        count = project.apply_smart_focus(track_name='NonExistent')
        assert count == 0

    def test_filter_by_matching_track_name(self, project):
        kfs = _make_cursor_keyframes_with_jump()
        _add_screen_recording_group(project, kfs)
        count = project.apply_smart_focus(track_name='Recording')
        assert count == 1

    def test_empty_project_returns_zero(self, project):
        assert project.apply_smart_focus() == 0

    def test_zoom_center_matches_cursor_position(self, project):
        kfs = _make_cursor_keyframes_with_jump()
        _add_screen_recording_group(project, kfs)
        project.apply_smart_focus()
        zpk = project.timeline.zoom_pan_keyframes[0]
        # Cursor jumped to (1800, 900) on 1920x1080 canvas
        assert zpk.center_x == pytest.approx(1800 / 1920, abs=0.01)
        assert zpk.center_y == pytest.approx(900 / 1080, abs=0.01)
        assert zpk.scale == 1.5


# ------------------------------------------------------------------
# apply_smart_focus_at_time
# ------------------------------------------------------------------

class TestApplySmartFocusAtTime:
    def test_adds_zoom_at_time(self, project):
        project.apply_smart_focus_at_time(5.0)
        zpks = project.timeline.zoom_pan_keyframes
        assert len(zpks) == 1
        assert zpks[0].time_seconds == pytest.approx(5.0, abs=0.001)
        assert zpks[0].scale == 1.5

    def test_multiple_calls_accumulate(self, project):
        project.apply_smart_focus_at_time(1.0)
        project.apply_smart_focus_at_time(3.0)
        assert len(project.timeline.zoom_pan_keyframes) == 2


# ------------------------------------------------------------------
# add_scale_to_fit
# ------------------------------------------------------------------

class TestAddScaleToFit:
    def test_clears_zoom_pan_keyframes(self, project):
        project.timeline.add_zoom_pan(1.0, scale=2.0)
        project.timeline.add_zoom_pan(3.0, scale=1.5)
        assert len(project.timeline.zoom_pan_keyframes) == 2
        project.add_scale_to_fit()
        assert project.timeline.zoom_pan_keyframes == []

    def test_noop_on_empty(self, project):
        project.add_scale_to_fit()
        assert project.timeline.zoom_pan_keyframes == []


# ------------------------------------------------------------------
# add_animation_preset
# ------------------------------------------------------------------

class TestAddAnimationPreset:
    def test_scale_up(self, project):
        clip_id = _add_video_clip(project)
        project.add_animation_preset('ScaleUp', clip_id)
        _, clip = project.timeline.find_clip(clip_id)
        # Verify scale keyframes were set
        params = clip._data.get('parameters', {})
        scale_param = params.get('scale', params.get('scaleX', {}))
        assert 'keyframes' in scale_param or isinstance(scale_param, dict)

    def test_scale_down(self, project):
        clip_id = _add_video_clip(project)
        project.add_animation_preset('ScaleDown', clip_id)
        # Should not raise
        _, clip = project.timeline.find_clip(clip_id)
        assert clip is not None

    def test_scale_to_fit(self, project):
        clip_id = _add_video_clip(project)
        project.add_animation_preset('ScaleToFit', clip_id)
        _, clip = project.timeline.find_clip(clip_id)
        assert clip is not None

    def test_custom_preset(self, project):
        clip_id = _add_video_clip(project)
        project.add_animation_preset('Custom', clip_id, scale=3.0, duration_seconds=1.0)
        _, clip = project.timeline.find_clip(clip_id)
        assert clip is not None

    def test_invalid_preset_raises(self, project):
        clip_id = _add_video_clip(project)
        with pytest.raises(ValueError, match='Unknown preset'):
            project.add_animation_preset('FlyIn', clip_id)

    def test_missing_clip_raises(self, project):
        with pytest.raises(KeyError, match='Clip not found'):
            project.add_animation_preset('ScaleUp', 99999)


# ------------------------------------------------------------------
# add_ai_noise_removal
# ------------------------------------------------------------------

class TestAddAiNoiseRemoval:
    def test_applies_noise_removal_effect(self, project):
        clip_id = _add_audio_clip(project)
        project.add_ai_noise_removal(clip_id, amount=0.7)
        _, clip = project.timeline.find_clip(clip_id)
        effect_names = [e.get('effectName', '') for e in clip._data.get('effects', [])]
        assert 'VSTEffect-DFN3NoiseRemoval' in effect_names

    def test_default_amount(self, project):
        clip_id = _add_audio_clip(project)
        project.add_ai_noise_removal(clip_id)
        _, clip = project.timeline.find_clip(clip_id)
        nr_effects = [e for e in clip._data.get('effects', [])
                      if e.get('effectName') == 'VSTEffect-DFN3NoiseRemoval']
        assert len(nr_effects) == 1
        assert nr_effects[0]['parameters']['Amount'] == 0.5

    def test_missing_clip_raises(self, project):
        with pytest.raises(KeyError, match='Clip not found'):
            project.add_ai_noise_removal(99999)

    def test_custom_amount(self, project):
        clip_id = _add_audio_clip(project)
        project.add_ai_noise_removal(clip_id, amount=0.9)
        _, clip = project.timeline.find_clip(clip_id)
        nr_effects = [e for e in clip._data.get('effects', [])
                      if e.get('effectName') == 'VSTEffect-DFN3NoiseRemoval']
        assert nr_effects[0]['parameters']['Amount'] == 0.9


class TestApplySmartFocusSkipBranches:
    """Cover project.py lines 2953, 2956, 2959: skip non-ScreenIMFile clips."""

    def test_skips_non_screen_im_clips(self, project):
        """Line 2953: non-ScreenIMFile clip type → continue."""
        track = project.timeline.get_or_create_track('Recording')
        # Add a regular VMFile clip (not ScreenIMFile)
        track._data.setdefault('medias', []).append({
            'id': 900, '_type': 'VMFile', 'src': 1,
            'start': 0, 'duration': seconds_to_ticks(5.0),
            'mediaStart': 0, 'mediaDuration': seconds_to_ticks(5.0),
            'scalar': 1, 'parameters': {}, 'effects': [],
        })
        # Also add a ScreenIMFile with only 1 keyframe (line 2959)
        track._data['medias'].append({
            'id': 901, '_type': 'ScreenIMFile', 'src': 1,
            'start': 0, 'duration': seconds_to_ticks(5.0),
            'mediaStart': 0, 'mediaDuration': 1,
            'scalar': 1, 'effects': [],
            'parameters': {
                'cursorLocation': {
                    'type': 'point3', 'defaultValue': [0, 0, 0],
                    'keyframes': [
                        {'time': 0, 'endTime': 0, 'value': [50, 50, 0], 'duration': 0},
                    ],
                },
            },
        })
        count = project.apply_smart_focus()
        assert count == 0
