"""Tests for Project.export_project_report()."""
from __future__ import annotations

from pathlib import Path

import pytest

from camtasia.project import load_project


class TestExportProjectReport:
    """Tests for the export_project_report method."""

    def test_returns_path_object(self, project, tmp_path):
        out = tmp_path / 'report.md'
        result = project.export_project_report(out)
        assert result == out

    def test_file_is_created(self, project, tmp_path):
        out = tmp_path / 'report.md'
        project.export_project_report(out)
        assert out.exists()

    def test_contains_title_heading(self, project, tmp_path):
        project.title = 'My Test Project'
        out = tmp_path / 'report.md'
        project.export_project_report(out)
        text = out.read_text()
        assert '# Project Report: My Test Project' in text

    def test_contains_overview_section(self, project, tmp_path):
        out = tmp_path / 'report.md'
        project.export_project_report(out)
        text = out.read_text()
        assert '## Overview' in text

    def test_overview_contains_statistics_keys(self, project, tmp_path):
        out = tmp_path / 'report.md'
        project.export_project_report(out)
        text = out.read_text()
        for key in project.statistics():
            assert f'**{key}**' in text

    def test_contains_tracks_section(self, project, tmp_path):
        out = tmp_path / 'report.md'
        project.export_project_report(out)
        text = out.read_text()
        assert '## Tracks' in text

    def test_contains_validation_section(self, project, tmp_path):
        out = tmp_path / 'report.md'
        project.export_project_report(out)
        text = out.read_text()
        assert '## Validation' in text

    def test_empty_project_no_issues(self, project, tmp_path):
        out = tmp_path / 'report.md'
        project.export_project_report(out)
        text = out.read_text()
        assert 'No issues found.' in text

    def test_accepts_string_path(self, project, tmp_path):
        out = str(tmp_path / 'report.md')
        result = project.export_project_report(out)
        assert result.exists()

    def test_track_listing_shows_clip_count(self, project, tmp_path):
        out = tmp_path / 'report.md'
        project.export_project_report(out)
        text = out.read_text()
        for track in project.timeline.tracks:
            assert f'### {track.name}' in text
            assert f'- Clips: {len(track)}' in text

    def test_with_real_fixture(self, tmp_path):
        """Test with a fixture that has actual clips."""
        fixtures = Path(__file__).parent / 'fixtures'
        fixture = fixtures / 'test_project_a.tscproj'
        if not fixture.exists():
            pytest.skip('fixture not available')
        proj = load_project(fixture)
        out = tmp_path / 'report.md'
        result = proj.export_project_report(out)
        text = result.read_text()
        assert '# Project Report:' in text
        assert '## Overview' in text
        assert '## Tracks' in text
        assert '## Validation' in text

    def test_overwrites_existing_file(self, project, tmp_path):
        out = tmp_path / 'report.md'
        out.write_text('old content')
        project.export_project_report(out)
        text = out.read_text()
        assert 'old content' not in text
        assert '# Project Report:' in text


# ── Bug 11: JSON report rounds floats to 3 decimals ──


class TestJsonReportRoundsFloats:
    """JSON report should round float values to 3 decimal places."""

    def test_clip_seconds_rounded(self, project, tmp_path):
        import json

        from camtasia.export.report import export_project_report
        from camtasia.timing import seconds_to_ticks

        track = project.timeline.get_or_create_track('Test')
        track.add_clip('VMFile', 0, seconds_to_ticks(1.0), seconds_to_ticks(3.0))
        out = tmp_path / 'report.json'
        export_project_report(project, out, format='json')
        data = json.loads(out.read_text())
        for t in data['tracks']:
            for clip in t['clips']:
                s = str(clip['start_seconds'])
                d = str(clip['duration_seconds'])
                # At most 3 decimal places
                if '.' in s:
                    assert len(s.split('.')[1]) <= 3
                if '.' in d:
                    assert len(d.split('.')[1]) <= 3

    def test_duration_seconds_rounded(self, project, tmp_path):
        import json

        from camtasia.export.report import export_project_report

        out = tmp_path / 'report.json'
        export_project_report(project, out, format='json')
        data = json.loads(out.read_text())
        dur = str(data['duration_seconds'])
        if '.' in dur:
            assert len(dur.split('.')[1]) <= 3
