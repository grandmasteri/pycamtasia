"""Tests for Project.add_watermark() and Project.add_countdown()."""
from __future__ import annotations

from pathlib import Path

import pytest

from camtasia.project import load_project
from camtasia.timeline.clips import BaseClip

RESOURCES = Path(__file__).parent.parent / 'src' / 'camtasia' / 'resources'
FIXTURES = Path(__file__).parent / 'fixtures'
TEST_WAV = FIXTURES / 'empty.wav'



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


# ── add_watermark ──────────────────────────────────────────────────


class TestAddWatermarkReturn:
    def test_returns_base_clip(self):
        clip = _make_project().add_watermark(TEST_WAV)
        assert isinstance(clip, BaseClip)


class TestAddWatermarkOpacity:
    def test_default_opacity(self):
        clip = _make_project().add_watermark(TEST_WAV)
        assert clip.opacity == 0.3

    def test_custom_opacity(self):
        clip = _make_project().add_watermark(TEST_WAV, opacity=0.5)
        assert clip.opacity == 0.5


class TestAddWatermarkTrack:
    def test_default_track_name(self):
        proj = _make_project()
        proj.add_watermark(TEST_WAV)
        track = proj.timeline.find_track_by_name('Watermark')
        assert track is not None
        assert len(track) == 1

    def test_custom_track_name(self):
        proj = _make_project()
        proj.add_watermark(TEST_WAV, track_name='Logo')
        track = proj.timeline.find_track_by_name('Logo')
        assert track is not None
        assert len(track) == 1


class TestAddWatermarkDuration:
    def test_empty_project_uses_fallback(self):
        proj = _make_project()
        assert proj.duration_seconds == 0
        clip = proj.add_watermark(TEST_WAV)
        assert clip.duration_seconds > 0

    def test_clip_starts_at_zero(self):
        clip = _make_project().add_watermark(TEST_WAV)
        assert clip.start == 0


class TestAddWatermarkMedia:
    def test_media_imported(self):
        proj = _make_project()
        before = proj.media_count
        proj.add_watermark(TEST_WAV)
        assert proj.media_count == before + 1


class TestAddWatermarkStringPath:
    def test_string_path_accepted(self):
        clip = _make_project().add_watermark(str(TEST_WAV))
        assert isinstance(clip, BaseClip)


# ── add_countdown ──────────────────────────────────────────────────


class TestAddCountdownReturn:
    def test_returns_list(self):
        result = _make_project().add_countdown()
        assert isinstance(result, list)

    def test_default_returns_three_clips(self):
        result = _make_project().add_countdown()
        assert len(result) == 3

    def test_all_are_base_clips(self):
        for clip in _make_project().add_countdown():
            assert isinstance(clip, BaseClip)


class TestAddCountdownText:
    def test_text_is_descending(self):
        clips = _make_project().add_countdown(seconds=3)
        assert [c.text for c in clips] == ['3', '2', '1']

    def test_custom_seconds(self):
        clips = _make_project().add_countdown(seconds=5)
        assert len(clips) == 5
        assert clips[0].text == '5'
        assert clips[-1].text == '1'


class TestAddCountdownTrack:
    def test_default_track_name(self):
        proj = _make_project()
        proj.add_countdown()
        track = proj.timeline.find_track_by_name('Countdown')
        assert track is not None
        assert len(track) == 3

    def test_custom_track_name(self):
        proj = _make_project()
        proj.add_countdown(track_name='Timer')
        track = proj.timeline.find_track_by_name('Timer')
        assert track is not None


class TestAddCountdownTiming:
    def test_clips_are_sequential(self):
        clips = _make_project().add_countdown(seconds=3, per_number_seconds=1.0)
        starts = [c.start_seconds for c in clips]
        assert starts[0] < starts[1] < starts[2]

    def test_first_clip_starts_at_zero(self):
        clips = _make_project().add_countdown()
        assert clips[0].start_seconds == pytest.approx(0.0, abs=0.01)

    def test_custom_per_number_seconds(self):
        clips = _make_project().add_countdown(seconds=2, per_number_seconds=2.0)
        assert clips[1].start_seconds == pytest.approx(2.0, abs=0.01)


class TestAddCountdownFontSize:
    def test_font_size_is_96(self):
        clips = _make_project().add_countdown()
        assert clips[0].font['size'] == 96.0


class TestAddCountdownFades:
    def test_fades_applied(self):
        clips = _make_project().add_countdown()
        # fade_in/fade_out set opacity keyframes
        for clip in clips:
            assert clip._data.get('parameters', {}).get('opacity') is not None
