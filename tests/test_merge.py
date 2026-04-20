"""Tests for camtasia.operations.merge."""
from __future__ import annotations

from pathlib import Path

from camtasia import load_project
from camtasia.operations.merge import merge_tracks
from camtasia.timing import seconds_to_ticks

RESOURCES = Path(__file__).parent.parent / 'src' / 'camtasia' / 'resources'


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
        source = load_project(RESOURCES / 'new.cmproj')
        _populate_source(source)

        initial = project.timeline.track_count
        merge_tracks(source, project)

        assert project.timeline.track_count > initial


class TestMergeSkipsEmptyTracks:
    def test_empty_tracks_not_copied(self, project):
        source = load_project(RESOURCES / 'new.cmproj')
        # Add one non-empty and leave existing empty tracks
        _populate_source(source)
        empty_count = sum(1 for t in source.timeline.tracks if len(t) == 0)
        assert empty_count == 2  # source has 2 empty default tracks

        initial = project.timeline.track_count
        copied = merge_tracks(source, project)

        assert copied == 1
        assert project.timeline.track_count == initial + 1


class TestMergeAppliesOffset:
    def test_clips_offset(self, project):
        source = load_project(RESOURCES / 'new.cmproj')
        _populate_source(source)

        merge_tracks(source, project, offset_seconds=10.0)

        # Find the newly added track (last one)
        new_track = list(project.timeline.tracks)[-1]
        clip_data = new_track._data['medias'][0]
        assert clip_data['start'] == seconds_to_ticks(10.0)


class TestMergeReturnsCount:
    def test_returns_number_of_tracks_copied(self, project):
        source = load_project(RESOURCES / 'new.cmproj')
        _populate_source(source)

        result = merge_tracks(source, project)

        assert result == 1


class TestMergeRemapsMediaIds:
    def test_clip_src_remapped(self, project):
        source = load_project(RESOURCES / 'new.cmproj')
        _populate_source(source, media_id=10, name='unique_media')

        merge_tracks(source, project)

        # The target should have a sourceBin entry with a new ID
        target_ids = {e['id'] for e in project._data.get('sourceBin', [])}
        new_track = list(project.timeline.tracks)[-1]
        clip_src = new_track._data['medias'][0]['src']
        assert clip_src in target_ids


class TestMergeReusesExistingMedia:
    def test_merge_reuses_media_with_same_identity(self, project):
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
        actual_src = next(iter(merged_track.clips)).source_id
        assert actual_src == target_media.id


def _add_group_clip(track_data, clip_id, inner_ids, src_id, start=0):
    """Append a Group clip with internal tracks containing inner clips."""
    inner_medias = []
    for iid in inner_ids:
        inner_medias.append({
            '_type': 'VMFile', 'id': iid, 'src': src_id,
            'start': 0, 'duration': seconds_to_ticks(2.0),
            'video': {'id': iid + 100, 'src': src_id},
            'audio': {'id': iid + 200, 'src': src_id},
        })
    track_data['medias'].append({
        '_type': 'Group', 'id': clip_id, 'start': start,
        'duration': seconds_to_ticks(5.0),
        'tracks': [{'medias': inner_medias}],
    })


class TestMergeRemapsGroupInternalIds:
    def test_merge_remaps_group_internal_ids(self, project):
        source = load_project(RESOURCES / 'new.cmproj')
        _add_source(source, 10, 'clip')
        track = source.timeline.add_track('Group Track')
        _add_group_clip(track._data, clip_id=1, inner_ids=[2, 3], src_id=10)

        merge_tracks(source, project)

        new_track = list(project.timeline.tracks)[-1]
        group = new_track._data['medias'][0]

        # Collect all IDs recursively
        all_ids = []

        def collect_ids(d):
            if 'id' in d:
                all_ids.append(d['id'])
            for key in ('video', 'audio'):
                if key in d:
                    collect_ids(d[key])
            for t in d.get('tracks', []):
                for m in t.get('medias', []):
                    collect_ids(m)

        collect_ids(group)
        # All IDs must be unique
        assert len(all_ids) == len(set(all_ids))


