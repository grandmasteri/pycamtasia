"""Tests for Project.add_background_music()."""
from __future__ import annotations

from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / 'fixtures'
EMPTY_WAV = FIXTURES / 'empty.wav'


@pytest.mark.parametrize("path", [EMPTY_WAV, str(EMPTY_WAV)], ids=["Path", "str"])
def test_returns_base_clip(project, path):
    clip = project.add_background_music(path)
    assert clip.start == 0
    assert clip.volume == 0.3


def test_custom_volume(project):
    clip = project.add_background_music(EMPTY_WAV, volume=0.5)
    assert clip.volume == 0.5


def test_default_track_name(project):
    project.add_background_music(EMPTY_WAV)
    track = project.timeline.get_or_create_track('Background Music')
    clips = list(track.clips)
    assert len(clips) == 1
    assert clips[0].volume == 0.3


def test_custom_track_name(project):
    project.add_background_music(EMPTY_WAV, track_name='BGM')
    track = project.timeline.get_or_create_track('BGM')
    clips = list(track.clips)
    assert len(clips) == 1
    assert clips[0].start == 0


def test_empty_project_uses_fallback_duration(project):
    assert project.duration_seconds == 0
    clip = project.add_background_music(EMPTY_WAV)
    assert clip.duration_seconds == pytest.approx(60.0)


def test_no_fade_in(project):
    clip = project.add_background_music(EMPTY_WAV, fade_in_seconds=0)
    # Only fade-out should be present (default 3.0s)
    assert clip.volume == 0.3


def test_no_fade_out(project):
    clip = project.add_background_music(EMPTY_WAV, fade_out_seconds=0)
    # Only fade-in should be present (default 2.0s)
    assert clip.volume == 0.3


def test_no_fades(project):
    clip = project.add_background_music(EMPTY_WAV, fade_in_seconds=0, fade_out_seconds=0)
    assert 'opacity' not in clip._data.get('parameters', {})


def test_media_imported_to_bin(project):
    before = project.media_count
    project.add_background_music(EMPTY_WAV)
    assert project.media_count == before + 1


def test_custom_fade_values(project):
    clip = project.add_background_music(EMPTY_WAV, fade_in_seconds=1.0, fade_out_seconds=5.0)
    volume = clip._data.get('parameters', {}).get('volume')
    assert isinstance(volume, dict)
    assert len(volume['keyframes']) >= 2
