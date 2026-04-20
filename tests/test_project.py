from __future__ import annotations

from fractions import Fraction
import json
from pathlib import Path
import struct
import subprocess
import sys
from typing import ClassVar
from unittest.mock import MagicMock, patch
import zlib

import pytest

from camtasia.media_bin import MediaBin
from camtasia.operations.diff import diff_projects
from camtasia.operations.speed import _process_clip, _scale_clip_timing
from camtasia.operations.template import (
    _walk_clips,
    replace_media_source,
)
import camtasia.project as proj_mod
from camtasia.project import (
    Project,
    _probe_media,
    _probe_media_ffprobe,
    _remap_src_recursive,
    load_project,
    new_project,
    use_project,
)
from camtasia.timeline import Timeline
from camtasia.timeline.clips import BaseClip, clip_from_dict
from camtasia.timeline.clips.group import Group
from camtasia.timeline.track import Track
from camtasia.timing import seconds_to_ticks
from camtasia.validation import ValidationIssue, _check_group_required_fields, _check_timing_consistency

MINIMAL_PROJECT_DATA = {
    "editRate": 30,
    "authoringClientName": {
        "name": "Camtasia",
        "platform": "Mac",
        "version": "2020.0.8",
    },
    "sourceBin": [],
    "timeline": {
        "id": 1,
        "sceneTrack": {
            "scenes": [
                {
                    "csml": {
                        "tracks": [
                            {"trackIndex": 0, "medias": []},
                        ]
                    }
                }
            ]
        },
        "trackAttributes": [
            {
                "ident": "",
                "audioMuted": False,
                "videoHidden": False,
                "magnetic": False,
                "metadata": {"IsLocked": "False"},
            }
        ],
    },
}


def _create_cmproj(tmp_path: Path, data: dict | None = None) -> Path:
    """Create a minimal .cmproj bundle in tmp_path and return its path."""
    proj_dir = tmp_path / "test.cmproj"
    proj_dir.mkdir()
    tscproj = proj_dir / "project.tscproj"
    tscproj.write_text(json.dumps(data or MINIMAL_PROJECT_DATA))
    return proj_dir


class TestProjectLoad:
    def test_load_from_cmproj_directory(self, tmp_path: Path):
        proj_dir = _create_cmproj(tmp_path)
        project = Project(proj_dir)
        assert project.file_path == proj_dir

    def test_load_from_tscproj_file(self, tmp_path: Path):
        proj_dir = _create_cmproj(tmp_path)
        tscproj = proj_dir / "project.tscproj"
        project = Project(tscproj)
        assert project.file_path == tscproj

    def test_load_missing_tscproj_raises(self, tmp_path: Path):
        empty_dir = tmp_path / "empty.cmproj"
        empty_dir.mkdir()
        with pytest.raises(FileNotFoundError):
            Project(empty_dir)


class TestProjectProperties:
    def test_edit_rate(self, tmp_path: Path):
        project = Project(_create_cmproj(tmp_path))
        assert project.edit_rate == 30

    def test_edit_rate_default_when_missing(self, tmp_path: Path):
        data = {k: v for k, v in MINIMAL_PROJECT_DATA.items() if k != "editRate"}
        data["authoringClientName"] = MINIMAL_PROJECT_DATA["authoringClientName"]
        data["timeline"] = MINIMAL_PROJECT_DATA["timeline"]
        project = Project(_create_cmproj(tmp_path, data))
        assert project.edit_rate == 705_600_000

    def test_media_bin_returns_media_bin(self, project):
        assert isinstance(project.media_bin, MediaBin)
        assert list(project.media_bin) == []

    def test_timeline_returns_timeline(self, tmp_path: Path):
        project = Project(_create_cmproj(tmp_path))
        assert isinstance(project.timeline, Timeline)
        assert project.timeline.track_count == 1

    def test_authoring_client(self, tmp_path: Path):
        project = Project(_create_cmproj(tmp_path))
        actual_client = project.authoring_client
        assert actual_client.name == "Camtasia"
        assert actual_client.platform == "Mac"
        assert actual_client.version == "2020.0.8"


class TestProjectSave:
    def test_save_writes_valid_json(self, tmp_path: Path):
        proj_dir = _create_cmproj(tmp_path)
        project = Project(proj_dir)
        project.save()
        tscproj = proj_dir / "project.tscproj"
        reloaded = json.loads(tscproj.read_text())
        assert reloaded["editRate"] == 30
        assert reloaded["authoringClientName"]["name"] == "Camtasia"

    def test_save_persists_mutations(self, tmp_path: Path):
        proj_dir = _create_cmproj(tmp_path)
        project = Project(proj_dir)
        project.timeline.add_track("new-track")
        project.save()
        reloaded = json.loads((proj_dir / "project.tscproj").read_text())
        track_names = [
            a["ident"]
            for a in reloaded["timeline"]["trackAttributes"]
        ]
        assert set(track_names) == {"", "new-track"}


class TestLoadProject:
    def test_load_project_returns_project(self, tmp_path: Path):
        proj_dir = _create_cmproj(tmp_path)
        project = load_project(proj_dir)
        assert isinstance(project, Project)
        assert project.edit_rate == 30

    def test_load_project_with_string_path(self, tmp_path: Path):
        proj_dir = _create_cmproj(tmp_path)
        project = load_project(str(proj_dir))
        assert isinstance(project, Project)


class TestUseProject:
    def test_use_project_saves_on_exit(self, tmp_path: Path):
        proj_dir = _create_cmproj(tmp_path)
        with use_project(proj_dir) as proj:
            proj.timeline.add_track("ctx-track")
        reloaded = json.loads((proj_dir / "project.tscproj").read_text())
        track_names = [
            a["ident"]
            for a in reloaded["timeline"]["trackAttributes"]
        ]
        assert set(track_names) == {"", "ctx-track"}

    def test_use_project_no_save_on_exit(self, tmp_path: Path):
        proj_dir = _create_cmproj(tmp_path)
        original = (proj_dir / "project.tscproj").read_text()
        with use_project(proj_dir, save_on_exit=False) as proj:
            proj.timeline.add_track("should-not-persist")
        after = (proj_dir / "project.tscproj").read_text()
        assert original == after


class TestNewProject:
    def test_new_project_creates_cmproj(self, tmp_path: Path):
        project_path = tmp_path / "brand_new.cmproj"
        new_project(project_path)
        assert project_path.exists()
        assert (project_path / "project.tscproj").exists()

    def test_new_project_is_loadable(self, tmp_path: Path):
        project_path = tmp_path / "brand_new.cmproj"
        new_project(project_path)
        project = load_project(project_path)
        assert isinstance(project.timeline, Timeline)
        assert isinstance(project.media_bin, MediaBin)
        assert list(project.media_bin) == []


class TestProjectRepr:
    def test_project_repr(self, project):
        r = repr(project)
        assert r.startswith("<Project ")
        assert "tracks=" in r
        assert "clips=" in r
        assert r.endswith(">")