class TestRemapClipIdsAssetProperties:
    def test_dict_format_objects_in_asset_properties(self):
        from camtasia.operations.merge import _remap_asset_properties
        clip = {
            "id": 10,
            "attributes": {
                "assetProperties": [
                    {
                        "objects": [
                            {"media": 10, "other": "data"},
                            5,
                        ]
                    }
                ]
            },
        }
        _remap_asset_properties(clip, {10: 100})
        ap = clip["attributes"]["assetProperties"][0]["objects"]
        assert ap[0]["media"] == 100
        assert ap[1] == 5

    def test_int_objects_remapped(self):
        from camtasia.operations.merge import _remap_asset_properties
        clip = {
            "id": 20,
            "attributes": {
                "assetProperties": [
                    {"objects": [7]}
                ]
            },
        }
        _remap_asset_properties(clip, {7: 77})
        assert clip["attributes"]["assetProperties"][0]["objects"][0] == 77


class TestMergeStringFractionStart:
    """Bug 5: merge_tracks must handle string-fraction start values."""

    def test_string_fraction_start_does_not_crash(self, project):
        source = load_project(RESOURCES / 'new.cmproj')
        _add_source(source, 10, 'clip')
        track = source.timeline.add_track('Frac Track')
        clip = {
            '_type': 'VMFile', 'id': 1, 'src': 10,
            'start': '705600000/2', 'duration': seconds_to_ticks(5.0),
            'mediaStart': 0, 'mediaDuration': seconds_to_ticks(5.0),
            'scalar': 1, 'metadata': {}, 'parameters': {},
            'effects': [], 'attributes': {}, 'animationTracks': {},
        }
        track._data.setdefault('medias', []).append(clip)

        merge_tracks(source, project, offset_seconds=1.0)

        new_track = list(project.timeline.tracks)[-1]
        merged_start = new_track._data['medias'][0]['start']
        expected = 352_800_000 + seconds_to_ticks(1.0)
        assert merged_start == expected


class TestMergeCopiesTrackAttributes:
    """Bug 5: merge_tracks should copy source track attributes."""

    def test_audio_muted_copied(self, project):
        source = load_project(RESOURCES / 'new.cmproj')
        _populate_source(source)
        # Set audioMuted on the source track
        source_track = next(t for t in source.timeline.tracks if len(t) > 0)
        source_track._attributes['audioMuted'] = True

        merge_tracks(source, project)

        new_track = list(project.timeline.tracks)[-1]
        assert new_track._attributes.get('audioMuted') is True


class TestMergeTrackAttributesFromAttributes:
    """Bug 7: merge_tracks should read/write track attributes from _attributes, not _data."""

    def test_video_hidden_copied(self, project):
        source = load_project(RESOURCES / 'new.cmproj')
        _populate_source(source)
        source_track = next(t for t in source.timeline.tracks if len(t) > 0)
        source_track._attributes['videoHidden'] = True

        merge_tracks(source, project)

        new_track = list(project.timeline.tracks)[-1]
        assert new_track._attributes.get('videoHidden') is True
        assert new_track.video_hidden is True


class TestMergeNoDoubleRemapAssetProperties:
    """Bug 8: merge_tracks should not double-remap assetProperties."""

    def test_sibling_refs_remapped_once(self, project, tmp_path):
        import shutil
        src_proj = tmp_path / 'source.cmproj'
        shutil.copytree(RESOURCES / 'new.cmproj', src_proj)
        source = load_project(src_proj)
        track = source.timeline.add_track('V')
        track._data['medias'] = [
            {'id': 10, '_type': 'VMFile', 'src': 0, 'start': 0, 'duration': 100,
             'mediaStart': 0, 'mediaDuration': 100, 'scalar': 1,
             'metadata': {}, 'parameters': {}, 'effects': [],
             'attributes': {'ident': 'a', 'assetProperties': [
                 {'objects': [10, 11]}
             ]}, 'animationTracks': {}},
            {'id': 11, '_type': 'VMFile', 'src': 0, 'start': 100, 'duration': 100,
             'mediaStart': 0, 'mediaDuration': 100, 'scalar': 1,
             'metadata': {}, 'parameters': {}, 'effects': [],
             'attributes': {'ident': 'b'}, 'animationTracks': {}},
        ]

        merge_tracks(source, project)

        merged_track = [t for t in project.timeline.tracks if t.name == 'V'][-1]
        medias = merged_track._data['medias']
        new_a = medias[0]['id']
        new_b = medias[1]['id']
        ap = medias[0]['attributes']['assetProperties'][0]['objects']
        assert new_a in ap
        assert new_b in ap
        # Old IDs should not remain
        assert 10 not in ap
        assert 11 not in ap
