from __future__ import annotations

import pytest

from camtasia.timeline.timeline import Timeline


def _make_timeline_data(n_tracks=3, clips_per_track=0):
    tracks = []
    clip_id = 1
    for i in range(n_tracks):
        medias = []
        for j in range(clips_per_track):
            medias.append({
                "id": clip_id, "_type": "IMFile", "src": 10,
                "trackNumber": 0, "start": j * 1000, "duration": 1000,
                "mediaStart": 0, "mediaDuration": 1, "scalar": 1,
                "metadata": {}, "animationTracks": {}, "parameters": {},
                "effects": [],
            })
            clip_id += 1
        tracks.append({"trackIndex": i, "medias": medias})
    attrs = [
        {"ident": f"Track-{i}", "audioMuted": False, "videoHidden": False,
         "magnetic": False, "metadata": {"IsLocked": "False"}}
        for i in range(n_tracks)
    ]
    return {
        "id": 1,
        "sceneTrack": {"scenes": [{"csml": {"tracks": tracks}}]},
        "trackAttributes": attrs,
    }


class TestTimelineRepr:
    def test_repr(self):
        tl = Timeline(_make_timeline_data(3))
        assert repr(tl) == "Timeline(tracks=3)"

    def test_repr_empty(self):
        tl = Timeline(_make_timeline_data(0))
        assert repr(tl) == "Timeline(tracks=0)"


class TestTimelineLen:
    def test_len(self):
        tl = Timeline(_make_timeline_data(5))
        assert [t.index for t in tl.tracks] == [0, 1, 2, 3, 4]

    def test_len_empty(self):
        tl = Timeline(_make_timeline_data(0))
        assert list(tl.tracks) == []


class TestMoveTrackToBack:
    def test_moves_to_position_zero(self):
        tl = Timeline(_make_timeline_data(3))
        tl.move_track_to_back(2)
        names = [t.name for t in tl.tracks]
        assert names == ["Track-2", "Track-0", "Track-1"]

    def test_already_at_back_is_noop(self):
        tl = Timeline(_make_timeline_data(3))
        tl.move_track_to_back(0)
        names = [t.name for t in tl.tracks]
        assert names == ["Track-0", "Track-1", "Track-2"]


class TestMoveTrackToFront:
    def test_moves_to_last_position(self):
        tl = Timeline(_make_timeline_data(3))
        tl.move_track_to_front(0)
        names = [t.name for t in tl.tracks]
        assert names == ["Track-1", "Track-2", "Track-0"]

    def test_already_at_front_is_noop(self):
        tl = Timeline(_make_timeline_data(3))
        tl.move_track_to_front(2)
        names = [t.name for t in tl.tracks]
        assert names == ["Track-0", "Track-1", "Track-2"]


class TestTimelineFindClip:
    def test_found(self):
        tl = Timeline(_make_timeline_data(3, clips_per_track=2))
        # clip_id=3 is on track 1 (ids: track0=[1,2], track1=[3,4], track2=[5,6])
        result = tl.find_clip(3)
        assert result is not None
        track, clip = result
        assert track.index == 1
        assert clip.id == 3

    def test_not_found(self):
        tl = Timeline(_make_timeline_data(3, clips_per_track=2))
        assert tl.find_clip(999) is None

    def test_empty_timeline(self):
        tl = Timeline(_make_timeline_data(0))
        assert tl.find_clip(1) is None
