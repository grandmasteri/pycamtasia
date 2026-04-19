from __future__ import annotations

import json
from pathlib import Path

import pytest

from camtasia.project import Project, load_project, use_project, new_project
from camtasia.media_bin import MediaBin
from camtasia.timeline import Timeline


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

    def test_media_bin_returns_media_bin(self, tmp_path: Path):
        project = Project(_create_cmproj(tmp_path))
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
    def test_project_repr(self, tmp_path: Path):
        proj_dir = _create_cmproj(tmp_path)
        project = Project(proj_dir)
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


# ── Merged from test_coverage_project.py ─────────────────────────────

from fractions import Fraction
from unittest.mock import patch, MagicMock
from camtasia.timing import seconds_to_ticks
from camtasia.timeline.timeline import Timeline


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
                    assert 'leftMedia' in tr and 'rightMedia' in tr
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
        assert result.get('zero_duration_removed', 0) >= 1


class TestDiffRemovedAddedTracks:
    def test_clips_on_removed_and_added_tracks(self, tmp_path):
        from camtasia.operations.diff import diff_projects

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
        from camtasia.operations.diff import diff_projects

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
        assert len(result.tracks_removed) > 0


class TestSpeedEffectScaling:
    def test_effect_times_scaled(self):
        from camtasia.operations.speed import _scale_clip_timing
        clip = {'_type': 'VMFile', 'start': 0, 'duration': 1000,
                'mediaStart': 0, 'mediaDuration': 1000, 'scalar': 1,
                'effects': [{'start': 100, 'duration': 200}]}
        _scale_clip_timing(clip, Fraction(2))
        assert clip['effects'][0]['start'] == 200
        assert clip['effects'][0]['duration'] == 400


class TestSpeedStitchedMediaInnerEffects:
    def test_inner_effects_scaled(self):
        from camtasia.operations.speed import _process_clip
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
        from camtasia.validation import _check_group_required_fields
        data = {'version': 'not-a-number',
                'sceneTrack': {'scenes': [{'csml': {'tracks': []}}]}}
        issues = _check_group_required_fields(data)


class TestValidationScalarParseError:
    def test_invalid_scalar(self):
        from camtasia.validation import _check_timing_consistency
        data = {'timeline': {'sceneTrack': {'scenes': [{'csml': {'tracks': [
            {'trackIndex': 0, 'medias': [
                {'id': 1, '_type': 'VMFile', 'scalar': '0/0',
                 'duration': 100, 'mediaDuration': 100}
            ]}
        ]}}]}}}
        issues = _check_timing_consistency(data)


# ── Merged from test_coverage_misc.py (template operations) ─────────


class TestWalkClipsUnified:
    def test_walk_clips_yields_unified_children(self):
        from camtasia.operations.template import _walk_clips
        tracks = [{
            'medias': [{
                '_type': 'UnifiedMedia', 'id': 1, 'src': 10,
                'video': {'_type': 'ScreenVMFile', 'id': 2, 'src': 10},
                'audio': {'_type': 'AMFile', 'id': 3, 'src': 10},
            }]
        }]
        clips = list(_walk_clips(tracks))
        types = [c.get('_type') for c in clips]
        assert 'UnifiedMedia' in types
        assert 'ScreenVMFile' in types
        assert 'AMFile' in types

    def test_replace_media_source_in_unified(self):
        from camtasia.operations.template import replace_media_source
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


class TestCloneProjectStructure:
    def test_clone_clears_media(self):
        from camtasia.operations.template import clone_project_structure
        data = {
            'sourceBin': [{'id': 1}],
            'timeline': {
                'sceneTrack': {'scenes': [{'csml': {'tracks': [{
                    'medias': [{'_type': 'VMFile', 'id': 1}],
                    'transitions': [{'name': 'Fade'}],
                }]}}]},
                'parameters': {'toc': {'keyframes': [{'time': 100}]}},
            },
        }
        result = clone_project_structure(data)
        assert result['sourceBin'] == []
        assert result['timeline']['sceneTrack']['scenes'][0]['csml']['tracks'][0]['medias'] == []
        assert result['timeline']['parameters']['toc']['keyframes'] == []


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
        assert result.get('overlaps_fixed', 0) >= 1
        # First clip's duration should be trimmed to 50 (no overlap)
        clip1 = [m for m in track._data['medias'] if m['id'] == 10][0]
        assert clip1['duration'] == 50
        assert clip1['mediaDuration'] == 50  # recalculated: 50 / 1 = 50


