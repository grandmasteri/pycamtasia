"""Integration tests for callout (annotation) shapes, builders, and styling.

Each test creates a project with callout(s), saves, and opens in Camtasia
to verify the output is accepted without exceptions.
"""
from __future__ import annotations

import pytest

from camtasia import CalloutBuilder, CalloutKind, CalloutShape

from tests.integration_helpers import INTEGRATION_MARKERS, open_in_camtasia

pytestmark = INTEGRATION_MARKERS


class TestCalloutShapes:
    def test_arrow_callout_opens(self, project):
        track = project.timeline.add_track('Annotations')
        callout = track.add_callout('', start_seconds=0.0, duration_seconds=3.0)
        callout.shape = CalloutShape.ARROW
        open_in_camtasia(project)

    def test_rectangle_shape_callout_opens(self, project):
        track = project.timeline.add_track('Annotations')
        callout = track.add_callout('', start_seconds=0.0, duration_seconds=3.0)
        callout.shape = CalloutShape.SHAPE_RECTANGLE
        open_in_camtasia(project)

    def test_ellipse_shape_callout_opens(self, project):
        track = project.timeline.add_track('Annotations')
        callout = track.add_callout('', start_seconds=0.0, duration_seconds=3.0)
        callout.shape = CalloutShape.SHAPE_ELLIPSE
        open_in_camtasia(project)

    def test_triangle_shape_callout_opens(self, project):
        track = project.timeline.add_track('Annotations')
        callout = track.add_callout('', start_seconds=0.0, duration_seconds=3.0)
        callout.shape = CalloutShape.SHAPE_TRIANGLE
        open_in_camtasia(project)

    def test_text_rectangle_callout_opens(self, project):
        track = project.timeline.add_track('Annotations')
        callout = track.add_callout('Hello', start_seconds=0.0, duration_seconds=3.0)
        callout.shape = CalloutShape.TEXT_RECTANGLE
        open_in_camtasia(project)

    def test_text_arrow_callout_opens(self, project):
        track = project.timeline.add_track('Annotations')
        callout = track.add_callout('Note', start_seconds=0.0, duration_seconds=3.0)
        callout.shape = CalloutShape.TEXT_ARROW2
        open_in_camtasia(project)


class TestCalloutBuilderAndSequence:
    def test_callout_builder_opens(self, project):
        builder = CalloutBuilder('Built callout')
        builder.font('Arial', weight=700, size=48)
        builder.color(fill=(0, 0, 255, 200), font=(255, 255, 255, 255))
        builder.position(100, -50)
        builder.size(400, 100)
        track = project.timeline.add_track('Annotations')
        track.add_callout_from_builder(builder, start_seconds=0.0, duration_seconds=4.0)
        open_in_camtasia(project)

    def test_callout_sequence_opens(self, project):
        entries = [
            (0.0, 2.0, 'Step 1'),
            (2.5, 2.0, 'Step 2'),
            (5.0, 2.0, 'Step 3'),
        ]
        project.add_callout_sequence(entries, track_name='Steps', font_size=32.0)
        open_in_camtasia(project)


class TestCalloutStyling:
    def test_callout_with_custom_color_opens(self, project):
        track = project.timeline.add_track('Annotations')
        callout = track.add_callout('Colored', start_seconds=0.0, duration_seconds=3.0)
        callout.fill_color = (0.8, 0.2, 0.1, 0.9)
        open_in_camtasia(project)

    def test_callout_with_custom_position_opens(self, project):
        track = project.timeline.add_track('Annotations')
        callout = track.add_callout('Moved', start_seconds=0.0, duration_seconds=3.0)
        callout.move_to(200.0, -150.0)
        open_in_camtasia(project)


class TestMultipleCallouts:
    def test_multiple_callouts_on_one_track_opens(self, project):
        track = project.timeline.add_track('Annotations')
        for i in range(6):
            track.add_callout(f'Item {i}', start_seconds=i * 2.0, duration_seconds=1.5)
        open_in_camtasia(project)

    def test_callouts_across_multiple_tracks_opens(self, project):
        for i in range(3):
            track = project.timeline.add_track(f'Annotations {i}')
            track.add_callout(f'Track {i}', start_seconds=0.0, duration_seconds=3.0)
        open_in_camtasia(project)


class TestCalloutKinds:
    def test_remix_callout_opens(self, project):
        track = project.timeline.add_track('Annotations')
        callout = track.add_callout('Remix', start_seconds=0.0, duration_seconds=3.0)
        callout.shape = CalloutShape.SHAPE_RECTANGLE
        # Remix kind is set by default for shape callouts via the def dict
        assert callout.kind == '' or callout.kind == CalloutKind.REMIX.value
        open_in_camtasia(project)

    def test_win_blur_callout_opens(self, project):
        track = project.timeline.add_track('Annotations')
        callout = track.add_callout('', start_seconds=0.0, duration_seconds=3.0)
        # Set kind to WIN_BLUR via the definition dict
        callout._data.setdefault('def', {})['kind'] = CalloutKind.WIN_BLUR.value
        callout.shape = CalloutShape.SHAPE_RECTANGLE
        open_in_camtasia(project)
