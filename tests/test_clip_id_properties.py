"""Tests for Track.clip_ids, Timeline.all_clip_ids, and Project.next_available_id."""
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


def _media(clip_id: int) -> dict:
    return {
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


def _track(index: int, clip_ids: list[int]) -> dict:
    return {"trackIndex": index, "medias": [_media(cid) for cid in clip_ids]}


# ── Track.clip_ids ──────────────────────────────────────────────────

class TestTrackClipIds:
    def test_empty_track(self) -> None:
        attrs = {"ident": "T", "audioMuted": False, "videoHidden": False}
        track = Track(attrs, {"trackIndex": 0, "medias": []})
        assert track.clip_ids == []

    def test_single_clip(self) -> None:
        attrs = {"ident": "T", "audioMuted": False, "videoHidden": False}
        track = Track(attrs, _track(0, [42]))
        assert track.clip_ids == [42]

    def test_multiple_clips_preserves_order(self) -> None:
        attrs = {"ident": "T", "audioMuted": False, "videoHidden": False}
        track = Track(attrs, _track(0, [7, 3, 15]))
        assert track.clip_ids == [7, 3, 15]

    def test_returns_ints(self) -> None:
        attrs = {"ident": "T", "audioMuted": False, "videoHidden": False}
        track = Track(attrs, _track(0, [1]))
        assert all(isinstance(i, int) for i in track.clip_ids)


# ── Timeline.all_clip_ids ──────────────────────────────────────────

class TestAllClipIds:
    def test_empty_timeline(self) -> None:
        tl = Timeline(_make_timeline_data(tracks=[]))
        assert tl.all_clip_ids == set()

    def test_single_track(self) -> None:
        tl = Timeline(_make_timeline_data(tracks=[_track(0, [1, 2, 3])]))
        assert tl.all_clip_ids == {1, 2, 3}

    def test_multiple_tracks(self) -> None:
        tracks = [_track(0, [1, 2]), _track(1, [5, 10])]
        tl = Timeline(_make_timeline_data(tracks=tracks))
        assert tl.all_clip_ids == {1, 2, 5, 10}

    def test_returns_set(self) -> None:
        tl = Timeline(_make_timeline_data(tracks=[_track(0, [1])]))
        assert isinstance(tl.all_clip_ids, set)


# ── Project.next_available_id ──────────────────────────────────────

class TestNextAvailableId:
    def test_empty_project(self, project) -> None:  # type: ignore[no-untyped-def]
        assert project.next_available_id >= 1  # timeline itself has an ID

    def test_with_clips(self, project) -> None:  # type: ignore[no-untyped-def]
        track = project.timeline.add_track("Test")
        track.add_clip("AMFile", 1, 0, 705600000)
        existing_ids = project.timeline.all_clip_ids
        assert project.next_available_id == max(existing_ids) + 1

    def test_returns_int(self, project) -> None:  # type: ignore[no-untyped-def]
        assert isinstance(project.next_available_id, int)
