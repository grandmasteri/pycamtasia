from __future__ import annotations

import pytest

from camtasia.timeline.timeline import Timeline


def _make_timeline_data(
    tracks: list[dict] | None = None,
    track_attributes: list[dict] | None = None,
) -> dict:
    if tracks is None:
        tracks = [
            {"trackIndex": 0, "medias": []},
            {"trackIndex": 1, "medias": []},
            {"trackIndex": 2, "medias": []},
        ]
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


def _track_names(timeline: Timeline) -> list[str]:
    return [t.name for t in timeline.tracks]


def _track_indices(timeline: Timeline) -> list[int]:
    return [t.index for t in timeline.tracks]


class TestMoveTrack:
    def test_move_track_swaps_correctly(self):
        data = _make_timeline_data()
        timeline = Timeline(data)
        timeline.move_track(0, 2)
        actual_result = _track_names(timeline)
        assert actual_result == ["Track-1", "Track-2", "Track-0"]

    def test_move_track_renumbers_indices(self):
        data = _make_timeline_data()
        timeline = Timeline(data)
        timeline.move_track(0, 2)
        actual_result = _track_indices(timeline)
        assert actual_result == [0, 1, 2]

    def test_move_track_keeps_attributes_in_sync(self):
        data = _make_timeline_data()
        timeline = Timeline(data)
        timeline.move_track(2, 0)
        actual_names = _track_names(timeline)
        actual_attr_idents = [a["ident"] for a in data["trackAttributes"]]
        assert actual_names == ["Track-2", "Track-0", "Track-1"]
        assert actual_attr_idents == ["Track-2", "Track-0", "Track-1"]

    def test_move_track_same_position_is_noop(self):
        data = _make_timeline_data()
        timeline = Timeline(data)
        timeline.move_track(1, 1)
        actual_result = _track_names(timeline)
        assert actual_result == ["Track-0", "Track-1", "Track-2"]

    def test_move_track_invalid_from_index_raises(self):
        data = _make_timeline_data()
        timeline = Timeline(data)
        with pytest.raises(IndexError, match="Track index out of range"):
            timeline.move_track(5, 0)

    def test_move_track_invalid_to_index_raises(self):
        data = _make_timeline_data()
        timeline = Timeline(data)
        with pytest.raises(IndexError, match="Track index out of range"):
            timeline.move_track(0, 5)

    def test_move_track_negative_index_raises(self):
        data = _make_timeline_data()
        timeline = Timeline(data)
        with pytest.raises(IndexError, match="Track index out of range"):
            timeline.move_track(-1, 0)


class TestReorderTracks:
    def test_full_reorder(self):
        data = _make_timeline_data()
        timeline = Timeline(data)
        timeline.reorder_tracks([2, 0, 1])
        actual_names = _track_names(timeline)
        assert actual_names == ["Track-2", "Track-0", "Track-1"]

    def test_reorder_renumbers_indices(self):
        data = _make_timeline_data()
        timeline = Timeline(data)
        timeline.reorder_tracks([2, 1, 0])
        actual_result = _track_indices(timeline)
        assert actual_result == [0, 1, 2]

    def test_reorder_keeps_attributes_in_sync(self):
        data = _make_timeline_data()
        timeline = Timeline(data)
        timeline.reorder_tracks([1, 2, 0])
        actual_attr_idents = [a["ident"] for a in data["trackAttributes"]]
        assert actual_attr_idents == ["Track-1", "Track-2", "Track-0"]

    def test_reorder_identity_is_noop(self):
        data = _make_timeline_data()
        timeline = Timeline(data)
        timeline.reorder_tracks([0, 1, 2])
        actual_result = _track_names(timeline)
        assert actual_result == ["Track-0", "Track-1", "Track-2"]

    def test_partial_list_raises(self):
        data = _make_timeline_data()
        timeline = Timeline(data)
        with pytest.raises(ValueError, match="order must contain exactly all"):
            timeline.reorder_tracks([0, 1])

    def test_duplicate_indices_raises(self):
        data = _make_timeline_data()
        timeline = Timeline(data)
        with pytest.raises(ValueError, match="order must contain exactly all"):
            timeline.reorder_tracks([0, 0, 1])

    def test_wrong_indices_raises(self):
        data = _make_timeline_data()
        timeline = Timeline(data)
        with pytest.raises(ValueError, match="order must contain exactly all"):
            timeline.reorder_tracks([0, 1, 99])

    def test_reorder_with_fewer_attrs_than_tracks(self):
        """Bug 13: attrs shorter than tracks should be padded before reorder."""
        tracks = [
            {"trackIndex": 0, "medias": []},
            {"trackIndex": 1, "medias": []},
            {"trackIndex": 2, "medias": []},
        ]
        # Only 2 attrs for 3 tracks
        attrs = [
            {"ident": "Track-0", "audioMuted": False},
            {"ident": "Track-1", "audioMuted": False},
        ]
        data = _make_timeline_data(tracks=tracks, track_attributes=attrs)
        timeline = Timeline(data)
        # Should not raise IndexError
        timeline.reorder_tracks([2, 0, 1])
        actual_names = _track_names(timeline)
        # Track-2 had no attrs → gets empty dict → name is ''
        assert actual_names == ["", "Track-0", "Track-1"]
        assert _track_indices(timeline) == [0, 1, 2]
