"""Tests for Project.import_and_convert_audio and convert_audio_to_wav."""
from __future__ import annotations

from pathlib import Path
import subprocess
from unittest.mock import MagicMock, patch


class TestImportAndConvertAudio:
    """Tests for the combined convert + import convenience method."""

    def test_skips_conversion_for_pcm_wav(self, project):
        """Already-PCM files should be imported directly without conversion."""
        mock_result = MagicMock(stdout='pcm_s16le\n', returncode=0)
        with patch('subprocess.run', return_value=mock_result), \
             patch.object(project, 'import_media', return_value='imported') as mock_import, \
             patch.object(project, 'convert_audio_to_wav') as mock_convert:
            result = project.import_and_convert_audio('/tmp/voice.wav')

        assert result == 'imported'
        mock_import.assert_called_once_with(Path('/tmp/voice.wav'))
        mock_convert.assert_not_called()

    def test_converts_non_pcm_audio(self, project):
        """Non-PCM audio (e.g. MP3) should be converted then imported."""
        mock_probe = MagicMock(stdout='mp3\n', returncode=0)
        wav_path = Path('/tmp/voice.wav')
        with patch('subprocess.run', return_value=mock_probe), \
             patch.object(project, 'convert_audio_to_wav', return_value=wav_path) as mock_convert, \
             patch.object(project, 'import_media', return_value='imported') as mock_import:
            result = project.import_and_convert_audio('/tmp/voice.mp3', sample_rate=44100)

        assert result == 'imported'
        mock_convert.assert_called_once_with(Path('/tmp/voice.mp3'), sample_rate=44100)
        mock_import.assert_called_once_with(wav_path)

    def test_converts_when_ffprobe_not_found(self, project):
        """When ffprobe is missing, should convert anyway."""
        wav_path = Path('/tmp/voice.wav')
        with patch('subprocess.run', side_effect=FileNotFoundError), \
             patch.object(project, 'convert_audio_to_wav', return_value=wav_path) as mock_convert, \
             patch.object(project, 'import_media', return_value='imported') as mock_import:
            result = project.import_and_convert_audio('/tmp/voice.mp3')

        assert result == 'imported'
        mock_convert.assert_called_once()
        mock_import.assert_called_once_with(wav_path)

    def test_converts_when_ffprobe_fails(self, project):
        """When ffprobe returns non-zero, should convert anyway."""
        with patch('subprocess.run', side_effect=subprocess.CalledProcessError(1, 'ffprobe')), \
             patch.object(project, 'convert_audio_to_wav', return_value=Path('/tmp/x.wav')) as mock_convert, \
             patch.object(project, 'import_media', return_value='imported'):
            result = project.import_and_convert_audio('/tmp/voice.m4a')

        assert result == 'imported'
        mock_convert.assert_called_once()

    def test_default_sample_rate(self, project):
        """Default sample_rate should be 48000."""
        mock_probe = MagicMock(stdout='aac\n', returncode=0)
        with patch('subprocess.run', return_value=mock_probe), \
             patch.object(project, 'convert_audio_to_wav', return_value=Path('/tmp/x.wav')) as mock_convert, \
             patch.object(project, 'import_media', return_value='imported'):
            project.import_and_convert_audio('/tmp/voice.m4a')

        mock_convert.assert_called_once_with(Path('/tmp/voice.m4a'), sample_rate=48000)
