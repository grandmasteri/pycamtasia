"""Tests for camtasia.operations.cleanup."""
from __future__ import annotations

import copy

import pytest

from camtasia.operations.cleanup import compact_project, remove_empty_tracks, remove_orphaned_media
from camtasia.timing import seconds_to_ticks


def _add_source(project, media_id):
    """Add a minimal sourceBin entry."""
    project._data.setdefault('sourceBin', []).append({
        'id': media_id,
        'src': f'./media/{media_id}.mp4',
        'rect': [0, 0, 1920, 1080],
        'sourceTracks': [{'range': [0, 300], 'type': 0}],
    })


def _add_clip(project, src_id, clip_id=1):
    """Append a clip referencing *src_id* to the first track."""
    tracks = project._data['timeline']['sceneTrack']['scenes'][0]['csml']['tracks']
    tracks[0]['medias'].append({
        '_type': 'VMFile', 'id': clip_id, 'src': src_id,
        'start': 0, 'duration': seconds_to_ticks(5.0),
        'mediaStart': 0, 'mediaDuration': seconds_to_ticks(5.0),
        'scalar': 1, 'metadata': {}, 'parameters': {},
        'effects': [], 'attributes': {}, 'animationTracks': {},
    })


class TestRemoveOrphanedMedia:
    def test_removes_unused(self, project):
        _add_source(project, 10)
        _add_source(project, 20)
        _add_clip(project, src_id=10)

        removed = remove_orphaned_media(project)

        assert removed == [20]
        assert [e['id'] for e in project._data['sourceBin']] == [10]

    def test_keeps_referenced(self, project):
        _add_source(project, 10)
        _add_clip(project, src_id=10)

        removed = remove_orphaned_media(project)

        assert removed == []
        assert [e['id'] for e in project._data['sourceBin']] == [10]

    def test_empty_project(self, project):
        removed = remove_orphaned_media(project)

        assert removed == []
        assert project._data['sourceBin'] == []

    def test_preserves_group_nested_sources(self, project):
        """Sources referenced inside Group internal tracks must not be removed."""
        _add_source(project, 10)
        _add_source(project, 20)
        _add_source(project, 30)
        # Add a Group clip whose internal tracks reference src 10 and 20
        tracks = project._data['timeline']['sceneTrack']['scenes'][0]['csml']['tracks']
        tracks[0]['medias'].append({
            '_type': 'Group', 'id': 1,
            'start': 0, 'duration': seconds_to_ticks(5.0),
            'mediaStart': 0, 'mediaDuration': seconds_to_ticks(5.0),
            'scalar': 1, 'metadata': {}, 'parameters': {},
            'effects': [], 'attributes': {}, 'animationTracks': {},
            'tracks': [
                {'medias': [{
                    '_type': 'VMFile', 'id': 2, 'src': 20,
                    'start': 0, 'duration': seconds_to_ticks(5.0),
                    'mediaStart': 0, 'mediaDuration': seconds_to_ticks(5.0),
                    'scalar': 1, 'metadata': {}, 'parameters': {},
                    'effects': [], 'attributes': {}, 'animationTracks': {},
                }]},
                {'medias': [{
                    '_type': 'AMFile', 'id': 3, 'src': 10,
                    'start': 0, 'duration': seconds_to_ticks(5.0),
                    'mediaStart': 0, 'mediaDuration': seconds_to_ticks(5.0),
                    'scalar': 1, 'metadata': {}, 'parameters': {},
                    'effects': [], 'attributes': {}, 'animationTracks': {},
                }]},
            ],
        })

        removed = remove_orphaned_media(project)

        assert removed == [30]
        remaining = {e['id'] for e in project._data['sourceBin']}
        assert 10 in remaining
        assert 20 in remaining


class TestRemoveEmptyTracks:
    def test_remove_empty_tracks(self, project):
        # The new.cmproj fixture starts with empty tracks
        initial_count = project.timeline.track_count
        assert initial_count == 2

        removed = remove_empty_tracks(project)

        assert removed == initial_count
        assert project.timeline.track_count == 0


