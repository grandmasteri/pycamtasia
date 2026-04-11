"""Tests for camtasia.operations.merge."""
from __future__ import annotations

from camtasia import load_project
from camtasia.operations.merge import merge_tracks
from camtasia.timing import seconds_to_ticks


def _add_source(project, media_id, name='clip'):
    """Add a minimal sourceBin entry."""
    project._data.setdefault('sourceBin', []).append({
        'id': media_id,
        'src': f'./media/{name}.mp4',
        'rect': [0, 0, 1920, 1080],
        'sourceTracks': [{'range': [0, 300], 'type': 0}],
    })


def _add_clip(track_data, src_id, clip_id, start=0):
    """Append a clip to a raw track dict."""
    track_data['medias'].append({
        '_type': 'VMFile', 'id': clip_id, 'src': src_id,
        'start': start, 'duration': seconds_to_ticks(5.0),
        'mediaStart': 0, 'mediaDuration': seconds_to_ticks(5.0),
        'scalar': 1, 'metadata': {}, 'parameters': {},
        'effects': [], 'attributes': {}, 'animationTracks': {},
    })


def _populate_source(project, media_id=10, name='clip'):
    """Add a source and a clip on a new track."""
    _add_source(project, media_id, name)
    track = project.timeline.add_track('Source Track')
    _add_clip(track._data, media_id, clip_id=1, start=0)


class TestMergeCopiesTracks:
    def test_track_count_increases(self, project):
        from camtasia.project import load_project
        from pathlib import Path
        resources = Path(__file__).parent.parent / 'src' / 'camtasia' / 'resources'
        source = load_project(resources / 'new.cmproj')
        _populate_source(source)

        initial = project.timeline.track_count
        merge_tracks(source, project)

        assert project.timeline.track_count > initial


class TestMergeSkipsEmptyTracks:
    def test_empty_tracks_not_copied(self, project):
        from camtasia.project import load_project
        from pathlib import Path
        resources = Path(__file__).parent.parent / 'src' / 'camtasia' / 'resources'
        source = load_project(resources / 'new.cmproj')
        # Add one non-empty and leave existing empty tracks
        _populate_source(source)
        empty_count = sum(1 for t in source.timeline.tracks if len(t) == 0)
        assert empty_count > 0  # source has empty tracks

        initial = project.timeline.track_count
        copied = merge_tracks(source, project)

        assert copied == 1
        assert project.timeline.track_count == initial + 1


class TestMergeAppliesOffset:
    def test_clips_offset(self, project):
        from camtasia.project import load_project
        from pathlib import Path
        resources = Path(__file__).parent.parent / 'src' / 'camtasia' / 'resources'
        source = load_project(resources / 'new.cmproj')
        _populate_source(source)

        merge_tracks(source, project, offset_seconds=10.0)

        # Find the newly added track (last one)
        new_track = list(project.timeline.tracks)[-1]
        clip_data = new_track._data['medias'][0]
        assert clip_data['start'] == seconds_to_ticks(10.0)


class TestMergeReturnsCount:
    def test_returns_number_of_tracks_copied(self, project):
        from camtasia.project import load_project
        from pathlib import Path
        resources = Path(__file__).parent.parent / 'src' / 'camtasia' / 'resources'
        source = load_project(resources / 'new.cmproj')
        _populate_source(source)

        result = merge_tracks(source, project)

        assert result == 1


class TestMergeRemapsMediaIds:
    def test_clip_src_remapped(self, project):
        from camtasia.project import load_project
        from pathlib import Path
        resources = Path(__file__).parent.parent / 'src' / 'camtasia' / 'resources'
        source = load_project(resources / 'new.cmproj')
        _populate_source(source, media_id=10, name='unique_media')

        merge_tracks(source, project)

        # The target should have a sourceBin entry with a new ID
        target_ids = {e['id'] for e in project._data.get('sourceBin', [])}
        new_track = list(project.timeline.tracks)[-1]
        clip_src = new_track._data['medias'][0]['src']
        assert clip_src in target_ids


class TestMergeReusesExistingMedia:
    def test_merge_reuses_media_with_same_identity(self, project):
        from pathlib import Path
        wav = Path(__file__).parent / 'fixtures' / 'empty.wav'
        # Import same media into both source and target
        target_media = project.import_media(wav)
        
        source = load_project(str(project.file_path))
        source_media = source.import_media(wav)
        track = source.timeline.add_track('Audio')
        track.add_clip('AMFile', source_media.id, 0, 705600000)
        
        merge_tracks(source, project)
        # The merged clip should reference the target's existing media ID
        merged_track = list(project.timeline.tracks)[-1]
        actual_src = list(merged_track.clips)[0].source_id
        assert actual_src == target_media.id
