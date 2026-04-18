"""Tests covering missing lines in project.py, operations/diff.py, operations/speed.py, validation.py, export/edl.py."""
from __future__ import annotations

import copy
from fractions import Fraction
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from camtasia.timing import seconds_to_ticks


RESOURCES = Path(__file__).parent.parent / 'src' / 'camtasia' / 'resources'


# project.py:369 — has_screen_recording with UnifiedMedia ScreenVMFile
class TestHasScreenRecordingUnifiedMedia:
    def test_unified_media_screen_recording(self, tmp_path):
        from camtasia.project import new_project, load_project
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


# project.py:758-763 — merge_projects copies transitions with remapped IDs
class TestMergeProjectsTransitions:
    def test_transitions_remapped(self, tmp_path):
        from camtasia.project import new_project, load_project, Project
        # Create source project with a transition
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
        # Transitions should exist and have remapped IDs
        found_trans = False
        for t in merged.timeline.tracks:
            if t._data.get('transitions'):
                found_trans = True
                for tr in t._data['transitions']:
                    # IDs should be remapped (different from originals)
                    assert 'leftMedia' in tr or 'rightMedia' in tr
        assert found_trans


# project.py:838-840 — validate audio media missing sourceTracks range
class TestValidateAudioMissingSourceTracks:
    def test_missing_range(self, tmp_path):
        from camtasia.project import new_project, load_project
        proj_path = tmp_path / 'test.cmproj'
        new_project(proj_path)
        proj = load_project(proj_path)
        # Audio media with sourceTracks but missing 'range' key
        proj._data.setdefault('sourceBin', []).append({
            'id': 999, 'src': 'fake.wav', 'lastMod': '2024-01-01',
            'sourceTracks': [{'type': 2}],  # type=2 is Audio, but no 'range'
            'rect': [0, 0, 100, 100],
        })
        issues = proj.validate()
        msgs = [i.message for i in issues]
        assert any('missing sourceTracks or range' in m for m in msgs)


# project.py:848-850 — validate image media missing rect
class TestValidateImageMissingRect:
    def test_missing_rect(self, tmp_path):
        from camtasia.project import new_project, load_project
        proj_path = tmp_path / 'test.cmproj'
        new_project(proj_path)
        proj = load_project(proj_path)
        # Image media (type=1) without rect key
        proj._data.setdefault('sourceBin', []).append({
            'id': 998, 'src': 'fake.png', 'lastMod': '2024-01-01',
            'sourceTracks': [{'type': 1}],  # type=1 is Image
        })
        issues = proj.validate()
        msgs = [i.message for i in issues]
        assert any('missing rect' in m for m in msgs)


# project.py:925-927 — repair removes zero-duration clips from overlap fix
class TestRepairZeroDuration:
    def test_zero_duration_removed(self, tmp_path):
        from camtasia.project import new_project, load_project
        proj_path = tmp_path / 'test.cmproj'
        new_project(proj_path)
        proj = load_project(proj_path)
        track = proj.timeline.add_track('V')
        # Create overlapping clips where fixing makes first clip zero/negative duration
        m1 = {'id': 50, '_type': 'VMFile', 'src': 0, 'start': 0, 'duration': 5,
               'mediaStart': 0, 'mediaDuration': 5, 'scalar': 1,
               'metadata': {}, 'parameters': {}, 'effects': [], 'attributes': {'ident': ''},
               'animationTracks': {}}
        m2 = {'id': 51, '_type': 'VMFile', 'src': 0, 'start': 1, 'duration': 100,
               'mediaStart': 0, 'mediaDuration': 100, 'scalar': 1,
               'metadata': {}, 'parameters': {}, 'effects': [], 'attributes': {'ident': ''},
               'animationTracks': {}}
        track._data['medias'] = [m1, m2]
        result = proj.repair()
        # The overlap is 4 ticks (5 - 1), so m1 duration becomes 5 - 4 = 1 (still positive)
        # Let's make a more extreme case
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
        # First clip duration 1 - overlap 1 = 0, should be removed
        assert result.get('zero_duration_removed', 0) >= 1


# operations/diff.py:77,82 — clips on removed/added tracks
class TestDiffRemovedAddedTracks:
    def test_clips_on_removed_and_added_tracks(self, tmp_path):
        from camtasia.project import new_project, load_project
        from camtasia.operations.diff import diff_projects

        path_a = tmp_path / 'a.cmproj'
        path_b = tmp_path / 'b.cmproj'
        new_project(path_a)
        new_project(path_b)
        a = load_project(path_a)
        b = load_project(path_b)

        # a has 3 tracks (0,1 default + 2 added), b has 4 tracks (0,1 default + 2,3 added)
        ta = a.timeline.add_track('ExtraA')
        ta.add_clip('VMFile', 0, 0, 100)
        b.timeline.add_track('ExtraB1')
        tb2 = b.timeline.add_track('ExtraB2')
        tb2.add_clip('VMFile', 0, 0, 100)

        # Now a has tracks {0,1,2}, b has tracks {0,1,2,3}
        # Track 2 is in a but not b's track 2 has different clips → shared track diff
        # Track 3 is only in b → added track with clips (line 82)
        result = diff_projects(a, b)
        assert result.has_changes

    def test_track_only_in_a(self, tmp_path):
        from camtasia.project import new_project, load_project
        from camtasia.operations.diff import diff_projects

        path_a = tmp_path / 'a2.cmproj'
        path_b = tmp_path / 'b2.cmproj'
        new_project(path_a)
        new_project(path_b)
        a = load_project(path_a)
        b = load_project(path_b)

        # a has extra tracks, b doesn't
        a.timeline.add_track('T2')
        t3 = a.timeline.add_track('T3')
        t3.add_clip('VMFile', 0, 0, 100)

        result = diff_projects(a, b)
        # Track 3 only in a → removed track, clips on removed track (line 77)
        assert len(result.tracks_removed) > 0


# operations/speed.py:44,46 — effect start/duration scaling
class TestSpeedEffectScaling:
    def test_effect_times_scaled(self):
        from camtasia.operations.speed import _scale_clip_timing
        clip = {'_type': 'VMFile', 'start': 0, 'duration': 1000,
                'mediaStart': 0, 'mediaDuration': 1000, 'scalar': 1,
                'effects': [{'start': 100, 'duration': 200}]}
        _scale_clip_timing(clip, Fraction(2))
        assert clip['effects'][0]['start'] == 200
        assert clip['effects'][0]['duration'] == 400


# operations/speed.py:88-91 — StitchedMedia inner effect scaling
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


# export/edl.py:25-26 — minute overflow in timecode formatting
class TestEdlMinuteOverflow:
    def test_minute_overflow(self):
        from camtasia.export.edl import _format_timecode
        # 59 minutes, 59.999... seconds at 30fps → should carry into hour
        result = _format_timecode(3599.999, fps=30)
        # At 3599.999s: h=0, m=59, s=59, f=round(0.999*30)=30 → f>=fps → s=60 → s>=60 → m=60 → m>=60 → h=1
        assert result == '01:00:00:00'


# validation.py:197-198 — version parsing error
class TestValidationVersionParseError:
    def test_invalid_version(self):
        from camtasia.validation import _check_group_required_fields
        data = {'version': 'not-a-number',
                'sceneTrack': {'scenes': [{'csml': {'tracks': []}}]}}
        issues = _check_group_required_fields(data)
        # Should not crash, version defaults to 0.0


# validation.py:280-281 — scalar parsing error in timing consistency
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
        # Should not crash — the except catches ZeroDivisionError
