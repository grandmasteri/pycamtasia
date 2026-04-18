from __future__ import annotations

import pytest

from camtasia.media_bin.media_bin import Media
from camtasia.timeline.clips.group import Group


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _group_dict(**overrides):
    base = {
        'id': 1, '_type': 'Group', 'src': 0,
        'start': 0, 'duration': 100, 'mediaStart': 0,
        'mediaDuration': 100, 'scalar': 1,
        'metadata': {}, 'parameters': {}, 'effects': [],
        'attributes': {'ident': ''}, 'animationTracks': {},
        'tracks': [],
    }
    base.update(overrides)
    return base


def _media_dict(**overrides):
    base = {
        'id': 1,
        'src': './media/recording.trec',
        'rect': [0, 0, 1920, 1080],
        'lastMod': '20250101T120000',
        'sourceTracks': [],
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Group.is_screen_recording
# ---------------------------------------------------------------------------

class TestIsScreenRecording:
    def test_unified_media_returns_true(self):
        data = _group_dict(tracks=[
            {'medias': [{'_type': 'UnifiedMedia', 'src': 1, 'video': {'_type': 'ScreenVMFile'}}]},
        ])
        actual_result = Group(data).is_screen_recording
        assert actual_result is True

    def test_screen_vmfile_returns_true(self):
        data = _group_dict(tracks=[
            {'medias': [{'_type': 'ScreenVMFile', 'src': 1}]},
        ])
        actual_result = Group(data).is_screen_recording
        assert actual_result is True

    @pytest.mark.parametrize('clip_type', ['VMFile', 'IMFile'])
    def test_non_screen_recording_returns_false(self, clip_type):
        data = _group_dict(tracks=[
            {'medias': [{'_type': clip_type, 'src': 1}]},
        ])
        actual_result = Group(data).is_screen_recording
        assert actual_result is False

    def test_no_internal_tracks_returns_false(self):
        data = _group_dict(tracks=[])
        actual_result = Group(data).is_screen_recording
        assert actual_result is False


# ---------------------------------------------------------------------------
# Group.internal_media_src
# ---------------------------------------------------------------------------

class TestInternalMediaSrc:
    def test_unified_media_returns_video_src(self):
        data = _group_dict(tracks=[
            {'medias': [{'_type': 'UnifiedMedia', 'video': {'src': 42}}]},
        ])
        actual_result = Group(data).internal_media_src
        expected_result = 42
        assert actual_result == expected_result

    def test_screen_vmfile_returns_src(self):
        data = _group_dict(tracks=[
            {'medias': [{'_type': 'ScreenVMFile', 'src': 99}]},
        ])
        actual_result = Group(data).internal_media_src
        expected_result = 99
        assert actual_result == expected_result

    def test_non_screen_recording_returns_none(self):
        data = _group_dict(tracks=[
            {'medias': [{'_type': 'VMFile', 'src': 1}]},
        ])
        actual_result = Group(data).internal_media_src
        assert actual_result is None


# ---------------------------------------------------------------------------
# Media.duration_seconds
# ---------------------------------------------------------------------------

class TestMediaDurationSeconds:
    def test_video_track_returns_correct_duration(self):
        data = _media_dict(sourceTracks=[
            {'type': 0, 'range': [0, 30000], 'editRate': 1000},
        ])
        actual_result = Media(data).duration_seconds
        expected_result = 30.0
        assert actual_result == pytest.approx(expected_result)

    def test_audio_only_returns_correct_duration(self):
        data = _media_dict(sourceTracks=[
            {'type': 2, 'range': [0, 441000], 'editRate': 44100},
        ])
        actual_result = Media(data).duration_seconds
        expected_result = 10.0
        assert actual_result == pytest.approx(expected_result)

    def test_no_source_tracks_returns_none(self):
        data = _media_dict(sourceTracks=[])
        actual_result = Media(data).duration_seconds
        assert actual_result is None

    def test_video_preferred_over_audio(self):
        data = _media_dict(sourceTracks=[
            {'type': 0, 'range': [0, 5000], 'editRate': 1000},
            {'type': 2, 'range': [0, 441000], 'editRate': 44100},
        ])
        actual_result = Media(data).duration_seconds
        expected_result = 5.0
        assert actual_result == pytest.approx(expected_result)
