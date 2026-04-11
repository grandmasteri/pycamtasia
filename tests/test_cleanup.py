"""Tests for camtasia.operations.cleanup."""
from __future__ import annotations

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


class TestRemoveEmptyTracks:
    def test_remove_empty_tracks(self, project):
        # The new.cmproj fixture starts with empty tracks
        initial_count = project.timeline.track_count
        assert initial_count > 0

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
        assert result['empty_tracks_removed'] >= 0
        assert set(result.keys()) == {'orphaned_media_removed', 'empty_tracks_removed'}
