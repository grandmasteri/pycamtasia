"""Tests covering remaining gaps for 100% coverage."""
from __future__ import annotations

import copy
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from camtasia.timing import seconds_to_ticks, ticks_to_seconds


# ------------------------------------------------------------------
# project.py:36-41 — Video track in _probe_media pymediainfo path
# ------------------------------------------------------------------

class TestProbeMediaVideoTrack:
    def test_video_track_extracts_dimensions_and_framerate(self):
        from camtasia.project import _probe_media

        tracks = [
            SimpleNamespace(track_type='Video', width=1920, height=1080,
                            duration=10000, frame_rate='30.0'),
        ]
        mock_mi = MagicMock()
        mock_mi.MediaInfo.parse.return_value = MagicMock(tracks=tracks)

        with patch.dict('sys.modules', {'pymediainfo': mock_mi}):
            result = _probe_media(Path('/fake/video.mp4'))

        assert result['width'] == 1920
        assert result['height'] == 1080
        assert result['duration_seconds'] == 10.0
        assert result['frame_rate'] == 30.0
        assert result['_backend'] == 'pymediainfo'


# ------------------------------------------------------------------
# project.py:62-63 — except Exception in _probe_media
# ------------------------------------------------------------------

class TestProbeMediaException:
    def test_exception_falls_back_to_ffprobe(self):
        from camtasia.project import _probe_media

        mock_mi = MagicMock()
        mock_mi.MediaInfo.parse.side_effect = RuntimeError('corrupt file')

        with patch.dict('sys.modules', {'pymediainfo': mock_mi}), \
             patch('camtasia.project._probe_media_ffprobe', return_value={'_backend': 'ffprobe'}) as mock_ff:
            result = _probe_media(Path('/fake/bad.mp4'))

        mock_ff.assert_called_once()
        assert result['_backend'] == 'ffprobe'


# ------------------------------------------------------------------
# project.py:217 — print inside validate() loop in save()
# ------------------------------------------------------------------

class TestSaveWithValidationIssues:
    def test_save_prints_validation_issues(self, tmp_path):
        from camtasia.project import new_project, load_project
        from camtasia.validation import ValidationIssue

        proj_path = tmp_path / 'test.cmproj'
        new_project(proj_path)
        proj = load_project(proj_path)

        fake_issue = ValidationIssue('warning', 'test issue', None)
        with patch.object(proj, 'validate', return_value=[fake_issue]):
            proj.save()


# ------------------------------------------------------------------
# project.py:318-323 — .tscshadervid import branch
# ------------------------------------------------------------------

class TestImportShaderVid:
    def test_import_tscshadervid_sets_shader_defaults(self, tmp_path):
        from camtasia.project import new_project, load_project

        proj_path = tmp_path / 'test.cmproj'
        new_project(proj_path)
        proj = load_project(proj_path)

        shader_file = tmp_path / 'effect.tscshadervid'
        shader_file.write_bytes(b'\x00' * 10)

        with patch('camtasia.project._probe_media', return_value={}):
            media = proj.import_media(shader_file)

        st = media._data['sourceTracks'][0]
        assert st['range'][1] == 9223372036854775807
        assert media._data['rect'][2] == 1920
        assert media._data['rect'][3] == 1080


# ------------------------------------------------------------------
# base.py:287 — return None when opacity keyframes list is empty
# ------------------------------------------------------------------

class TestOpacityEmptyKeyframes:
    def test_empty_keyframes_returns_none(self):
        from camtasia.timeline.clips.base import BaseClip

        data = {
            'id': 1, '_type': 'VMFile', 'src': 0,
            'start': 0, 'duration': 100, 'mediaStart': 0,
            'parameters': {'opacity': {'keyframes': []}},
        }
        clip = BaseClip(data)
        assert clip._get_existing_opacity_keyframes() is None


# ------------------------------------------------------------------
# group.py:105-194 — set_internal_segment_speeds
# ------------------------------------------------------------------

def _group_with_unified_media():
    return {
        'id': 1, '_type': 'Group', 'src': 0,
        'start': 0, 'duration': seconds_to_ticks(100),
        'mediaStart': 0, 'mediaDuration': seconds_to_ticks(100),
        'scalar': 1, 'metadata': {}, 'parameters': {}, 'effects': [],
        'attributes': {'ident': ''}, 'animationTracks': {},
        'tracks': [
            {'medias': [{'id': 10, '_type': 'VMFile', 'src': 1,
                         'start': 0, 'duration': seconds_to_ticks(100),
                         'mediaStart': 0, 'mediaDuration': seconds_to_ticks(100),
                         'scalar': 1}]},
            {'medias': [{'id': 11, '_type': 'UnifiedMedia',
                         'video': {'src': 2, 'attributes': {'ident': 'rec'},
                                   'parameters': {}, 'effects': []},
                         'start': 0, 'duration': seconds_to_ticks(100),
                         'mediaStart': 0, 'mediaDuration': seconds_to_ticks(100)}]},
        ],
    }


