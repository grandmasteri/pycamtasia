"""Tests for REV-resources-001 and REV-resources-002 in app_validation.py."""
from __future__ import annotations

from unittest.mock import MagicMock, mock_open, patch

import pytest

from camtasia.app_validation import camtasia_validate


@pytest.fixture
def fake_project(tmp_path):
    proj = tmp_path / 'demo.cmproj'
    proj.mkdir()
    return proj


class TestPopenLifecycle:
    """REV-resources-001: Popen must be stored and properly terminated."""

    def test_popen_terminate_and_wait_called(self, fake_project):
        mock_proc = MagicMock()
        mock_proc.wait.return_value = 0

        with (
            patch('camtasia.app_validation.subprocess') as mock_sub,
            patch('camtasia.app_validation.time'),
            patch('camtasia.app_validation.tempfile.NamedTemporaryFile'),
            patch('camtasia.app_validation.Path.read_text', return_value='clean\n'),
            patch('builtins.open', mock_open()),
        ):
            mock_sub.Popen.return_value = mock_proc
            camtasia_validate(fake_project)

        mock_proc.terminate.assert_called_once()
        mock_proc.wait.assert_called_once()


class TestTempLogCleanup:
    """REV-resources-002: Temp log file must be cleaned up after use."""

    def test_temp_log_file_deleted(self, fake_project, tmp_path):
        log_file = tmp_path / 'test.log'
        log_file.write_text('')

        mock_ntf = MagicMock()
        mock_ntf.__enter__ = MagicMock(return_value=mock_ntf)
        mock_ntf.__exit__ = MagicMock(return_value=False)
        mock_ntf.name = str(log_file)

        mock_proc = MagicMock()
        mock_proc.wait.return_value = 0

        with (
            patch('camtasia.app_validation.subprocess') as mock_sub,
            patch('camtasia.app_validation.time'),
            patch('camtasia.app_validation.tempfile.NamedTemporaryFile', return_value=mock_ntf),
            patch('builtins.open', mock_open()),
        ):
            mock_sub.Popen.return_value = mock_proc
            camtasia_validate(fake_project)

        assert not log_file.exists(), 'temp log file should be cleaned up'