class TestFromTemplate:
    def test_from_template_creates_project(self, tmp_path: Path):
        dest = tmp_path / "templated.cmproj"
        proj = Project.new(dest)
        assert dest.exists()
        assert isinstance(proj, Project)
        assert proj.width == 1920
        assert proj.height == 1080

    def test_from_template_custom_settings(self, tmp_path: Path):
        dest = tmp_path / "custom.cmproj"
        proj = Project.new(
            dest, width=3840, height=2160, title="My Video",
        )
        assert proj.width == 3840
        assert proj.height == 2160
        assert proj.title == "My Video"



class TestHasScreenRecordingUnifiedMedia:
    def test_unified_media_screen_recording(self, tmp_path):
        proj_path = tmp_path / 'test.cmproj'
        new_project(proj_path)
        proj = load_project(proj_path)
        track = proj.timeline.add_track('Screen')
        m = {'id': 99, '_type': 'UnifiedMedia', 'src': 0, 'start': 0, 'duration': 100,
             'mediaStart': 0, 'mediaDuration': 100, 'scalar': 1,
             'metadata': {}, 'parameters': {}, 'effects': [], 'attributes': {'ident': ''},
             'animationTracks': {},
             'video': {'_type': 'ScreenVMFile', 'id': 100}}
        track._data.setdefault('medias', []).append(m)
        assert proj.has_screen_recording is True


class TestMergeProjectsTransitions:
    def test_transitions_remapped(self, tmp_path):
        src_path = tmp_path / 'src.cmproj'
        new_project(src_path)
        src = load_project(src_path)
        track = src.timeline.add_track('V')
        c1 = track.add_clip('VMFile', 0, 0, 100)
        c2 = track.add_clip('VMFile', 0, 100, 100)
        track._data.setdefault('transitions', []).append({
            'start': 100, 'duration': 10, 'leftMedia': c1.id, 'rightMedia': c2.id,
        })
        src.save()

        out_path = tmp_path / 'merged.cmproj'
        merged = Project.merge_projects([src], out_path)
        found_trans = False
        for t in merged.timeline.tracks:
            if t._data.get('transitions'):
                found_trans = True
                for tr in t._data['transitions']:
                    assert 'leftMedia' in tr
                    assert 'rightMedia' in tr
        assert found_trans


class TestValidateAudioMissingSourceTracks:
    def test_missing_range(self, tmp_path):
        proj_path = tmp_path / 'test.cmproj'
        new_project(proj_path)
        proj = load_project(proj_path)
        proj._data.setdefault('sourceBin', []).append({
            'id': 999, 'src': 'fake.wav', 'lastMod': '2024-01-01',
            'sourceTracks': [{'type': 2}],
            'rect': [0, 0, 100, 100],
        })
        issues = proj.validate()
        msgs = [i.message for i in issues]
        assert any('missing sourceTracks or range' in m for m in msgs)


class TestValidateImageMissingRect:
    def test_missing_rect(self, tmp_path):
        proj_path = tmp_path / 'test.cmproj'
        new_project(proj_path)
        proj = load_project(proj_path)
        proj._data.setdefault('sourceBin', []).append({
            'id': 998, 'src': 'fake.png', 'lastMod': '2024-01-01',
            'sourceTracks': [{'type': 1}],
        })
        issues = proj.validate()
        msgs = [i.message for i in issues]
        assert any('missing rect' in m for m in msgs)


class TestRepairZeroDuration:
    def test_zero_duration_removed(self, tmp_path):
        proj_path = tmp_path / 'test.cmproj'
        new_project(proj_path)
        proj = load_project(proj_path)
        track = proj.timeline.add_track('V')
        track._data['medias'] = [
            {'id': 60, '_type': 'VMFile', 'src': 0, 'start': 0, 'duration': 1,
             'mediaStart': 0, 'mediaDuration': 1, 'scalar': 1,
             'metadata': {}, 'parameters': {}, 'effects': [], 'attributes': {'ident': ''},
             'animationTracks': {}},
            {'id': 61, '_type': 'VMFile', 'src': 0, 'start': 0, 'duration': 100,
             'mediaStart': 0, 'mediaDuration': 100, 'scalar': 1,
             'metadata': {}, 'parameters': {}, 'effects': [], 'attributes': {'ident': ''},
             'animationTracks': {}},
        ]
        result = proj.repair()
        assert result.get('zero_duration_removed', 0) == 1


class TestDiffRemovedAddedTracks:
    def test_clips_on_removed_and_added_tracks(self, tmp_path):
        path_a = tmp_path / 'a.cmproj'
        path_b = tmp_path / 'b.cmproj'
        new_project(path_a)
        new_project(path_b)
        a = load_project(path_a)
        b = load_project(path_b)

        ta = a.timeline.add_track('ExtraA')
        ta.add_clip('VMFile', 0, 0, 100)
        b.timeline.add_track('ExtraB1')
        tb2 = b.timeline.add_track('ExtraB2')
        tb2.add_clip('VMFile', 0, 0, 100)

        result = diff_projects(a, b)
        assert result.has_changes

    def test_track_only_in_a(self, tmp_path):
        path_a = tmp_path / 'a2.cmproj'
        path_b = tmp_path / 'b2.cmproj'
        new_project(path_a)
        new_project(path_b)
        a = load_project(path_a)
        b = load_project(path_b)

        a.timeline.add_track('T2')
        t3 = a.timeline.add_track('T3')
        t3.add_clip('VMFile', 0, 0, 100)

        result = diff_projects(a, b)
        assert set(result.tracks_removed) == {2, 3}


class TestSpeedEffectScaling:
    def test_effect_times_scaled(self):
        clip = {'_type': 'VMFile', 'start': 0, 'duration': 1000,
                'mediaStart': 0, 'mediaDuration': 1000, 'scalar': 1,
                'effects': [{'start': 100, 'duration': 200}]}
        _scale_clip_timing(clip, Fraction(2))
        assert clip['effects'][0]['start'] == 200
        assert clip['effects'][0]['duration'] == 400


class TestSpeedStitchedMediaInnerEffects:
    def test_inner_effects_scaled(self):
        clip = {'_type': 'StitchedMedia', 'start': 0, 'duration': 1000,
                'mediaStart': 0, 'mediaDuration': 1000, 'scalar': 1,
                'metadata': {}, 'effects': [],
                'medias': [{'start': 0, 'duration': 500, 'mediaStart': 0, 'mediaDuration': 500,
                            'effects': [{'start': 10, 'duration': 20}]}]}
        _process_clip(clip, Fraction(2))
        inner_effect = clip['medias'][0]['effects'][0]
        assert inner_effect['start'] == 20
        assert inner_effect['duration'] == 40


class TestValidationVersionParseError:
    def test_invalid_version(self):
        data = {'version': 'not-a-number',
                'sceneTrack': {'scenes': [{'csml': {'tracks': []}}]}}
        _check_group_required_fields(data)


class TestValidationScalarParseError:
    def test_invalid_scalar(self):
        data = {'timeline': {'sceneTrack': {'scenes': [{'csml': {'tracks': [
            {'trackIndex': 0, 'medias': [
                {'id': 1, '_type': 'VMFile', 'scalar': '0/0',
                 'duration': 100, 'mediaDuration': 100}
            ]}
        ]}}]}}}
        _check_timing_consistency(data)


