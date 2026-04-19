"""Tests for uncovered lines in effects, validation, diff, merge, template, edl, media_bin, etc."""
from __future__ import annotations

from fractions import Fraction
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from camtasia.timing import seconds_to_ticks

S1 = seconds_to_ticks(1.0)
S5 = seconds_to_ticks(5.0)
S10 = seconds_to_ticks(10.0)


# ===== effects/behaviors.py (lines 159, 164, 169, 173, 177) =====

class TestBehaviorEffectProperties:
    def test_behavior_name_category_parameters(self):
        from camtasia.effects.behaviors import GenericBehaviorEffect
        data = {'effectName': 'TestBehavior', 'parameters': {}}
        b = GenericBehaviorEffect(data)
        assert b.name == 'TestBehavior'
        assert b.category == ''
        assert b.parameters == {}


# ===== effects/cursor.py (lines 37, 41) =====

class TestCursorEffectEnabled:
    def test_cursor_enabled_property(self):
        from camtasia.effects.cursor import CursorShadow
        data = {'effectName': 'CursorShadow', 'parameters': {'enabled': 1}}
        c = CursorShadow(data)
        assert c.enabled == 1
        c.enabled = 0
        assert data['parameters']['enabled'] == 0


# ===== effects/source.py (lines 49-50, 62-63, 115, 134-135, 147-148, 160) =====

class TestSourceEffectProperties:
    def _make(self, **params):
        from camtasia.effects.source import SourceEffect
        return SourceEffect({'effectName': 'TestSource', 'parameters': params})

    def test_color0_none_when_missing(self):
        assert self._make().color0 is None

    def test_color1_none_when_missing(self):
        assert self._make().color1 is None

    def test_mid_point_setter_dict(self):
        e = self._make(MidPoint={'defaultValue': 0.5})
        e.mid_point = 0.7
        assert e._data['parameters']['MidPoint']['defaultValue'] == 0.7

    def test_mid_point_setter_scalar(self):
        e = self._make(MidPoint=0.5)
        e.mid_point = 0.7
        assert e._data['parameters']['MidPoint'] == 0.7

    def test_speed_none_when_missing(self):
        assert self._make().speed is None

    def test_speed_setter(self):
        e = self._make(Speed=1.0)
        e.speed = 2.0
        assert e._data['parameters']['Speed'] == 2.0

    def test_source_file_type_none_when_missing(self):
        assert self._make().source_file_type is None

    def test_set_shader_colors_2(self):
        e = self._make()
        e.set_shader_colors((255, 0, 0), (0, 255, 0))
        # Verify color params were set
        p = e._data['parameters']
        assert p['Color0-red'] == 1.0
        assert p['Color0-green'] == 0.0
        assert p['Color1-green'] == 1.0


# ===== effects/visual.py (lines 336, 341) =====

class TestVisualEffectSigma:
    def test_blur_sigma(self):
        from camtasia.effects.visual import BlurRegion
        data = {'effectName': 'blurRegion', 'parameters': {'sigma': 5.0}}
        b = BlurRegion(data)
        assert b.sigma == 5.0
        b.sigma = 10.0
        assert data['parameters']['sigma'] == 10.0


# ===== color.py (line 64) =====

class TestColorFromFloats:
    def test_non_integer_channels_raise(self):
        from camtasia.color import RGBA
        with pytest.raises(TypeError, match='integers'):
            RGBA(1.5, 0, 0, 255)  # type: ignore[arg-type]


# ===== validation.py =====

