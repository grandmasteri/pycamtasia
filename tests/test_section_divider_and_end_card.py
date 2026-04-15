"""Tests for Project.add_section_divider() and Project.add_end_card()."""
from __future__ import annotations

import pytest
from pathlib import Path


@pytest.fixture
def project():
    from camtasia.project import load_project
    resources = Path(__file__).parent.parent / 'src' / 'camtasia' / 'resources'
    return load_project(resources / 'new.cmproj')


# --- add_section_divider ---

class TestAddSectionDividerBasic:
    def test_returns_clip(self, project):
        clip = project.add_section_divider('Chapter 1', at_seconds=10.0)
        assert clip is not None

    def test_clip_text(self, project):
        clip = project.add_section_divider('Intro', at_seconds=0.0)
        assert clip.text == 'Intro'

    def test_default_track_name(self, project):
        project.add_section_divider('Part 1', at_seconds=5.0)
        track = project.timeline.find_track_by_name('Section Dividers')
        assert track is not None
        assert len(track) == 1

    def test_custom_track_name(self, project):
        project.add_section_divider('Part 1', at_seconds=5.0, track_name='Dividers')
        track = project.timeline.find_track_by_name('Dividers')
        assert track is not None

    def test_font_size_48(self, project):
        clip = project.add_section_divider('Title', at_seconds=0.0)
        assert clip.font['size'] == 48.0

    def test_default_duration(self, project):
        clip = project.add_section_divider('Title', at_seconds=0.0)
        assert abs(clip.duration_seconds - 3.0) < 0.1

    def test_custom_duration(self, project):
        clip = project.add_section_divider('Title', at_seconds=0.0, duration_seconds=7.0)
        assert abs(clip.duration_seconds - 7.0) < 0.1


class TestAddSectionDividerFades:
    def test_fades_applied_by_default(self, project):
        clip = project.add_section_divider('Faded', at_seconds=0.0)
        assert clip._data.get('parameters', {}).get('opacity') is not None

    def test_no_fades_when_zero(self, project):
        clip = project.add_section_divider('NoFade', at_seconds=0.0, fade_seconds=0.0)
        assert clip.effect_count == 0


class TestAddSectionDividerMarker:
    def test_marker_added(self, project):
        project.add_section_divider('Chapter 2', at_seconds=30.0)
        marker_names = [m.name for m in project.timeline.markers]
        assert 'Chapter 2' in marker_names

    def test_multiple_dividers_add_multiple_markers(self, project):
        project.add_section_divider('Part A', at_seconds=10.0)
        project.add_section_divider('Part B', at_seconds=20.0)
        marker_names = [m.name for m in project.timeline.markers]
        assert 'Part A' in marker_names
        assert 'Part B' in marker_names


# --- add_end_card ---

class TestAddEndCardBasic:
    def test_returns_clip(self, project):
        clip = project.add_end_card()
        assert clip is not None

    def test_default_text(self, project):
        clip = project.add_end_card()
        assert clip.text == 'Thank You'

    def test_custom_title(self, project):
        clip = project.add_end_card(title_text='The End')
        assert clip.text == 'The End'

    def test_subtitle_combined(self, project):
        clip = project.add_end_card(title_text='Thanks', subtitle_text='See you next time')
        assert clip.text == 'Thanks\nSee you next time'

    def test_no_subtitle_no_newline(self, project):
        clip = project.add_end_card(title_text='Bye', subtitle_text='')
        assert '\n' not in clip.text

    def test_default_track_name(self, project):
        project.add_end_card()
        track = project.timeline.find_track_by_name('End Card')
        assert track is not None
        assert len(track) == 1

    def test_custom_track_name(self, project):
        project.add_end_card(track_name='Outro')
        track = project.timeline.find_track_by_name('Outro')
        assert track is not None

    def test_font_size_48(self, project):
        clip = project.add_end_card()
        assert clip.font['size'] == 48.0

    def test_default_duration(self, project):
        clip = project.add_end_card()
        assert abs(clip.duration_seconds - 5.0) < 0.1

    def test_custom_duration(self, project):
        clip = project.add_end_card(duration_seconds=10.0)
        assert abs(clip.duration_seconds - 10.0) < 0.1


class TestAddEndCardFades:
    def test_fades_applied_by_default(self, project):
        clip = project.add_end_card()
        assert clip._data.get('parameters', {}).get('opacity') is not None

    def test_no_fades_when_zero(self, project):
        clip = project.add_end_card(fade_seconds=0.0)
        assert clip.effect_count == 0


class TestAddEndCardPosition:
    def test_placed_at_timeline_end(self, project):
        # Empty project has 0 duration, so end card starts at 0
        clip = project.add_end_card()
        assert clip.start_seconds == pytest.approx(0.0, abs=0.1)
