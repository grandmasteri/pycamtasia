from __future__ import annotations

import json
from pathlib import Path

import pytest

from camtasia.export.srt import _format_srt_time, export_markers_as_srt
from camtasia.export.report import export_project_report
from camtasia.timing import seconds_to_ticks


def _add_markers(project, labels_and_seconds):
    for label, secs in labels_and_seconds:
        project.timeline.add_marker(label, secs)


def _add_clip(project, start_seconds=0.0, duration_seconds=5.0):
    track = project.timeline.get_or_create_track('Test')
    track.add_clip(
        'VMFile', None,
        seconds_to_ticks(start_seconds),
        seconds_to_ticks(duration_seconds),
    )


# ── SRT tests ──────────────────────────────────────────────────────


def test_srt_marker_count(project, tmp_path):
    _add_markers(project, [('A', 1.0), ('B', 5.0), ('C', 10.0)])
    out = export_markers_as_srt(project, tmp_path / 'out.srt')
    blocks = [b for b in out.read_text().split('\n\n') if b.strip()]
    assert len(blocks) == 3


def test_srt_timecodes(project, tmp_path):
    _add_markers(project, [('Hello', 61.5)])
    text = export_markers_as_srt(project, tmp_path / 'out.srt').read_text()
    assert '00:01:01,500 --> 00:01:04,500' in text


def test_srt_custom_duration(project, tmp_path):
    _add_markers(project, [('X', 0.0)])
    text = export_markers_as_srt(project, tmp_path / 'out.srt', duration_seconds=5.0).read_text()
    assert '00:00:00,000 --> 00:00:05,000' in text


def test_srt_empty_markers(project, tmp_path):
    out = export_markers_as_srt(project, tmp_path / 'out.srt')
    assert out.read_text() == ''


# ── Report tests ───────────────────────────────────────────────────


def test_report_markdown_has_headers(project, tmp_path):
    text = export_project_report(project, tmp_path / 'report.md').read_text()
    assert '# Project Report' in text


def test_report_markdown_has_tracks(project, tmp_path):
    _add_clip(project)
    text = export_project_report(project, tmp_path / 'report.md').read_text()
    assert '## Tracks' in text
    assert 'Test' in text


def test_report_json_valid(project, tmp_path):
    out = export_project_report(project, tmp_path / 'report.json', format='json')
    data = json.loads(out.read_text())
    for key in ('project', 'canvas', 'duration_seconds', 'track_count', 'tracks', 'media_count', 'media'):
        assert key in data


def test_report_json_has_tracks(project, tmp_path):
    _add_clip(project, start_seconds=0.0, duration_seconds=3.0)
    out = export_project_report(project, tmp_path / 'report.json', format='json')
    data = json.loads(out.read_text())
    assert isinstance(data['tracks'], list)
    assert any(t['clip_count'] > 0 for t in data['tracks'])
    clip = next(c for t in data['tracks'] for c in t['clips'])
    assert 'id' in clip and 'type' in clip and 'start_seconds' in clip and 'duration_seconds' in clip


# ── _format_srt_time unit tests ────────────────────────────────────


@pytest.mark.parametrize('seconds, expected', [
    (0.0, '00:00:00,000'),
    (61.5, '00:01:01,500'),
    (3661.123, '01:01:01,123'),
])
def test_format_srt_time(seconds, expected):
    assert _format_srt_time(seconds) == expected


class TestReportWithMedia:
    def test_markdown_report_includes_media(self, project, tmp_path):
        from camtasia.export import export_project_report
        # Import a media file to populate the media bin
        import shutil
        wav = Path(__file__).parent / 'fixtures' / 'empty.wav'
        project.import_media(wav)
        output = tmp_path / 'report.md'
        export_project_report(project, output, format='markdown')
        actual_content = output.read_text()
        assert '## Media Bin' in actual_content
        assert 'empty' in actual_content

    def test_json_report_includes_media(self, project, tmp_path):
        from camtasia.export import export_project_report
        import shutil
        wav = Path(__file__).parent / 'fixtures' / 'empty.wav'
        project.import_media(wav)
        output = tmp_path / 'report.json'
        export_project_report(project, output, format='json')
        actual_data = json.loads(output.read_text())
        assert actual_data['media_count'] >= 1
        actual_identities = [m['identity'] for m in actual_data['media']]
        assert 'empty' in actual_identities