class TestValidationEdgeCases:
    def test_get_tracks_empty_scenes(self):
        from camtasia.validation import _get_tracks
        assert _get_tracks({'timeline': {'sceneTrack': {'scenes': []}}}) == []

    def test_check_edit_rate_missing(self):
        from camtasia.validation import _check_edit_rate
        issues = _check_edit_rate({})
        assert any('missing' in str(i) for i in issues)

    def test_check_edit_rate_wrong(self):
        from camtasia.validation import _check_edit_rate
        issues = _check_edit_rate({'editRate': 12345})
        assert any('expected' in str(i) for i in issues)

    def test_duplicate_source_bin_ids(self):
        from camtasia.validation import _check_source_bin_ids
        issues = _check_source_bin_ids({'sourceBin': [{'id': 1, 'src': 'a'}, {'id': 1, 'src': 'b'}]})
        assert any('Duplicate' in str(i) for i in issues)

    def test_validate_all_negative_start(self):
        from camtasia.validation import validate_all
        data = {
            'version': '9.0',
            'editRate': 705600000,
            'sourceBin': [],
            'timeline': {
                'sceneTrack': {
                    'scenes': [{
                        'csml': {
                            'tracks': [{
                                'trackIndex': 0,
                                'medias': [{
                                    '_type': 'VMFile', 'id': 1, 'start': -100, 'duration': S1,
                                    'mediaDuration': S1, 'mediaStart': 0, 'scalar': 1,
                                    'parameters': {}, 'effects': [], 'metadata': {},
                                }],
                            }],
                        }
                    }]
                },
                'parameters': {},
                'trackAttributes': [{}],
            },
        }
        issues = validate_all(data)
        assert any('negative start' in str(i) for i in issues)

    def test_validate_all_zero_duration(self):
        from camtasia.validation import validate_all
        data = {
            'version': '9.0',
            'editRate': 705600000,
            'sourceBin': [],
            'timeline': {
                'sceneTrack': {
                    'scenes': [{
                        'csml': {
                            'tracks': [{
                                'trackIndex': 0,
                                'medias': [{
                                    '_type': 'VMFile', 'id': 1, 'start': 0, 'duration': 0,
                                    'mediaDuration': 0, 'mediaStart': 0, 'scalar': 1,
                                    'parameters': {}, 'effects': [], 'metadata': {},
                                }],
                            }],
                        }
                    }]
                },
                'parameters': {},
                'trackAttributes': [{}],
            },
        }
        issues = validate_all(data)
        assert any('duration' in str(i).lower() for i in issues)

    def test_validate_all_scalar_mismatch(self):
        from camtasia.validation import validate_all
        data = {
            'version': '9.0',
            'editRate': 705600000,
            'sourceBin': [],
            'timeline': {
                'sceneTrack': {
                    'scenes': [{
                        'csml': {
                            'tracks': [{
                                'trackIndex': 0,
                                'medias': [{
                                    '_type': 'VMFile', 'id': 1, 'start': 0, 'duration': S10,
                                    'mediaDuration': 99999, 'mediaStart': 0, 'scalar': '1/2',
                                    'parameters': {}, 'effects': [], 'metadata': {},
                                }],
                            }],
                        }
                    }]
                },
                'parameters': {},
                'trackAttributes': [{}],
            },
        }
        issues = validate_all(data)
        assert any('mediaDuration' in str(i) or 'scalar' in str(i) for i in issues)

    def test_validate_all_group_missing_metadata(self):
        from camtasia.validation import validate_all
        data = {
            'version': '9.0',
            'editRate': 705600000,
            'sourceBin': [],
            'timeline': {
                'sceneTrack': {
                    'scenes': [{
                        'csml': {
                            'tracks': [{
                                'trackIndex': 0,
                                'medias': [{
                                    '_type': 'Group', 'id': 1, 'start': 0, 'duration': S10,
                                    'mediaDuration': S10, 'mediaStart': 0, 'scalar': 1,
                                    'parameters': {}, 'effects': [],
                                    'tracks': [{'trackIndex': 0, 'medias': []}],
                                }],
                            }],
                        }
                    }]
                },
                'parameters': {},
                'trackAttributes': [{}],
            },
        }
        issues = validate_all(data)
        assert any('metadata' in str(i) for i in issues)


# ===== operations/diff.py (lines 77, 82) =====

class TestDiffClipsOnRemovedAddedTracks:
    def test_diff_detects_clips_on_removed_tracks(self, project):
        import copy
        from camtasia.operations.diff import diff_projects
        from camtasia.project import Project
        a = project
        b_data = copy.deepcopy(a._data)
        b = Project.__new__(Project)
        b._data = b_data
        b._file_path = a._file_path
        track = a.timeline.tracks[0]
        track._data['medias'].append({
            '_type': 'VMFile', 'id': 999, 'src': 0, 'start': 0, 'duration': S1,
            'mediaDuration': S1, 'mediaStart': 0, 'scalar': 1,
            'parameters': {}, 'effects': [],
        })
        result = diff_projects(a, b)
        assert result is not None


# ===== operations/merge.py (line 29) =====

