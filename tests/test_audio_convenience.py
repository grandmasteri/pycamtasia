"""Tests for audio convenience methods on AMFile and Track."""
import pytest

from camtasia.timeline.clips.audio import AMFile
from camtasia.timeline.track import Track


def _make_amfile(**overrides):
    data = {
        'id': 1,
        '_type': 'AMFile',
        'start': 0,
        'duration': 705600000,
        'mediaStart': 0,
        'mediaDuration': 705600000,
        'scalar': 1,
        'attributes': {'gain': 1.0},
        'parameters': {},
        'metadata': {},
        **overrides,
    }
    return AMFile(data)


def _make_track(**attr_overrides):
    attrs = {'ident': 'Track 1', **attr_overrides}
    data = {'trackIndex': 0, 'medias': []}
    return Track(attrs, data)


class TestIsMuted:
    def test_is_muted_true(self):
        clip = _make_amfile(attributes={'gain': 0.0})
        assert clip.is_muted is True

    def test_is_muted_false(self):
        clip = _make_amfile(attributes={'gain': 1.0})
        assert clip.is_muted is False


class TestSetGain:
    def test_set_gain_valid(self):
        clip = _make_amfile()
        clip.set_gain(0.5)
        assert clip.gain == 0.5

    def test_set_gain_negative_raises(self):
        clip = _make_amfile()
        with pytest.raises(ValueError, match='non-negative'):
            clip.set_gain(-0.1)

    def test_set_gain_chaining(self):
        clip = _make_amfile()
        result = clip.set_gain(2.0)
        assert result is clip


class TestNormalizeGain:
    def test_normalize_gain_default(self):
        clip = _make_amfile()
        clip.normalize_gain()
        assert clip._data['attributes']['loudnessNormalization'] is True
        assert clip._data.get('attributes', {}).get('loudnessNormalization', False) is True

    def test_normalize_gain_custom(self):
        clip = _make_amfile()
        result = clip.normalize_gain()
        assert clip._data.get('attributes', {}).get('loudnessNormalization', False) is True
        assert result is clip


class TestTrackMuteUnmute:
    def test_track_mute_unmute(self):
        track = _make_track()
        assert track.audio_muted is False
        track.mute()
        assert track.audio_muted is True
        track.unmute()
        assert track.audio_muted is False


class TestTrackHideShow:
    def test_track_hide_show(self):
        track = _make_track()
        assert track.video_hidden is False
        track.hide()
        assert track.video_hidden is True
        track.show()
        assert track.video_hidden is False
