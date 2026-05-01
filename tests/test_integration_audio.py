"""Integration tests for pycamtasia audio features.

Each test creates a project with audio clips, applies audio effects,
and validates via open_in_camtasia (which enforces the validator contract).
"""
from __future__ import annotations

from pathlib import Path

import pytest

from tests.integration_helpers import CAMTASIA_APP, INTEGRATION_MARKERS, open_in_camtasia

FIXTURES = Path(__file__).parent / 'fixtures'
EMPTY_WAV = FIXTURES / 'empty.wav'

pytestmark = INTEGRATION_MARKERS


def _add_audio_clip(project, duration_seconds: float = 5.0):
    """Import empty.wav and place an audio clip on a new track."""
    media = project.import_media(EMPTY_WAV)
    track = project.timeline.add_track('Audio')
    clip = track.add_audio(media.id, start_seconds=0.0, duration_seconds=duration_seconds)
    return clip


class TestAudioFadeIn:
    def test_short_fade_in(self, project):
        clip = _add_audio_clip(project)
        clip.add_audio_fade_in(0.5)
        open_in_camtasia(project)

    def test_long_fade_in(self, project):
        clip = _add_audio_clip(project)
        clip.add_audio_fade_in(3.0)
        open_in_camtasia(project)


class TestAudioFadeOut:
    def test_short_fade_out(self, project):
        clip = _add_audio_clip(project)
        clip.add_audio_fade_out(0.5)
        open_in_camtasia(project)

    def test_long_fade_out(self, project):
        clip = _add_audio_clip(project)
        clip.add_audio_fade_out(3.0)
        open_in_camtasia(project)


class TestAudioFadeInAndOut:
    def test_both_fades_on_same_clip(self, project):
        clip = _add_audio_clip(project, duration_seconds=10.0)
        clip.add_audio_fade_in(2.0)
        clip.add_audio_fade_out(2.0)
        open_in_camtasia(project)


class TestAudioPoint:
    def test_volume_envelope_keyframes(self, project):
        clip = _add_audio_clip(project, duration_seconds=10.0)
        clip.add_audio_point(0.0, 0.0)
        clip.add_audio_point(2.0, 1.0)
        clip.add_audio_point(5.0, 0.5)
        clip.add_audio_point(9.0, 0.0)
        open_in_camtasia(project)


class TestEqualizer:
    def test_single_band(self, project):
        clip = _add_audio_clip(project)
        clip.add_equalizer([(1000.0, 3.0)])
        open_in_camtasia(project)

    def test_multiple_bands(self, project):
        clip = _add_audio_clip(project)
        clip.add_equalizer([
            (100.0, -6.0),
            (1000.0, 3.0),
            (8000.0, 6.0),
        ])
        open_in_camtasia(project)


class TestAudioVisualizer:
    def test_default_visualizer(self, project):
        clip = _add_audio_clip(project)
        clip.add_audio_visualizer()
        open_in_camtasia(project)


class TestAiNoiseRemoval:
    def test_noise_removal_via_project(self, project):
        clip = _add_audio_clip(project)
        project.add_ai_noise_removal(clip.id, amount=0.7)
        open_in_camtasia(project)


class TestBackgroundMusic:
    def test_background_music_with_fades(self, project):
        # Need at least one clip on timeline for background music to span
        _add_audio_clip(project, duration_seconds=10.0)
        project.add_background_music(EMPTY_WAV, volume=0.2, fade_in_seconds=1.0, fade_out_seconds=2.0)
        open_in_camtasia(project)


class TestStackedAudioEffects:
    def test_fade_equalizer_visualizer(self, project):
        clip = _add_audio_clip(project, duration_seconds=10.0)
        clip.add_audio_fade_in(1.0)
        clip.add_audio_fade_out(1.0)
        clip.add_equalizer([(500.0, 2.0), (4000.0, -3.0)])
        clip.add_audio_visualizer()
        open_in_camtasia(project)


class TestMultiTrackAudio:
    def test_different_effects_per_track(self, project):
        media = project.import_media(EMPTY_WAV)
        track1 = project.timeline.add_track('Audio 1')
        clip1 = track1.add_audio(media.id, start_seconds=0.0, duration_seconds=5.0)
        clip1.add_audio_fade_in(1.0)

        track2 = project.timeline.add_track('Audio 2')
        clip2 = track2.add_audio(media.id, start_seconds=0.0, duration_seconds=5.0)
        clip2.add_equalizer([(200.0, 4.0)])
        clip2.add_noise_removal(amount=0.6)
        open_in_camtasia(project)


class TestAudioDurationEdgeCases:
    def test_very_short_clip(self, project):
        clip = _add_audio_clip(project, duration_seconds=0.1)
        clip.add_audio_fade_in(0.05)
        open_in_camtasia(project)

    def test_long_clip(self, project):
        clip = _add_audio_clip(project, duration_seconds=60.0)
        clip.add_audio_fade_in(5.0)
        clip.add_audio_fade_out(10.0)
        open_in_camtasia(project)