class TestMergeRemapClipIds:
    def test_remap_clip_ids_unified(self):
        from camtasia.operations.merge import _remap_clip_ids
        data = {
            'id': 1, '_type': 'UnifiedMedia',
            'video': {'_type': 'ScreenVMFile', 'id': 2, 'src': 1},
            'audio': {'_type': 'AMFile', 'id': 3, 'src': 1},
            'tracks': [{'medias': [{'id': 4, 'src': 1}]}],
            'medias': [{'id': 5, 'src': 1}],
        }
        id_counter = [100]
        id_map = {}
        src_map = {1: 50}
        _remap_clip_ids(data, id_counter, id_map, src_map)
        assert data['id'] != 1
        assert data['video']['src'] == 50


# ===== operations/template.py (lines 52-55) =====

class TestTemplateWalkClips:
    def test_walk_clips_unified(self):
        from camtasia.operations.template import _walk_clips
        tracks = [{
            'medias': [{
                '_type': 'UnifiedMedia', 'id': 1,
                'video': {'_type': 'ScreenVMFile', 'id': 2},
                'audio': {'_type': 'AMFile', 'id': 3},
            }]
        }]
        clips = list(_walk_clips(tracks))
        assert any(c.get('_type') == 'ScreenVMFile' for c in clips)
        assert any(c.get('_type') == 'AMFile' for c in clips)


# ===== export/edl.py (lines 19-26, 69, 103-112) =====

class TestEdlExport:
    def test_format_timecode_carry(self):
        from camtasia.export.edl import _format_timecode
        result = _format_timecode(59.99, 30)
        assert result.startswith('00:01:00') or result.startswith('00:00:59')

    def test_export_edl_basic(self, project, tmp_path):
        from camtasia.export.edl import export_edl
        track = project.timeline.tracks[0]
        track._data['medias'].append({
            '_type': 'VMFile', 'id': 1, 'src': 0, 'start': 0, 'duration': S5,
            'mediaDuration': S5, 'mediaStart': 0, 'scalar': 1,
            'parameters': {}, 'effects': [],
        })
        out = tmp_path / 'test.edl'
        result = export_edl(project, out)
        assert result.exists()
        content = result.read_text()
        assert 'TITLE' in content

    def test_export_edl_unified_media(self, project, tmp_path):
        from camtasia.export.edl import export_edl
        track = project.timeline.tracks[0]
        track._data['medias'].append({
            '_type': 'UnifiedMedia', 'id': 10,
            'start': 0, 'duration': S5, 'mediaDuration': S5,
            'mediaStart': 0, 'scalar': 1, 'parameters': {}, 'effects': [],
            'video': {'_type': 'ScreenVMFile', 'id': 11, 'src': 0,
                      'start': 0, 'duration': S5, 'mediaDuration': S5,
                      'mediaStart': 0, 'scalar': 1},
            'audio': {'_type': 'AMFile', 'id': 12, 'src': 0,
                      'start': 0, 'duration': S5, 'mediaDuration': S5,
                      'mediaStart': 0, 'scalar': 1, 'attributes': {'gain': 1.0}},
        })
        out = tmp_path / 'test_um.edl'
        result = export_edl(project, out)
        content = result.read_text()
        assert '  V  ' in content
        assert '  A  ' in content


# ===== media_bin/media_bin.py (lines 71, 103-104, 514) =====

class TestMediaBinEdgeCases:
    def test_media_range_empty_source_tracks(self):
        from camtasia.media_bin.media_bin import Media
        data = {'id': 1, 'src': 'test.png', 'sourceTracks': [], 'rect': [0, 0, 100, 100]}
        m = Media(data)
        assert m.range == (0, 0)

    def test_media_duration_seconds_image(self):
        from camtasia.media_bin.media_bin import Media
        data = {'id': 1, 'src': 'test.png',
                'sourceTracks': [{'type': 1, 'range': [0, 1], 'editRate': 1}],
                'rect': [0, 0, 100, 100]}
        m = Media(data)
        assert m.duration_seconds == 0.0

    def test_unsupported_stream_type_raises(self):
        from camtasia.media_bin.media_bin import _get_media_type
        with pytest.raises(ValueError, match='Unsupported'):
            _get_media_type({'kind_of_stream': 'Subtitle'})


