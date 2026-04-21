"""Tests for Project.add_title_card and Project.add_subtitle_track."""
from __future__ import annotations

import pytest

from camtasia.timeline.clips import BaseClip
from camtasia.timing import ticks_to_seconds

# ── add_title_card ──────────────────────────────────────────────────


class TestAddTitleCard:
    def test_returns_base_clip(self, project):
        result = project.add_title_card('Hello')
        assert isinstance(result, BaseClip)

    def test_creates_track_with_default_name(self, project):
        project.add_title_card('Hello')
        track = project.timeline.find_track_by_name('Titles')
        assert track is not None

    def test_creates_track_with_custom_name(self, project):
        project.add_title_card('Hello', track_name='MyTitles')
        track = project.timeline.find_track_by_name('MyTitles')
        assert track is not None

    def test_default_duration(self, project):
        clip = project.add_title_card('Hello')
        assert ticks_to_seconds(clip.duration) == pytest.approx(5.0)

    def test_custom_duration(self, project):
        clip = project.add_title_card('Hello', duration_seconds=10.0)
        assert ticks_to_seconds(clip.duration) == pytest.approx(10.0)

    def test_custom_start(self, project):
        clip = project.add_title_card('Hello', start_seconds=3.0)
        assert ticks_to_seconds(clip.start) == pytest.approx(3.0)

    def test_no_fade_when_zero(self, project):
        """fade_seconds=0 should skip fade_in/fade_out without error."""
        clip = project.add_title_card('Hello', fade_seconds=0)
        assert isinstance(clip, BaseClip)

    def test_multiple_title_cards_on_same_track(self, project):
        project.add_title_card('First', start_seconds=0.0)
        project.add_title_card('Second', start_seconds=6.0)
        track = project.timeline.find_track_by_name('Titles')
        assert track is not None
        clip_ids = list(track.clip_ids)
        assert len(clip_ids) == 2


# ── add_subtitle_track ──────────────────────────────────────────────


class TestAddSubtitleTrack:
    def test_returns_list_of_clips(self, project):
        entries: list[tuple[float, float, str]] = [
            (0.0, 2.0, 'Hello'),
            (3.0, 2.0, 'World'),
        ]
        result = project.add_subtitle_track(entries)
        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(c, BaseClip) for c in result)

    def test_creates_track_with_default_name(self, project):
        project.add_subtitle_track([(0.0, 1.0, 'Hi')])
        track = project.timeline.find_track_by_name('Subtitles')
        assert track is not None

    def test_creates_track_with_custom_name(self, project):
        project.add_subtitle_track([(0.0, 1.0, 'Hi')], track_name='Captions')
        track = project.timeline.find_track_by_name('Captions')
        assert track is not None

    def test_empty_entries_returns_empty_list(self, project):
        result = project.add_subtitle_track([])
        assert result == []

    def test_subtitle_positions(self, project):
        entries: list[tuple[float, float, str]] = [
            (1.0, 2.0, 'First'),
            (5.0, 3.0, 'Second'),
        ]
        clips = project.add_subtitle_track(entries)
        assert ticks_to_seconds(clips[0].start) == pytest.approx(1.0)
        assert ticks_to_seconds(clips[0].duration) == pytest.approx(2.0)
        assert ticks_to_seconds(clips[1].start) == pytest.approx(5.0)
        assert ticks_to_seconds(clips[1].duration) == pytest.approx(3.0)

    def test_subtitle_count_matches_entries(self, project):
        entries: list[tuple[float, float, str]] = [
            (0.0, 1.0, 'A'),
            (2.0, 1.0, 'B'),
            (4.0, 1.0, 'C'),
        ]
        clips = project.add_subtitle_track(entries)
        assert len(clips) == 3

    def test_preserves_entry_order(self, project):
        entries: list[tuple[float, float, str]] = [
            (0.0, 1.0, 'First'),
            (2.0, 1.0, 'Second'),
        ]
        clips = project.add_subtitle_track(entries)
        assert ticks_to_seconds(clips[0].start) < ticks_to_seconds(clips[1].start)


# ── add_caption ─────────────────────────────────────────────────────

class TestAddCaption:
    def test_add_caption_creates_single_callout(self, project):
        clip = project.add_caption('Hello world', 1.0, 2.0)
        assert clip.clip_type == 'Callout'
        track = project.timeline.find_track_by_name('Subtitles')
        assert track is not None
        assert len(list(track.clips)) == 1

    def test_add_caption_appends_to_existing_subtitle_track(self, project):
        project.add_caption('One', 0.0, 1.0)
        project.add_caption('Two', 1.0, 1.0)
        track = project.timeline.find_track_by_name('Subtitles')
        assert len(list(track.clips)) == 2

    def test_add_caption_respects_custom_track_name(self, project):
        project.add_caption('CC', 0.0, 1.0, track_name='CC')
        assert project.timeline.find_track_by_name('CC') is not None
        assert project.timeline.find_track_by_name('Subtitles') is None
