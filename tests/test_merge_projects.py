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
