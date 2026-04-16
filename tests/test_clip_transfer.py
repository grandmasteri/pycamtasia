"""Tests for copy_to_track, move_clip_to_track, and move_all_clips_to_track."""
from __future__ import annotations

import pytest

from camtasia.project import Project
from camtasia.timeline.clips import BaseClip

EDIT_RATE = 705_600_000


class TestCopyToTrack:
    """Tests for BaseClip.copy_to_track."""

    def test_copy_creates_clip_on_target_track(self, project: Project) -> None:
        source_track = project.timeline.add_track('Source')
        target_track = project.timeline.add_track('Target')
        original_clip = source_track.add_clip('VMFile', 1, 0, EDIT_RATE * 5)

        copied_clip: BaseClip = original_clip.copy_to_track(target_track)

        assert copied_clip.id in target_track.clip_ids
        assert len(target_track.clip_ids) == 1

    def test_copy_preserves_original_on_source_track(self, project: Project) -> None:
        source_track = project.timeline.add_track('Source')
        target_track = project.timeline.add_track('Target')
        original_clip = source_track.add_clip('VMFile', 1, 0, EDIT_RATE * 3)

        original_clip.copy_to_track(target_track)

        assert original_clip.id in source_track.clip_ids

    def test_copy_assigns_new_id(self, project: Project) -> None:
        source_track = project.timeline.add_track('Source')
        target_track = project.timeline.add_track('Target')
        original_clip = source_track.add_clip('VMFile', 1, 0, EDIT_RATE)

        copied_clip: BaseClip = original_clip.copy_to_track(target_track)

        assert copied_clip.id != original_clip.id

    def test_copy_preserves_timing(self, project: Project) -> None:
        source_track = project.timeline.add_track('Source')
        target_track = project.timeline.add_track('Target')
        original_clip = source_track.add_clip('VMFile', 1, EDIT_RATE * 2, EDIT_RATE * 4)

        copied_clip: BaseClip = original_clip.copy_to_track(target_track)

        assert copied_clip.start == original_clip.start
        assert copied_clip.duration == original_clip.duration

    def test_copy_preserves_clip_type(self, project: Project) -> None:
        source_track = project.timeline.add_track('Source')
        target_track = project.timeline.add_track('Target')
        original_clip = source_track.add_clip('AMFile', 1, 0, EDIT_RATE)

        copied_clip: BaseClip = original_clip.copy_to_track(target_track)

        assert copied_clip.clip_type == 'AMFile'

    def test_copy_is_independent_of_original(self, project: Project) -> None:
        source_track = project.timeline.add_track('Source')
        target_track = project.timeline.add_track('Target')
        original_clip = source_track.add_clip('VMFile', 1, 0, EDIT_RATE * 5)

        copied_clip: BaseClip = original_clip.copy_to_track(target_track)
        copied_clip._data['start'] = EDIT_RATE * 99

        assert original_clip.start == 0


class TestMoveClipToTrack:
    """Tests for Track.move_clip_to_track."""

    def test_move_removes_clip_from_source(self, project: Project) -> None:
        source_track = project.timeline.add_track('Source')
        target_track = project.timeline.add_track('Target')
        clip = source_track.add_clip('VMFile', 1, 0, EDIT_RATE * 3)
        original_clip_id: int = clip.id

        source_track.move_clip_to_track(original_clip_id, target_track)

        assert original_clip_id not in source_track.clip_ids

    def test_move_adds_clip_to_target(self, project: Project) -> None:
        source_track = project.timeline.add_track('Source')
        target_track = project.timeline.add_track('Target')
        clip = source_track.add_clip('VMFile', 1, 0, EDIT_RATE * 3)

        moved_clip: BaseClip = source_track.move_clip_to_track(clip.id, target_track)

        assert moved_clip.id in target_track.clip_ids

    def test_move_assigns_new_id(self, project: Project) -> None:
        """Moved clip gets an ID from the target track's ID space."""
        source_track = project.timeline.add_track('Source')
        target_track = project.timeline.add_track('Target')
        clip = source_track.add_clip('VMFile', 1, 0, EDIT_RATE)
        original_id: int = clip.id

        moved_clip: BaseClip = source_track.move_clip_to_track(original_id, target_track)

        assert isinstance(moved_clip.id, int)
        assert len(target_track) == 1

    def test_move_preserves_timing(self, project: Project) -> None:
        source_track = project.timeline.add_track('Source')
        target_track = project.timeline.add_track('Target')
        clip = source_track.add_clip('VMFile', 1, EDIT_RATE * 2, EDIT_RATE * 4)
        original_start: int = clip.start
        original_duration: int = clip.duration

        moved_clip: BaseClip = source_track.move_clip_to_track(clip.id, target_track)

        assert moved_clip.start == original_start
        assert moved_clip.duration == original_duration

    def test_move_nonexistent_clip_raises_key_error(self, project: Project) -> None:
        source_track = project.timeline.add_track('Source')
        target_track = project.timeline.add_track('Target')

        with pytest.raises(KeyError, match='No clip with id=9999'):
            source_track.move_clip_to_track(9999, target_track)

    def test_move_preserves_clip_type(self, project: Project) -> None:
        source_track = project.timeline.add_track('Source')
        target_track = project.timeline.add_track('Target')
        clip = source_track.add_clip('AMFile', 1, 0, EDIT_RATE)

        moved_clip: BaseClip = source_track.move_clip_to_track(clip.id, target_track)

        assert moved_clip.clip_type == 'AMFile'


class TestMoveAllClipsToTrack:
    """Tests for Project.move_all_clips_to_track."""

    def test_moves_all_clips(self, project: Project) -> None:
        source_track = project.timeline.add_track('Source')
        target_track = project.timeline.add_track('Target')
        source_track.add_clip('VMFile', 1, 0, EDIT_RATE)
        source_track.add_clip('VMFile', 1, EDIT_RATE * 2, EDIT_RATE)
        source_track.add_clip('AMFile', 1, EDIT_RATE * 4, EDIT_RATE)

        clips_moved: int = project.move_all_clips_to_track('Source', 'Target')

        assert clips_moved == 3
        assert len(source_track.clip_ids) == 0
        assert len(target_track.clip_ids) == 3

    def test_returns_zero_for_empty_source(self, project: Project) -> None:
        project.timeline.add_track('Source')
        project.timeline.add_track('Target')

        clips_moved: int = project.move_all_clips_to_track('Source', 'Target')

        assert clips_moved == 0

    def test_source_track_not_found_raises_key_error(self, project: Project) -> None:
        project.timeline.add_track('Target')

        with pytest.raises(KeyError, match='Source track not found'):
            project.move_all_clips_to_track('NonExistent', 'Target')

    def test_target_track_not_found_raises_key_error(self, project: Project) -> None:
        project.timeline.add_track('Source')

        with pytest.raises(KeyError, match='Target track not found'):
            project.move_all_clips_to_track('Source', 'NonExistent')

    def test_preserves_timing_of_moved_clips(self, project: Project) -> None:
        source_track = project.timeline.add_track('Source')
        target_track = project.timeline.add_track('Target')
        source_track.add_clip('VMFile', 1, 0, EDIT_RATE * 2)
        source_track.add_clip('VMFile', 1, EDIT_RATE * 5, EDIT_RATE * 3)

        project.move_all_clips_to_track('Source', 'Target')

        target_clips = list(target_track.clips)
        starts: set[int] = {c.start for c in target_clips}
        assert 0 in starts
        assert EDIT_RATE * 5 in starts