class TestWalkClipsUnified:
    def test_walk_clips_yields_unified_children(self):
        tracks = [{
            'medias': [{
                '_type': 'UnifiedMedia', 'id': 1, 'src': 10,
                'video': {'_type': 'ScreenVMFile', 'id': 2, 'src': 10},
                'audio': {'_type': 'AMFile', 'id': 3, 'src': 10},
            }]
        }]
        clips = list(_walk_clips(tracks))
        types = {c.get('_type') for c in clips}
        assert types == {'UnifiedMedia', 'ScreenVMFile', 'AMFile'}

    def test_replace_media_source_in_unified(self):
        data = {
            'timeline': {'sceneTrack': {'scenes': [{'csml': {'tracks': [{
                'medias': [{
                    '_type': 'UnifiedMedia', 'id': 1,
                    'video': {'_type': 'ScreenVMFile', 'id': 2, 'src': 10},
                    'audio': {'_type': 'AMFile', 'id': 3, 'src': 10},
                }]
            }]}}]}},
        }
        count = replace_media_source(data, 10, 20)
        assert count == 2
        um = data['timeline']['sceneTrack']['scenes'][0]['csml']['tracks'][0]['medias'][0]
        assert um['video']['src'] == 20
        assert um['audio']['src'] == 20


class TestRepairOverlapFix:
    """Test repair() overlap detection and mediaDuration recalculation."""

    def test_overlap_fixed_and_media_duration_recalculated(self, project, tmp_path):
        track = project.timeline.tracks[0]
        # Create two overlapping clips: clip1 at 0-100, clip2 at 50-150
        track._data.setdefault('medias', []).extend([
            {'_type': 'VMFile', 'id': 10, 'src': 0, 'start': 0, 'duration': 100,
             'mediaDuration': 100, 'mediaStart': 0, 'scalar': 1,
             'parameters': {}, 'effects': [], 'metadata': {}, 'animationTracks': {}},
            {'_type': 'VMFile', 'id': 11, 'src': 0, 'start': 50, 'duration': 100,
             'mediaDuration': 100, 'mediaStart': 0, 'scalar': 1,
             'parameters': {}, 'effects': [], 'metadata': {}, 'animationTracks': {}},
        ])
        result = project.repair()
        assert result.get('overlaps_fixed', 0) == 1
        # First clip's duration should be trimmed to 50 (no overlap)
        clip1 = next(m for m in track._data['medias'] if m['id'] == 10)
        assert clip1['duration'] == 50
        assert clip1['mediaDuration'] == 50  # recalculated: 50 / 1 = 50


def _make_timeline(track_specs):
    """Build a Timeline with tracks described as (name, media_list) tuples."""
    tracks = []
    attrs = []
    for i, (name, medias) in enumerate(track_specs):
        tracks.append({'trackIndex': i, 'medias': medias})
        attrs.append({'ident': name})
    data = {
        'sceneTrack': {'scenes': [{'csml': {'tracks': tracks}}]},
        'trackAttributes': attrs,
    }
    return Timeline(data)


def _make_project_data(track_medias_list):
    """Build minimal Project._data with given track medias."""
    tracks = []
    attrs = []
    for i, medias in enumerate(track_medias_list):
        tracks.append({'trackIndex': i, 'medias': medias})
        attrs.append({'ident': f'Track{i}'})
    return {
        'timeline': {
            'sceneTrack': {'scenes': [{'csml': {'tracks': tracks}}]},
            'trackAttributes': attrs,
        },
        'sourceBin': [],
    }


def test_project_has_screen_recording_with_real_data():
    """Test has_screen_recording against a real project fixture."""
    fixture = Path(__file__).parent / 'fixtures' / 'techsmith_sample.tscproj'
    data = json.loads(fixture.read_text())
    tracks = data['timeline']['sceneTrack']['scenes'][0]['csml']['tracks']

    has_screen = False
    for t in tracks:
        for m in t.get('medias', []):
            clip = clip_from_dict(m)
            if isinstance(clip, Group) and clip.is_screen_recording:
                has_screen = True
    # TechSmith sample has ScreenVMFile clips
    # (may or may not be inside Groups depending on the sample)
    assert has_screen is False




def test_media_count(project):
    assert project.media_count == 0




def test_project_is_empty_true(project):
    assert project.is_empty is True


def test_project_is_empty_false():
    fixture = Path(__file__).parent / 'fixtures' / 'test_project_c.tscproj'
    proj = load_project(fixture)
    assert proj.is_empty is False




def test_project_describe():
    fixture = Path(__file__).parent / 'fixtures' / 'test_project_c.tscproj'
    proj = load_project(fixture)
    desc = proj.describe()
    assert isinstance(desc, str)
    expected_substrings = {
        f'Project: {proj.file_path.name}',
        f'{proj.frame_rate}fps',
        'Duration:',
        'Tracks:',
        'Clips:',
        'Media:',
        'Health:',
    }
    for s in expected_substrings:
        assert s in desc


def test_project_describe_unhealthy(project):
    with patch.object(project, 'validate', return_value=[ValidationIssue('error', 'bad')]):
        actual = project.describe()
        assert '❌' in actual




def test_project_track_count():
    media = {'id': 1, '_type': 'VMFile', 'start': 0, 'duration': 100}
    proj = MagicMock(spec=Project)
    proj._data = _make_project_data([[media], []])
    proj.timeline = Timeline(proj._data['timeline'])
    assert Project.track_count.fget(proj) == 2


def test_project_clip_count():
    m1 = {'id': 1, '_type': 'VMFile', 'start': 0, 'duration': 100}
    m2 = {'id': 2, '_type': 'VMFile', 'start': 100, 'duration': 200}
    proj = MagicMock(spec=Project)
    proj._data = _make_project_data([[m1], [m2]])
    proj.timeline = Timeline(proj._data['timeline'])
    assert Project.clip_count.fget(proj) == 2


def test_project_duration_seconds(project):
    actual = project.duration_seconds
    assert isinstance(actual, float)
    assert actual == 0.0


def test_find_media_by_extension(project):
    wav = Path(__file__).parent / 'fixtures' / 'empty.wav'
    project.import_media(wav)
    actual = project.find_media_by_extension('wav')
    assert [Path(m.source).name for m in actual] == ['empty.wav']
    actual_none = project.find_media_by_extension('xyz')
    assert actual_none == []




def test_project_remove_all_effects(project):
    # Add a clip with effects to the project
    track = next(iter(project.timeline.tracks))
    media = {
        '_type': 'VMFile', 'id': 999, 'start': 0, 'duration': seconds_to_ticks(5.0),
        'effects': [{'effectName': 'FakeEffect1'}, {'effectName': 'FakeEffect2'}],
    }
    track._data['medias'].append(media)
    removed = project.remove_all_effects()
    assert removed == 2
    # Verify effects are cleared
    for t in project.timeline.tracks:
        for clip in t.clips:
            assert clip._data.get('effects', []) == []




