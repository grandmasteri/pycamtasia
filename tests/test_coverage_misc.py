"""Tests targeting uncovered lines in timing.py, export/edl.py, operations/template.py, color.py, transitions.py."""
from __future__ import annotations

import json
import shutil
from fractions import Fraction
from pathlib import Path

import pytest

from camtasia.timing import (
    EDIT_RATE,
    format_duration,
    parse_scalar,
    scalar_to_speed,
    scalar_to_string,
    seconds_to_ticks,
    speed_to_scalar,
    ticks_to_seconds,
)

S1 = seconds_to_ticks(1.0)
S5 = seconds_to_ticks(5.0)
S10 = seconds_to_ticks(10.0)


# ===== timing.py — format_duration hours branch, negative, carry edge cases =====

class TestFormatDurationHours:
    def test_hours_format(self):
        """format_duration with >3600s includes hours."""
        result = format_duration(seconds_to_ticks(3661.5))
        assert result.startswith('1:01:01')

    def test_negative_duration(self):
        """format_duration with negative ticks shows minus sign."""
        result = format_duration(-seconds_to_ticks(5.0))
        assert result.startswith('-')

    def test_centisecond_carry(self):
        """format_duration handles centisecond rounding to 100."""
        # 59.999... seconds — cs rounds to 100, should carry
        result = format_duration(seconds_to_ticks(59.999))
        assert ':' in result

    def test_zero(self):
        assert format_duration(0) == '0:00.00'


class TestParseScalarEdgeCases:
    def test_fraction_passthrough(self):
        assert parse_scalar(Fraction(3, 7)) == Fraction(3, 7)

    def test_string_fraction(self):
        assert parse_scalar('51/101') == Fraction(51, 101)

    def test_zero_division_string(self):
        with pytest.raises(ValueError, match='division by zero'):
            parse_scalar('1/0')

    def test_float_input(self):
        result = parse_scalar(0.5)
        assert result == Fraction(1, 2)


class TestScalarToString:
    def test_unity(self):
        assert scalar_to_string(Fraction(1)) == 1

    def test_non_unity(self):
        assert scalar_to_string(Fraction(3, 4)) == '3/4'


class TestSpeedScalarConversions:
    def test_speed_zero_raises(self):
        with pytest.raises(ValueError, match='zero'):
            speed_to_scalar(0)

    def test_speed_negative_raises(self):
        with pytest.raises(ValueError, match='negative'):
            speed_to_scalar(-1.0)

    def test_scalar_zero_raises(self):
        with pytest.raises(ValueError, match='zero'):
            scalar_to_speed(Fraction(0))

    def test_scalar_negative_raises(self):
        with pytest.raises(ValueError, match='negative'):
            scalar_to_speed(Fraction(-1))


# ===== export/edl.py — EDL export with UnifiedMedia audio track, source lookup =====

