"""Tests for camtasia.app_validation — Camtasia open-in-app integration harness."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, call, mock_open, patch

import pytest

from camtasia.app_validation import CamtasiaValidationResult, camtasia_validate


@pytest.fixture
def fake_project(tmp_path):
    proj = tmp_path / 'demo.cmproj'
    proj.mkdir()
    return proj


class TestCamtasiaValidateSuccess:
    def test_returns_success_on_clean_log(self, fake_project):
        with (
            patch('camtasia.app_validation.subprocess') as mock_sub,
            patch('camtasia.app_validation.time'),
            patch('camtasia.app_validation.tempfile.NamedTemporaryFile'),
            patch('camtasia.app_validation.Path.read_text', return_value='normal startup output\n'),
            patch('builtins.open', mock_open()),
        ):
            mock_sub.Popen.return_value = MagicMock()
            result = camtasia_validate(fake_project)

        assert result.success is True
        assert result.exception_count == 0
        assert result.project_path == fake_project


class TestCamtasiaValidateWithExceptions:
    def test_detects_exceptions_in_log(self, fake_project):
        log_content = 'line1\nEXCEPTION in module foo\nAbort trap: 6\nEXCEPTION again\n'
        with (
            patch('camtasia.app_validation.subprocess') as mock_sub,
            patch('camtasia.app_validation.time'),
            patch('camtasia.app_validation.tempfile.NamedTemporaryFile'),
            patch('camtasia.app_validation.Path.read_text', return_value=log_content),
            patch('builtins.open', mock_open()),
        ):
            mock_sub.Popen.return_value = MagicMock()
            result = camtasia_validate(fake_project)

        assert result.success is False
        assert result.exception_count == 3  # 2 EXCEPTION + 1 Abort


class TestCamtasiaValidateRemovesAutosave:
    def test_removes_autosave_file(self, tmp_path):
        proj = tmp_path / 'demo.cmproj'
        proj.mkdir()
        autosave = tmp_path / '~demo.cmproj'
        autosave.touch()

        with (
            patch('camtasia.app_validation.subprocess') as mock_sub,
            patch('camtasia.app_validation.time'),
            patch('camtasia.app_validation.tempfile.NamedTemporaryFile'),
            patch('camtasia.app_validation.Path.read_text', return_value=''),
            patch('builtins.open', mock_open()),
        ):
            mock_sub.Popen.return_value = MagicMock()
            camtasia_validate(proj)

        assert not autosave.exists()


class TestCamtasiaValidateKillsExisting:
    def test_calls_pkill_before_launch(self, fake_project):
        with (
            patch('camtasia.app_validation.subprocess') as mock_sub,
            patch('camtasia.app_validation.time'),
            patch('camtasia.app_validation.tempfile.NamedTemporaryFile'),
            patch('camtasia.app_validation.Path.read_text', return_value=''),
            patch('builtins.open', mock_open()),
        ):
            mock_sub.Popen.return_value = MagicMock()
            camtasia_validate(fake_project)

        # First call should be pkill (kill existing), then Popen (launch), then pkill (cleanup)
        first_call = mock_sub.run.call_args_list[0]
        assert first_call == call(['pkill', '-f', 'Camtasia'], stderr=mock_sub.DEVNULL)
        # Popen should come after the first pkill
        mock_sub.Popen.assert_called_once()


class TestCamtasiaValidateCustomTimeout:
    def test_respects_custom_timeout(self, fake_project):
        with (
            patch('camtasia.app_validation.subprocess') as mock_sub,
            patch('camtasia.app_validation.time') as mock_time,
            patch('camtasia.app_validation.tempfile.NamedTemporaryFile'),
            patch('camtasia.app_validation.Path.read_text', return_value=''),
            patch('builtins.open', mock_open()),
        ):
            mock_sub.Popen.return_value = MagicMock()
            camtasia_validate(fake_project, timeout_seconds=30)

        # sleep(2) for initial kill wait, then sleep(30) for the custom timeout
        assert mock_time.sleep.call_args_list == [call(2), call(30)]
