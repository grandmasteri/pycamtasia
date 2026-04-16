"""Tests for Track.first_gap, Track.largest_gap, Project.validate_and_report, BaseClip.time_range_formatted."""
from __future__ import annotations

import json
import pytest
from pathlib import Path
from unittest.mock import patch, PropertyMock

from camtasia.project import load_project

RESOURCES = Path(__file__).parent.parent / 'src' / 'camtasia' / 'resources'


# Module-level list to prevent TemporaryDirectory from being GC'd during test
_TEMP_DIRS: list = []

def _isolated_project():
    """Load template into an isolated temp copy (safe for parallel execution)."""
    import shutil, tempfile
    from camtasia.project import load_project
    td = tempfile.TemporaryDirectory()
    _TEMP_DIRS.append(td)  # prevent premature GC
    dst = Path(td.name) / 'test.cmproj'
    shutil.copytree(RESOURCES / 'new.cmproj', dst)
    return load_project(dst)

def project():
    return _isolated_project()


# ── Track.first_gap ──────────────────────────────────────────────────


class TestFirstGap:
    """Tests for Track.first_gap property."""

    def test_first_gap_returns_none_when_no_gaps(self, project):
        """first_gap is None when track has no gaps."""
        track = project.timeline.tracks[0]
        with patch.object(type(track), 'gaps', return_value=[]):
            assert track.first_gap is None

    def test_first_gap_returns_first_element(self, project):
        """first_gap returns the first gap tuple."""
        track = project.timeline.tracks[0]
        fake_gaps: list[tuple[float, float]] = [(1.0, 2.0), (5.0, 8.0)]
        with patch.object(type(track), 'gaps', return_value=fake_gaps):
            assert track.first_gap == (1.0, 2.0)

    def test_first_gap_single_gap(self, project):
        """first_gap works with exactly one gap."""
        track = project.timeline.tracks[0]
        with patch.object(type(track), 'gaps', return_value=[(3.5, 7.0)]):
            assert track.first_gap == (3.5, 7.0)


# ── Track.largest_gap ────────────────────────────────────────────────


class TestLargestGap:
    """Tests for Track.largest_gap property."""

    def test_largest_gap_returns_none_when_no_gaps(self, project):
        """largest_gap is None when track has no gaps."""
        track = project.timeline.tracks[0]
        with patch.object(type(track), 'gaps', return_value=[]):
            assert track.largest_gap is None

    def test_largest_gap_returns_widest(self, project):
        """largest_gap returns the gap with the greatest duration."""
        track = project.timeline.tracks[0]
        fake_gaps: list[tuple[float, float]] = [(0.0, 1.0), (3.0, 10.0), (12.0, 13.0)]
        with patch.object(type(track), 'gaps', return_value=fake_gaps):
            assert track.largest_gap == (3.0, 10.0)

    def test_largest_gap_single_gap(self, project):
        """largest_gap works with exactly one gap."""
        track = project.timeline.tracks[0]
        with patch.object(type(track), 'gaps', return_value=[(2.0, 5.0)]):
            assert track.largest_gap == (2.0, 5.0)

    def test_largest_gap_equal_durations(self, project):
        """largest_gap returns first when durations are equal (max behavior)."""
        track = project.timeline.tracks[0]
        fake_gaps: list[tuple[float, float]] = [(0.0, 2.0), (5.0, 7.0)]
        with patch.object(type(track), 'gaps', return_value=fake_gaps):
            result = track.largest_gap
            assert result is not None
            assert result[1] - result[0] == 2.0


# ── Project.validate_and_report ──────────────────────────────────────


class TestValidateAndReport:
    """Tests for Project.validate_and_report method."""

    def test_no_issues_returns_clean_message(self, project):
        """validate_and_report returns 'No issues found.' when validation passes."""
        with patch.object(type(project), 'validate', return_value=[]):
            assert project.validate_and_report() == 'No issues found.'

    def test_single_issue_report(self, project):
        """validate_and_report formats a single issue correctly."""
        from camtasia.validation import ValidationIssue
        mock_issues: list[ValidationIssue] = [
            ValidationIssue('error', 'Something broke'),
        ]
        with patch.object(type(project), 'validate', return_value=mock_issues):
            report: str = project.validate_and_report()
            assert report.startswith('1 issue(s) found:')
            assert '  [error] Something broke' in report

    def test_multiple_issues_report(self, project):
        """validate_and_report formats multiple issues with correct count."""
        from camtasia.validation import ValidationIssue
        mock_issues: list[ValidationIssue] = [
            ValidationIssue('error', 'Bad clip'),
            ValidationIssue('warning', 'Missing file'),
        ]
        with patch.object(type(project), 'validate', return_value=mock_issues):
            report: str = project.validate_and_report()
            lines: list[str] = report.split('\n')
            assert lines[0] == '2 issue(s) found:'
            assert lines[1] == '  [error] Bad clip'
            assert lines[2] == '  [warning] Missing file'


# ── BaseClip.time_range_formatted ────────────────────────────────────


class TestTimeRangeFormatted:
    def test_time_range_formatted(self):
        from camtasia.timeline.clips.base import BaseClip
        from camtasia.timing import seconds_to_ticks
        data = {'_type': 'VMFile', 'id': 1, 'start': seconds_to_ticks(65.0), 'duration': seconds_to_ticks(30.0)}
        clip = BaseClip(data)
        actual: str = clip.time_range_formatted
        assert actual == '1:05 - 1:35'

    def test_time_range_formatted_zero_start(self):
        from camtasia.timeline.clips.base import BaseClip
        from camtasia.timing import seconds_to_ticks
        data = {'_type': 'VMFile', 'id': 1, 'start': 0, 'duration': seconds_to_ticks(5.0)}
        clip = BaseClip(data)
        actual: str = clip.time_range_formatted
        assert actual == '0:00 - 0:05'


class TestProjectTrackNames:
    def test_track_names(self, project):
        project.timeline.add_track('Alpha')
        project.timeline.add_track('Beta')
        assert 'Alpha' in project.track_names
        assert 'Beta' in project.track_names


class TestIsSilent:
    def test_is_silent_when_muted(self):
        from camtasia.timeline.clips.base import BaseClip
        data = {'_type': 'AMFile', 'id': 1, 'start': 0, 'duration': 100, 'attributes': {'gain': 0.0}, 'parameters': {'volume': 1.0}}
        clip = BaseClip(data)
        assert clip.is_silent is True

    def test_not_silent(self):
        from camtasia.timeline.clips.base import BaseClip
        data = {'_type': 'AMFile', 'id': 1, 'start': 0, 'duration': 100, 'attributes': {'gain': 1.0}, 'parameters': {'volume': 1.0}}
        clip = BaseClip(data)
        assert clip.is_silent is False


class TestTotalClipDurationTicks:
    def test_total_clip_duration_ticks(self):
        from camtasia.timeline.track import Track
        data = {'trackIndex': 0, 'medias': [
            {'id': 1, '_type': 'AMFile', 'start': 0, 'duration': 100},
            {'id': 2, '_type': 'AMFile', 'start': 200, 'duration': 300},
        ], 'transitions': []}
        track = Track({'ident': 'test'}, data)
        assert track.total_clip_duration_ticks == 400
