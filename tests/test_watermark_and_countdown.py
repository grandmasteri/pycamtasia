"""Tests for Project.add_watermark() and Project.add_countdown()."""
from __future__ import annotations

from pathlib import Path

import pytest

from camtasia.timeline.clips import BaseClip

FIXTURES = Path(__file__).parent / 'fixtures'
TEST_WAV = FIXTURES / 'empty.wav'


# ── add_watermark ──────────────────────────────────────────────────


class TestAddWatermarkReturn:
    def test_returns_base_clip(self, project):
        actual_clip = project.add_watermark(TEST_WAV)
        assert isinstance(actual_clip, BaseClip)


class TestAddWatermarkOpacity:
    def test_default_opacity(self, project):
        actual_clip = project.add_watermark(TEST_WAV)
        assert actual_clip.opacity == 0.3

    def test_custom_opacity(self, project):
        actual_clip = project.add_watermark(TEST_WAV, opacity=0.5)
        assert actual_clip.opacity == 0.5


class TestAddWatermarkTrack:
    def test_default_track_name(self, project):
        project.add_watermark(TEST_WAV)
        track = project.timeline.find_track_by_name('Watermark')
        assert track is not None
        assert len(track) == 1

    def test_custom_track_name(self, project):
        project.add_watermark(TEST_WAV, track_name='Logo')
        track = project.timeline.find_track_by_name('Logo')
        assert track is not None
        assert len(track) == 1


class TestAddWatermarkDuration:
    def test_empty_project_uses_fallback(self, project):
        assert project.duration_seconds == 0
        actual_clip = project.add_watermark(TEST_WAV)
        assert actual_clip.duration_seconds > 0

    def test_clip_starts_at_zero(self, project):
        actual_clip = project.add_watermark(TEST_WAV)
        assert actual_clip.start == 0


class TestAddWatermarkMedia:
    def test_media_imported(self, project):
        before = project.media_count
        project.add_watermark(TEST_WAV)
        assert project.media_count == before + 1


class TestAddWatermarkStringPath:
    def test_string_path_accepted(self, project):
        actual_clip = project.add_watermark(str(TEST_WAV))
        assert isinstance(actual_clip, BaseClip)


# ── add_countdown ──────────────────────────────────────────────────


class TestAddCountdownReturn:
    def test_returns_list(self, project):
        actual_result = project.add_countdown()
        assert isinstance(actual_result, list)

    def test_default_returns_three_clips(self, project):
        actual_result = project.add_countdown()
        assert [c.text for c in actual_result] == ['3', '2', '1']

    def test_all_are_base_clips(self, project):
        for clip in project.add_countdown():
            assert isinstance(clip, BaseClip)


class TestAddCountdownText:
    def test_text_is_descending(self, project):
        clips = project.add_countdown(seconds=3)
        assert [c.text for c in clips] == ['3', '2', '1']

    def test_custom_seconds(self, project):
        clips = project.add_countdown(seconds=5)
        assert [c.text for c in clips] == ['5', '4', '3', '2', '1']


class TestAddCountdownTrack:
    def test_default_track_name(self, project):
        project.add_countdown()
        track = project.timeline.find_track_by_name('Countdown')
        assert track is not None
        assert len(track) == 3

    def test_custom_track_name(self, project):
        project.add_countdown(track_name='Timer')
        track = project.timeline.find_track_by_name('Timer')
        assert track is not None


class TestAddCountdownTiming:
    def test_clips_are_sequential(self, project):
        clips = project.add_countdown(seconds=3, per_number_seconds=1.0)
        starts = [c.start_seconds for c in clips]
        assert starts[0] < starts[1] < starts[2]

    def test_first_clip_starts_at_zero(self, project):
        clips = project.add_countdown()
        assert clips[0].start_seconds == pytest.approx(0.0, abs=0.01)

    def test_custom_per_number_seconds(self, project):
        clips = project.add_countdown(seconds=2, per_number_seconds=2.0)
        assert clips[1].start_seconds == pytest.approx(2.0, abs=0.01)


class TestAddCountdownFontSize:
    def test_font_size_is_96(self, project):
        clips = project.add_countdown()
        assert clips[0].font['size'] == 96.0


class TestAddCountdownFades:
    def test_fades_applied(self, project):
        clips = project.add_countdown()
        for clip in clips:
            assert clip._data.get('parameters', {}).get('opacity') is not None