class TestGroupSetInternalSegmentSpeeds:
    def test_creates_screenvm_clips(self):
        from camtasia.timeline.clips.group import Group
        data = _group_with_unified_media()
        group = Group(data)
        group.set_internal_segment_speeds([(0, 50, 50), (50, 100, 25)])
        # Internal track should now have 2 ScreenVMFile clips
        media_track = data['tracks'][1]
        assert [m['_type'] for m in media_track['medias']] == ['ScreenVMFile', 'ScreenVMFile']

    def test_updates_group_duration(self):
        from camtasia.timeline.clips.group import Group
        data = _group_with_unified_media()
        group = Group(data)
        group.set_internal_segment_speeds([(0, 50, 30), (50, 100, 20)])
        assert data['duration'] == seconds_to_ticks(50)

    def test_extends_vmfile_on_other_tracks(self):
        from camtasia.timeline.clips.group import Group
        data = _group_with_unified_media()
        group = Group(data)
        group.set_internal_segment_speeds([(0, 50, 50), (50, 100, 50)])
        vmfile = data['tracks'][0]['medias'][0]
        assert vmfile['duration'] == seconds_to_ticks(100)

    def test_no_unified_media_raises(self):
        from camtasia.timeline.clips.group import Group
        data = {
            'id': 1, '_type': 'Group', 'src': 0,
            'start': 0, 'duration': 100, 'mediaStart': 0,
            'mediaDuration': 100, 'scalar': 1,
            'tracks': [{'medias': [{'id': 10, '_type': 'AMFile'}]}],
        }
        group = Group(data)
        with pytest.raises(ValueError, match='No internal track'):
            group.set_internal_segment_speeds([(0, 50, 50)])

    def test_stitched_media_template(self):
        from camtasia.timeline.clips.group import Group
        data = _group_with_unified_media()
        # Replace UnifiedMedia with StitchedMedia
        data['tracks'][1]['medias'] = [{'id': 11, '_type': 'StitchedMedia',
                                         'src': 2, 'attributes': {'ident': 'rec'}}]
        group = Group(data)
        group.set_internal_segment_speeds([(0, 50, 50)])
        assert data['tracks'][1]['medias'][0]['_type'] == 'ScreenVMFile'

    def test_scalar_is_string_when_not_one(self):
        from camtasia.timeline.clips.group import Group
        data = _group_with_unified_media()
        group = Group(data)
        # 2x speed: 100s source in 50s timeline
        group.set_internal_segment_speeds([(0, 100, 50)])
        clip = data['tracks'][1]['medias'][0]
        assert isinstance(clip['scalar'], str)

    def test_scalar_is_int_one_for_normal_speed(self):
        from camtasia.timeline.clips.group import Group
        data = _group_with_unified_media()
        group = Group(data)
        group.set_internal_segment_speeds([(0, 50, 50)])
        clip = data['tracks'][1]['medias'][0]
        assert clip['scalar'] == 1


# ------------------------------------------------------------------
# track.py:332 — unknown title preset raises ValueError
# ------------------------------------------------------------------

class TestTitlePresetUnknown:
    def test_unknown_preset_raises(self):
        from camtasia.timeline.track import Track
        attrs = {'ident': 'test', 'audioMuted': False, 'videoHidden': False}
        data = {'trackIndex': 0, 'medias': []}
        track = Track(attrs, data)
        with pytest.raises(ValueError, match='Unknown title preset'):
            track.add_title('Hello', 0, 5, preset='nonexistent')


# ------------------------------------------------------------------
# track.py:701 — missing clip in set_segment_speeds
# ------------------------------------------------------------------

class TestSetSegmentSpeedsMissingClip:
    def test_missing_clip_raises(self):
        from camtasia.timeline.track import Track
        attrs = {'ident': 'test', 'audioMuted': False, 'videoHidden': False}
        data = {'trackIndex': 0, 'medias': []}
        track = Track(attrs, data)
        with pytest.raises(KeyError, match='No clip with id=999'):
            track.set_segment_speeds(999, [(30, 1.0)])


# ------------------------------------------------------------------
# track.py:786 — missing clip in split_clip
# ------------------------------------------------------------------

class TestSplitClipMissingClip:
    def test_missing_clip_raises(self):
        from camtasia.timeline.track import Track
        attrs = {'ident': 'test', 'audioMuted': False, 'videoHidden': False}
        data = {'trackIndex': 0, 'medias': []}
        track = Track(attrs, data)
        with pytest.raises(KeyError, match='No clip with id=999'):
            track.split_clip(999, 5.0)


# ------------------------------------------------------------------
# track.py:793 — split point outside clip range
# ------------------------------------------------------------------

class TestSplitClipOutOfRange:
    def test_split_before_clip_raises(self):
        from camtasia.timeline.track import Track
        attrs = {'ident': 'test', 'audioMuted': False, 'videoHidden': False}
        clip = {
            'id': 1, '_type': 'VMFile', 'src': 1, 'trackNumber': 0,
            'start': seconds_to_ticks(10.0), 'duration': seconds_to_ticks(10.0),
            'mediaStart': 0, 'mediaDuration': seconds_to_ticks(10.0),
            'scalar': 1, 'metadata': {}, 'parameters': {}, 'effects': [],
            'animationTracks': {},
        }
        data = {'trackIndex': 0, 'medias': [clip]}
        track = Track(attrs, data)
        with pytest.raises(ValueError, match='outside clip range'):
            track.split_clip(1, 5.0)  # before clip start at 10s
