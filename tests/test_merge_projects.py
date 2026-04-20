"""Tests for Project.merge_projects classmethod."""
from __future__ import annotations

from pathlib import Path

import pytest

from camtasia.project import Project

RESOURCES = Path(__file__).parent.parent / 'src' / 'camtasia' / 'resources'


@pytest.fixture
def project_a(tmp_path):
    return Project.new(tmp_path / 'a.cmproj', title='Project A')


@pytest.fixture
def project_b(tmp_path):
    return Project.new(tmp_path / 'b.cmproj', title='Project B')



@pytest.mark.timeout(30)
def test_merge_empty_projects(tmp_path, project_a, project_b):
    merged = Project.merge_projects(
        [project_a, project_b],
        tmp_path / 'merged.cmproj',
    )
    assert merged.title == 'Merged Project'
    assert (tmp_path / 'merged.cmproj').exists()



@pytest.mark.timeout(30)
def test_merge_custom_title(tmp_path, project_a, project_b):
    merged = Project.merge_projects(
        [project_a, project_b],
        tmp_path / 'merged.cmproj',
        title='Combined',
    )
    assert merged.title == 'Combined'



@pytest.mark.timeout(30)
def test_merge_empty_list(tmp_path):
    merged = Project.merge_projects([], tmp_path / 'merged.cmproj')
    assert merged.clip_count == 0
    assert merged.track_count == 2



@pytest.mark.timeout(30)
def test_merge_single_project(tmp_path, project_a):
    merged = Project.merge_projects(
        [project_a],
        tmp_path / 'merged.cmproj',
    )
    assert isinstance(merged, Project)



@pytest.mark.timeout(30)
def test_merge_preserves_tracks(tmp_path):
    a = Project.new(tmp_path / 'a.cmproj', title='A')
    a.timeline.add_track('Track-A')
    a.save()

    b = Project.new(tmp_path / 'b.cmproj', title='B')
    b.timeline.add_track('Track-B')
    b.save()

    merged = Project.merge_projects(
        [a, b],
        tmp_path / 'merged.cmproj',
    )
    names = merged.track_names
    assert {'Track-A', 'Track-B'}.issubset(set(names))



@pytest.mark.timeout(30)
def test_merge_copies_media_bin(tmp_path):
    a = Project.new(tmp_path / 'a.cmproj', title='A')
    # Manually add a source bin entry
    a._data.setdefault('sourceBin', []).append({
        'id': 99, 'src': './media/test.png',
        'rect': [0, 0, 100, 100],
        'lastMod': '20260101T000000',
        'sourceTracks': [{'range': [0, 1], 'type': 1, 'editRate': 1,
                          'trackRect': [0, 0, 100, 100], 'sampleRate': 1,
                          'bitDepth': 8, 'numChannels': 0}],
    })
    a.save()

    merged = Project.merge_projects(
        [a],
        tmp_path / 'merged.cmproj',
    )
    sources = [e.get('src') for e in merged._data.get('sourceBin', [])]
    assert './media/test.png' in sources



@pytest.mark.timeout(30)
def test_merge_result_is_loadable(tmp_path, project_a):
    out = tmp_path / 'merged.cmproj'
    Project.merge_projects([project_a], out)
    reloaded = Project.load(out)
    assert reloaded.title == 'Merged Project'



@pytest.mark.timeout(30)
@pytest.mark.filterwarnings("ignore::UserWarning")
def test_merge_clips_get_unique_ids(tmp_path):
    a = Project.new(tmp_path / 'a.cmproj', title='A')
    track_a = a.timeline.add_track('T')
    track_a._data.setdefault('medias', []).append({
        'id': 1, 'start': 0, 'duration': 705600000,
        '_type': 'IMFile', 'src': 0,
    })
    a.save()

    b = Project.new(tmp_path / 'b.cmproj', title='B')
    track_b = b.timeline.add_track('T')
    track_b._data.setdefault('medias', []).append({
        'id': 1, 'start': 0, 'duration': 705600000,
        '_type': 'IMFile', 'src': 0,
    })
    b.save()

    merged = Project.merge_projects(
        [a, b],
        tmp_path / 'merged.cmproj',
    )
    # Collect all clip IDs from merged tracks
    ids = []
    for track in merged.timeline.tracks:
        for clip in track.clips:
            ids.append(clip.id)
    # All IDs should be unique
    assert len(ids) == len(set(ids))