def test_project_effect_summary(project):
    track = project.timeline.add_track('Test')
    c1 = track.add_clip('VMFile', 1, 0, 100)
    c1._data['effects'] = [{'effectName': 'Blur'}, {'effectName': 'Glow'}]
    c2 = track.add_clip('VMFile', 1, 100, 100)
    c2._data['effects'] = [{'effectName': 'Blur'}]
    result = project.effect_summary
    assert result == {'Blur': 2, 'Glow': 1}




def test_project_clip_type_summary(project):
    track = project.timeline.add_track('Test')
    track.add_clip('VMFile', 1, 0, 100)
    track.add_clip('AMFile', 1, 100, 100)
    track.add_clip('VMFile', 1, 200, 100)
    result = project.clip_type_summary
    assert result['VMFile'] == 2
    assert result['AMFile'] == 1




def test_summary_table():
    medias0 = [
        {'id': 1, '_type': 'ScreenRecording', 'start': 0, 'duration': 300, 'effects': [
            {'effectName': 'Blur'},
        ]},
        {'id': 2, '_type': 'UnifiedMedia', 'start': 300, 'duration': 600, 'effects': []},
    ]
    medias1 = []
    proj = MagicMock(spec=Project)
    proj._data = _make_project_data([medias0, medias1])
    proj.timeline = Timeline(proj._data['timeline'])
    proj.clip_count = 2
    proj.duration_seconds = 30.0

    result = Project.summary_table(proj)
    lines = result.split('\n')
    assert lines[0] == '| Track | Clips | Types | Duration | Effects |'
    assert lines[1].startswith('|---')
    # Track0 row
    assert '| Track0 |' in lines[2]
    assert '| 2 |' in lines[2]
    # Track1 row (empty)
    assert '| Track1 |' in lines[3]
    assert '| 0 |' in lines[3]
    # Total row
    assert '**Total**' in lines[4]
    assert '**2**' in lines[4]
    assert '**30.0s**' in lines[4]


def test_has_audio(project):
    assert project.has_audio is False  # empty project has no audio


def test_has_video(project):
    assert project.has_video is False  # empty project has no video




def test_source_bin_paths(tmp_path):
    project_dir = tmp_path / 'test.tscproj'
    project_dir.mkdir()
    project_file = project_dir / 'project.tscproj'
    project_data = {
        'title': 'test',
        'sourceBin': [
            {'id': 1, 'src': 'clip_a.mp4', 'rect': [0, 0, 100, 100], 'lastMod': '0', 'sourceTracks': []},
            {'id': 2, 'src': 'clip_b.wav', 'rect': [0, 0, 0, 0], 'lastMod': '0', 'sourceTracks': []},
        ],
        'timeline': {
            'sceneTrack': {'scenes': [{'csml': {'tracks': []}}]},
            'trackAttributes': [],
        },
        'authoringClientName': {'name': 'test', 'platform': 'test', 'version': '1'},
    }
    project_file.write_text(json.dumps(project_data))

    project = Project(project_dir)
    source_paths: list[str] = project.source_bin_paths
    assert {Path(p).name for p in source_paths} == {'clip_a.mp4', 'clip_b.wav'}




def test_total_effect_count(project):
    track = project.timeline.add_track('FX')
    clip = track.add_clip('VMFile', 1, 0, 705600000)
    clip.add_drop_shadow()
    clip.add_round_corners()
    assert project.total_effect_count == 2




def test_project_average_clip_duration(project):
    track = project.timeline.add_track('Test')
    track.add_clip('VMFile', 1, 0, 705600000 * 3)  # 3s
    track.add_clip('VMFile', 1, 705600000 * 4, 705600000 * 5)  # 5s
    assert project.average_clip_duration_seconds == pytest.approx(4.0)


def test_project_average_clip_duration_empty(project):
    assert project.average_clip_duration_seconds == 0.0




def test_replace_media_path(project):
    project._data.setdefault('sourceBin', []).extend([
        {'src': '/old/path/video.mp4'},
        {'src': '/old/path/audio.wav'},
    ])
    replaced_count: int = project.replace_media_path('/old/path', '/new/path')
    assert replaced_count == 2
    assert project._data['sourceBin'][-2]['src'] == '/new/path/video.mp4'
    assert project._data['sourceBin'][-1]['src'] == '/new/path/audio.wav'


def test_replace_media_path_no_match(project):
    project._data.setdefault('sourceBin', []).append({'src': '/some/other/file.mp4'})
    replaced_count: int = project.replace_media_path('/nonexistent', '/replacement')
    assert replaced_count == 0
    assert project._data['sourceBin'][-1]['src'] == '/some/other/file.mp4'




def test_project_has_effects(project):
    assert project.has_effects is False




def test_project_has_transitions(project):
    assert project.has_transitions is False




def test_project_has_keyframes(project):
    assert project.has_keyframes is False




def test_project_empty_tracks_returns_tracks_with_no_clips():
    """Project.empty_tracks delegates to timeline.empty_tracks."""
    timeline = _make_timeline([
        ('Audio', [{'id': 1, 'start': 0, 'duration': 100}]),
        ('Empty', []),
        ('Also Empty', []),
    ])
    empty_track_names: list[str] = [t.name for t in timeline.empty_tracks]
    assert set(empty_track_names) == {'Empty', 'Also Empty'}


def test_project_empty_tracks_returns_empty_list_when_all_have_clips():
    """Project.empty_tracks returns [] when every track has clips."""
    timeline = _make_timeline([
        ('A', [{'id': 1, 'start': 0, 'duration': 100}]),
    ])
    empty_tracks: list = timeline.empty_tracks
    assert empty_tracks == []




def test_remove_track_by_name_found(project):
    """remove_track_by_name removes the first matching track and returns True."""
    project.timeline.add_track('Disposable')
    initial_track_count: int = project.track_count
    removed: bool = project.remove_track_by_name('Disposable')
    assert removed is True
    assert project.track_count == initial_track_count - 1


def test_remove_track_by_name_not_found(project):
    """remove_track_by_name returns False when no track matches."""
    removed: bool = project.remove_track_by_name('NonExistent')
    assert removed is False


def test_remove_track_by_name_only_first(project):
    """remove_track_by_name removes only the first track with a duplicate name."""
    project.timeline.add_track('Dup')
    project.timeline.add_track('Dup')
    count_before: int = project.track_count
    project.remove_track_by_name('Dup')
    assert project.track_count == count_before - 1
    remaining_names: list[str] = [t.name for t in project.timeline.tracks]
    assert 'Dup' in remaining_names


def test_project_empty_tracks_property(project):
    """Project.empty_tracks delegates to timeline.empty_tracks."""
    actual_empty: list = project.empty_tracks
    assert isinstance(actual_empty, list)




