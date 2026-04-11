"""Tests for camtasia.timeline.track — attribute flags, clip helpers, transitions."""
from __future__ import annotations

from typing import Any

import pytest

from camtasia.timeline.track import Track
from camtasia.timeline.clips import VMFile, AMFile, Callout, IMFile
from camtasia.timing import EDIT_RATE, seconds_to_ticks


def _track(
    index: int = 0,
    name: str = "Test",
    medias: list[dict] | None = None,
) -> Track:
    attrs: dict[str, Any] = {
        "ident": name,
        "audioMuted": False,
        "videoHidden": False,
        "magnetic": False,
        "solo": False,
        "metadata": {"IsLocked": "False"},
    }
    data: dict[str, Any] = {
        "trackIndex": index,
        "medias": medias or [],
        "transitions": [],
        "parameters": {},
    }
    return Track(attrs, data)


class TestTrackAttributeFlags:
    def test_audio_muted_getter_and_setter(self):
        track = _track()
        assert track.audio_muted is False
        track.audio_muted = True
        assert track.audio_muted is True

    def test_video_hidden_getter_and_setter(self):
        track = _track()
        assert track.video_hidden is False
        track.video_hidden = True
        assert track.video_hidden is True

    def test_magnetic_getter_and_setter(self):
        track = _track()
        assert track.magnetic is False
        track.magnetic = True
        assert track.magnetic is True

    def test_solo_getter_and_setter(self):
        track = _track()
        assert track.solo is False
        track.solo = True
        assert track.solo is True

    def test_is_locked_getter_and_setter(self):
        track = _track()
        assert track.is_locked is False
        track.is_locked = True
        assert track.is_locked is True


class TestTrackClipIteration:
    def test_medias_alias_returns_same_as_clips(self):
        track = _track()
        track.add_clip("IMFile", 1, 0, EDIT_RATE)
        actual_via_clips = [c.id for c in track.clips]
        actual_via_medias = [c.id for c in track.medias]
        assert actual_via_clips == actual_via_medias


class TestTrackAddVideo:
    def test_add_video_returns_vmfile(self):
        track = _track()
        actual_clip = track.add_video(source_id=10, start_seconds=1.0, duration_seconds=5.0)
        assert isinstance(actual_clip, VMFile)
        assert actual_clip.start == seconds_to_ticks(1.0)
        assert actual_clip.duration == seconds_to_ticks(5.0)


class TestTrackAddAudio:
    def test_add_audio_returns_amfile(self):
        track = _track()
        actual_clip = track.add_audio(source_id=20, start_seconds=0.0, duration_seconds=3.0)
        assert isinstance(actual_clip, AMFile)
        assert actual_clip.start == 0
        assert actual_clip.duration == seconds_to_ticks(3.0)


class TestTrackAddCallout:
    def test_add_callout_returns_callout(self):
        track = _track()
        actual_clip = track.add_callout(
            text="Hello World",
            start_seconds=2.0,
            duration_seconds=4.0,
        )
        assert isinstance(actual_clip, Callout)
        assert actual_clip.start == seconds_to_ticks(2.0)
        assert actual_clip.duration == seconds_to_ticks(4.0)


class TestTrackTransitions:
    def test_add_transition(self):
        track = _track()
        clip_a = track.add_image(1, 0.0, 5.0)
        clip_b = track.add_image(2, 5.0, 5.0)
        actual_transition = track.add_transition("FadeThroughBlack", clip_a, clip_b, 0.5)
        assert actual_transition.name == "FadeThroughBlack"
        assert actual_transition.left_media_id == clip_a.id
        assert actual_transition.right_media_id == clip_b.id

    def test_add_fade_through_black(self):
        track = _track()
        clip_a = track.add_image(1, 0.0, 5.0)
        clip_b = track.add_image(2, 5.0, 5.0)
        actual_transition = track.add_fade_through_black(clip_a, clip_b, 1.0)
        assert actual_transition.name == "FadeThroughBlack"
        assert actual_transition.duration == seconds_to_ticks(1.0)


