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


@pytest.mark.timeout(30)
def test_merge_accumulates_offset_in_ticks(tmp_path):
    """Bug 2: merge_projects must accumulate cursor in ticks to avoid float drift."""
    from camtasia.timing import seconds_to_ticks

    a = Project.new(tmp_path / 'a.cmproj', title='A')
    track_a = a.timeline.add_track('T')
    track_a._data.setdefault('medias', []).append({
        'id': 1, 'start': 0, 'duration': seconds_to_ticks(1.0 / 3),
        '_type': 'IMFile', 'src': 0,
    })
    a.save()

    b = Project.new(tmp_path / 'b.cmproj', title='B')
    track_b = b.timeline.add_track('T')
    track_b._data.setdefault('medias', []).append({
        'id': 1, 'start': 0, 'duration': seconds_to_ticks(1.0 / 3),
        '_type': 'IMFile', 'src': 0,
    })
    b.save()

    c = Project.new(tmp_path / 'c.cmproj', title='C')
    track_c = c.timeline.add_track('T')
    track_c._data.setdefault('medias', []).append({
        'id': 1, 'start': 0, 'duration': seconds_to_ticks(1.0),
        '_type': 'IMFile', 'src': 0,
    })
    c.save()

    merged = Project.merge_projects([a, b, c], tmp_path / 'merged.cmproj')
    # All clip starts should be exact integers (no float rounding artifacts)
    for track in merged.timeline.tracks:
        for media in track._data.get('medias', []):
            assert isinstance(media['start'], int), f"start should be int, got {type(media['start'])}"


# ── Bug 8: _remap_clip_ids dead code removed ──


def test_remap_clip_ids_removed():
    """_remap_clip_ids was dead code and should no longer exist."""
    import camtasia.operations.merge as mod
    assert not hasattr(mod, '_remap_clip_ids')


@pytest.mark.timeout(30)
def test_merge_cursor_uses_integer_ticks(tmp_path):
    """Bug 1: merge_projects cursor should use max integer tick end, not float round-trip."""
    a = Project.new(tmp_path / 'a.cmproj', title='A')
    b = Project.new(tmp_path / 'b.cmproj', title='B')

    # Add a clip to project A with a known tick-precise end
    track_a = a.timeline.add_track('V')
    clip_start = 0
    clip_duration = 705600000 * 3  # exactly 3 seconds in ticks
    track_a._data['medias'] = [{
        'id': 10, '_type': 'VMFile', 'src': 0,
        'start': clip_start, 'duration': clip_duration,
        'mediaStart': 0, 'mediaDuration': clip_duration,
        'scalar': 1, 'metadata': {}, 'parameters': {},
        'effects': [], 'attributes': {}, 'animationTracks': {},
    }]
    a.save()

    # Add a clip to project B
    track_b = b.timeline.add_track('V')
    track_b._data['medias'] = [{
        'id': 20, '_type': 'VMFile', 'src': 0,
        'start': 0, 'duration': 705600000,
        'mediaStart': 0, 'mediaDuration': 705600000,
        'scalar': 1, 'metadata': {}, 'parameters': {},
        'effects': [], 'attributes': {}, 'animationTracks': {},
    }]
    b.save()

    merged = Project.merge_projects([a, b], tmp_path / 'merged.cmproj')
    # B's clip should start exactly at A's clip end (integer ticks)
    all_clips = list(merged.timeline.all_clips())
    b_clip = [c for c in all_clips if c.start == clip_duration]
    assert len(b_clip) == 1, f"Expected B's clip at tick {clip_duration}"


class TestStripAssetPropertiesStitchedMedia:
    def test_strip_recurses_into_stitched_media_children(self):
        from camtasia.operations.merge import _strip_asset_properties
        clip = {
            '_type': 'StitchedMedia',
            'medias': [{
                'attributes': {'assetProperties': [{'objects': [5]}]},
            }],
        }
        saved = _strip_asset_properties(clip)
        assert len(saved) == 1
        assert 'assetProperties' not in clip['medias'][0]['attributes']


@pytest.mark.timeout(30)
def test_merge_projects_copies_media_files(tmp_path):
    """Bug 3: merge_projects should copy actual media files to the merged project."""
    a = Project.new(tmp_path / 'a.cmproj', title='A')
    # Create a fake media file in project A
    media_dir = tmp_path / 'a.cmproj' / 'media'
    media_dir.mkdir(parents=True, exist_ok=True)
    fake_media = media_dir / 'clip.mp4'
    fake_media.write_bytes(b'fake video data')
    # Add a sourceBin entry referencing it
    a._data.setdefault('sourceBin', []).append({
        'id': 1, 'src': './media/clip.mp4',
        'rect': [0, 0, 1920, 1080],
        'sourceTracks': [{'range': [0, 300], 'type': 0}],
    })
    a.save()

    merged = Project.merge_projects([a], tmp_path / 'merged.cmproj')  # noqa: F841
    # The media file should have been copied to the merged project
    merged_media = tmp_path / 'merged.cmproj' / 'media' / 'clip.mp4'
    assert merged_media.exists(), 'Media file was not copied to merged project'
    assert merged_media.read_bytes() == b'fake video data'


# ── Bug 3: merge_projects uses removeprefix('./') not lstrip('./') ───


@pytest.mark.timeout(30)
def test_merge_projects_removeprefix_preserves_dotdot_paths(tmp_path):
    """lstrip('./') would mangle '../shared/file' to 'shared/file'.
    removeprefix('./') only strips the exact prefix './'."""
    a = Project.new(tmp_path / 'a.cmproj', title='A')
    # Add a sourceBin entry with a path that starts with './' but also has dots
    a._data.setdefault('sourceBin', []).append({
        'id': 1, 'src': './...dotty/clip.mp4',
        'rect': [0, 0, 1920, 1080],
        'lastMod': '20260101T000000',
        'sourceTracks': [{'range': [0, 300], 'type': 0, 'editRate': 30,
                          'trackRect': [0, 0, 1920, 1080], 'sampleRate': 30,
                          'bitDepth': 24, 'numChannels': 0,
                          'integratedLUFS': 100.0, 'peakLevel': -1.0,
                          'tag': 0, 'metaData': '', 'parameters': {}}],
    })
    a.save()

    merged = Project.merge_projects([a], tmp_path / 'merged.cmproj')
    # The source path should be preserved in the merged project's sourceBin
    sources = [e.get('src') for e in merged._data.get('sourceBin', [])]
    assert './...dotty/clip.mp4' in sources
