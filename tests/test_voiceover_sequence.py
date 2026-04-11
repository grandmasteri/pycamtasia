"""Tests for Project.add_voiceover_sequence()."""
from __future__ import annotations

from pathlib import Path

from camtasia.project import load_project
from camtasia.timeline.clips import AMFile

RESOURCES = Path(__file__).parent.parent / 'src' / 'camtasia' / 'resources'
FIXTURES = Path(__file__).parent / 'fixtures'
EMPTY_WAV = FIXTURES / 'empty.wav'
EMPTY2_WAV = FIXTURES / 'empty2.wav'


def _make_project():
    return load_project(RESOURCES / 'new.cmproj')


def test_single_file():
    proj = _make_project()
    result = proj.add_voiceover_sequence([EMPTY_WAV])
    assert 'empty.wav' in result
    entry = result['empty.wav']
    assert entry['start'] == 0.0
    assert entry['duration'] > 0
    assert isinstance(entry['clip'], AMFile)


def test_multiple_files():
    proj = _make_project()
    result = proj.add_voiceover_sequence([EMPTY_WAV, EMPTY2_WAV])
    assert set(result.keys()) == {'empty.wav', 'empty2.wav'}
    # Second clip starts after first clip's duration
    assert result['empty2.wav']['start'] == result['empty.wav']['duration']


def test_pauses():
    proj = _make_project()
    result = proj.add_voiceover_sequence(
        [EMPTY_WAV, EMPTY2_WAV],
        pauses={'empty.wav': 2.0},
    )
    # Second clip starts after first duration + 2s pause
    assert result['empty2.wav']['start'] == result['empty.wav']['duration'] + 2.0


def test_custom_track_name():
    proj = _make_project()
    proj.add_voiceover_sequence([EMPTY_WAV], track_name='VO Track')
    track = proj.timeline.get_or_create_track('VO Track')
    clips = list(track.clips)
    assert [type(c).__name__ for c in clips] == ['AMFile']


def test_default_track_name():
    proj = _make_project()
    proj.add_voiceover_sequence([EMPTY_WAV])
    track = proj.timeline.get_or_create_track('Audio')
    clips = list(track.clips)
    assert [type(c).__name__ for c in clips] == ['AMFile']


def test_empty_list():
    proj = _make_project()
    result = proj.add_voiceover_sequence([])
    assert result == {}


def test_no_pauses_default():
    proj = _make_project()
    result = proj.add_voiceover_sequence([EMPTY_WAV, EMPTY2_WAV])
    # No pause: second starts right after first
    assert result['empty2.wav']['start'] == result['empty.wav']['duration']


def test_string_paths():
    proj = _make_project()
    result = proj.add_voiceover_sequence([str(EMPTY_WAV)])
    assert 'empty.wav' in result