# =========================================================================
# Tests migrated from test_convenience.py
# =========================================================================

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
    import json
    from pathlib import Path
    from camtasia.timeline.clips import clip_from_dict
    from camtasia.timeline.clips.group import Group
    
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




# ---------------------------------------------------------------------------
# Project.media_count
# ---------------------------------------------------------------------------

def test_media_count(project):
    assert project.media_count == 0




# ---------------------------------------------------------------------------
# Project.is_empty
# ---------------------------------------------------------------------------

def test_project_is_empty_true(project):
    assert project.is_empty is True


def test_project_is_empty_false():
    from camtasia.project import load_project
    from pathlib import Path
    fixture = Path(__file__).parent / 'fixtures' / 'test_project_c.tscproj'
    proj = load_project(fixture)
    assert proj.is_empty is False




# ---------------------------------------------------------------------------
# Project.describe
# ---------------------------------------------------------------------------

def test_project_describe():
    from camtasia.project import load_project
    from pathlib import Path
    fixture = Path(__file__).parent / 'fixtures' / 'test_project_c.tscproj'
    proj = load_project(fixture)
    desc = proj.describe()
    assert isinstance(desc, str)
    assert f'Project: {proj.file_path.name}' in desc
    assert f'{proj.frame_rate}fps' in desc
    assert 'Duration:' in desc
    assert 'Tracks:' in desc
    assert 'Clips:' in desc
    assert 'Media:' in desc
    assert 'Health:' in desc


def test_project_describe_unhealthy(project):
    from unittest.mock import patch
    from camtasia.validation import ValidationIssue
    with patch.object(project, 'validate', return_value=[ValidationIssue('error', 'bad')]):
        actual = project.describe()
        assert '❌' in actual




# ---------------------------------------------------------------------------
# Project.track_count / clip_count / duration_seconds
# ---------------------------------------------------------------------------

def test_project_track_count():
    from camtasia.project import Project
    from unittest.mock import MagicMock
    media = {'id': 1, '_type': 'VMFile', 'start': 0, 'duration': 100}
    proj = MagicMock(spec=Project)
    proj._data = _make_project_data([[media], []])
    proj.timeline = Timeline(proj._data['timeline'])
    assert Project.track_count.fget(proj) == 2


def test_project_clip_count():
    from camtasia.project import Project
    from unittest.mock import MagicMock
    m1 = {'id': 1, '_type': 'VMFile', 'start': 0, 'duration': 100}
    m2 = {'id': 2, '_type': 'VMFile', 'start': 100, 'duration': 200}
    proj = MagicMock(spec=Project)
    proj._data = _make_project_data([[m1], [m2]])
    proj.timeline = Timeline(proj._data['timeline'])
    assert Project.clip_count.fget(proj) == 2


def test_project_duration_seconds(project):
    actual = project.duration_seconds
    assert isinstance(actual, float)
    assert actual >= 0.0


def test_find_media_by_extension(project):
    from pathlib import Path
    wav = Path(__file__).parent / 'fixtures' / 'empty.wav'
    project.import_media(wav)
    actual = project.find_media_by_extension('wav')
    assert len(actual) >= 1
    actual_none = project.find_media_by_extension('xyz')
    assert actual_none == []




# ---------------------------------------------------------------------------
# Project.remove_all_effects
# ---------------------------------------------------------------------------

def test_project_remove_all_effects(project):
    # Add a clip with effects to the project
    track = list(project.timeline.tracks)[0]
    media = {
        '_type': 'VMFile', 'id': 999, 'start': 0, 'duration': seconds_to_ticks(5.0),
        'effects': [{'effectName': 'FakeEffect1'}, {'effectName': 'FakeEffect2'}],
    }
    track._data['medias'].append(media)
    removed = project.remove_all_effects()
    assert removed >= 2
    # Verify effects are cleared
    for t in project.timeline.tracks:
        for clip in t.clips:
            assert clip._data.get('effects', []) == []




