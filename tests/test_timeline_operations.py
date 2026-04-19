"""Tests for Timeline.pack_all_tracks and Timeline.remove_empty_tracks."""
from __future__ import annotations

from camtasia.timeline.timeline import Timeline
from camtasia.timing import EDIT_RATE


def _make_timeline_data(
    tracks: list[dict] | None = None,
) -> dict:
    """Build minimal timeline data with matching trackAttributes."""
    scene_tracks = tracks or []
    attrs = [
        {"ident": f"Track {i}", "audioMuted": False, "videoHidden": False}
        for i in range(len(scene_tracks))
    ]
    for i, t in enumerate(scene_tracks):
        t.setdefault("trackIndex", i)
        t.setdefault("medias", [])
    return {
        "id": 1,
        "parameters": {"toc": {"type": "string", "keyframes": []}},
        "sceneTrack": {"scenes": [{"csml": {"tracks": scene_tracks}}]},
        "trackAttributes": attrs,
    }


def _clip(clip_id: int, start: int, duration: int) -> dict:
    """Build a minimal clip dict."""
    return {"id": clip_id, "_type": "VMFile", "start": start, "duration": duration}


# ── pack_all_tracks ──────────────────────────────────────────────────


class TestPackAllTracks:
    def test_returns_zero_for_empty_timeline(self) -> None:
        timeline = Timeline(_make_timeline_data())
        assert timeline.pack_all_tracks() == 0

    def test_returns_zero_when_all_tracks_empty(self) -> None:
        timeline = Timeline(_make_timeline_data([
            {"medias": []},
            {"medias": []},
        ]))
        assert timeline.pack_all_tracks() == 0

    def test_packs_single_track_with_gap(self) -> None:
        tracks = [{
            "medias": [
                _clip(1, start=0, duration=100),
                _clip(2, start=500, duration=200),
            ],
            "transitions": [],
        }]
        timeline = Timeline(_make_timeline_data(tracks))

        packed_count: int = timeline.pack_all_tracks()

        assert packed_count == 1
        medias = tracks[0]["medias"]
        assert medias[0]["start"] == 0
        assert medias[1]["start"] == 100

    def test_packs_multiple_tracks(self) -> None:
        tracks = [
            {
                "medias": [
                    _clip(1, start=0, duration=100),
                    _clip(2, start=300, duration=100),
                ],
                "transitions": [],
            },
            {
                "medias": [
                    _clip(3, start=50, duration=200),
                    _clip(4, start=1000, duration=100),
                ],
                "transitions": [],
            },
        ]
        timeline = Timeline(_make_timeline_data(tracks))

        packed_count: int = timeline.pack_all_tracks()

        assert packed_count == 2
        assert tracks[0]["medias"][0]["start"] == 0
        assert tracks[0]["medias"][1]["start"] == 100
        assert tracks[1]["medias"][0]["start"] == 0
        assert tracks[1]["medias"][1]["start"] == 200

    def test_skips_empty_tracks(self) -> None:
        tracks = [
            {"medias": [_clip(1, start=500, duration=100)], "transitions": []},
            {"medias": []},
        ]
        timeline = Timeline(_make_timeline_data(tracks))

        packed_count: int = timeline.pack_all_tracks()

        assert packed_count == 1
        assert tracks[0]["medias"][0]["start"] == 0

    def test_already_packed_track_is_idempotent(self) -> None:
        tracks = [{
            "medias": [
                _clip(1, start=0, duration=100),
                _clip(2, start=100, duration=200),
            ],
            "transitions": [],
        }]
        timeline = Timeline(_make_timeline_data(tracks))

        timeline.pack_all_tracks()

        assert tracks[0]["medias"][0]["start"] == 0
        assert tracks[0]["medias"][1]["start"] == 100


# ── remove_empty_tracks ──────────────────────────────────────────


class TestRemoveAllEmptyTracks:
    def test_returns_zero_when_no_empty_tracks(self) -> None:
        tracks = [{"medias": [_clip(1, 0, 100)]}]
        timeline = Timeline(_make_timeline_data(tracks))
        assert timeline.remove_empty_tracks() == 0

    def test_removes_single_empty_track(self) -> None:
        tracks = [
            {"medias": [_clip(1, 0, 100)]},
            {"medias": []},
        ]
        timeline = Timeline(_make_timeline_data(tracks))

        removed_count: int = timeline.remove_empty_tracks()

        assert removed_count == 1
        assert timeline.track_count == 1

    def test_removes_all_empty_tracks(self) -> None:
        tracks = [
            {"medias": []},
            {"medias": [_clip(1, 0, 100)]},
            {"medias": []},
        ]
        timeline = Timeline(_make_timeline_data(tracks))

        removed_count: int = timeline.remove_empty_tracks()

        assert removed_count == 2
        assert timeline.track_count == 1

    def test_returns_zero_for_empty_timeline(self) -> None:
        timeline = Timeline(_make_timeline_data())
        assert timeline.remove_empty_tracks() == 0

    def test_removes_all_when_every_track_empty(self) -> None:
        tracks = [{"medias": []}, {"medias": []}]
        timeline = Timeline(_make_timeline_data(tracks))

        removed_count: int = timeline.remove_empty_tracks()

        assert removed_count == 2
        assert timeline.track_count == 0

    def test_delegates_to_remove_empty_tracks(self) -> None:
        """Verify remove_empty_tracks produces the same result as remove_empty_tracks."""
        tracks_a = [{"medias": []}, {"medias": [_clip(1, 0, 100)]}, {"medias": []}]
        tracks_b = [{"medias": []}, {"medias": [_clip(1, 0, 100)]}, {"medias": []}]

        timeline_a = Timeline(_make_timeline_data(tracks_a))
        timeline_b = Timeline(_make_timeline_data(tracks_b))

        count_a: int = timeline_a.remove_empty_tracks()
        count_b: int = timeline_b.remove_empty_tracks()

        assert count_a == count_b
        assert timeline_a.track_count == timeline_b.track_count


def test_timeline_duration_seconds_property(project):
    """Timeline.duration_seconds delegates to total_duration_seconds."""
    assert project.timeline.duration_seconds == 0.0
