"""Tests for camtasia.app_validation — Camtasia open-in-app integration harness."""
from __future__ import annotations

from unittest.mock import MagicMock, call, mock_open, patch

import pytest

from camtasia.app_validation import camtasia_validate
from camtasia.timing import seconds_to_ticks as _s2t
from camtasia.validation import (
    _check_edit_rate,
    _check_source_bin_ids,
    _get_tracks,
    validate_all,
)


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


_S1_VAL = _s2t(1.0)
_S10_VAL = _s2t(10.0)


class TestValidationEdgeCases:
    def test_get_tracks_empty_scenes(self):
        assert _get_tracks({'timeline': {'sceneTrack': {'scenes': []}}}) == []

    def test_check_edit_rate_missing(self):
        issues = _check_edit_rate({})
        assert any('missing' in str(i) for i in issues)

    def test_check_edit_rate_wrong(self):
        issues = _check_edit_rate({'editRate': 12345})
        assert any('expected' in str(i) for i in issues)

    def test_duplicate_source_bin_ids(self):
        issues = _check_source_bin_ids({'sourceBin': [{'id': 1, 'src': 'a'}, {'id': 1, 'src': 'b'}]})
        assert any('Duplicate' in str(i) for i in issues)

    def test_validate_all_negative_start(self):
        data = {
            'version': '9.0',
            'editRate': 705600000,
            'sourceBin': [],
            'timeline': {
                'sceneTrack': {
                    'scenes': [{
                        'csml': {
                            'tracks': [{
                                'trackIndex': 0,
                                'medias': [{
                                    '_type': 'VMFile', 'id': 1, 'start': -100, 'duration': _S1_VAL,
                                    'mediaDuration': _S1_VAL, 'mediaStart': 0, 'scalar': 1,
                                    'parameters': {}, 'effects': [], 'metadata': {},
                                }],
                            }],
                        }
                    }]
                },
                'parameters': {},
                'trackAttributes': [{}],
            },
        }
        issues = validate_all(data)
        assert any('negative start' in str(i) for i in issues)

    def test_validate_all_zero_duration(self):
        data = {
            'version': '9.0',
            'editRate': 705600000,
            'sourceBin': [],
            'timeline': {
                'sceneTrack': {
                    'scenes': [{
                        'csml': {
                            'tracks': [{
                                'trackIndex': 0,
                                'medias': [{
                                    '_type': 'VMFile', 'id': 1, 'start': 0, 'duration': 0,
                                    'mediaDuration': 0, 'mediaStart': 0, 'scalar': 1,
                                    'parameters': {}, 'effects': [], 'metadata': {},
                                }],
                            }],
                        }
                    }]
                },
                'parameters': {},
                'trackAttributes': [{}],
            },
        }
        issues = validate_all(data)
        assert any('duration' in str(i).lower() for i in issues)

    def test_validate_all_scalar_mismatch(self):
        data = {
            'version': '9.0',
            'editRate': 705600000,
            'sourceBin': [],
            'timeline': {
                'sceneTrack': {
                    'scenes': [{
                        'csml': {
                            'tracks': [{
                                'trackIndex': 0,
                                'medias': [{
                                    '_type': 'VMFile', 'id': 1, 'start': 0, 'duration': _S10_VAL,
                                    'mediaDuration': 99999, 'mediaStart': 0, 'scalar': '1/2',
                                    'parameters': {}, 'effects': [], 'metadata': {},
                                }],
                            }],
                        }
                    }]
                },
                'parameters': {},
                'trackAttributes': [{}],
            },
        }
        issues = validate_all(data)
        assert any('mediaDuration' in str(i) or 'scalar' in str(i) for i in issues)

    def test_validate_all_group_missing_metadata(self):
        data = {
            'version': '9.0',
            'editRate': 705600000,
            'sourceBin': [],
            'timeline': {
                'sceneTrack': {
                    'scenes': [{
                        'csml': {
                            'tracks': [{
                                'trackIndex': 0,
                                'medias': [{
                                    '_type': 'Group', 'id': 1, 'start': 0, 'duration': _S10_VAL,
                                    'mediaDuration': _S10_VAL, 'mediaStart': 0, 'scalar': 1,
                                    'parameters': {}, 'effects': [],
                                    'tracks': [{'trackIndex': 0, 'medias': []}],
                                }],
                            }],
                        }
                    }]
                },
                'parameters': {},
                'trackAttributes': [{}],
            },
        }
        issues = validate_all(data)
        assert any('metadata' in str(i) for i in issues)
