"""Integration tests for behavior presets not covered by test_camtasia_integration.py.

Covers: reveal, sliding, flyOut, pulsating, shifting, emphasize, jiggle,
plus edge cases: stacked behaviors, behaviors on shape callouts, and
behaviors on short-duration clips.
"""
from __future__ import annotations

import pytest

from camtasia import seconds_to_ticks
from camtasia.annotations import callouts, shapes

from tests.integration_helpers import INTEGRATION_MARKERS, open_in_camtasia

pytestmark = INTEGRATION_MARKERS


class TestRemainingBehaviorPresets:
    """Each remaining BehaviorPreset opens in Camtasia without exceptions."""

    @pytest.mark.parametrize('preset', [
        'reveal',
        'sliding',
        'flyOut',
        'pulsating',
        'shifting',
        'emphasize',
        'jiggle',
    ])
    def test_behavior_opens(self, project, preset):
        track = project.timeline.add_track('Callouts')
        callout = track.add_callout('Test', start_seconds=0.0, duration_seconds=5.0)
        callout.add_behavior(preset)
        open_in_camtasia(project)


class TestBehaviorEdgeCases:
    """Edge cases: stacking, shapes, short durations."""

    def test_multiple_behaviors_on_one_callout(self, project):
        """Stacking fade + pulsating + jiggle on a single callout."""
        track = project.timeline.add_track('Callouts')
        callout = track.add_callout('Stacked', start_seconds=0.0, duration_seconds=5.0)
        callout.add_behavior('fade')
        callout.add_behavior('pulsating')
        callout.add_behavior('jiggle')
        open_in_camtasia(project)

    def test_behavior_on_arrow_callout(self, project):
        """flyIn behavior on an arrow shape callout."""
        track = project.timeline.add_track('Shapes')
        arrow_def = callouts.arrow(head=(200, 0))
        clip = track.add_clip(
            'Callout', None,
            0, seconds_to_ticks(5.0),
            attributes={'ident': '', 'autoRotateText': True},
            **{'def': arrow_def},
        )
        clip.add_behavior('flyIn')
        open_in_camtasia(project)

    def test_behavior_on_rectangle_callout(self, project):
        """emphasize behavior on a rectangle shape callout."""
        track = project.timeline.add_track('Shapes')
        rect_def = shapes.rectangle(width=300.0, height=200.0)
        clip = track.add_clip(
            'Callout', None,
            0, seconds_to_ticks(5.0),
            attributes={'ident': '', 'autoRotateText': True},
            **{'def': rect_def},
        )
        clip.add_behavior('emphasize')
        open_in_camtasia(project)

    def test_behavior_on_short_duration_clip(self, project):
        """Behavior on a very short (0.5s) callout still opens."""
        track = project.timeline.add_track('Callouts')
        callout = track.add_callout('Quick', start_seconds=0.0, duration_seconds=0.5)
        callout.add_behavior('reveal')
        open_in_camtasia(project)