@pytest.mark.timeout(30)
def test_merge_remaps_asset_properties_sibling_refs(tmp_path):
    """Bug 6: merge_tracks must remap assetProperties.objects sibling refs correctly."""
    from camtasia.operations.merge import merge_tracks

    source = Project.new(tmp_path / 'src.cmproj', title='Source')
    target = Project.new(tmp_path / 'tgt.cmproj', title='Target')

    # Add a clip with assetProperties referencing sibling clip IDs
    track = source.timeline.add_track('V')
    clip_a = {'id': 10, '_type': 'VMFile', 'src': 0, 'start': 0, 'duration': 100,
              'mediaStart': 0, 'mediaDuration': 100, 'scalar': 1,
              'metadata': {}, 'parameters': {}, 'effects': [],
              'attributes': {'ident': 'a', 'assetProperties': [
                  {'objects': [10, 11]}  # references to sibling clip IDs
              ]},
              'animationTracks': {}}
    clip_b = {'id': 11, '_type': 'VMFile', 'src': 0, 'start': 100, 'duration': 100,
              'mediaStart': 0, 'mediaDuration': 100, 'scalar': 1,
              'metadata': {}, 'parameters': {}, 'effects': [],
              'attributes': {'ident': 'b'},
              'animationTracks': {}}
    track._data['medias'] = [clip_a, clip_b]
    source.save()

    count = merge_tracks(source, target)
    assert count == 1

    # Find the merged clips
    merged_track = None
    for t in target.timeline.tracks:
        if t.name == 'V':
            merged_track = t
            break
    assert merged_track is not None
    merged_medias = merged_track._data['medias']
    assert len(merged_medias) == 2

    # Get the new IDs
    new_id_a = merged_medias[0]['id']
    new_id_b = merged_medias[1]['id']

    # assetProperties should reference the NEW IDs, not the old ones
    ap = merged_medias[0]['attributes']['assetProperties'][0]['objects']
    assert new_id_a in ap
    assert new_id_b in ap
    assert 10 not in ap
    assert 11 not in ap


class TestMergeRemapInternalPaths:
    def test_src_remap_recurses_into_stitched_media(self):
        """_remap_src_in_clip covers stitched media children."""
        from camtasia.operations.merge import _remap_src_in_clip
        clip = {
            '_type': 'StitchedMedia', 'src': 100,
            'medias': [{'_type': 'VMFile', 'src': 101}],
        }
        _remap_src_in_clip(clip, {100: 200, 101: 201})
        assert clip['src'] == 200
        assert clip['medias'][0]['src'] == 201

    def test_asset_properties_remap_dict_objects(self):
        """_remap_asset_properties handles dict objects with 'media' key."""
        from camtasia.operations.merge import _remap_asset_properties
        clip = {
            'attributes': {
                'assetProperties': [{'objects': [
                    {'media': 10, 'other': 'x'},
                    {'media': 20},
                ]}]
            }
        }
        _remap_asset_properties(clip, {10: 100, 20: 200})
        objs = clip['attributes']['assetProperties'][0]['objects']
        assert objs[0]['media'] == 100
        assert objs[0]['other'] == 'x'
        assert objs[1]['media'] == 200

    def test_asset_properties_remap_recurses_into_stitched(self):
        """_remap_asset_properties recurses into StitchedMedia child medias."""
        from camtasia.operations.merge import _remap_asset_properties
        clip = {
            '_type': 'StitchedMedia',
            'medias': [{
                'attributes': {'assetProperties': [{'objects': [5]}]},
            }],
        }
        _remap_asset_properties(clip, {5: 55})
        assert clip['medias'][0]['attributes']['assetProperties'][0]['objects'] == [55]