class TestTrackImageSequence:
    def test_creates_clips_without_transitions(self):
        track = _track()
        actual_clips = track.add_image_sequence([1, 2, 3], start_seconds=0.0, duration_per_image_seconds=2.0)
        assert all(isinstance(c, IMFile) for c in actual_clips)
        actual_starts = [c.start for c in actual_clips]
        assert actual_starts == [seconds_to_ticks(0.0), seconds_to_ticks(2.0), seconds_to_ticks(4.0)]

    def test_creates_clips_with_transitions(self):
        track = _track()
        actual_clips = track.add_image_sequence(
            [1, 2, 3], start_seconds=0.0,
            duration_per_image_seconds=2.0, transition_seconds=0.5,
        )
        assert [type(c).__name__ for c in actual_clips] == ['IMFile', 'IMFile', 'IMFile']
        actual_transitions = list(track.transitions)
        assert [t.name for t in actual_transitions] == ["FadeThroughBlack", "FadeThroughBlack"]


class TestTrackEndTime:
    def test_empty_track_returns_zero(self):
        track = _track()
        assert track.end_time_seconds() == 0.0

    def test_returns_max_clip_end(self):
        track = _track()
        track.add_image(1, 0.0, 5.0)
        track.add_image(2, 5.0, 3.0)
        assert track.end_time_seconds() == pytest.approx(8.0)


class TestTrackRemoveClip:
    def test_remove_clip_by_id(self):
        track = _track()
        clip = track.add_image(1, 0.0, 5.0)
        track.remove_clip(clip.id)
        assert list(track.clips) == []

    def test_remove_nonexistent_clip_raises(self):
        track = _track()
        with pytest.raises(KeyError, match="No clip with id=999"):
            track.remove_clip(999)


class TestTrackMarkers:
    def test_track_markers_property(self):
        track = _track()
        assert list(track.markers) == []


class TestTrackRepr:
    def test_repr(self):
        track = _track(index=2, name="My Track")
        assert repr(track) == "Track(name='My Track', index=2)"


class TestPerMediaMarkers:
    def test_iterates_markers_with_adjusted_times(self):
        media_data = {
            "start": 1000,
            "mediaStart": 500,
            "parameters": {
                "toc": {
                    "keyframes": [
                        {"time": 600, "value": "Marker A"},
                        {"time": 800, "value": "Marker B"},
                    ]
                }
            },
        }
        from camtasia.timeline.track import _PerMediaMarkers
        markers = _PerMediaMarkers(media_data)
        actual_markers = list(markers)
        assert [(m.name, m.time) for m in actual_markers] == [
            ("Marker A", 1000 + (600 - 500)),
            ("Marker B", 1000 + (800 - 500)),
        ]

    def test_len(self):
        media_data = {
            "parameters": {
                "toc": {
                    "keyframes": [{"time": 0, "value": "M1"}]
                }
            }
        }
        from camtasia.timeline.track import _PerMediaMarkers
        markers = list(_PerMediaMarkers(media_data))
        assert [m.name for m in markers] == ["M1"]

    def test_empty_markers(self):
        from camtasia.timeline.track import _PerMediaMarkers
        assert list(_PerMediaMarkers({})) == []


class TestClipAccessorMarkers:
    def test_clip_has_per_media_markers(self):
        """Clips yielded by track.clips should have markers attached."""
        from camtasia.timeline.track import _PerMediaMarkers
        attrs = {"ident": "T", "audioMuted": False, "videoHidden": False,
                 "magnetic": False, "metadata": {"IsLocked": "False"}}
        data = {
            "trackIndex": 0,
            "medias": [{
                "_type": "IMFile", "id": 1, "start": 0, "duration": EDIT_RATE,
                "mediaStart": 0, "mediaDuration": EDIT_RATE, "scalar": 1,
                "src": 1, "metadata": {}, "animationTracks": {}, "effects": [],
                "parameters": {
                    "toc": {"keyframes": [{"time": 100, "value": "Mark"}]}
                },
            }],
            "transitions": [],
        }
        track = Track(attrs, data)
        actual_clip = list(track.clips)[0]
        actual_markers = list(actual_clip.markers)
        assert actual_markers[0].name == "Mark"