class TestProbeMediaPymediainfo:
    def test_pymediainfo_video_track(self, monkeypatch):

        class FakeTrack:
            def __init__(self, track_type, **kw):
                self.track_type = track_type
                self.width = kw.get('width')
                self.height = kw.get('height')
                self.duration = kw.get('duration')
                self.frame_rate = kw.get('frame_rate')
                self.sampling_rate = kw.get('sampling_rate')
                self.channel_s = kw.get('channel_s')
                self.bit_depth = kw.get('bit_depth')

        class FakeInfo:
            tracks: ClassVar[list] = [
                FakeTrack('General'),
                FakeTrack('Video', width=1920, height=1080, duration=5000, frame_rate='30.0'),
            ]

        class FakeMediaInfo:
            @staticmethod
            def parse(path):
                return FakeInfo()

        fake_module = type(sys)('pymediainfo')
        fake_module.MediaInfo = FakeMediaInfo
        monkeypatch.setitem(sys.modules, 'pymediainfo', fake_module)

        result = _probe_media(Path('/fake/video.mp4'))
        assert result['width'] == 1920
        assert result['height'] == 1080
        assert result['_backend'] == 'pymediainfo'

    def test_pymediainfo_import_error_falls_back_to_ffprobe(self, monkeypatch):
        """When pymediainfo raises ImportError, _probe_media falls back to ffprobe."""

        # Make pymediainfo import fail
        monkeypatch.delitem(sys.modules, 'pymediainfo', raising=False)
        real_import = __builtins__['__import__'] if isinstance(__builtins__, dict) else __builtins__.__import__
        def _fail_pymediainfo(name, *a, **kw):
            if name == 'pymediainfo':
                raise ImportError('mocked')
            return real_import(name, *a, **kw)
        monkeypatch.setattr('builtins.__import__', _fail_pymediainfo)

        # Make ffprobe return valid data
        call_count = [0]
        def fake_run(*args, **kwargs):
            call_count[0] += 1
            r = type('R', (), {'stdout': '', 'returncode': 0})()
            if call_count[0] == 1:
                r.stdout = '1280,720\n'
            elif call_count[0] == 2:
                r.stdout = '10.0\n'
            return r
        monkeypatch.setattr(subprocess, 'run', fake_run)

        result = _probe_media(Path('/fake/video.mp4'))
        assert result['width'] == 1280
        assert result['height'] == 720
        assert result['duration_seconds'] == 10.0

    def test_pymediainfo_exception_falls_back_to_ffprobe(self, monkeypatch):
        """When pymediainfo.parse raises an exception, _probe_media falls back to ffprobe."""

        class BadMediaInfo:
            @staticmethod
            def parse(path):
                raise RuntimeError('parse failed')

        fake_module = type(sys)('pymediainfo')
        fake_module.MediaInfo = BadMediaInfo
        monkeypatch.setitem(sys.modules, 'pymediainfo', fake_module)

        call_count = [0]
        def fake_run(*args, **kwargs):
            call_count[0] += 1
            r = type('R', (), {'stdout': '', 'returncode': 0})()
            if call_count[0] == 1:
                r.stdout = '640,480\n'
            elif call_count[0] == 2:
                r.stdout = '5.0\n'
            return r
        monkeypatch.setattr(subprocess, 'run', fake_run)

        result = _probe_media(Path('/fake/video.mp4'))
        assert result['width'] == 640
        assert result['duration_seconds'] == 5.0



class TestProbeMediaFfprobe:
    def test_ffprobe_parses_width_height(self, monkeypatch):

        call_count = [0]
        def fake_run(*args, **kwargs):
            call_count[0] += 1
            result = type('R', (), {'stdout': '', 'returncode': 0})()
            if call_count[0] == 1:
                result.stdout = '1920,1080\n'
            elif call_count[0] == 2:
                result.stdout = '5.5\n'
            return result

        monkeypatch.setattr(subprocess, 'run', fake_run)
        result = _probe_media_ffprobe(Path('/fake/video.mp4'))
        assert result['width'] == 1920
        assert result['height'] == 1080
        assert result['duration_seconds'] == 5.5

    def test_ffprobe_exception_returns_minimal(self, monkeypatch):

        def fail_run(*args, **kwargs):
            raise OSError('ffprobe not found')

        monkeypatch.setattr(subprocess, 'run', fail_run)
        result = _probe_media_ffprobe(Path('/fake/video.mp4'))
        assert '_backend' in result
        assert 'width' not in result
        assert 'duration_seconds' not in result



class TestRemapSrcRecursive:
    def test_remaps_src(self):
        clip = {'src': 1}
        _remap_src_recursive(clip, {1: 10})
        assert clip['src'] == 10

    def test_remaps_video_audio(self):
        clip = {'src': 1, 'video': {'src': 2}, 'audio': {'src': 3}}
        _remap_src_recursive(clip, {1: 10, 2: 20, 3: 30})
        assert clip['video']['src'] == 20
        assert clip['audio']['src'] == 30

    def test_remaps_tracks(self):
        clip = {'tracks': [{'medias': [{'src': 5}]}]}
        _remap_src_recursive(clip, {5: 50})
        assert clip['tracks'][0]['medias'][0]['src'] == 50

    def test_remaps_medias(self):
        clip = {'medias': [{'src': 7}]}
        _remap_src_recursive(clip, {7: 70})
        assert clip['medias'][0]['src'] == 70



class TestHasScreenRecordingDirect:
    def test_screen_vmfile_clip(self, project):
        track = project.timeline.add_track('Screen')
        track._data.setdefault('medias', []).append({
            'id': 99, '_type': 'ScreenVMFile', 'src': 0, 'start': 0, 'duration': 100,
            'mediaStart': 0, 'mediaDuration': 100, 'scalar': 1,
        })
        assert project.has_screen_recording is True



class TestSwapTracksShortAttrs:
    def test_warns_when_attrs_too_short(self, tmp_path, monkeypatch):
        """When trackAttributes is shorter than the track indices being swapped, a ValueError is raised."""
        data = json.loads(json.dumps(MINIMAL_PROJECT_DATA))
        data['timeline']['sceneTrack']['scenes'][0]['csml']['tracks'] = [
            {'trackIndex': 0, 'medias': []},
            {'trackIndex': 1, 'medias': []},
        ]
        # Only 1 trackAttribute entry — shorter than max(0, 1)
        data['timeline']['trackAttributes'] = [
            {'ident': 'A', 'audioMuted': False, 'videoHidden': False},
        ]
        proj_dir = _create_cmproj(tmp_path, data)
        proj = Project(proj_dir)
        tracks_data = data['timeline']['sceneTrack']['scenes'][0]['csml']['tracks']
        track_a = Track({'ident': 'A'}, tracks_data[0])
        track_b = Track({'ident': 'B'}, tracks_data[1])
        results = [track_a, track_b]
        call_idx = [0]
        orig_find = Timeline.find_track_by_name
        def patched_find(self_tl, name):
            i = call_idx[0]
            call_idx[0] += 1
            return results[i] if i < len(results) else orig_find(self_tl, name)
        monkeypatch.setattr(Timeline, 'find_track_by_name', patched_find)
        with pytest.raises(ValueError, match='trackAttributes length'):
            proj.swap_tracks('A', 'B')



