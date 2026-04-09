from __future__ import annotations

import pytest

from camtasia.timeline.track import Track
from camtasia.timeline.clips import BaseClip, AMFile, VMFile, IMFile
from camtasia.timeline.transitions import TransitionList


def _make_track(
    index: int = 0,
    name: str = "test-track",
    audio_muted: bool = False,
    video_hidden: bool = False,
    is_locked: str = "False",
    medias: list[dict] | None = None,
    transitions: list[dict] | None = None,
) -> Track:
    attrs = {
        "ident": name,
        "audioMuted": audio_muted,
        "videoHidden": video_hidden,
        "magnetic": False,
        "metadata": {"IsLocked": is_locked},
    }
    data: dict = {
        "trackIndex": index,
        "medias": medias or [],
    }
    if transitions is not None:
        data["transitions"] = transitions
    return Track(attrs, data)


def _make_clip_dict(
    clip_id: int = 1,
    clip_type: str = "VMFile",
    src: int = 1,
    start: int = 0,
    duration: int = 100,
) -> dict:
    return {
        "id": clip_id,
        "_type": clip_type,
        "src": src,
        "start": start,
        "duration": duration,
        "mediaStart": 0,
        "mediaDuration": duration,
        "scalar": 1,
        "metadata": {},
        "animationTracks": {},
        "parameters": {},
        "effects": [],
    }


class TestTrackProperties:
    def test_name(self):
        track = _make_track(name="My Track")
        assert track.name == "My Track"

    def test_name_setter(self):
        track = _make_track(name="old")
        track.name = "new"
        assert track.name == "new"

    def test_index(self):
        track = _make_track(index=3)
        assert track.index == 3

    def test_audio_muted_false(self):
        track = _make_track(audio_muted=False)
        assert track.audio_muted is False

    def test_audio_muted_true(self):
        track = _make_track(audio_muted=True)
        assert track.audio_muted is True

    def test_video_hidden_false(self):
        track = _make_track(video_hidden=False)
        assert track.video_hidden is False

    def test_video_hidden_true(self):
        track = _make_track(video_hidden=True)
        assert track.video_hidden is True

    def test_is_locked_false(self):
        track = _make_track(is_locked="False")
        assert track.is_locked is False

    def test_is_locked_true(self):
        track = _make_track(is_locked="True")
        assert track.is_locked is True


class TestTrackClips:
    def test_empty_track_has_no_clips(self):
        track = _make_track()
        assert list(track.clips) == []

    def test_clips_yields_typed_objects(self):
        medias = [
            _make_clip_dict(clip_id=1, clip_type="VMFile"),
            _make_clip_dict(clip_id=2, clip_type="AMFile"),
            _make_clip_dict(clip_id=3, clip_type="IMFile"),
        ]
        track = _make_track(medias=medias)
        actual_clips = list(track.clips)
        assert isinstance(actual_clips[0], VMFile)
        assert isinstance(actual_clips[1], AMFile)
        assert isinstance(actual_clips[2], IMFile)
        actual_ids = [c.id for c in actual_clips]
        assert actual_ids == [1, 2, 3]

    def test_clips_len(self):
        medias = [_make_clip_dict(clip_id=1), _make_clip_dict(clip_id=2)]
        track = _make_track(medias=medias)
        actual_ids = [c.id for c in track.clips]
        assert actual_ids == [1, 2]

    def test_clips_getitem_by_id(self):
        medias = [_make_clip_dict(clip_id=10, clip_type="IMFile", src=5)]
        track = _make_track(medias=medias)
        actual_clip = track.clips[10]
        assert actual_clip.id == 10
        assert isinstance(actual_clip, IMFile)

    def test_clips_getitem_missing_raises(self):
        track = _make_track(medias=[_make_clip_dict(clip_id=1)])
        with pytest.raises(KeyError, match="No clip with id=999"):
            track.clips[999]


class TestTrackTransitions:
    def test_transitions_returns_transition_list(self):
        track = _make_track()
        assert isinstance(track.transitions, TransitionList)

    def test_empty_transitions(self):
        track = _make_track()
        assert list(track.transitions) == []

    def test_transitions_from_data(self):
        transitions = [
            {
                "name": "FadeThroughBlack",
                "duration": 1000,
                "leftMedia": 1,
                "rightMedia": 2,
                "attributes": {},
            }
        ]
        track = _make_track(transitions=transitions)
        actual_transitions = list(track.transitions)
        assert actual_transitions[0].name == "FadeThroughBlack"
        assert actual_transitions[0].duration == 1000
        assert actual_transitions[0].left_media_id == 1
        assert actual_transitions[0].right_media_id == 2


class TestTrackAddClip:
    def test_add_clip_creates_correct_json(self):
        track = _make_track()
        actual_clip = track.add_clip(
            clip_type="AMFile",
            source_id=5,
            start=1000,
            duration=5000,
        )
        assert isinstance(actual_clip, AMFile)
        assert actual_clip.clip_type == "AMFile"
        assert actual_clip.source_id == 5
        assert actual_clip.start == 1000
        assert actual_clip.duration == 5000

    def test_add_clip_without_source_id(self):
        track = _make_track()
        actual_clip = track.add_clip(
            clip_type="Callout",
            source_id=None,
            start=0,
            duration=3000,
        )
        assert actual_clip.source_id is None

    def test_add_clip_increments_id(self):
        track = _make_track(medias=[_make_clip_dict(clip_id=5)])
        actual_clip = track.add_clip("VMFile", source_id=1, start=200, duration=100)
        assert actual_clip.id == 6

    def test_add_clip_appears_in_iteration(self):
        track = _make_track()
        track.add_clip("VMFile", source_id=1, start=0, duration=100)
        actual_clips = list(track.clips)
        assert actual_clips[0].clip_type == "VMFile"
        assert actual_clips[0].start == 0


class TestTrackRemoveClip:
    def test_remove_clip_by_id(self):
        medias = [
            _make_clip_dict(clip_id=1),
            _make_clip_dict(clip_id=2),
        ]
        track = _make_track(medias=medias)
        track.remove_clip(1)
        actual_ids = [c.id for c in track.clips]
        assert actual_ids == [2]

    def test_remove_clip_missing_raises(self):
        track = _make_track(medias=[_make_clip_dict(clip_id=1)])
        with pytest.raises(KeyError, match="No clip with id=999"):
            track.remove_clip(999)

    def test_remove_all_clips(self):
        track = _make_track(medias=[_make_clip_dict(clip_id=1)])
        track.remove_clip(1)
        assert list(track.clips) == []
