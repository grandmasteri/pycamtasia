from __future__ import annotations

import pytest

from camtasia.timeline.marker import Marker
from camtasia.timeline.timeline import Timeline
from camtasia.timeline.track import Track


def _make_timeline_data(
    tracks: list[dict] | None = None,
    track_attributes: list[dict] | None = None,
    markers: list[dict] | None = None,
) -> dict:
    if tracks is None:
        tracks = [
            {"trackIndex": 0, "medias": []},
            {"trackIndex": 1, "medias": []},
        ]
    if track_attributes is None:
        track_attributes = [
            {
                "ident": f"Track-{i}",
                "audioMuted": False,
                "videoHidden": False,
                "magnetic": False,
                "metadata": {"IsLocked": "False"},
            }
            for i in range(len(tracks))
        ]
    data: dict = {
        "id": 1,
        "sceneTrack": {
            "scenes": [{"csml": {"tracks": tracks}}]
        },
        "trackAttributes": track_attributes,
    }
    if markers:
        data["parameters"] = {
            "toc": {
                "type": "string",
                "keyframes": markers,
            }
        }
    return data


class TestTimelineTracks:
    def test_iteration_yields_track_objects(self):
        data = _make_timeline_data()
        timeline = Timeline(data)
        actual_tracks = list(timeline.tracks)
        assert all(isinstance(t, Track) for t in actual_tracks)
        actual_names = [t.name for t in actual_tracks]
        assert actual_names == ["Track-0", "Track-1"]

    def test_track_count(self):
        data = _make_timeline_data()
        timeline = Timeline(data)
        assert timeline.track_count == 2

    def test_track_count_empty(self):
        data = _make_timeline_data(tracks=[], track_attributes=[])
        timeline = Timeline(data)
        assert timeline.track_count == 0

    def test_get_track_by_index(self):
        data = _make_timeline_data()
        timeline = Timeline(data)
        actual_track = timeline.tracks[1]
        assert actual_track.name == "Track-1"
        assert actual_track.index == 1

    def test_get_track_missing_index_raises(self):
        data = _make_timeline_data()
        timeline = Timeline(data)
        with pytest.raises(KeyError, match="No track with index=99"):
            timeline.tracks[99]


class TestTimelineAddTrack:
    def test_add_track_increases_count(self):
        data = _make_timeline_data()
        timeline = Timeline(data)
        new_track = timeline.add_track("new-track")
        assert timeline.track_count == 3
        assert new_track.name == "new-track"

    def test_add_track_is_retrievable(self):
        data = _make_timeline_data()
        timeline = Timeline(data)
        timeline.add_track("added")
        actual_track = timeline.tracks[2]
        assert actual_track.name == "added"
        assert actual_track.index == 2


class TestTimelineRemoveTrack:
    def test_remove_track_decreases_count(self):
        data = _make_timeline_data()
        timeline = Timeline(data)
        timeline.remove_track(0)
        assert timeline.track_count == 1

    def test_remove_track_renumbers_indices(self):
        tracks = [
            {"trackIndex": 0, "medias": []},
            {"trackIndex": 1, "medias": []},
            {"trackIndex": 2, "medias": []},
        ]
        attrs = [
            {"ident": "A", "audioMuted": False, "videoHidden": False, "magnetic": False, "metadata": {"IsLocked": "False"}},
            {"ident": "B", "audioMuted": False, "videoHidden": False, "magnetic": False, "metadata": {"IsLocked": "False"}},
            {"ident": "C", "audioMuted": False, "videoHidden": False, "magnetic": False, "metadata": {"IsLocked": "False"}},
        ]
        data = _make_timeline_data(tracks=tracks, track_attributes=attrs)
        timeline = Timeline(data)
        timeline.remove_track(1)
        actual_tracks = list(timeline.tracks)
        actual_names = [t.name for t in actual_tracks]
        actual_indices = [t.index for t in actual_tracks]
        assert actual_names == ["A", "C"]
        assert actual_indices == [0, 1]

    def test_remove_track_keeps_track_attributes_in_sync(self):
        tracks = [
            {"trackIndex": 0, "medias": []},
            {"trackIndex": 1, "medias": []},
        ]
        attrs = [
            {"ident": "keep", "audioMuted": False, "videoHidden": False, "magnetic": False, "metadata": {"IsLocked": "False"}},
            {"ident": "remove", "audioMuted": False, "videoHidden": False, "magnetic": False, "metadata": {"IsLocked": "False"}},
        ]
        data = _make_timeline_data(tracks=tracks, track_attributes=attrs)
        timeline = Timeline(data)
        timeline.remove_track(1)
        remaining_attrs = data["trackAttributes"]
        assert [a["ident"] for a in remaining_attrs] == ["keep"]

    def test_remove_missing_track_raises(self):
        data = _make_timeline_data()
        timeline = Timeline(data)
        with pytest.raises(KeyError, match="No track with index=99"):
            timeline.remove_track(99)


class TestTimelineMarkers:
    def test_no_markers_initially(self):
        data = _make_timeline_data()
        timeline = Timeline(data)
        assert list(timeline.markers) == []

    def test_markers_from_data(self):
        marker_keyframes = [
            {"time": 150, "endTime": 150, "value": "marker-1", "duration": 0},
            {"time": 300, "endTime": 300, "value": "marker-2", "duration": 0},
        ]
        data = _make_timeline_data(markers=marker_keyframes)
        timeline = Timeline(data)
        actual_markers = sorted(timeline.markers, key=lambda m: m.time)
        expected_markers = [
            Marker(name="marker-1", time=150),
            Marker(name="marker-2", time=300),
        ]
        assert actual_markers == expected_markers

    def test_add_marker(self):
        data = _make_timeline_data()
        timeline = Timeline(data)
        timeline.markers.add("new-marker", 500)
        actual_markers = list(timeline.markers)
        assert actual_markers == [Marker(name="new-marker", time=500)]

    def test_remove_marker(self):
        marker_keyframes = [
            {"time": 100, "endTime": 100, "value": "m1", "duration": 0},
            {"time": 200, "endTime": 200, "value": "m2", "duration": 0},
        ]
        data = _make_timeline_data(markers=marker_keyframes)
        timeline = Timeline(data)
        timeline.markers.remove_at(100)
        actual_markers = list(timeline.markers)
        assert actual_markers == [Marker(name="m2", time=200)]
