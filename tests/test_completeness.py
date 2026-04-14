from __future__ import annotations

from camtasia.media_bin.media_bin import Media
from camtasia.timeline.clips.group import Group
from camtasia.timeline.clips.unified import UnifiedMedia
from camtasia.timeline.clips.stitched import StitchedMedia


class TestMediaSourceTracks:
    def test_source_tracks_returns_list(self):
        actual_tracks = Media({
            'id': 1, 'src': './media/test.mp4', 'rect': [0, 0, 1920, 1080],
            'lastMod': '20250101T120000',
            'sourceTracks': [
                {'type': 0, 'editRate': 30, 'range': [0, 9000]},
                {'type': 2, 'editRate': 44100, 'range': [0, 441000]},
            ],
        }).source_tracks
        assert [t['type'] for t in actual_tracks] == [0, 2]

    def test_source_tracks_empty_when_missing(self):
        actual_tracks = Media({
            'id': 1, 'src': './media/test.png', 'rect': [0, 0, 100, 100],
            'lastMod': '20250101T120000',
        }).source_tracks
        assert actual_tracks == []

    def test_video_edit_rate_returns_int(self):
        actual_rate = Media({
            'id': 1, 'src': './media/test.mp4', 'rect': [0, 0, 1920, 1080],
            'lastMod': '20250101T120000',
            'sourceTracks': [{'type': 0, 'editRate': 30, 'range': [0, 9000]}],
        }).video_edit_rate
        expected_rate = 30
        assert actual_rate == expected_rate

    def test_video_edit_rate_none_when_no_video_track(self):
        actual_rate = Media({
            'id': 1, 'src': './media/test.wav', 'rect': [0, 0, 0, 0],
            'lastMod': '20250101T120000',
            'sourceTracks': [{'type': 2, 'editRate': 44100, 'range': [0, 441000]}],
        }).video_edit_rate
        assert actual_rate is None


class TestGroupFindInternalClip:
    def _make_group(self) -> Group:
        return Group({
            'id': 1, '_type': 'Group', 'start': 0, 'duration': 100,
            'mediaStart': 0, 'mediaDuration': 100, 'scalar': 1,
            'tracks': [{
                'trackIndex': 0,
                'medias': [
                    {'id': 10, '_type': 'ScreenVMFile', 'start': 0, 'duration': 100,
                     'mediaStart': 0, 'mediaDuration': 100, 'scalar': 1},
                    {'id': 11, '_type': 'AMFile', 'start': 0, 'duration': 100,
                     'mediaStart': 0, 'mediaDuration': 100, 'scalar': 1},
                ],
            }],
        })

    def test_find_existing_clip(self):
        actual_clip = self._make_group().find_internal_clip('AMFile')
        assert actual_clip is not None
        assert actual_clip.clip_type == 'AMFile'

    def test_find_returns_none_when_not_found(self):
        actual_clip = self._make_group().find_internal_clip('VMFile')
        assert actual_clip is None


class TestUnifiedMediaImprovements:
    def _make_unified(self) -> UnifiedMedia:
        return UnifiedMedia({
            'id': 1, '_type': 'UnifiedMedia', 'start': 0, 'duration': 100,
            'mediaStart': 0, 'mediaDuration': 100, 'scalar': 1,
            'video': {'id': 2, '_type': 'ScreenVMFile', 'src': 42,
                      'start': 0, 'duration': 100, 'mediaStart': 0,
                      'mediaDuration': 100, 'scalar': 1},
            'audio': {'id': 3, '_type': 'AMFile',
                      'attributes': {'gain': 1.0},
                      'start': 0, 'duration': 100, 'mediaStart': 0,
                      'mediaDuration': 100, 'scalar': 1},
        })

    def test_source_id(self):
        actual_id = self._make_unified().source_id
        expected_id = 42
        assert actual_id == expected_id

    def test_source_id_none_when_no_video(self):
        actual_id = UnifiedMedia({
            'id': 1, '_type': 'UnifiedMedia', 'start': 0, 'duration': 100,
            'mediaStart': 0, 'mediaDuration': 100, 'scalar': 1,
        }).source_id
        assert actual_id is None

    def test_mute_audio(self):
        actual_clip = self._make_unified()
        actual_result = actual_clip.mute_audio()
        expected_gain = 0.0
        assert actual_clip._data['audio']['attributes']['gain'] == expected_gain
        assert actual_result is actual_clip

    def test_mute_audio_no_audio(self):
        actual_clip = UnifiedMedia({
            'id': 1, '_type': 'UnifiedMedia', 'start': 0, 'duration': 100,
            'mediaStart': 0, 'mediaDuration': 100, 'scalar': 1,
            'video': {'id': 2, '_type': 'ScreenVMFile', 'src': 42,
                      'start': 0, 'duration': 100, 'mediaStart': 0,
                      'mediaDuration': 100, 'scalar': 1},
        })
        actual_result = actual_clip.mute_audio()
        assert actual_result is actual_clip


class TestStitchedMediaImprovements:
    def _make_stitched(self) -> StitchedMedia:
        return StitchedMedia({
            'id': 1, '_type': 'StitchedMedia', 'start': 0, 'duration': 200,
            'mediaStart': 0, 'mediaDuration': 200, 'scalar': 1,
            'medias': [
                {'id': 10, '_type': 'ScreenVMFile', 'start': 0, 'duration': 100,
                 'mediaStart': 0, 'mediaDuration': 100, 'scalar': 1},
                {'id': 11, '_type': 'ScreenVMFile', 'start': 100, 'duration': 100,
                 'mediaStart': 100, 'mediaDuration': 100, 'scalar': 1},
            ],
        })

    def test_segment_count(self):
        actual_count = self._make_stitched().segment_count
        expected_count = 2
        assert actual_count == expected_count

    def test_segment_count_empty(self):
        actual_count = StitchedMedia({
            'id': 1, '_type': 'StitchedMedia', 'start': 0, 'duration': 0,
            'mediaStart': 0, 'mediaDuration': 0, 'scalar': 1,
        }).segment_count
        expected_count = 0
        assert actual_count == expected_count

    def test_clear_segments(self):
        actual_clip = self._make_stitched()
        actual_clip.clear_segments()
        expected_count = 0
        assert actual_clip.segment_count == expected_count
        assert actual_clip._data['medias'] == []
