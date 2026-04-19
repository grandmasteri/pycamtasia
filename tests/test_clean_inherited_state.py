"""Tests for MarkerList.clear, Project.remove_orphaned_media, and Project.clean_inherited_state."""
from __future__ import annotations

import pytest

from camtasia.timeline.markers import MarkerList


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_keyframe(value: str, time: int) -> dict:
    return {"time": time, "endTime": time, "value": value, "duration": 0}


def _make_data_with_markers(*keyframes: dict) -> dict:
    return {"parameters": {"toc": {"type": "string", "keyframes": list(keyframes)}}}


# ---------------------------------------------------------------------------
# MarkerList.clear
# ---------------------------------------------------------------------------

class TestMarkerListClear:
    def test_clear_removes_all_markers(self):
        data = _make_data_with_markers(
            _make_keyframe("M1", 100),
            _make_keyframe("M2", 200),
        )
        ml = MarkerList(data)
        ml.clear()
        assert len(ml) == 0
        assert list(ml) == []

    def test_clear_on_empty_is_noop(self):
        data = _make_data_with_markers()
        ml = MarkerList(data)
        ml.clear()
        assert len(ml) == 0

    def test_clear_creates_path_if_missing(self):
        data: dict = {}
        ml = MarkerList(data)
        ml.clear()
        assert len(ml) == 0
        # Path was created
        assert data["parameters"]["toc"]["keyframes"] == []

    def test_add_after_clear(self):
        data = _make_data_with_markers(_make_keyframe("M1", 100))
        ml = MarkerList(data)
        ml.clear()
        ml.add("New", 500)
        assert len(ml) == 1
        assert list(ml)[0].name == "New"


# ---------------------------------------------------------------------------
# Project.remove_orphaned_media
# ---------------------------------------------------------------------------

class TestRemoveOrphanedMedia:
    def test_removes_unreferenced_media(self, project):
        # Add media to source bin that no clip references
        project._data.setdefault('sourceBin', []).append({
            'id': 9999,
            'src': './orphan.png',
            'rect': [0, 0, 100, 100],
            'lastMod': '20260101T000000',
            'sourceTracks': [{'range': [0, 1], 'type': 1, 'editRate': 1,
                              'trackRect': [0, 0, 100, 100], 'sampleRate': 0,
                              'bitDepth': 0, 'numChannels': 0}],
        })
        count = project.remove_orphaned_media()
        assert count == 1
        remaining_ids = [e['id'] for e in project._data['sourceBin']]
        assert 9999 not in remaining_ids

    def test_returns_zero_when_nothing_orphaned(self, project):
        # Empty project has no media at all
        project._data['sourceBin'] = []
        assert project.remove_orphaned_media() == 0

    def test_keeps_referenced_media(self, project):
        # Add a media entry and a clip that references it
        project._data.setdefault('sourceBin', []).append({
            'id': 42,
            'src': './used.png',
            'rect': [0, 0, 100, 100],
            'lastMod': '20260101T000000',
            'sourceTracks': [{'range': [0, 1], 'type': 1, 'editRate': 1,
                              'trackRect': [0, 0, 100, 100], 'sampleRate': 0,
                              'bitDepth': 0, 'numChannels': 0}],
        })
        track = project.timeline.tracks[0]
        track.add_clip('IMFile', 42, 0, 705_600_000)
        count = project.remove_orphaned_media()
        remaining_ids = [e['id'] for e in project._data['sourceBin']]
        assert 42 in remaining_ids


# ---------------------------------------------------------------------------
# Project.clean_inherited_state
# ---------------------------------------------------------------------------

class TestCleanInheritedState:
    def _add_clip_and_marker(self, project):
        """Add a regular clip, a marker, and a media entry."""
        project._data.setdefault('sourceBin', []).append({
            'id': 50,
            'src': './clip.png',
            'rect': [0, 0, 100, 100],
            'lastMod': '20260101T000000',
            'sourceTracks': [{'range': [0, 1], 'type': 1, 'editRate': 1,
                              'trackRect': [0, 0, 100, 100], 'sampleRate': 0,
                              'bitDepth': 0, 'numChannels': 0}],
        })
        track = project.timeline.tracks[0]
        track.add_clip('IMFile', 50, 0, 705_600_000)
        project.timeline.markers.add("Chapter 1", 0)
        return project

    def test_clears_clips_and_markers(self, project):
        self._add_clip_and_marker(project)
        assert project.clip_count == 1
        assert len(project.timeline.markers) == 1

        project.clean_inherited_state()

        assert project.clip_count == 0
        assert len(project.timeline.markers) == 0

    def test_removes_orphaned_media_after_clearing(self, project):
        self._add_clip_and_marker(project)
        project.clean_inherited_state()
        remaining_ids = [e['id'] for e in project._data.get('sourceBin', [])]
        assert 50 not in remaining_ids

    def test_preserve_groups_true_keeps_groups(self, project):
        """When preserve_groups=True, Group clips survive the clean."""
        track = project.timeline.tracks[0]
        # Manually insert a Group clip into the track data
        group_data = {
            'id': 100,
            '_type': 'Group',
            'start': 0,
            'duration': 705_600_000,
            'mediaStart': 0,
            'mediaDuration': 705600000, 'scalar': 1,
            'tracks': [{'medias': [], 'trackIndex': 0, 'transitions': []}],
            'parameters': {},
            'effects': [],
        }
        track._data.setdefault('medias', []).append(group_data)
        # Also add a regular clip
        track.add_clip('IMFile', 1, 705_600_000, 705_600_000)
        project.timeline.markers.add("M", 0)

        initial_clip_count = len(track.clips)
        assert initial_clip_count == 2

        project.clean_inherited_state(preserve_groups=True)

        # Group should survive
        surviving_types = [c.clip_type for c in track.clips]
        assert 'Group' in surviving_types
        # Non-group clips should be gone
        assert 'IMFile' not in surviving_types
        # Markers cleared
        assert len(project.timeline.markers) == 0

    def test_preserve_groups_false_removes_everything(self, project):
        track = project.timeline.tracks[0]
        group_data = {
            'id': 101,
            '_type': 'Group',
            'start': 0,
            'duration': 705_600_000,
            'mediaStart': 0,
            'mediaDuration': 705600000, 'scalar': 1,
            'tracks': [{'medias': [], 'trackIndex': 0, 'transitions': []}],
            'parameters': {},
            'effects': [],
        }
        track._data.setdefault('medias', []).append(group_data)
        project.timeline.markers.add("M", 0)

        project.clean_inherited_state(preserve_groups=False)

        assert project.clip_count == 0
        assert len(project.timeline.markers) == 0

    def test_clean_on_empty_project(self, project):
        """Cleaning an already-empty project should not raise."""
        project.clean_inherited_state()
        assert project.clip_count == 0
        assert len(project.timeline.markers) == 0
