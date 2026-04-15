"""Tests for Project.add_background_music()."""
from __future__ import annotations

from pathlib import Path

from camtasia.project import load_project
from camtasia.timeline.clips import BaseClip

RESOURCES = Path(__file__).parent.parent / 'src' / 'camtasia' / 'resources'
FIXTURES = Path(__file__).parent / 'fixtures'
EMPTY_WAV = FIXTURES / 'empty.wav'


def _make_project():
    return load_project(RESOURCES / 'new.cmproj')


def test_returns_base_clip():
    proj = _make_project()
    clip = proj.add_background_music(EMPTY_WAV)
    assert isinstance(clip, BaseClip)


def test_default_volume():
    proj = _make_project()
    clip = proj.add_background_music(EMPTY_WAV)
    assert clip.volume == 0.3


def test_custom_volume():
    proj = _make_project()
    clip = proj.add_background_music(EMPTY_WAV, volume=0.5)
    assert clip.volume == 0.5


def test_default_track_name():
    proj = _make_project()
    proj.add_background_music(EMPTY_WAV)
    track = proj.timeline.get_or_create_track('Background Music')
    assert len(list(track.clips)) == 1


def test_custom_track_name():
    proj = _make_project()
    proj.add_background_music(EMPTY_WAV, track_name='BGM')
    track = proj.timeline.get_or_create_track('BGM')
    assert len(list(track.clips)) == 1


def test_clip_starts_at_zero():
    proj = _make_project()
    clip = proj.add_background_music(EMPTY_WAV)
    assert clip.start == 0


def test_empty_project_uses_fallback_duration():
    proj = _make_project()
    assert proj.duration_seconds == 0
    clip = proj.add_background_music(EMPTY_WAV)
    assert clip.duration_seconds > 0


def test_string_path_accepted():
    proj = _make_project()
    clip = proj.add_background_music(str(EMPTY_WAV))
    assert isinstance(clip, BaseClip)


def test_no_fade_in():
    proj = _make_project()
    # Should not raise when fade_in_seconds=0
    clip = proj.add_background_music(EMPTY_WAV, fade_in_seconds=0)
    assert isinstance(clip, BaseClip)


def test_no_fade_out():
    proj = _make_project()
    # Should not raise when fade_out_seconds=0
    clip = proj.add_background_music(EMPTY_WAV, fade_out_seconds=0)
    assert isinstance(clip, BaseClip)


def test_no_fades():
    proj = _make_project()
    clip = proj.add_background_music(EMPTY_WAV, fade_in_seconds=0, fade_out_seconds=0)
    assert isinstance(clip, BaseClip)


def test_media_imported_to_bin():
    proj = _make_project()
    before = proj.media_count
    proj.add_background_music(EMPTY_WAV)
    assert proj.media_count == before + 1


def test_custom_fade_values():
    proj = _make_project()
    clip = proj.add_background_music(EMPTY_WAV, fade_in_seconds=1.0, fade_out_seconds=5.0)
    assert isinstance(clip, BaseClip)