class TestAllClipsNested:
    def test_stitched_media_nested(self, project):
        track = project.timeline.tracks[0]
        track._data['medias'] = [{
            'id': 1, '_type': 'StitchedMedia', 'start': 0, 'duration': 100,
            'medias': [{'id': 2, '_type': 'VMFile', 'start': 0, 'duration': 50}],
        }]
        clips = project.all_clips
        types = {c.clip_type for _, c in clips}
        assert types == {'StitchedMedia', 'VMFile'}

    def test_unified_media_nested(self, project):
        track = project.timeline.tracks[0]
        track._data['medias'] = [{
            'id': 1, '_type': 'UnifiedMedia', 'start': 0, 'duration': 100,
            'video': {'id': 2, '_type': 'VMFile', 'start': 0, 'duration': 100},
            'audio': {'id': 3, '_type': 'AMFile', 'start': 0, 'duration': 100},
        }]
        clips = project.all_clips
        types = {c.clip_type for _, c in clips}
        assert types == {'UnifiedMedia', 'VMFile', 'AMFile'}



class TestValidateOverlaps:
    def test_overlapping_clips_reported(self, project):
        track = project.timeline.tracks[0]
        track._data['medias'] = [
            {'id': 1, '_type': 'VMFile', 'start': 0, 'duration': 200},
            {'id': 2, '_type': 'VMFile', 'start': 100, 'duration': 200},
        ]
        issues = project.validate()
        overlap_issues = [i for i in issues if 'Overlapping' in i.message]
        assert 'clip 1' in overlap_issues[0].message
        assert 'clip 2' in overlap_issues[0].message



class TestValidateAndReport:
    def test_no_issues(self, project):
        report = project.validate_and_report()
        assert 'No issues found' in report

    def test_with_issues(self, project):
        track = project.timeline.tracks[0]
        track._data['medias'] = [
            {'id': 1, '_type': 'VMFile', 'start': 0, 'duration': 200},
            {'id': 2, '_type': 'VMFile', 'start': 100, 'duration': 200},
        ]
        report = project.validate_and_report()
        assert 'issue(s) found' in report



class TestSaveSpecialFloats:
    def test_infinity_replaced(self, project):
        project._data['timeline']['sceneTrack']['scenes'][0]['csml']['tracks'][0]['medias'] = [{
            'id': 1, '_type': 'VMFile', 'start': 0, 'duration': 100,
            'parameters': {'scale': float('inf'), 'neg': float('-inf'), 'bad': float('nan')},
        }]
        project.save()
        text = (project.file_path / 'project.tscproj').read_text()
        assert '-Infinity' not in text
        assert 'NaN' not in text



class TestImportMediaUnknownExtension:
    def test_raises_for_unknown_extension(self, project, tmp_path):
        bad_file = tmp_path / 'file.xyz'
        bad_file.write_bytes(b'\x00')
        with pytest.raises(ValueError, match="Cannot determine media type"):
            project.import_media(bad_file)



class TestImportMediaDurationDefaults:
    def test_audio_duration_from_probe(self, project, tmp_path, monkeypatch):
        wav = tmp_path / 'test.wav'
        wav.write_bytes(b'\x00')
        monkeypatch.setattr(proj_mod, '_probe_media', lambda p: {
            '_backend': 'ffprobe', 'duration_seconds': 2.0, 'sample_rate': 44100,
        })
        media = project.import_media(wav)
        assert media is not None

    def test_video_duration_from_probe(self, project, tmp_path, monkeypatch):
        mp4 = tmp_path / 'test.mp4'
        mp4.write_bytes(b'\x00')
        monkeypatch.setattr(proj_mod, '_probe_media', lambda p: {
            '_backend': 'ffprobe', 'duration_seconds': 3.0, 'frame_rate': 30,
        })
        media = project.import_media(mp4)
        assert media is not None



class TestMediaSummary:
    def test_media_summary_counts_extensions(self, project, tmp_path, monkeypatch):
        # Add some media entries directly
        project._data['sourceBin'] = [
            {'id': 1, 'src': './media/a.mov', 'rect': [0,0,1920,1080], 'lastMod': '20200101T000000',
             'sourceTracks': [{'type': 0, 'editRate': 30, 'range': [0, 100], 'trackRect': [0,0,1920,1080],
                               'sampleRate': 0, 'bitDepth': 0, 'numChannels': 0}]},
            {'id': 2, 'src': './media/b.mov', 'rect': [0,0,1920,1080], 'lastMod': '20200101T000000',
             'sourceTracks': [{'type': 0, 'editRate': 30, 'range': [0, 100], 'trackRect': [0,0,1920,1080],
                               'sampleRate': 0, 'bitDepth': 0, 'numChannels': 0}]},
            {'id': 3, 'src': './media/c.wav', 'rect': [0,0,0,0], 'lastMod': '20200101T000000',
             'sourceTracks': [{'type': 2, 'editRate': 44100, 'range': [0, 44100], 'trackRect': [0,0,0,0],
                               'sampleRate': 44100, 'bitDepth': 16, 'numChannels': 2}]},
        ]
        summary = project.media_summary
        assert summary['mov'] == 2
        assert summary['wav'] == 1



class TestRescaleTimeline:
    def test_rescale_timeline(self, project):
        track = project.timeline.tracks[0]
        track._data['medias'] = [
            {'id': 1, '_type': 'VMFile', 'start': 0, 'duration': 1000, 'mediaDuration': 1000, 'scalar': 1},
        ]
        project.rescale_timeline(2.0)
        assert track._data['medias'][0]['duration'] == 2000



class TestNormalizeAudio:
    def test_normalize_unified_media(self, project):
        track = project.timeline.tracks[0]
        track._data['medias'] = [{
            'id': 1, '_type': 'UnifiedMedia', 'start': 0, 'duration': 100,
            'audio': {'_type': 'AMFile', 'attributes': {'gain': 0.5}},
        }]
        count = project.normalize_audio(target_gain=0.8)
        assert count == 2

    def test_normalize_amfile(self, project):
        track = project.timeline.tracks[0]
        track._data['medias'] = [{
            'id': 1, '_type': 'AMFile', 'src': 0, 'start': 0, 'duration': 100,
            'mediaStart': 0, 'mediaDuration': 100, 'scalar': 1,
            'channelNumber': '0,1',
            'attributes': {'ident': '', 'gain': 0.5, 'mixToMono': False, 'loudnessNormalization': False},
        }]
        count = project.normalize_audio(target_gain=0.9)
        assert count == 1



class TestHealthReportGaps:
    def test_gaps_in_health_report(self, project):
        track = project.timeline.tracks[0]
        track._data['medias'] = [
            {'id': 1, '_type': 'VMFile', 'start': 0, 'duration': 100},
            {'id': 2, '_type': 'VMFile', 'start': 300, 'duration': 100},
        ]
        report = project.health_report()
        assert '- Gaps:' in report

    def test_transitions_in_health_report(self, project):
        track = project.timeline.tracks[0]
        track._data['medias'] = [
            {'id': 1, '_type': 'VMFile', 'start': 0, 'duration': 200},
            {'id': 2, '_type': 'VMFile', 'start': 200, 'duration': 200},
        ]
        track._data['transitions'] = [{
            'name': 'FadeThroughBlack', 'duration': 100,
            'leftMedia': 1, 'rightMedia': 2,
            'attributes': {'bypass': False, 'reverse': False, 'trivial': False,
                           'useAudioPreRoll': True, 'useVisualPreRoll': True},
        }]
        report = project.health_report()
        assert '- Transitions:' in report


