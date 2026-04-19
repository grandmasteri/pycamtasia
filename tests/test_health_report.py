"""Tests for Project.health_report()."""
from __future__ import annotations


class TestHealthReportEmpty:
    """health_report on an empty project."""

    def test_returns_string(self, project):
        report = project.health_report()
        assert isinstance(report, str)

    def test_contains_title_heading(self, project):
        project.title = 'My Project'
        report = project.health_report()
        assert '# Health Report: My Project' in report

    def test_contains_statistics_section(self, project):
        report = project.health_report()
        assert '## Statistics' in report

    def test_contains_validation_section(self, project):
        report = project.health_report()
        assert '## Validation' in report

    def test_contains_tracks_section(self, project):
        report = project.health_report()
        assert '## Tracks' in report

    def test_all_checks_passed_when_clean(self, project):
        report = project.health_report()
        assert 'All checks passed.' in report

    def test_statistics_keys_present(self, project):
        report = project.health_report()
        for key in ('title', 'duration_seconds', 'track_count', 'clip_count'):
            assert f'- {key}:' in report


class TestHealthReportWithContent:
    """health_report on a project with clips."""

    def test_track_details_show_clip_count(self, project):
        track = project.timeline.tracks[0]
        track.add_callout('Hello', 0, 5.0, font_size=24.0)
        report = project.health_report()
        assert '- Clips: 1' in report

    def test_track_details_show_duration(self, project):
        track = project.timeline.tracks[0]
        track.add_callout('Hello', 0, 5.0, font_size=24.0)
        report = project.health_report()
        assert '- Duration:' in report

    def test_track_name_appears(self, project):
        track = project.timeline.tracks[0]
        name = track.name
        report = project.health_report()
        assert f'### {name}' in report


class TestHealthReportValidationIssues:
    """health_report when validation finds issues."""

    def test_shows_error_count(self, project):
        # Inject a clip referencing a non-existent source ID
        track = project.timeline.tracks[0]
        track._data.setdefault('medias', []).append({
            'id': 9999, '_type': 'VMFile',
            'src': 77777,
            'trackIndex': 0,
            'start': 0,
            'duration': 100,
            'mediaStart': 0,
            'mediaDuration': 100,
            'type': 'VMFile',
            'attributes': {'ident': 'test'},
            'parameters': {'gestureMode': 0},
            'effects': [],
        })
        report = project.health_report()
        assert '- Errors:' in report

    def test_shows_warning_count(self, project):
        # Add orphaned media to trigger a warning
        project._data.setdefault('sourceBin', []).append({
            'id': 88888,
            'src': './media/orphan.png',
            'rect': [0, 0, 100, 100],
            'lastMod': '20260101T000000',
            'sourceTracks': [{'range': [0, 1], 'type': 2, 'editRate': 1,
                              'trackRect': [0, 0, 100, 100], 'sampleRate': 0,
                              'bitDepth': 0, 'numChannels': 0}],
        })
        report = project.health_report()
        assert '- Warnings:' in report

    def test_issue_messages_listed(self, project):
        project._data.setdefault('sourceBin', []).append({
            'id': 88888,
            'src': './media/orphan.png',
            'rect': [0, 0, 100, 100],
            'lastMod': '20260101T000000',
            'sourceTracks': [{'range': [0, 1], 'type': 2, 'editRate': 1,
                              'trackRect': [0, 0, 100, 100], 'sampleRate': 0,
                              'bitDepth': 0, 'numChannels': 0}],
        })
        report = project.health_report()
        assert '[warning]' in report


class TestHealthReportGaps:
    """health_report gap reporting."""

    def test_gaps_shown_when_present(self, project):
        track = project.timeline.tracks[0]
        # Place two clips with a gap between them
        track.add_callout('A', 0, 2.0, font_size=24.0)
        track.add_callout('B', 5.0, 2.0, font_size=24.0)
        report = project.health_report()
        assert '- Gaps:' in report


class TestHealthReportStructure:
    """Verify the overall markdown structure."""

    def test_sections_in_order(self, project):
        report = project.health_report()
        stats_pos = report.index('## Statistics')
        valid_pos = report.index('## Validation')
        tracks_pos = report.index('## Tracks')
        assert stats_pos < valid_pos < tracks_pos

    def test_no_trailing_newline_issues(self, project):
        report = project.health_report()
        # Should not start or end with excessive blank lines
        assert not report.startswith('\n')
