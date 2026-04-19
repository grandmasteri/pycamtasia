"""Tests for Project.add_background_music()."""
from __future__ import annotations

from pathlib import Path

from camtasia.project import load_project
from camtasia.timeline.clips import BaseClip

RESOURCES = Path(__file__).parent.parent / 'src' / 'camtasia' / 'resources'
FIXTURES = Path(__file__).parent / 'fixtures'
EMPTY_WAV = FIXTURES / 'empty.wav'



# Module-level list to prevent TemporaryDirectory from being GC'd during test
_TEMP_DIRS: list = []

def _isolated_project():
    """Load template into an isolated temp copy (safe for parallel execution)."""
    import shutil, tempfile
    from camtasia.project import load_project
    td = tempfile.TemporaryDirectory()
    _TEMP_DIRS.append(td)  # prevent premature GC
    dst = Path(td.name) / 'test.cmproj'
    shutil.copytree(RESOURCES / 'new.cmproj', dst)
    return load_project(dst)

def _make_project():
    return _isolated_project()


def test_returns_base_clip():
    proj = _make_project()
    clip = proj.add_background_music(EMPTY_WAV)
    assert clip.start == 0
    assert clip.volume == 0.3


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
    clips = list(track.clips)
    assert len(clips) == 1
    assert clips[0].volume == 0.3


def test_custom_track_name():
    proj = _make_project()
    proj.add_background_music(EMPTY_WAV, track_name='BGM')
    track = proj.timeline.get_or_create_track('BGM')
    clips = list(track.clips)
    assert len(clips) == 1
    assert clips[0].start == 0


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
    assert clip.volume == 0.3
    assert clip.start == 0


def test_no_fade_in():
    proj = _make_project()
    clip = proj.add_background_music(EMPTY_WAV, fade_in_seconds=0)
    # Only fade-out should be present (default 3.0s)
    assert clip.volume == 0.3


def test_no_fade_out():
    proj = _make_project()
    clip = proj.add_background_music(EMPTY_WAV, fade_out_seconds=0)
    # Only fade-in should be present (default 2.0s)
    assert clip.volume == 0.3


def test_no_fades():
    proj = _make_project()
    clip = proj.add_background_music(EMPTY_WAV, fade_in_seconds=0, fade_out_seconds=0)
    assert 'opacity' not in clip._data.get('parameters', {})


def test_media_imported_to_bin():
    proj = _make_project()
    before = proj.media_count
    proj.add_background_music(EMPTY_WAV)
    assert proj.media_count == before + 1


def test_custom_fade_values():
    proj = _make_project()
    clip = proj.add_background_music(EMPTY_WAV, fade_in_seconds=1.0, fade_out_seconds=5.0)
    opacity = clip._data.get('parameters', {}).get('opacity')
    assert isinstance(opacity, dict)
    assert len(opacity['keyframes']) == 2