# ── Helpers for video production tests ──────────────────────────────

FIXTURES = Path(__file__).parent / 'fixtures'
EMPTY_WAV = FIXTURES / 'empty.wav'
EMPTY2_WAV = FIXTURES / 'empty2.wav'
TEST_WAV = FIXTURES / 'empty.wav'


def _make_minimal_png(path: Path) -> None:
    """Write a valid 1x1 white PNG file."""
    signature = b'\x89PNG\r\n\x1a\n'
    ihdr_data = struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0)
    ihdr = _png_chunk(b'IHDR', ihdr_data)
    raw_row = b'\x00\xff\xff\xff'
    idat = _png_chunk(b'IDAT', zlib.compress(raw_row))
    iend = _png_chunk(b'IEND', b'')
    path.write_bytes(signature + ihdr + idat + iend)


def _png_chunk(chunk_type: bytes, data: bytes) -> bytes:
    length = struct.pack('>I', len(data))
    crc = struct.pack('>I', zlib.crc32(chunk_type + data) & 0xFFFFFFFF)
    return length + chunk_type + data + crc


# ── Project.add_voiceover_sequence_v2 ───────────────────────────────


class TestAddVoiceoverSequenceV2:
    def test_single_audio_file(self, project):
        placed = project.add_voiceover_sequence_v2([EMPTY_WAV])
        assert placed[0].clip_type == 'AMFile'
        assert placed[0].start == 0

    def test_multiple_audio_files(self, project):
        placed = project.add_voiceover_sequence_v2([EMPTY_WAV, EMPTY2_WAV])
        assert [c.clip_type for c in placed] == ['AMFile', 'AMFile']

    def test_clips_are_sequential(self, project):
        placed = project.add_voiceover_sequence_v2([EMPTY_WAV, EMPTY2_WAV])
        first_end = placed[0].start_seconds + placed[0].duration_seconds
        assert abs(placed[1].start_seconds - first_end) < 0.01

    def test_custom_start_seconds(self, project):
        placed = project.add_voiceover_sequence_v2([EMPTY_WAV], start_seconds=10.0)
        assert abs(placed[0].start_seconds - 10.0) < 0.01

    def test_gap_between_clips(self, project):
        placed = project.add_voiceover_sequence_v2([EMPTY_WAV, EMPTY2_WAV], gap_seconds=2.0)
        first_end = placed[0].start_seconds + placed[0].duration_seconds
        assert abs(placed[1].start_seconds - first_end - 2.0) < 0.01

    def test_custom_track_name(self, project):
        project.add_voiceover_sequence_v2([EMPTY_WAV], track_name='Narration')
        track = project.timeline.get_or_create_track('Narration')
        assert next(iter(track)).clip_type == 'AMFile'

    def test_empty_list_returns_empty(self, project):
        assert project.add_voiceover_sequence_v2([]) == []

    def test_string_paths_accepted(self, project):
        placed = project.add_voiceover_sequence_v2([str(EMPTY_WAV)])
        assert placed[0].clip_type == 'AMFile'


# ── Project.add_image_sequence ──────────────────────────────────────


class TestAddImageSequence:
    @pytest.fixture(autouse=True)
    def _create_test_images(self, tmp_path: Path):
        self.image_a = tmp_path / 'slide_a.png'
        self.image_b = tmp_path / 'slide_b.png'
        _make_minimal_png(self.image_a)
        _make_minimal_png(self.image_b)

    def test_single_image(self, project):
        placed = project.add_image_sequence([self.image_a])
        assert placed[0].clip_type == 'IMFile'
        assert placed[0].start_seconds == pytest.approx(0.0, abs=0.01)

    def test_multiple_images(self, project):
        placed = project.add_image_sequence([self.image_a, self.image_b])
        assert [c.clip_type for c in placed] == ['IMFile', 'IMFile']

    def test_clips_are_sequential(self, project):
        placed = project.add_image_sequence(
            [self.image_a, self.image_b], per_image_seconds=4.0, fade_seconds=0)
        first_end = placed[0].start_seconds + placed[0].duration_seconds
        assert abs(placed[1].start_seconds - first_end) < 0.01

    def test_per_image_duration(self, project):
        placed = project.add_image_sequence([self.image_a], per_image_seconds=7.0, fade_seconds=0)
        assert abs(placed[0].duration_seconds - 7.0) < 0.01

    def test_custom_start_seconds(self, project):
        placed = project.add_image_sequence([self.image_a], start_seconds=5.0)
        assert abs(placed[0].start_seconds - 5.0) < 0.01

    def test_custom_track_name(self, project):
        project.add_image_sequence([self.image_a], track_name='Slides')
        track = project.timeline.get_or_create_track('Slides')
        assert next(iter(track)).clip_type == 'IMFile'

    def test_fade_applied_by_default(self, project):
        placed = project.add_image_sequence([self.image_a], fade_seconds=0.5)
        anim = placed[0]._data.get('animationTracks', {})
        assert 'visual' in anim
        assert len(anim.get('visual', [])) == 2

    def test_no_fade_when_zero(self, project):
        placed = project.add_image_sequence([self.image_a], fade_seconds=0)
        anim = placed[0]._data.get('animationTracks', {})
        assert anim.get('visual', []) == []

    def test_empty_list_returns_empty(self, project):
        assert project.add_image_sequence([]) == []

    def test_string_paths_accepted(self, project):
        placed = project.add_image_sequence([str(self.image_a)])
        assert placed[0].clip_type == 'IMFile'


# ── Project.add_watermark ──────────────────────────────────────────


class TestAddWatermarkReturn:
    def test_returns_base_clip(self, project):
        actual_clip = project.add_watermark(TEST_WAV)
        assert isinstance(actual_clip, BaseClip)


class TestAddWatermarkOpacity:
    def test_default_opacity(self, project):
        actual_clip = project.add_watermark(TEST_WAV)
        assert actual_clip.opacity == 0.3

    def test_custom_opacity(self, project):
        actual_clip = project.add_watermark(TEST_WAV, opacity=0.5)
        assert actual_clip.opacity == 0.5


class TestAddWatermarkTrack:
    def test_default_track_name(self, project):
        project.add_watermark(TEST_WAV)
        track = project.timeline.find_track_by_name('Watermark')
        assert track is not None
        assert next(iter(track)).clip_type == 'IMFile'

    def test_custom_track_name(self, project):
        project.add_watermark(TEST_WAV, track_name='Logo')
        track = project.timeline.find_track_by_name('Logo')
        assert track is not None
        assert next(iter(track)).clip_type == 'IMFile'


class TestAddWatermarkDuration:
    def test_empty_project_uses_fallback(self, project):
        assert project.duration_seconds == 0
        actual_clip = project.add_watermark(TEST_WAV)
        assert actual_clip.duration_seconds == pytest.approx(60.0)

    def test_clip_starts_at_zero(self, project):
        actual_clip = project.add_watermark(TEST_WAV)
        assert actual_clip.start == 0


