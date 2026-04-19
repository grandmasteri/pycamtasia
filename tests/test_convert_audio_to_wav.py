"""Tests for Project.convert_audio_to_wav static method."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from camtasia.project import Project


@patch('subprocess.run')
def test_default_output_replaces_extension(mock_run):
    result = Project.convert_audio_to_wav('/tmp/voice.mp3')
    assert result == Path('/tmp/voice.wav')
    mock_run.assert_called_once_with(
        ['ffmpeg', '-y', '-i', '/tmp/voice.mp3', '-acodec', 'pcm_s16le',
         '-ar', '48000', '/tmp/voice.wav'],
        capture_output=True, check=True,
    )


@patch('subprocess.run')
def test_explicit_output_path(mock_run):
    result = Project.convert_audio_to_wav('/tmp/voice.mp3', '/out/converted.wav')
    assert result == Path('/out/converted.wav')
    assert mock_run.call_args[0][0][-1] == '/out/converted.wav'


@patch('subprocess.run')
def test_custom_sample_rate(mock_run):
    Project.convert_audio_to_wav('/tmp/voice.mp3', sample_rate=44100)
    assert mock_run.call_args[0][0][7] == '44100'


@patch('subprocess.run')
def test_accepts_path_objects(mock_run):
    result = Project.convert_audio_to_wav(Path('/tmp/voice.mp3'), Path('/tmp/out.wav'))
    assert result == Path('/tmp/out.wav')
    mock_run.assert_called_once()


@patch('subprocess.run', side_effect=FileNotFoundError('ffmpeg not found'))
def test_raises_when_ffmpeg_missing(mock_run):
    with pytest.raises(FileNotFoundError):
        Project.convert_audio_to_wav('/tmp/voice.mp3')


@patch('subprocess.run')
def test_called_as_static_method(mock_run):
    """Can be called without a Project instance."""
    result = Project.convert_audio_to_wav('/tmp/a.aac')
    assert result == Path('/tmp/a.wav')