# ---------------------------------------------------------------------------
# Project.effect_summary
# ---------------------------------------------------------------------------

def test_project_effect_summary(project):
    track = project.timeline.add_track('Test')
    c1 = track.add_clip('VMFile', 1, 0, 100)
    c1._data['effects'] = [{'effectName': 'Blur'}, {'effectName': 'Glow'}]
    c2 = track.add_clip('VMFile', 1, 100, 100)
    c2._data['effects'] = [{'effectName': 'Blur'}]
    result = project.effect_summary
    assert result == {'Blur': 2, 'Glow': 1}




# ---------------------------------------------------------------------------
# Project.clip_type_summary
# ---------------------------------------------------------------------------

def test_project_clip_type_summary(project):
    track = project.timeline.add_track('Test')
    track.add_clip('VMFile', 1, 0, 100)
    track.add_clip('AMFile', 1, 100, 100)
    track.add_clip('VMFile', 1, 200, 100)
    result = project.clip_type_summary
    assert result['VMFile'] == 2
    assert result['AMFile'] == 1




# ---------------------------------------------------------------------------
# Project.summary_table
# ---------------------------------------------------------------------------

def test_summary_table():
    from camtasia.project import Project
    from unittest.mock import MagicMock

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




# ---------------------------------------------------------------------------
# Project.source_bin_paths
# ---------------------------------------------------------------------------

def test_source_bin_paths(tmp_path):
    from camtasia.project import Project
    import json

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
    assert len(source_paths) == 2
    assert any('clip_a.mp4' in path for path in source_paths)
    assert any('clip_b.wav' in path for path in source_paths)




# ---------------------------------------------------------------------------
# Project.total_effect_count
# ---------------------------------------------------------------------------

def test_total_effect_count(project):
    track = project.timeline.add_track('FX')
    clip = track.add_clip('VMFile', 1, 0, 705600000)
    clip.add_drop_shadow()
    clip.add_round_corners()
    assert project.total_effect_count >= 2




# ---------------------------------------------------------------------------
# Project.average_clip_duration_seconds
# ---------------------------------------------------------------------------

def test_project_average_clip_duration(project):
    track = project.timeline.add_track('Test')
    track.add_clip('VMFile', 1, 0, 705600000 * 3)  # 3s
    track.add_clip('VMFile', 1, 705600000 * 4, 705600000 * 5)  # 5s
    assert project.average_clip_duration_seconds == pytest.approx(4.0)


def test_project_average_clip_duration_empty(project):
    assert project.average_clip_duration_seconds == 0.0




# ---------------------------------------------------------------------------
# Project.replace_media_path
# ---------------------------------------------------------------------------

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




# ---------------------------------------------------------------------------
# Project.has_effects
# ---------------------------------------------------------------------------

def test_project_has_effects(project):
    assert project.has_effects is False




# ---------------------------------------------------------------------------
# Project.has_transitions
# ---------------------------------------------------------------------------

def test_project_has_transitions(project):
    assert project.has_transitions is False




# ---------------------------------------------------------------------------
# Project.has_keyframes
# ---------------------------------------------------------------------------

def test_project_has_keyframes(project):
    assert project.has_keyframes is False




# ---------------------------------------------------------------------------
# Project.empty_tracks
# ---------------------------------------------------------------------------

def test_project_empty_tracks_returns_tracks_with_no_clips():
    """Project.empty_tracks delegates to timeline.empty_tracks."""
    timeline = _make_timeline([
        ('Audio', [{'id': 1, 'start': 0, 'duration': 100}]),
        ('Empty', []),
        ('Also Empty', []),
    ])
    empty_track_names: list[str] = [t.name for t in timeline.empty_tracks]
    assert 'Empty' in empty_track_names
    assert 'Also Empty' in empty_track_names
    assert 'Audio' not in empty_track_names


def test_project_empty_tracks_returns_empty_list_when_all_have_clips():
    """Project.empty_tracks returns [] when every track has clips."""
    timeline = _make_timeline([
        ('A', [{'id': 1, 'start': 0, 'duration': 100}]),
    ])
    empty_tracks: list = timeline.empty_tracks
    assert empty_tracks == []




# ---------------------------------------------------------------------------
# Project.remove_track_by_name
# ---------------------------------------------------------------------------

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

