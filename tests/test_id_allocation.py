from __future__ import annotations

from camtasia.timeline.timeline import Timeline
from camtasia.timeline.track import Track


def _make_timeline_data(
    tracks: list[dict] | None = None,
    track_attributes: list[dict] | None = None,
) -> dict:
    if tracks is None:
        tracks = []
    if track_attributes is None:
        track_attributes = [
            {"ident": f"Track-{i}", "audioMuted": False, "videoHidden": False,
             "magnetic": False, "metadata": {"IsLocked": "False"}}
            for i in range(len(tracks))
        ]
    return {
        "id": 1,
        "sceneTrack": {"scenes": [{"csml": {"tracks": tracks}}]},
        "trackAttributes": track_attributes,
    }


def _media_dict(clip_id: int, **overrides: object) -> dict:
    base: dict = {
        "id": clip_id,
        "_type": "VMFile",
        "src": 1,
        "start": 0,
        "duration": 100,
        "mediaStart": 0,
        "mediaDuration": 100,
        "scalar": 1,
        "metadata": {},
        "animationTracks": {},
        "parameters": {},
        "effects": [],
    }
    base.update(overrides)
    return base


class TestNextClipId:
    """Timeline.next_clip_id() — project-wide ID allocator."""

    def test_empty_project_returns_1(self):
        data = _make_timeline_data(tracks=[])
        timeline = Timeline(data)
        actual_result = timeline.next_clip_id()
        assert actual_result == 2  # timeline data has id=1

    def test_single_track(self):
        tracks = [{"trackIndex": 0, "medias": [_media_dict(5)]}]
        data = _make_timeline_data(tracks=tracks)
        timeline = Timeline(data)
        actual_result = timeline.next_clip_id()
        assert actual_result == 6

    def test_multiple_tracks_returns_global_max(self):
        tracks = [
            {"trackIndex": 0, "medias": [_media_dict(3)]},
            {"trackIndex": 1, "medias": [_media_dict(10)]},
            {"trackIndex": 2, "medias": [_media_dict(7)]},
        ]
        data = _make_timeline_data(tracks=tracks)
        timeline = Timeline(data)
        actual_result = timeline.next_clip_id()
        assert actual_result == 11

    def test_nested_group_ids_included(self):
        group_media = _media_dict(2, _type="Group", tracks=[
            {"trackIndex": 0, "medias": [_media_dict(20)]},
        ])
        tracks = [
            {"trackIndex": 0, "medias": [_media_dict(1)]},
            {"trackIndex": 1, "medias": [group_media]},
        ]
        data = _make_timeline_data(tracks=tracks)
        timeline = Timeline(data)
        actual_result = timeline.next_clip_id()
        assert actual_result == 21

    def test_unified_media_video_audio_ids_included(self):
        unified = {
            "id": 5,
            "_type": "UnifiedMedia",
            "video": {"id": 30, "_type": "ScreenVMFile", "src": 1},
            "audio": {"id": 25, "_type": "AMFile", "src": 1},
            "start": 0, "duration": 100, "mediaStart": 0,
            "mediaDuration": 100, "scalar": 1, "effects": [],
        }
        tracks = [
            {"trackIndex": 0, "medias": [unified]},
        ]
        data = _make_timeline_data(tracks=tracks)
        timeline = Timeline(data)
        actual_result = timeline.next_clip_id()
        assert actual_result == 31

    def test_deeply_nested_group_with_unified_media(self):
        """Group containing a track with UnifiedMedia — all IDs scanned."""
        unified = {
            "id": 10,
            "_type": "UnifiedMedia",
            "video": {"id": 50, "_type": "ScreenVMFile", "src": 1},
            "audio": {"id": 40, "_type": "AMFile", "src": 1},
            "start": 0, "duration": 100, "mediaStart": 0,
            "mediaDuration": 100, "scalar": 1, "effects": [],
        }
        group_media = _media_dict(2, _type="Group", tracks=[
            {"trackIndex": 0, "medias": [unified]},
        ])
        tracks = [{"trackIndex": 0, "medias": [group_media]}]
        data = _make_timeline_data(tracks=tracks)
        timeline = Timeline(data)
        actual_result = timeline.next_clip_id()
        assert actual_result == 51


class TestTrackNextClipIdWithAllTracks:
    """Track._next_clip_id() uses _all_tracks when provided."""

    def test_track_with_all_tracks_scans_globally(self):
        track_a = {"trackIndex": 0, "medias": [_media_dict(3)]}
        track_b = {"trackIndex": 1, "medias": [_media_dict(15)]}
        all_tracks = [track_a, track_b]
        track = Track({"ident": "A"}, track_a, _all_tracks=all_tracks)
        actual_result = track._next_clip_id()
        assert actual_result == 16

    def test_track_without_all_tracks_scans_only_self(self):
        """Backward compat: Track created without _all_tracks still works."""
        data = {"trackIndex": 0, "medias": [_media_dict(7)]}
        track = Track({"ident": "A"}, data)
        actual_result = track._next_clip_id()
        assert actual_result == 8

    def test_track_without_all_tracks_empty(self):
        data = {"trackIndex": 0, "medias": []}
        track = Track({"ident": "A"}, data)
        actual_result = track._next_clip_id()
        assert actual_result == 1


class TestTrackAccessorPassesAllTracks:
    """_TrackAccessor passes _all_tracks so Track objects see all IDs."""

    def test_add_clip_on_second_track_avoids_collision(self):
        tracks = [
            {"trackIndex": 0, "medias": [_media_dict(10)]},
            {"trackIndex": 1, "medias": []},
        ]
        data = _make_timeline_data(tracks=tracks)
        timeline = Timeline(data)
        track_1 = timeline.tracks[1]
        clip = track_1.add_clip("VMFile", source_id=1, start=0, duration=100)
        assert clip.id == 11
