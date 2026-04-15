"""Tests for feature gaps #3-#6."""
from __future__ import annotations

import pytest

from camtasia.timeline.transitions import TransitionList


# ---------------------------------------------------------------------------
# Gap #3: TransitionList.clear()
# ---------------------------------------------------------------------------

class TestTransitionListClear:
    def test_clear_empties_transitions(self, project):
        track = project.timeline.tracks[0]
        c1 = track.add_video(1, 0, 5)
        c2 = track.add_video(1, 5, 5)
        track.transitions.add('FadeThroughBlack', c1.id, c2.id, 100_000)
        assert len(track.transitions) == 1

        track.transitions.clear()
        assert len(track.transitions) == 0

    def test_clear_on_empty_is_noop(self, project):
        track = project.timeline.tracks[0]
        track.transitions.clear()
        assert len(track.transitions) == 0

    def test_clear_preserves_clips(self, project):
        track = project.timeline.tracks[0]
        c1 = track.add_video(1, 0, 5)
        c2 = track.add_video(1, 5, 5)
        track.transitions.add('FadeThroughBlack', c1.id, c2.id, 100_000)
        track.transitions.clear()
        assert len(track) == 2  # clips still present


# ---------------------------------------------------------------------------
# Gap #4: GroupTrack.transitions
# ---------------------------------------------------------------------------

class TestGroupTrackTransitions:
    def test_group_track_has_transitions_property(self, project):
        track = project.timeline.tracks[0]
        group = track.add_group(0, 10, internal_tracks=[
            {'trackIndex': 0, 'medias': [], 'transitions': []},
        ])
        gt = group.tracks[0]
        assert isinstance(gt.transitions, TransitionList)
        assert len(gt.transitions) == 0

    def test_group_track_transitions_reflects_data(self, project):
        track = project.timeline.tracks[0]
        group = track.add_group(0, 10, internal_tracks=[
            {
                'trackIndex': 0,
                'medias': [
                    {'id': 900, '_type': 'VMFile', 'start': 0, 'duration': 100},
                    {'id': 901, '_type': 'VMFile', 'start': 100, 'duration': 100},
                ],
                'transitions': [
                    {'name': 'FadeThroughBlack', 'duration': 50,
                     'leftMedia': 900, 'rightMedia': 901, 'attributes': {}},
                ],
            },
        ])
        gt = group.tracks[0]
        assert len(gt.transitions) == 1
        assert gt.transitions[0].name == 'FadeThroughBlack'


# ---------------------------------------------------------------------------
# Gap #5: Project.repair()
# ---------------------------------------------------------------------------

class TestProjectRepair:
    def test_repair_removes_stale_transitions(self, project):
        track = project.timeline.tracks[0]
        c1 = track.add_video(1, 0, 5)
        c2 = track.add_video(1, 5, 5)
        track.transitions.add('FadeThroughBlack', c1.id, c2.id, 100_000)
        # Remove c2 without cleaning transitions (simulate stale state)
        track._data['medias'] = [m for m in track._data['medias'] if m['id'] != c2.id]

        result = project.repair()
        assert result['stale_transitions_removed'] == 1
        assert len(track.transitions) == 0

    def test_repair_keeps_valid_transitions(self, project):
        track = project.timeline.tracks[0]
        c1 = track.add_video(1, 0, 5)
        c2 = track.add_video(1, 5, 5)
        track.transitions.add('FadeThroughBlack', c1.id, c2.id, 100_000)

        result = project.repair()
        assert result['stale_transitions_removed'] == 0
        assert len(track.transitions) == 1

    def test_repair_returns_zero_counts_when_clean(self, project):
        result = project.repair()
        assert result['stale_transitions_removed'] == 0
        assert 'stale_transitions_removed' in result


# ---------------------------------------------------------------------------
# Gap #6: Track.remove_all_clips()
# ---------------------------------------------------------------------------

class TestTrackRemoveAllClips:
    def test_remove_all_clips_returns_count(self, project):
        track = project.timeline.tracks[0]
        track.add_video(1, 0, 5)
        track.add_video(1, 5, 5)
        track.add_audio(1, 10, 5)
        assert track.remove_all_clips() == 3

    def test_remove_all_clips_empties_track(self, project):
        track = project.timeline.tracks[0]
        track.add_video(1, 0, 5)
        track.add_video(1, 5, 5)
        track.remove_all_clips()
        assert len(track) == 0
        assert track.is_empty

    def test_remove_all_clips_clears_transitions(self, project):
        track = project.timeline.tracks[0]
        c1 = track.add_video(1, 0, 5)
        c2 = track.add_video(1, 5, 5)
        track.transitions.add('FadeThroughBlack', c1.id, c2.id, 100_000)
        track.remove_all_clips()
        assert len(track.transitions) == 0

    def test_remove_all_clips_on_empty_returns_zero(self, project):
        track = project.timeline.tracks[0]
        assert track.remove_all_clips() == 0

    def test_remove_all_clips_preserves_track_identity(self, project):
        track = project.timeline.tracks[0]
        track.name = 'MyTrack'
        track.add_video(1, 0, 5)
        track.remove_all_clips()
        assert track.name == 'MyTrack'
        assert track.index == project.timeline.tracks[0].index


class TestTrackClearWithGroupTransitions:
    def test_clear_removes_group_internal_transitions(self):
        """clear() removes transitions from Group clips' internal tracks."""
        from camtasia.timeline.track import Track
        group_media = {
            'id': 1, '_type': 'Group', 'start': 0, 'duration': 100,
            'tracks': [
                {'trackIndex': 0, 'medias': [{'id': 10, '_type': 'VMFile', 'start': 0, 'duration': 50}],
                 'transitions': [{'name': 'Fade', 'duration': 10, 'leftMedia': 10, 'rightMedia': 11}]},
            ],
        }
        data = {'trackIndex': 0, 'medias': [group_media], 'transitions': []}
        track = Track({'ident': 'test'}, data)
        track.clear()
        assert data['medias'] == []
