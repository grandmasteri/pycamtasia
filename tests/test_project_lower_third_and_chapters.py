"""Tests for Project.add_lower_third() and Project.add_chapter_markers()."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from camtasia.project import Project
from camtasia.timing import seconds_to_ticks


MINIMAL_PROJECT_DATA = {
    "editRate": 30,
    "authoringClientName": {
        "name": "Camtasia",
        "platform": "Mac",
        "version": "2020.0.8",
    },
    "sourceBin": [],
    "timeline": {
        "id": 1,
        "sceneTrack": {
            "scenes": [
                {
                    "csml": {
                        "tracks": [
                            {"trackIndex": 0, "medias": []},
                        ]
                    }
                }
            ]
        },
        "trackAttributes": [
            {
                "ident": "",
                "audioMuted": False,
                "videoHidden": False,
                "magnetic": False,
                "metadata": {"IsLocked": "False"},
            }
        ],
    },
}


def _create_project(tmp_path: Path, data: dict | None = None) -> Project:
    proj_dir = tmp_path / "test.cmproj"
    proj_dir.mkdir()
    (proj_dir / "project.tscproj").write_text(json.dumps(data or MINIMAL_PROJECT_DATA))
    return Project(proj_dir)


# ── add_lower_third ──────────────────────────────────────────────


class TestAddLowerThird:
    def test_returns_callout_clip(self, tmp_path: Path):
        proj = _create_project(tmp_path)
        clip = proj.add_lower_third("Speaker Name")
        assert clip is not None

    def test_title_only(self, tmp_path: Path):
        proj = _create_project(tmp_path)
        clip = proj.add_lower_third("Speaker Name")
        # The callout text should be exactly the title
        assert "Speaker Name" in str(clip._data)

    def test_title_and_subtitle(self, tmp_path: Path):
        proj = _create_project(tmp_path)
        clip = proj.add_lower_third("Speaker Name", subtitle_text="CEO, Acme Corp")
        raw = json.dumps(clip._data)
        assert "Speaker Name" in raw
        assert "CEO, Acme Corp" in raw

    def test_creates_track_with_default_name(self, tmp_path: Path):
        proj = _create_project(tmp_path)
        proj.add_lower_third("Title")
        names = proj.track_names
        assert "Lower Thirds" in names

    def test_custom_track_name(self, tmp_path: Path):
        proj = _create_project(tmp_path)
        proj.add_lower_third("Title", track_name="My LTs")
        assert "My LTs" in proj.track_names

    def test_custom_timing(self, tmp_path: Path):
        proj = _create_project(tmp_path)
        clip = proj.add_lower_third("Title", start_seconds=10.0, duration_seconds=3.0)
        assert clip.start == seconds_to_ticks(10.0)
        assert clip.duration == seconds_to_ticks(3.0)

    def test_font_size_is_28(self, tmp_path: Path):
        proj = _create_project(tmp_path)
        clip = proj.add_lower_third("Title")
        # font_size=28.0 is passed to add_callout
        raw = json.dumps(clip._data)
        assert "28" in raw

    def test_fade_applied_by_default(self, tmp_path: Path):
        proj = _create_project(tmp_path)
        clip = proj.add_lower_third("Title")
        # Fades add effects/parameters to the clip data
        visual = clip._data.get('animationTracks', {}).get('visual', [])
        assert len(visual) > 0

    def test_no_fade_when_zero(self, tmp_path: Path):
        proj = _create_project(tmp_path)
        clip = proj.add_lower_third("Title", fade_seconds=0)
        # With no fade, effects list should be empty or absent
        effects = clip._data.get("effects", [])
        # No fade-related effects should be present
        fade_effects = [e for e in effects if "fade" in e.get("effectName", "").lower()]
        assert len(fade_effects) == 0

    def test_default_duration_is_five_seconds(self, tmp_path: Path):
        proj = _create_project(tmp_path)
        clip = proj.add_lower_third("Title")
        assert clip.duration == seconds_to_ticks(5.0)

    def test_multiple_lower_thirds_same_track(self, tmp_path: Path):
        proj = _create_project(tmp_path)
        proj.add_lower_third("First", start_seconds=0.0)
        proj.add_lower_third("Second", start_seconds=6.0)
        track = proj.timeline.find_track_by_name("Lower Thirds")
        assert len(track) == 2


# ── add_chapter_markers ──────────────────────────────────────────


class TestAddChapterMarkers:
    def test_returns_count(self, tmp_path: Path):
        proj = _create_project(tmp_path)
        chapters = [(0.0, "Intro"), (30.0, "Main"), (120.0, "Outro")]
        assert proj.add_chapter_markers(chapters) == 3

    def test_markers_added_to_timeline(self, tmp_path: Path):
        proj = _create_project(tmp_path)
        chapters = [(0.0, "Intro"), (60.0, "Chapter 1")]
        proj.add_chapter_markers(chapters)
        markers = list(proj.timeline.markers)
        assert len(markers) == 2

    def test_marker_names(self, tmp_path: Path):
        proj = _create_project(tmp_path)
        chapters = [(0.0, "Intro"), (60.0, "Chapter 1")]
        proj.add_chapter_markers(chapters)
        names = [m.name for m in proj.timeline.markers]
        assert names == ["Intro", "Chapter 1"]

    def test_marker_times(self, tmp_path: Path):
        proj = _create_project(tmp_path)
        chapters = [(10.0, "A"), (20.0, "B")]
        proj.add_chapter_markers(chapters)
        times = [m.time for m in proj.timeline.markers]
        assert times == [seconds_to_ticks(10.0), seconds_to_ticks(20.0)]

    def test_empty_chapters(self, tmp_path: Path):
        proj = _create_project(tmp_path)
        assert proj.add_chapter_markers([]) == 0
        assert len(list(proj.timeline.markers)) == 0

    def test_single_chapter(self, tmp_path: Path):
        proj = _create_project(tmp_path)
        proj.add_chapter_markers([(0.0, "Start")])
        markers = list(proj.timeline.markers)
        assert len(markers) == 1
        assert markers[0].name == "Start"
        assert markers[0].time == 0
