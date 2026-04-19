"""Tests for Project.summary(), Project.__repr__, and Project.__str__."""
from __future__ import annotations

import pytest


class TestSummary:
    def test_contains_title(self, project):
        project.title = 'My Video'
        text = project.summary()
        assert 'Project: My Video' in text

    @pytest.mark.parametrize("substring_fn", [
        lambda p: f'Duration: {p.total_duration_formatted}',
        lambda p: f'Resolution: {p.width}x{p.height}',
        lambda p: f'Tracks: {p.track_count}',
        lambda p: f'Clips: {p.clip_count}',
        lambda p: f'Groups: {p.group_count}',
    ])
    def test_contains_field(self, project, substring_fn):
        assert substring_fn(project) in project.summary()

    def test_media_files_shown_when_bin_nonempty(self, project):
        # Add a media entry so the bin is non-empty
        project._data.setdefault('sourceBin', []).append({
            'id': 999, 'src': './media/test.png', 'rect': [0, 0, 100, 100],
            'lastMod': '20260101T000000',
            'sourceTracks': [{'range': [0, 1], 'type': 2, 'editRate': 1,
                              'trackRect': [0, 0, 100, 100], 'sampleRate': 0,
                              'bitDepth': 0, 'numChannels': 0,
                              'integratedLUFS': 100.0, 'peakLevel': -1.0}],
        })
        text = project.summary()
        assert 'Media files:' in text

    def test_media_files_absent_when_bin_empty(self, project):
        project._data['sourceBin'] = []
        text = project.summary()
        assert 'Media files:' not in text

    def test_validation_clean_when_no_issues(self, project):
        project._data['sourceBin'] = []
        text = project.summary()
        assert 'Validation: clean' in text

    def test_validation_issues_shown(self, project):
        # Inject a broken source bin entry to trigger validation issues
        project._data.setdefault('sourceBin', []).append({
            'id': 888, 'src': './media/missing.wav', 'rect': [0, 0, 0, 0],
            'lastMod': '20260101T000000',
            'sourceTracks': [{'range': [0, 0], 'type': 1, 'editRate': 44100,
                              'trackRect': [0, 0, 0, 0], 'sampleRate': 44100,
                              'bitDepth': 16, 'numChannels': 2,
                              'integratedLUFS': 100.0, 'peakLevel': -1.0}],
        })
        text = project.summary()
        assert 'Validation issues:' in text

    def test_is_multiline(self, project):
        text = project.summary()
        lines = text.strip().split('\n')
        assert lines[0].startswith('Project:')
        assert lines[-1] == 'Validation: clean'

    def test_returns_string(self, project):
        assert 'Project:' in project.summary()


class TestRepr:
    def test_repr_is_one_liner(self, project):
        r = repr(project)
        assert '\n' not in r

    @pytest.mark.parametrize("substring_fn", [
        lambda p: f'{p.width}x{p.height}',
        lambda p: f'tracks={p.track_count}',
        lambda p: f'clips={p.clip_count}',
    ])
    def test_repr_contains_field(self, project, substring_fn):
        assert substring_fn(project) in repr(project)

    def test_repr_contains_title(self, project):
        project.title = 'Demo'
        r = repr(project)
        assert "'Demo'" in r

    def test_repr_starts_with_angle_bracket(self, project):
        assert repr(project).startswith('<Project ')

    def test_repr_ends_with_angle_bracket(self, project):
        assert repr(project).endswith('>')


class TestStr:
    @pytest.mark.parametrize("substring_fn", [
        lambda p: p.total_duration_formatted,
        lambda p: f'{p.track_count} tracks',
        lambda p: f'{p.clip_count} clips',
    ])
    def test_str_contains_field(self, project, substring_fn):
        assert substring_fn(project) in str(project)

    def test_str_contains_title(self, project):
        project.title = 'Demo'
        assert 'Demo' in str(project)

    def test_str_is_one_liner(self, project):
        assert '\n' not in str(project)
