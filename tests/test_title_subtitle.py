"""Tests for Project.add_title_card and Project.add_subtitle_track."""
from __future__ import annotations

from pathlib import Path

import pytest

from camtasia.project import load_project
from camtasia.timeline.clips import BaseClip

RESOURCES = Path(__file__).parent.parent / 'src' / 'camtasia' / 'resources'



def _isolated_project():
    """Load template into an isolated temp copy (safe for parallel execution)."""
    import shutil, tempfile
    from camtasia.project import load_project
    tmp = tempfile.mkdtemp()
    dst = Path(tmp) / 'test.cmproj'
    shutil.copytree(RESOURCES / 'new.cmproj', dst)
    return load_project(dst)

def _make_project():
    return _isolated_project()


# ── add_title_card ──────────────────────────────────────────────────


class TestAddTitleCard:
    def test_returns_base_clip(self):
        proj = _make_project()
        result = proj.add_title_card('Hello')
        assert isinstance(result, BaseClip)

    def test_creates_track_with_default_name(self):
        proj = _make_project()
        proj.add_title_card('Hello')
        track = proj.timeline.find_track_by_name('Titles')
        assert track is not None

    def test_creates_track_with_custom_name(self):
        proj = _make_project()
        proj.add_title_card('Hello', track_name='MyTitles')
        track = proj.timeline.find_track_by_name('MyTitles')
        assert track is not None

    def test_default_duration(self):
        proj = _make_project()
        clip = proj.add_title_card('Hello')
        from camtasia.timing import ticks_to_seconds
        assert ticks_to_seconds(clip.duration) == pytest.approx(5.0)

    def test_custom_duration(self):
        proj = _make_project()
        clip = proj.add_title_card('Hello', duration_seconds=10.0)
        from camtasia.timing import ticks_to_seconds
        assert ticks_to_seconds(clip.duration) == pytest.approx(10.0)

    def test_custom_start(self):
        proj = _make_project()
        clip = proj.add_title_card('Hello', start_seconds=3.0)
        from camtasia.timing import ticks_to_seconds
        assert ticks_to_seconds(clip.start) == pytest.approx(3.0)

    def test_no_fade_when_zero(self):
        """fade_seconds=0 should skip fade_in/fade_out without error."""
        proj = _make_project()
        clip = proj.add_title_card('Hello', fade_seconds=0)
        assert isinstance(clip, BaseClip)

    def test_multiple_title_cards_on_same_track(self):
        proj = _make_project()
        clip_a = proj.add_title_card('First', start_seconds=0.0)
        clip_b = proj.add_title_card('Second', start_seconds=6.0)
        track = proj.timeline.find_track_by_name('Titles')
        assert track is not None
        clip_ids = list(track.clip_ids)
        assert len(clip_ids) >= 2


# ── add_subtitle_track ──────────────────────────────────────────────


class TestAddSubtitleTrack:
    def test_returns_list_of_clips(self):
        proj = _make_project()
        entries: list[tuple[float, float, str]] = [
            (0.0, 2.0, 'Hello'),
            (3.0, 2.0, 'World'),
        ]
        result = proj.add_subtitle_track(entries)
        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(c, BaseClip) for c in result)

    def test_creates_track_with_default_name(self):
        proj = _make_project()
        proj.add_subtitle_track([(0.0, 1.0, 'Hi')])
        track = proj.timeline.find_track_by_name('Subtitles')
        assert track is not None

    def test_creates_track_with_custom_name(self):
        proj = _make_project()
        proj.add_subtitle_track([(0.0, 1.0, 'Hi')], track_name='Captions')
        track = proj.timeline.find_track_by_name('Captions')
        assert track is not None

    def test_empty_entries_returns_empty_list(self):
        proj = _make_project()
        result = proj.add_subtitle_track([])
        assert result == []

    def test_subtitle_positions(self):
        proj = _make_project()
        entries: list[tuple[float, float, str]] = [
            (1.0, 2.0, 'First'),
            (5.0, 3.0, 'Second'),
        ]
        clips = proj.add_subtitle_track(entries)
        from camtasia.timing import ticks_to_seconds
        assert ticks_to_seconds(clips[0].start) == pytest.approx(1.0)
        assert ticks_to_seconds(clips[0].duration) == pytest.approx(2.0)
        assert ticks_to_seconds(clips[1].start) == pytest.approx(5.0)
        assert ticks_to_seconds(clips[1].duration) == pytest.approx(3.0)

    def test_subtitle_count_matches_entries(self):
        proj = _make_project()
        entries: list[tuple[float, float, str]] = [
            (0.0, 1.0, 'A'),
            (2.0, 1.0, 'B'),
            (4.0, 1.0, 'C'),
        ]
        clips = proj.add_subtitle_track(entries)
        assert len(clips) == 3

    def test_preserves_entry_order(self):
        proj = _make_project()
        entries: list[tuple[float, float, str]] = [
            (0.0, 1.0, 'First'),
            (2.0, 1.0, 'Second'),
        ]
        clips = proj.add_subtitle_track(entries)
        from camtasia.timing import ticks_to_seconds
        assert ticks_to_seconds(clips[0].start) < ticks_to_seconds(clips[1].start)