class TestAddWatermarkMedia:
    def test_media_imported(self, project):
        before = project.media_count
        project.add_watermark(TEST_WAV)
        assert project.media_count == before + 1


class TestAddWatermarkStringPath:
    def test_string_path_accepted(self, project):
        actual_clip = project.add_watermark(str(TEST_WAV))
        assert isinstance(actual_clip, BaseClip)


# ── Project.add_countdown ──────────────────────────────────────────


class TestAddCountdownReturn:
    def test_returns_list(self, project):
        actual_result = project.add_countdown()
        assert isinstance(actual_result, list)

    def test_default_returns_three_clips(self, project):
        actual_result = project.add_countdown()
        assert [c.text for c in actual_result] == ['3', '2', '1']

    def test_all_are_base_clips(self, project):
        for clip in project.add_countdown():
            assert isinstance(clip, BaseClip)


class TestAddCountdownText:
    def test_text_is_descending(self, project):
        clips = project.add_countdown(seconds=3)
        assert [c.text for c in clips] == ['3', '2', '1']

    def test_custom_seconds(self, project):
        clips = project.add_countdown(seconds=5)
        assert [c.text for c in clips] == ['5', '4', '3', '2', '1']


class TestAddCountdownTrack:
    def test_default_track_name(self, project):
        project.add_countdown()
        track = project.timeline.find_track_by_name('Countdown')
        assert track is not None
        assert [c.clip_type for c in track] == ['Callout', 'Callout', 'Callout']

    def test_custom_track_name(self, project):
        project.add_countdown(track_name='Timer')
        track = project.timeline.find_track_by_name('Timer')
        assert track is not None


class TestAddCountdownTiming:
    def test_clips_are_sequential(self, project):
        clips = project.add_countdown(seconds=3, per_number_seconds=1.0)
        starts = [c.start_seconds for c in clips]
        assert starts[0] < starts[1] < starts[2]

    def test_first_clip_starts_at_zero(self, project):
        clips = project.add_countdown()
        assert clips[0].start_seconds == pytest.approx(0.0, abs=0.01)

    def test_custom_per_number_seconds(self, project):
        clips = project.add_countdown(seconds=2, per_number_seconds=2.0)
        assert clips[1].start_seconds == pytest.approx(2.0, abs=0.01)


class TestAddCountdownFontSize:
    def test_font_size_is_96(self, project):
        clips = project.add_countdown()
        assert clips[0].font['size'] == 96.0


class TestAddCountdownFades:
    def test_fades_applied(self, project):
        clips = project.add_countdown()
        for clip in clips:
            assert clip._data.get('parameters', {}).get('opacity') is not None


# ── Project.add_section_divider ────────────────────────────────────


class TestAddSectionDividerBasic:
    def test_returns_clip(self, project):
        clip = project.add_section_divider('Chapter 1', at_seconds=10.0)
        assert clip is not None

    def test_clip_text(self, project):
        clip = project.add_section_divider('Intro', at_seconds=0.0)
        assert clip.text == 'Intro'

    def test_default_track_name(self, project):
        project.add_section_divider('Part 1', at_seconds=5.0)
        track = project.timeline.find_track_by_name('Section Dividers')
        assert track is not None
        assert next(iter(track)).clip_type == 'Callout'

    def test_custom_track_name(self, project):
        project.add_section_divider('Part 1', at_seconds=5.0, track_name='Dividers')
        track = project.timeline.find_track_by_name('Dividers')
        assert track is not None

    def test_font_size_48(self, project):
        clip = project.add_section_divider('Title', at_seconds=0.0)
        assert clip.font['size'] == 48.0

    def test_default_duration(self, project):
        clip = project.add_section_divider('Title', at_seconds=0.0)
        assert clip.duration_seconds == pytest.approx(3.0, abs=0.1)

    def test_custom_duration(self, project):
        clip = project.add_section_divider('Title', at_seconds=0.0, duration_seconds=7.0)
        assert clip.duration_seconds == pytest.approx(7.0, abs=0.1)


class TestAddSectionDividerFades:
    def test_fades_applied_by_default(self, project):
        clip = project.add_section_divider('Faded', at_seconds=0.0)
        assert clip._data.get('parameters', {}).get('opacity') is not None

    def test_no_fades_when_zero(self, project):
        clip = project.add_section_divider('NoFade', at_seconds=0.0, fade_seconds=0.0)
        assert clip.effect_count == 0


class TestAddSectionDividerMarker:
    def test_marker_added(self, project):
        project.add_section_divider('Chapter 2', at_seconds=30.0)
        marker_names = [m.name for m in project.timeline.markers]
        assert 'Chapter 2' in marker_names

    def test_multiple_dividers_add_multiple_markers(self, project):
        project.add_section_divider('Part A', at_seconds=10.0)
        project.add_section_divider('Part B', at_seconds=20.0)
        marker_names = [m.name for m in project.timeline.markers]
        assert 'Part A' in marker_names
        assert 'Part B' in marker_names


# ── Project.add_end_card ───────────────────────────────────────────


class TestAddEndCardBasic:
    def test_returns_clip(self, project):
        clip = project.add_end_card()
        assert clip is not None

    def test_default_text(self, project):
        clip = project.add_end_card()
        assert clip.text == 'Thank You'

    def test_custom_title(self, project):
        clip = project.add_end_card(title_text='The End')
        assert clip.text == 'The End'

    def test_subtitle_combined(self, project):
        clip = project.add_end_card(title_text='Thanks', subtitle_text='See you next time')
        assert clip.text == 'Thanks\nSee you next time'

    def test_no_subtitle_no_newline(self, project):
        clip = project.add_end_card(title_text='Bye', subtitle_text='')
        assert '\n' not in clip.text

    def test_default_track_name(self, project):
        project.add_end_card()
        track = project.timeline.find_track_by_name('End Card')
        assert track is not None
        assert next(iter(track)).clip_type == 'Callout'

    def test_custom_track_name(self, project):
        project.add_end_card(track_name='Outro')
        track = project.timeline.find_track_by_name('Outro')
        assert track is not None

    def test_font_size_48(self, project):
        clip = project.add_end_card()
        assert clip.font['size'] == 48.0

    def test_default_duration(self, project):
        clip = project.add_end_card()
        assert clip.duration_seconds == pytest.approx(5.0, abs=0.1)

    def test_custom_duration(self, project):
        clip = project.add_end_card(duration_seconds=10.0)
        assert clip.duration_seconds == pytest.approx(10.0, abs=0.1)


class TestAddEndCardFades:
    def test_fades_applied_by_default(self, project):
        clip = project.add_end_card()
        assert clip._data.get('parameters', {}).get('opacity') is not None

    def test_no_fades_when_zero(self, project):
        clip = project.add_end_card(fade_seconds=0.0)
        assert clip.effect_count == 0


class TestAddEndCardPosition:
    def test_placed_at_timeline_end(self, project):
        clip = project.add_end_card()
        assert clip.start_seconds == pytest.approx(0.0, abs=0.1)