class TestCompactProject:
    def test_returns_summary(self, project):
        _add_source(project, 10)
        _add_source(project, 20)
        _add_clip(project, src_id=10)

        result = compact_project(project)

        assert result['orphaned_media_removed'] == 1
        assert result['empty_tracks_removed'] == 1
        assert set(result.keys()) == {'orphaned_media_removed', 'empty_tracks_removed'}


class TestCollectSourceIdsFromUnifiedMedia:
    def test_preserves_unified_media_video_audio_sources(self, project):
        # Add a Group with UnifiedMedia containing video.src and audio.src
        track = project.timeline.add_track('Screen')
        track._data['medias'] = [{
            'id': 100, '_type': 'Group', 'start': 0, 'duration': 100,
            'tracks': [{'medias': [{
                'id': 101, '_type': 'UnifiedMedia',
                'video': {'id': 102, '_type': 'ScreenVMFile', 'src': 50},
                'audio': {'id': 103, '_type': 'AMFile', 'src': 51},
            }]}],
        }]
        # Add source bin entries for 50 and 51
        project._data['sourceBin'].append({'id': 50, 'src': 'video.trec'})
        project._data['sourceBin'].append({'id': 51, 'src': 'audio.trec'})
        removed = remove_orphaned_media(project)
        # Sources 50 and 51 should NOT be removed
        remaining_ids = {s['id'] for s in project._data['sourceBin']}
        assert 50 in remaining_ids
        assert 51 in remaining_ids


class TestCompactMethod:
    def test_compact_method_returns_summary(self, project):
        _add_source(project, 10)
        _add_source(project, 20)
        _add_clip(project, src_id=10)

        result = project.compact()

        assert result['orphaned_media_removed'] == 1
        assert result['empty_tracks_removed'] == 1

    def test_compact_validates_after_cleanup(self, project):
        # Add a zero-range audio source referenced by a clip so it survives cleanup
        project._data.setdefault('sourceBin', []).append({
            'id': 99,
            'src': './media/bad.wav',
            'rect': [0, 0, 0, 0],
            'sourceTracks': [{'range': [0, 0], 'type': 1}],
        })
        _add_clip(project, src_id=99)

        with pytest.raises(ValueError, match='Validation errors after compact'):
            project.compact()



STITCHED_MEDIA_CLEANUP = {
    '_type': 'StitchedMedia', 'id': 10, 'start': 0, 'duration': 100,
    'mediaStart': 0, 'mediaDuration': 100, 'scalar': 1,
    'parameters': {}, 'effects': [], 'metadata': {}, 'animationTracks': {},
    'minMediaStart': 0,
    'medias': [
        {'_type': 'AMFile', 'id': 11, 'start': 0, 'duration': 50, 'src': 1,
         'mediaStart': 0, 'mediaDuration': 50, 'scalar': 1,
         'parameters': {}, 'effects': [], 'metadata': {}, 'animationTracks': {}},
        {'_type': 'AMFile', 'id': 12, 'start': 50, 'duration': 50, 'src': 1,
         'mediaStart': 0, 'mediaDuration': 50, 'scalar': 1,
         'parameters': {}, 'effects': [], 'metadata': {}, 'animationTracks': {}},
    ],
}


def _inject_clips_cleanup(project, clip_dicts):
    tracks = project._data['timeline']['sceneTrack']['scenes'][0]['csml']['tracks']
    for clip in clip_dicts:
        tracks[0]['medias'].append(clip)


class TestCleanupStitchedMediaSources:
    def test_stitched_media_sub_clip_sources_not_orphaned(self, project):
        _add_source(project, 1)
        _add_source(project, 2)
        _add_source(project, 999)
        _inject_clips_cleanup(project, [copy.deepcopy(STITCHED_MEDIA_CLEANUP)])
        removed = remove_orphaned_media(project)
        assert 1 not in removed
        assert 999 in removed