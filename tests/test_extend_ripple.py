"""Tests for Track.extend_clip with ripple option."""
from __future__ import annotations

import pytest

from camtasia.timing import seconds_to_ticks


class TestExtendClipRipple:
    def test_ripple_false_does_not_move_subsequent(self, project):
        track = project.timeline.get_or_create_track('T')
        c1 = track.add_image(0, start_seconds=0.0, duration_seconds=5.0)
        c2 = track.add_image(0, start_seconds=5.0, duration_seconds=5.0)
        original_c2_start = c2.start
        track.extend_clip(c1.id, extend_seconds=2.0)
        # c2 should NOT have moved
        assert c2.start == original_c2_start

    def test_ripple_true_pushes_subsequent_forward(self, project):
        track = project.timeline.get_or_create_track('T')
        c1 = track.add_image(0, start_seconds=0.0, duration_seconds=5.0)
        c2 = track.add_image(0, start_seconds=5.0, duration_seconds=5.0)
        c3 = track.add_image(0, start_seconds=10.0, duration_seconds=5.0)
        track.extend_clip(c1.id, extend_seconds=2.0, ripple=True)
        # c2 and c3 should have moved forward by 2 seconds
        assert c2.start == seconds_to_ticks(7.0)
        assert c3.start == seconds_to_ticks(12.0)

    def test_ripple_negative_pulls_subsequent_back(self, project):
        track = project.timeline.get_or_create_track('T')
        c1 = track.add_image(0, start_seconds=0.0, duration_seconds=5.0)
        c2 = track.add_image(0, start_seconds=5.0, duration_seconds=5.0)
        track.extend_clip(c1.id, extend_seconds=-2.0, ripple=True)
        assert c2.start == seconds_to_ticks(3.0)

    def test_ripple_does_not_move_earlier_clips(self, project):
        track = project.timeline.get_or_create_track('T')
        c1 = track.add_image(0, start_seconds=0.0, duration_seconds=5.0)
        c2 = track.add_image(0, start_seconds=5.0, duration_seconds=5.0)
        c3 = track.add_image(0, start_seconds=10.0, duration_seconds=5.0)
        track.extend_clip(c2.id, extend_seconds=1.0, ripple=True)
        # c1 should not move; c3 should move forward
        assert c1.start == seconds_to_ticks(0.0)
        assert c3.start == seconds_to_ticks(11.0)

    def test_ripple_raises_on_nonpositive_duration(self, project):
        track = project.timeline.get_or_create_track('T')
        c1 = track.add_image(0, start_seconds=0.0, duration_seconds=2.0)
        with pytest.raises(ValueError, match='negative'):
            track.extend_clip(c1.id, extend_seconds=-3.0, ripple=True)

    def test_extend_clip_to_delegates_without_ripple(self, project):
        track = project.timeline.get_or_create_track('T')
        c1 = track.add_image(0, start_seconds=0.0, duration_seconds=5.0)
        c2 = track.add_image(0, start_seconds=5.0, duration_seconds=5.0)
        track.extend_clip_to(c1.id, target_duration_seconds=7.0)
        # extend_clip_to doesn't pass ripple, so c2 should not move
        assert c2.start == seconds_to_ticks(5.0)
