"""Integration tests for export features (CSV, EDL, SRT).

Each test exports from a project, verifies the export output, then
confirms the original project still opens in Camtasia (exports must
not mutate the project).
"""
from __future__ import annotations

import csv

import pytest

from camtasia import export_csv, export_edl, export_markers_as_srt
from camtasia.timing import seconds_to_ticks

from tests.integration_helpers import INTEGRATION_MARKERS, open_in_camtasia

pytestmark = INTEGRATION_MARKERS


def _add_markers(project, count: int = 3):
    """Add `count` markers at 1-second intervals."""
    for i in range(count):
        project.timeline.add_marker(f'Marker {i + 1}', float(i + 1))


def _add_clips(project, count: int = 4):
    """Add `count` clips sequentially on a track."""
    track = project.timeline.get_or_create_track('Video')
    for i in range(count):
        track.add_clip('VMFile', 1, seconds_to_ticks(i * 5.0), seconds_to_ticks(5.0))


class TestSrtExport:
    def test_export_srt_does_not_corrupt_project(self, project, tmp_path):
        _add_markers(project, 3)
        srt_path = tmp_path / 'markers.srt'
        export_markers_as_srt(project, srt_path)
        assert srt_path.exists()
        open_in_camtasia(project)

    def test_srt_round_trip_marker_count(self, project, tmp_path):
        _add_markers(project, 5)
        srt_path = tmp_path / 'markers.srt'
        export_markers_as_srt(project, srt_path)
        blocks = [b for b in srt_path.read_text().split('\n\n') if b.strip()]
        assert len(blocks) == 5
        open_in_camtasia(project)

    def test_srt_empty_markers(self, project, tmp_path):
        srt_path = tmp_path / 'empty.srt'
        export_markers_as_srt(project, srt_path)
        assert srt_path.read_text() == ''
        open_in_camtasia(project)


class TestEdlExport:
    def test_export_edl_does_not_corrupt_project(self, project, tmp_path):
        _add_clips(project, 4)
        edl_path = tmp_path / 'timeline.edl'
        export_edl(project, edl_path, title='Test')
        assert edl_path.exists()
        content = edl_path.read_text()
        assert 'TITLE: Test' in content
        assert 'FCM: NON-DROP FRAME' in content
        # Verify event lines exist
        event_lines = [l for l in content.splitlines() if l and l[0].isdigit()]
        assert len(event_lines) == 4
        open_in_camtasia(project)

    def test_edl_empty_timeline(self, project, tmp_path):
        edl_path = tmp_path / 'empty.edl'
        export_edl(project, edl_path)
        content = edl_path.read_text()
        assert 'TITLE:' in content
        event_lines = [l for l in content.splitlines() if l and l[0].isdigit()]
        assert len(event_lines) == 0
        open_in_camtasia(project)


class TestCsvExport:
    def test_export_csv_does_not_corrupt_project(self, project, tmp_path):
        _add_clips(project, 3)
        project.timeline.add_track('Audio')
        csv_path = tmp_path / 'timeline.csv'
        export_csv(project, csv_path)
        assert csv_path.exists()
        with csv_path.open() as f:
            reader = csv.reader(f)
            rows = list(reader)
        assert rows[0][0] == 'track_name'  # header
        assert len(rows) == 4  # header + 3 clips
        open_in_camtasia(project)

    def test_csv_include_nested_true_vs_false(self, project, tmp_path):
        track = project.timeline.get_or_create_track('Video')
        c1 = track.add_clip('VMFile', 1, 0, seconds_to_ticks(5.0))
        c2 = track.add_clip('VMFile', 1, seconds_to_ticks(5.0), seconds_to_ticks(5.0))
        track.group_clips([c1.id, c2.id])

        nested_path = tmp_path / 'nested.csv'
        flat_path = tmp_path / 'flat.csv'
        export_csv(project, nested_path, include_nested=True)
        export_csv(project, flat_path, include_nested=False)

        nested_rows = nested_path.read_text().splitlines()
        flat_rows = flat_path.read_text().splitlines()
        # Nested should have more rows (group + inner clips)
        assert len(nested_rows) > len(flat_rows)
        open_in_camtasia(project)

    def test_csv_empty_timeline(self, project, tmp_path):
        csv_path = tmp_path / 'empty.csv'
        export_csv(project, csv_path)
        with csv_path.open() as f:
            rows = list(csv.reader(f))
        assert len(rows) == 1  # header only
        open_in_camtasia(project)