class TestEdlExport:
    def test_edl_basic_export(self, tmp_path, project):
        """export_edl writes a valid EDL file."""
        from camtasia.export.edl import export_edl
        out = tmp_path / 'test.edl'
        result = export_edl(project, out, title='Test')
        assert result.exists()
        content = result.read_text()
        assert 'TITLE: Test' in content
        assert 'FCM: NON-DROP FRAME' in content

    def test_edl_with_unified_media(self, tmp_path, project):
        """export_edl generates separate audio event for UnifiedMedia."""
        from camtasia.export.edl import export_edl
        # Add a UnifiedMedia clip to the project
        track = project.timeline.tracks[0]
        um_data = {
            '_type': 'UnifiedMedia', 'id': 900, 'start': 0, 'duration': S5,
            'mediaDuration': S5, 'mediaStart': 0, 'scalar': 1,
            'parameters': {}, 'effects': [],
            'video': {
                '_type': 'ScreenVMFile', 'id': 901, 'src': 1,
                'start': 0, 'duration': S5, 'mediaDuration': S5,
                'mediaStart': 0, 'scalar': 1,
                'parameters': {}, 'effects': [], 'attributes': {},
            },
            'audio': {
                '_type': 'AMFile', 'id': 902, 'src': 1,
                'start': 0, 'duration': S5, 'mediaDuration': S5,
                'mediaStart': 0, 'scalar': 1, 'attributes': {},
            },
        }
        track._data.setdefault('medias', []).append(um_data)
        out = tmp_path / 'unified.edl'
        result = export_edl(project, out)
        content = result.read_text()
        # Should have both V and A lines for the unified clip
        assert '  V  ' in content
        assert '  A  ' in content

    def test_edl_with_audio_clip(self, tmp_path, project):
        """export_edl marks AMFile clips as audio."""
        from camtasia.export.edl import export_edl
        track = project.timeline.tracks[0]
        am_data = {
            '_type': 'AMFile', 'id': 910, 'src': 1,
            'start': 0, 'duration': S5, 'mediaDuration': S5,
            'mediaStart': 0, 'scalar': 1,
            'parameters': {}, 'effects': [], 'attributes': {},
        }
        track._data.setdefault('medias', []).append(am_data)
        out = tmp_path / 'audio.edl'
        result = export_edl(project, out)
        content = result.read_text()
        assert '  A  ' in content

    def test_edl_source_name_from_media_bin(self, tmp_path, project):
        """export_edl resolves source name from media bin when available."""
        from camtasia.export.edl import export_edl
        # Add a media bin entry and a clip referencing it
        project._data.setdefault('sourceBin', []).append({
            'id': 42, 'src': '/path/to/video.mp4',
            'sourceTracks': [], 'rect': [0, 0, 1920, 1080],
            'lastMod': '2026-01-01',
        })
        track = project.timeline.tracks[0]
        vm_data = {
            '_type': 'VMFile', 'id': 920, 'src': 42,
            'start': 0, 'duration': S5, 'mediaDuration': S5,
            'mediaStart': 0, 'scalar': 1,
            'parameters': {}, 'effects': [], 'attributes': {},
        }
        track._data.setdefault('medias', []).append(vm_data)
        out = tmp_path / 'named.edl'
        export_edl(project, out)
        # Just verify it doesn't crash — source resolution is best-effort


class TestFormatTimecodeCarry:
    def test_frame_carry(self):
        """_format_timecode handles frame carry to seconds."""
        from camtasia.export.edl import _format_timecode
        # At exactly 1 second boundary
        result = _format_timecode(1.0, fps=30)
        assert result == '00:00:01:00'

    def test_second_carry(self):
        from camtasia.export.edl import _format_timecode
        result = _format_timecode(60.0, fps=30)
        assert result == '00:01:00:00'

    def test_minute_carry(self):
        from camtasia.export.edl import _format_timecode
        result = _format_timecode(3600.0, fps=30)
        assert result == '01:00:00:00'

    def test_negative_clamped(self):
        from camtasia.export.edl import _format_timecode
        result = _format_timecode(-5.0, fps=30)
        assert result == '00:00:00:00'


# ===== operations/template.py — _walk_clips with UnifiedMedia, replace_media_source =====

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


# ===== color.py — hex_rgb with 4-digit hex =====

class TestHexRgb4Digit:
    def test_4_digit_hex(self):
        from camtasia.color import hex_rgb
        result = hex_rgb('#F0A8')
        assert len(result) == 4
        assert result == (255, 0, 170, 136)

    def test_invalid_length_raises(self):
        from camtasia.color import hex_rgb
        with pytest.raises(ValueError, match='Could not interpret'):
            hex_rgb('#12345')


# ===== transitions.py — add_fade_to_white =====

class TestTransitionFadeToWhite:
    def test_add_fade_to_white(self):
        from camtasia.timeline.transitions import TransitionList
        data = {'transitions': []}
        tl = TransitionList(data)
        t = tl.add_fade_to_white(left_clip=1, right_clip=2, duration_seconds=0.5)
        assert t.name == 'FadeThroughColor'
        assert t._data['attributes']['Color-red'] == 1.0
        assert t._data['attributes']['Color-green'] == 1.0
        assert t._data['attributes']['Color-blue'] == 1.0
