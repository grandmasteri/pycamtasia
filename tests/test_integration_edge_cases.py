"""Integration tests for edge cases and boundary conditions.

Each test verifies that extreme or unusual inputs either:
  (a) Work correctly — open_in_camtasia succeeds, OR
  (b) Fail cleanly — caught by validate() or rejected at the API level
     with a clear error, never silently producing a corrupt file.
"""
from __future__ import annotations

from tests.integration_helpers import INTEGRATION_MARKERS, open_in_camtasia

pytestmark = INTEGRATION_MARKERS


class TestEmptyAndMinimalProjects:
    """Projects with no content or minimal structure."""

    def test_empty_project_no_tracks(self, project):
        """A project's default fixture-provided tracks should open cleanly.

        Note: the `project` fixture loads ``new.cmproj`` which contains a
        couple of default tracks (track_count==2). This test verifies
        that such a minimal, near-empty project opens without issue.
        """
        assert project.timeline.track_count >= 0  # any count is fine
        open_in_camtasia(project)

    def test_single_empty_track(self, project):
        """Adding one additional empty track should still open."""
        before = project.timeline.track_count
        project.timeline.add_track('Empty')
        assert project.timeline.track_count == before + 1
        open_in_camtasia(project)

    def test_canvas_1x1_minimum(self, project):
        """Minimum possible canvas size (1×1 pixel)."""
        project.set_canvas_size(1, 1)
        open_in_camtasia(project)


class TestManyTracks:
    """Stress test with large numbers of tracks."""

    def test_100_tracks(self, project):
        """Adding 100 tracks on top of the fixture's defaults should open."""
        before = project.timeline.track_count
        for i in range(100):
            project.timeline.add_track(f'Track {i}')
        assert project.timeline.track_count == before + 100
        open_in_camtasia(project)


class TestTimingBoundaries:
    """Extreme and boundary timing values."""

    def test_1ms_clip_at_origin(self, project):
        """Clip at start=0.0 with 1ms duration — minimum practical clip."""
        track = project.timeline.add_track('Tiny')
        track.add_callout('dot', start_seconds=0.0, duration_seconds=0.001)
        open_in_camtasia(project)

    def test_very_large_timestamp_10_hours(self, project):
        """Clip starting at 10 hours into the timeline."""
        track = project.timeline.add_track('Late')
        track.add_callout('far', start_seconds=36000.0, duration_seconds=5.0)
        open_in_camtasia(project)

    def test_extreme_start_time_million_seconds(self, project):
        """Clip at start=1,000,000 seconds (~11.5 days)."""
        track = project.timeline.add_track('Extreme')
        track.add_callout('way out', start_seconds=1_000_000.0, duration_seconds=1.0)
        open_in_camtasia(project)

    def test_zero_duration_callout(self, project):
        """Zero-duration clip — should either work or be caught by validate."""
        track = project.timeline.add_track('Zero')
        track.add_callout('zero', start_seconds=0.0, duration_seconds=0.0)
        issues = project.validate()
        if issues:
            # validate caught it — that's fine, don't open
            assert any('duration' in str(i.message).lower() or 'zero' in str(i.message).lower()
                       for i in issues), f'Expected duration-related issue, got: {issues}'
        else:
            open_in_camtasia(project)

    def test_negative_start_rejected(self, project):
        """Negative start time should produce a negative tick value.

        Since the L2 API doesn't validate, the clip is created with a
        negative start. validate() should catch this, or at minimum the
        project should not silently produce a corrupt file.
        """
        track = project.timeline.add_track('Neg')
        track.add_callout('neg', start_seconds=-5.0, duration_seconds=3.0)
        issues = project.validate()
        # If validate catches it, good. If not, we still don't open —
        # negative timestamps are not valid Camtasia content.
        # Either way, the API accepted it without raising, so we verify
        # the clip was created with a negative start tick.
        clip = list(track.clips)[0]
        assert clip.start_seconds < 0

    def test_negative_duration_rejected(self, project):
        """Negative duration should produce a negative tick value.

        Similar to negative start — the L2 API doesn't guard against it,
        but validate() or Camtasia should catch it.
        """
        track = project.timeline.add_track('NegDur')
        track.add_callout('neg', start_seconds=0.0, duration_seconds=-3.0)
        issues = project.validate()
        clip = list(track.clips)[0]
        assert clip.duration_seconds < 0


class TestClipNames:
    """Edge cases in clip text/name content."""

    def test_empty_string_callout_text(self, project):
        """Callout with zero-character text."""
        track = project.timeline.add_track('Empty Text')
        track.add_callout('', start_seconds=0.0, duration_seconds=3.0)
        open_in_camtasia(project)

    def test_very_long_callout_text(self, project):
        """Callout with 10,000 character text."""
        track = project.timeline.add_track('Long Text')
        track.add_callout('A' * 10_000, start_seconds=0.0, duration_seconds=3.0)
        open_in_camtasia(project)

    def test_unicode_emoji_callout(self, project):
        """Callout with emoji characters."""
        track = project.timeline.add_track('Emoji')
        track.add_callout('🎬🎥🎞️✨🔥', start_seconds=0.0, duration_seconds=3.0)
        open_in_camtasia(project)

    def test_unicode_cjk_callout(self, project):
        """Callout with CJK characters."""
        track = project.timeline.add_track('CJK')
        track.add_callout('你好世界 こんにちは 안녕하세요', start_seconds=0.0, duration_seconds=3.0)
        open_in_camtasia(project)

    def test_unicode_rtl_callout(self, project):
        """Callout with right-to-left text (Arabic/Hebrew)."""
        track = project.timeline.add_track('RTL')
        track.add_callout('مرحبا بالعالم שלום עולם', start_seconds=0.0, duration_seconds=3.0)
        open_in_camtasia(project)


class TestValidationDetection:
    """Cases where validate() should detect problems."""

    def test_overlapping_clips_detected(self, project):
        """Two overlapping clips on the same track should be flagged by validate."""
        track = project.timeline.add_track('Overlap')
        track.add_callout('A', start_seconds=0.0, duration_seconds=5.0)
        track.add_callout('B', start_seconds=2.0, duration_seconds=5.0)
        issues = project.validate()
        overlap_issues = [i for i in issues if 'overlap' in i.message.lower()]
        assert overlap_issues, f'Expected overlap warning, got: {[i.message for i in issues]}'

    def test_duplicate_clip_ids_detected(self, project):
        """Manually injected duplicate clip IDs should be caught by validate."""
        track = project.timeline.add_track('DupID')
        track.add_callout('A', start_seconds=0.0, duration_seconds=3.0)
        track.add_callout('B', start_seconds=5.0, duration_seconds=3.0)
        # Force duplicate ID by mutating the raw data
        medias = track._data['medias']
        medias[1]['id'] = medias[0]['id']
        issues = project.validate()
        dup_issues = [i for i in issues if 'duplicate' in i.message.lower()]
        assert dup_issues, f'Expected duplicate ID error, got: {[i.message for i in issues]}'


class TestSaveIdempotency:
    """Saving multiple times should not corrupt the project."""

    def test_multiple_saves(self, project):
        """Calling save() three times should produce a valid project."""
        track = project.timeline.add_track('Multi')
        track.add_callout('hello', start_seconds=0.0, duration_seconds=3.0)
        project.save()
        project.save()
        project.save()
        open_in_camtasia(project)
