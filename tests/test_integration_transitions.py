"""Integration tests for transition types not covered by test_camtasia_integration.py.

Covers: add_card_swipe, add_cube_rotate, add_fade_to_white, add_gradient_wipe,
add_slide, add_swap, add_wipe, plus edge cases (zero duration, oversized duration,
multiple transitions, audio transitions, mismatched clip durations).
"""
from __future__ import annotations

from pathlib import Path

from tests.integration_helpers import INTEGRATION_MARKERS, open_in_camtasia

pytestmark = INTEGRATION_MARKERS

FIXTURES = Path(__file__).parent / 'fixtures'
EMPTY_WAV = FIXTURES / 'empty.wav'


def _two_audio_clips(project, dur1=2.0, dur2=2.0):
    """Helper: import audio, create track with two adjacent clips."""
    media = project.import_media(EMPTY_WAV)
    track = project.timeline.add_track('Audio')
    c1 = track.add_audio(media.id, start_seconds=0.0, duration_seconds=dur1)
    c2 = track.add_audio(media.id, start_seconds=dur1, duration_seconds=dur2)
    return track, c1, c2


class TestRemainingTransitions:
    """Tests for transitions not already covered in test_camtasia_integration.py."""

    def test_card_swipe_opens(self, project):
        track, c1, c2 = _two_audio_clips(project)
        track.transitions.add_card_swipe(c1.id, c2.id, duration_seconds=0.5)
        open_in_camtasia(project)

    def test_cube_rotate_opens(self, project):
        track, c1, c2 = _two_audio_clips(project)
        track.transitions.add_cube_rotate(c1.id, c2.id, duration_seconds=0.5)
        open_in_camtasia(project)

    def test_fade_to_white_opens(self, project):
        track, c1, c2 = _two_audio_clips(project)
        track.transitions.add_fade_to_white(c1.id, c2.id, duration_seconds=0.5)
        open_in_camtasia(project)

    def test_gradient_wipe_opens(self, project):
        track, c1, c2 = _two_audio_clips(project)
        track.transitions.add_gradient_wipe(c1.id, c2.id, duration_seconds=0.5)
        open_in_camtasia(project)

    def test_slide_opens(self, project):
        track, c1, c2 = _two_audio_clips(project)
        track.transitions.add_slide(c1.id, c2.id, duration_seconds=0.5, direction='left')
        open_in_camtasia(project)

    def test_swap_opens(self, project):
        track, c1, c2 = _two_audio_clips(project)
        track.transitions.add_swap(c1.id, c2.id, duration_seconds=0.5)
        open_in_camtasia(project)

    def test_wipe_opens(self, project):
        track, c1, c2 = _two_audio_clips(project)
        track.transitions.add_wipe(c1.id, c2.id, duration_seconds=0.5, direction='right')
        open_in_camtasia(project)


class TestTransitionEdgeCases:
    """Edge cases for transition behavior."""

    def test_zero_duration_transition(self, project):
        """Transition with duration=0 should be caught by validate or open cleanly."""
        track, c1, c2 = _two_audio_clips(project)
        track.transitions.add_dissolve(c1.id, c2.id, duration_seconds=0.0)
        open_in_camtasia(project)

    def test_transition_longer_than_clips(self, project):
        """Transition longer than both clips — validator should catch or Camtasia handles."""
        track, c1, c2 = _two_audio_clips(project, dur1=1.0, dur2=1.0)
        track.transitions.add_dissolve(c1.id, c2.id, duration_seconds=5.0)
        open_in_camtasia(project)

    def test_multiple_transitions_in_sequence(self, project):
        """Three clips with transitions between each pair on same track."""
        media = project.import_media(EMPTY_WAV)
        track = project.timeline.add_track('Audio')
        c1 = track.add_audio(media.id, start_seconds=0.0, duration_seconds=3.0)
        c2 = track.add_audio(media.id, start_seconds=3.0, duration_seconds=3.0)
        c3 = track.add_audio(media.id, start_seconds=6.0, duration_seconds=3.0)
        track.transitions.add_dissolve(c1.id, c2.id, duration_seconds=0.5)
        track.transitions.add_card_flip(c2.id, c3.id, duration_seconds=0.5)
        open_in_camtasia(project)

    def test_transition_between_audio_clips(self, project):
        """Explicit test that transitions work between audio-only clips."""
        track, c1, c2 = _two_audio_clips(project, dur1=4.0, dur2=4.0)
        track.transitions.add_swap(c1.id, c2.id, duration_seconds=1.0)
        open_in_camtasia(project)

    def test_transition_mismatched_clip_durations(self, project):
        """Transition between a very short first clip and a very long second clip."""
        track, c1, c2 = _two_audio_clips(project, dur1=0.5, dur2=10.0)
        track.transitions.add_slide(c1.id, c2.id, duration_seconds=0.3)
        open_in_camtasia(project)
