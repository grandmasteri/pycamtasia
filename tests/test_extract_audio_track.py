"""Tests for Project.extract_audio_track()."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def project():
    from camtasia.project import load_project
    resources = Path(__file__).parent.parent / 'src' / 'camtasia' / 'resources'
    return load_project(resources / 'new.cmproj')


@pytest.fixture
def project_with_audio(project):
    """Project with audio clips on two tracks backed by media bin entries."""
    # Add two media bin entries
    project._data.setdefault('sourceBin', []).extend([
        {'id': 100, 'src': 'media/narration.wav', 'rect': [0, 0, 0, 0],
         'sourceTracks': [{'range': [0, 44100], 'type': 2, 'editRate': 44100,
                           'trackRect': [0, 0, 0, 0], 'sampleRate': 44100,
                           'bitDepth': 16, 'numChannels': 1}]},
        {'id': 200, 'src': 'media/music.mp3', 'rect': [0, 0, 0, 0],
         'sourceTracks': [{'range': [0, 44100], 'type': 2, 'editRate': 44100,
                           'trackRect': [0, 0, 0, 0], 'sampleRate': 44100,
                           'bitDepth': 16, 'numChannels': 2}]},
    ])
    # Place audio clips on tracks
    t1 = project.timeline.add_track('VO')
    t1.add_audio(100, start_seconds=0, duration_seconds=1)
    t2 = project.timeline.add_track('Music')
    t2.add_audio(200, start_seconds=0, duration_seconds=1)
    return project


class TestExtractAudioTrack:
    def test_returns_path(self, project_with_audio, tmp_path):
        out = tmp_path / 'audio.txt'
        result = project_with_audio.extract_audio_track(out)
        assert isinstance(result, Path)
        assert result == out

    def test_file_is_created(self, project_with_audio, tmp_path):
        out = tmp_path / 'audio.txt'
        project_with_audio.extract_audio_track(out)
        assert out.exists()

    def test_all_tracks_lists_all_audio(self, project_with_audio, tmp_path):
        out = tmp_path / 'audio.txt'
        project_with_audio.extract_audio_track(out)
        lines = out.read_text().splitlines()
        assert len(lines) == 2
        assert 'media/narration.wav' in lines[0]
        assert 'media/music.mp3' in lines[1]

    def test_filter_by_track_name(self, project_with_audio, tmp_path):
        out = tmp_path / 'audio.txt'
        project_with_audio.extract_audio_track(out, track_name='VO')
        lines = out.read_text().splitlines()
        assert len(lines) == 1
        assert 'narration.wav' in lines[0]

    def test_filter_nonexistent_track_produces_empty(self, project_with_audio, tmp_path):
        out = tmp_path / 'audio.txt'
        project_with_audio.extract_audio_track(out, track_name='NoSuchTrack')
        assert out.read_text() == ''

    def test_empty_project_produces_empty_file(self, project, tmp_path):
        out = tmp_path / 'audio.txt'
        project.extract_audio_track(out)
        assert out.read_text() == ''

    def test_accepts_string_path(self, project_with_audio, tmp_path):
        out = str(tmp_path / 'audio.txt')
        result = project_with_audio.extract_audio_track(out)
        assert result.exists()

    def test_non_audio_clips_excluded(self, project, tmp_path):
        """Video clips should not appear in the output."""
        project._data.setdefault('sourceBin', []).append(
            {'id': 300, 'src': 'media/video.mp4', 'rect': [0, 0, 1920, 1080],
             'sourceTracks': [{'range': [0, 900], 'type': 0, 'editRate': 30,
                               'trackRect': [0, 0, 1920, 1080], 'sampleRate': 30,
                               'bitDepth': 32, 'numChannels': 0}]},
        )
        track = project.timeline.add_track('Video')
        track.add_video(300, start_seconds=0, duration_seconds=1)
        out = tmp_path / 'audio.txt'
        project.extract_audio_track(out)
        assert out.read_text() == ''
