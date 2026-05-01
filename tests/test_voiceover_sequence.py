"""Tests for Project.add_voiceover_sequence()."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch
import warnings

import pytest

from camtasia.timeline.clips import AMFile

FIXTURES = Path(__file__).parent / 'fixtures'
EMPTY_WAV = FIXTURES / 'empty.wav'
EMPTY2_WAV = FIXTURES / 'empty2.wav'


def test_single_file(project):
    actual_result = project.add_voiceover_sequence([EMPTY_WAV])
    assert 'empty.wav' in actual_result
    entry = actual_result['empty.wav']
    assert entry['start'] == 0.0
    assert entry['duration'] == pytest.approx(60.0)
    assert isinstance(entry['clip'], AMFile)


def test_multiple_files(project):
    actual_result = project.add_voiceover_sequence([EMPTY_WAV, EMPTY2_WAV])
    assert set(actual_result.keys()) == {'empty.wav', 'empty2.wav'}
    assert actual_result['empty2.wav']['start'] == actual_result['empty.wav']['duration']


def test_pauses(project):
    actual_result = project.add_voiceover_sequence(
        [EMPTY_WAV, EMPTY2_WAV],
        pauses={'empty.wav': 2.0},
    )
    assert actual_result['empty2.wav']['start'] == actual_result['empty.wav']['duration'] + 2.0


def test_custom_track_name(project):
    project.add_voiceover_sequence([EMPTY_WAV], track_name='VO Track')
    track = project.timeline.get_or_create_track('VO Track')
    clips = list(track.clips)
    assert [type(c).__name__ for c in clips] == ['AMFile']


def test_default_track_name(project):
    project.add_voiceover_sequence([EMPTY_WAV])
    track = project.timeline.get_or_create_track('Audio')
    clips = list(track.clips)
    assert [type(c).__name__ for c in clips] == ['AMFile']


def test_empty_list(project):
    actual_result = project.add_voiceover_sequence([])
    assert actual_result == {}


def test_no_pauses_default(project):
    actual_result = project.add_voiceover_sequence([EMPTY_WAV, EMPTY2_WAV])
    assert actual_result['empty2.wav']['start'] == actual_result['empty.wav']['duration']


def test_string_paths(project):
    actual_result = project.add_voiceover_sequence([str(EMPTY_WAV)])
    assert 'empty.wav' in actual_result

def test_voiceover_warns_when_probe_returns_no_duration(project):
    """Bug 3: add_voiceover_sequence should warn when duration cannot be probed."""
    def _probe_no_duration(path):
        return {}

    with patch("camtasia.project._probe_media", _probe_no_duration), warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = project.add_voiceover_sequence([EMPTY_WAV])
        assert len(w) == 1
        assert 'Could not probe duration' in str(w[0].message)
        assert result['empty.wav']['duration'] == 1.0
