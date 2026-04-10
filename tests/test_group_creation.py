from __future__ import annotations

import pytest

from camtasia.timeline.clips import Group, UnifiedMedia
from camtasia.timeline.clips.audio import AMFile
from camtasia.timeline.clips.screen_recording import ScreenVMFile
from camtasia.timeline.track import Track


@pytest.fixture
def track():
    attrs = {'ident': 'Track 1'}
    data = {'trackIndex': 0, 'medias': []}
    return Track(attrs, data)


class TestAddScreenRecordingCreatesGroup:
    def test_returned_clip_is_group(self, track):
        clip = track.add_screen_recording(source_id=2, start_seconds=0.0, duration_seconds=10.0)
        assert isinstance(clip, Group), f"Expected Group, got {type(clip).__name__}"


class TestGroupHasInternalTracks:
    def test_group_has_two_internal_tracks(self, track):
        clip = track.add_screen_recording(source_id=2, start_seconds=0.0, duration_seconds=10.0)
        actual_track_count = len(clip.tracks)
        assert actual_track_count == 2, f"Expected 2 internal tracks, got {actual_track_count}"

    def test_track_zero_has_vmfile(self, track):
        clip = track.add_screen_recording(source_id=2, start_seconds=0.0, duration_seconds=10.0)
        track0_clips = clip.tracks[0].clips
        assert len(track0_clips) == 1, f"Expected 1 clip on track 0, got {len(track0_clips)}"
        assert track0_clips[0].clip_type == 'VMFile', f"Expected VMFile, got {track0_clips[0].clip_type}"

    def test_track_one_has_unified_media(self, track):
        clip = track.add_screen_recording(source_id=2, start_seconds=0.0, duration_seconds=10.0)
        track1_clips = clip.tracks[1].clips
        assert len(track1_clips) == 1, f"Expected 1 clip on track 1, got {len(track1_clips)}"
        assert isinstance(track1_clips[0], UnifiedMedia), (
            f"Expected UnifiedMedia, got {type(track1_clips[0]).__name__}"
        )


class TestGroupUnifiedMediaHasVideoAndAudio:
    def test_unified_media_video_is_screen_vmfile(self, track):
        clip = track.add_screen_recording(source_id=2, start_seconds=0.0, duration_seconds=10.0)
        um = clip.tracks[1].clips[0]
        assert isinstance(um, UnifiedMedia)
        assert isinstance(um.video, ScreenVMFile), (
            f"Expected ScreenVMFile, got {type(um.video).__name__}"
        )

    def test_unified_media_audio_is_amfile(self, track):
        clip = track.add_screen_recording(source_id=2, start_seconds=0.0, duration_seconds=10.0)
        um = clip.tracks[1].clips[0]
        assert isinstance(um, UnifiedMedia)
        assert isinstance(um.audio, AMFile), f"Expected AMFile, got {type(um.audio).__name__}"

    def test_video_and_audio_share_source_id(self, track):
        clip = track.add_screen_recording(source_id=5, start_seconds=0.0, duration_seconds=10.0)
        um = clip.tracks[1].clips[0]
        assert um.video._data['src'] == 5, f"Expected video src=5, got {um.video._data['src']}"
        assert um.audio._data['src'] == 5, f"Expected audio src=5, got {um.audio._data['src']}"


class TestGroupClipPosition:
    def test_start_seconds(self, track):
        clip = track.add_screen_recording(source_id=2, start_seconds=5.0, duration_seconds=10.0)
        assert clip.start_seconds == pytest.approx(5.0), (
            f"Expected start 5.0s, got {clip.start_seconds}"
        )

    def test_duration_seconds(self, track):
        clip = track.add_screen_recording(source_id=2, start_seconds=0.0, duration_seconds=12.5)
        assert clip.duration_seconds == pytest.approx(12.5), (
            f"Expected duration 12.5s, got {clip.duration_seconds}"
        )


class TestGroupMuteWorks:
    def test_mute_sets_gain_to_zero(self, track):
        clip = track.add_screen_recording(source_id=2, start_seconds=0.0, duration_seconds=10.0)
        clip.mute()
        assert clip.gain == 0.0, f"Expected gain 0.0 after mute, got {clip.gain}"

    def test_mute_returns_self(self, track):
        clip = track.add_screen_recording(source_id=2, start_seconds=0.0, duration_seconds=10.0)
        result = clip.mute()
        assert result is clip, "mute() should return self for chaining"