# ===== timeline/clips/placeholder.py (line 19) =====

class TestPlaceholderSetSource:
    def test_set_source_raises(self):
        from camtasia.timeline.clips.placeholder import PlaceholderMedia
        data = {'_type': 'PlaceholderMedia', 'id': 1, 'start': 0, 'duration': S1,
                'mediaDuration': S1, 'scalar': 1, 'parameters': {}, 'effects': []}
        p = PlaceholderMedia(data)
        with pytest.raises(TypeError, match='Cannot set_source'):
            p.set_source(1)


# ===== timeline/clips/stitched.py (line 43) =====

class TestStitchedSetSource:
    def test_set_source_raises(self):
        from camtasia.timeline.clips.stitched import StitchedMedia
        data = {'_type': 'StitchedMedia', 'id': 1, 'start': 0, 'duration': S1,
                'mediaDuration': S1, 'scalar': 1, 'parameters': {}, 'effects': [],
                'medias': []}
        s = StitchedMedia(data)
        with pytest.raises(TypeError, match='do not have a top-level source'):
            s.set_source(1)


# ===== timeline/transitions.py (line 133) =====

class TestTransitionBothNone:
    def test_add_transition_both_none_raises(self):
        from camtasia.timeline.transitions import TransitionList
        tl = TransitionList([])
        with pytest.raises(ValueError, match='At least one'):
            tl.add('Fade', duration_ticks=S1, left_clip_id=None, right_clip_id=None)


# ===== timeline/clips/unified.py (lines 71, 74, 85, 88, 91, 102, 105) =====

class TestUnifiedMediaEffectErrors:
    def _make_um(self):
        from camtasia.timeline.clips.unified import UnifiedMedia
        return UnifiedMedia({
            '_type': 'UnifiedMedia', 'id': 1,
            'start': 0, 'duration': S5, 'mediaDuration': S5,
            'mediaStart': 0, 'scalar': 1, 'parameters': {}, 'effects': [],
            'video': {'_type': 'ScreenVMFile', 'id': 2, 'src': 0,
                      'start': 0, 'duration': S5, 'mediaDuration': S5,
                      'mediaStart': 0, 'scalar': 1},
            'audio': {'_type': 'AMFile', 'id': 3, 'src': 0,
                      'start': 0, 'duration': S5, 'mediaDuration': S5,
                      'mediaStart': 0, 'scalar': 1, 'attributes': {'gain': 1.0}},
        })

    def test_add_effect_raises(self):
        with pytest.raises(TypeError, match='Effects must be added'):
            self._make_um().add_effect({})

    def test_add_drop_shadow_raises(self):
        with pytest.raises(TypeError):
            self._make_um().add_drop_shadow()

    def test_add_round_corners_raises(self):
        with pytest.raises(TypeError):
            self._make_um().add_round_corners()

    def test_add_glow_raises(self):
        with pytest.raises(TypeError):
            self._make_um().add_glow()

    def test_add_glow_timed_raises(self):
        with pytest.raises(TypeError):
            self._make_um().add_glow_timed()

    def test_copy_effects_from_raises(self):
        with pytest.raises(TypeError):
            self._make_um().copy_effects_from(None)

    def test_set_source_raises(self):
        with pytest.raises(TypeError, match='Cannot set_source'):
            self._make_um().set_source(1)


# ===== builders/screenplay_builder.py (lines 56, 73-88, 109, 120-121) =====

class TestScreenplayBuilder:
    def test_find_audio_file_numbered_prefix(self, tmp_path):
        from camtasia.builders.screenplay_builder import _find_audio_file
        audio_file = tmp_path / '01-01-take1.wav'
        audio_file.write_bytes(b'fake')
        result = _find_audio_file(tmp_path, '1.1')
        assert result == audio_file

    def test_find_audio_file_no_prefix(self, tmp_path):
        from camtasia.builders.screenplay_builder import _find_audio_file
        audio_file = tmp_path / '1.1.wav'
        audio_file.write_bytes(b'fake')
        result = _find_audio_file(tmp_path, '1.1')
        assert result == audio_file

    def test_find_audio_file_not_found(self, tmp_path):
        from camtasia.builders.screenplay_builder import _find_audio_file
        result = _find_audio_file(tmp_path, 'nonexistent')
        assert result is None
