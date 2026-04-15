"""Tests for Project.summary(), Project.__repr__, and Project.__str__."""
from __future__ import annotations


class TestSummary:
    def test_contains_title(self, project):
        project.title = 'My Video'
        text = project.summary()
        assert 'Project: My Video' in text

    def test_contains_duration(self, project):
        text = project.summary()
        assert text.startswith('Project:')
        assert f'Duration: {project.total_duration_formatted}' in text

    def test_contains_resolution(self, project):
        text = project.summary()
        assert f'Resolution: {project.width}x{project.height}' in text

    def test_contains_track_count(self, project):
        text = project.summary()
        assert f'Tracks: {project.track_count}' in text

    def test_contains_clip_count(self, project):
        text = project.summary()
        assert f'Clips: {project.clip_count}' in text

    def test_contains_group_count(self, project):
        text = project.summary()
        assert f'Groups: {project.group_count}' in text

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
        assert len(lines) >= 6

    def test_returns_string(self, project):
        assert isinstance(project.summary(), str)


class TestRepr:
    def test_repr_is_one_liner(self, project):
        r = repr(project)
        assert '\n' not in r

    def test_repr_contains_title(self, project):
        project.title = 'Demo'
        r = repr(project)
        assert "'Demo'" in r

    def test_repr_contains_resolution(self, project):
        r = repr(project)
        assert f'{project.width}x{project.height}' in r

    def test_repr_contains_tracks(self, project):
        r = repr(project)
        assert f'tracks={project.track_count}' in r

    def test_repr_contains_clips(self, project):
        r = repr(project)
        assert f'clips={project.clip_count}' in r

    def test_repr_starts_with_angle_bracket(self, project):
        assert repr(project).startswith('<Project ')

    def test_repr_ends_with_angle_bracket(self, project):
        assert repr(project).endswith('>')


class TestStr:
    def test_str_contains_title(self, project):
        project.title = 'Demo'
        assert 'Demo' in str(project)

    def test_str_contains_duration(self, project):
        assert project.total_duration_formatted in str(project)

    def test_str_contains_track_count(self, project):
        assert f'{project.track_count} tracks' in str(project)

    def test_str_contains_clip_count(self, project):
        assert f'{project.clip_count} clips' in str(project)

    def test_str_is_one_liner(self, project):
        assert '\n' not in str(project)
