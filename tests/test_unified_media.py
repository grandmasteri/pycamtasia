from __future__ import annotations

from fractions import Fraction
import json
from pathlib import Path

import pytest

from camtasia.timeline.clips import UnifiedMedia, clip_from_dict
from camtasia.timeline.clips.audio import AMFile
from camtasia.timeline.clips.base import BaseClip
from camtasia.timeline.clips.screen_recording import ScreenVMFile
from camtasia.timing import seconds_to_ticks

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def unified_data():
    return {
        "_type": "UnifiedMedia",
        "id": 6,
        "video": {
            "_type": "ScreenVMFile",
            "id": 7,
            "src": 2,
            "trackNumber": 0,
            "attributes": {"ident": "Recording"},
            "parameters": {"scale0": 0.75, "scale1": 0.75},
            "effects": [],
        },
        "audio": {
            "_type": "AMFile",
            "id": 8,
            "src": 2,
            "trackNumber": 1,
            "attributes": {"ident": "", "gain": 1.0},
            "parameters": {},
            "effects": [
                {
                    "effectName": "VSTEffect-DFN3NoiseRemoval",
                    "bypassed": False,
                    "category": "categoryAudioEffects",
                    "parameters": {"Amount": 0.8, "Bypass": 0.0},
                }
            ],
        },
    }


class TestUnifiedMedia:
    def test_clip_from_dict_dispatches(self, unified_data):
        actual_clip = clip_from_dict(unified_data)
        assert isinstance(actual_clip, UnifiedMedia)

    def test_video_child(self, unified_data):
        clip = UnifiedMedia(unified_data)
        actual_video = clip.video
        assert isinstance(actual_video, ScreenVMFile)
        assert actual_video.id == 7

    def test_audio_child(self, unified_data):
        clip = UnifiedMedia(unified_data)
        actual_audio = clip.audio
        assert isinstance(actual_audio, AMFile)
        assert actual_audio.id == 8

    def test_has_audio_true(self, unified_data):
        clip = UnifiedMedia(unified_data)
        assert clip.has_audio is True

    def test_has_audio_false(self, unified_data):
        del unified_data["audio"]
        clip = UnifiedMedia(unified_data)
        assert clip.has_audio is False

    def test_audio_has_noise_removal_effect(self, unified_data):
        clip = UnifiedMedia(unified_data)
        actual_effects = clip.audio._data["effects"]
        assert actual_effects[0]["effectName"] == "VSTEffect-DFN3NoiseRemoval"

    def test_video_source_matches_audio_source(self, unified_data):
        clip = UnifiedMedia(unified_data)
        assert clip.video._data["src"] == clip.audio._data["src"] == 2


class TestUnifiedMediaIntegration:
    @pytest.fixture
    def project_data(self):
        fixture = FIXTURES / "test_project_d.tscproj"
        if not fixture.exists():
            pytest.skip("test_project_d.tscproj fixture not available")
        with open(fixture) as f:
            return json.load(f)

    def test_find_unified_media_in_real_project(self, project_data):
        tracks = project_data["timeline"]["sceneTrack"]["scenes"][0]["csml"]["tracks"]
        found = []
        for track in tracks:
            for media in track.get("medias", []):
                if media.get("_type") == "Group":
                    for inner_track in media.get("tracks", []):
                        for inner_media in inner_track.get("medias", []):
                            if inner_media.get("_type") == "UnifiedMedia":
                                found.append(clip_from_dict(inner_media))

        assert found != []
        actual_clip = found[0]
        assert isinstance(actual_clip, UnifiedMedia)
        assert actual_clip.has_audio is True
        assert isinstance(actual_clip.video, ScreenVMFile)
        assert isinstance(actual_clip.audio, AMFile)


class TestUnifiedMediaStreamTypes:
    def test_is_screen_recording(self):
        data = {
            "_type": "UnifiedMedia", "id": 6,
            "video": {"_type": "ScreenVMFile", "id": 7, "src": 2, "attributes": {}, "parameters": {}, "effects": []},
            "audio": {"_type": "AMFile", "id": 8, "src": 2, "attributes": {}, "parameters": {}, "effects": []},
        }
        clip = UnifiedMedia(data)
        assert clip.is_screen_recording is True
        assert clip.is_camera is False

    def test_is_camera(self):
        data = {
            "_type": "UnifiedMedia", "id": 9,
            "video": {"_type": "VMFile", "id": 10, "src": 2, "attributes": {}, "parameters": {}, "effects": []},
            "audio": {"_type": "AMFile", "id": 11, "src": 2, "attributes": {}, "parameters": {}, "effects": []},
        }
        clip = UnifiedMedia(data)
        assert clip.is_camera is True
        assert clip.is_screen_recording is False


# ── Merged from test_completeness.py ─────────────────────────────────


class TestUnifiedMediaImprovements:
    def _make_unified(self) -> UnifiedMedia:
        return UnifiedMedia({
            'id': 1, '_type': 'UnifiedMedia', 'start': 0, 'duration': 100,
            'mediaStart': 0, 'mediaDuration': 100, 'scalar': 1,
            'video': {'id': 2, '_type': 'ScreenVMFile', 'src': 42,
                      'start': 0, 'duration': 100, 'mediaStart': 0,
                      'mediaDuration': 100, 'scalar': 1},
            'audio': {'id': 3, '_type': 'AMFile',
                      'attributes': {'gain': 1.0},
                      'start': 0, 'duration': 100, 'mediaStart': 0,
                      'mediaDuration': 100, 'scalar': 1},
        })

    def test_source_id(self):
        assert self._make_unified().source_id == 42

    def test_source_id_none_when_no_video(self):
        assert UnifiedMedia({
            'id': 1, '_type': 'UnifiedMedia', 'start': 0, 'duration': 100,
            'mediaStart': 0, 'mediaDuration': 100, 'scalar': 1,
        }).source_id is None

    def test_mute_audio(self):
        actual_clip = self._make_unified()
        actual_result = actual_clip.mute_audio()
        assert actual_clip._data['audio']['attributes']['gain'] == 0.0
        assert actual_result is actual_clip

    def test_mute_audio_no_audio(self):
        actual_clip = UnifiedMedia({
            'id': 1, '_type': 'UnifiedMedia', 'start': 0, 'duration': 100,
            'mediaStart': 0, 'mediaDuration': 100, 'scalar': 1,
            'video': {'id': 2, '_type': 'ScreenVMFile', 'src': 42,
                      'start': 0, 'duration': 100, 'mediaStart': 0,
                      'mediaDuration': 100, 'scalar': 1},
        })
        actual_result = actual_clip.mute_audio()
        assert actual_result is actual_clip


# ==================================================================
# UnifiedMedia base clip behavior (from test_clip_coverage.py)
# ==================================================================

def test_base_clip_is_muted_unified_media():
    clip = BaseClip({
        '_type': 'UnifiedMedia',
        'id': 1, 'start': 0, 'duration': 100,
        'audio': {'attributes': {'gain': 0.0}},
    })
    assert clip.is_muted is True


def test_base_clip_mute_unified_media():
    clip = BaseClip({
        '_type': 'UnifiedMedia',
        'id': 1, 'start': 0, 'duration': 100,
        'audio': {'attributes': {'gain': 1.0}},
    })
    clip.mute()
    assert clip._data['audio']['attributes']['gain'] == 0.0


def test_base_clip_mute_unified_media_no_audio():
    clip = BaseClip({
        '_type': 'UnifiedMedia',
        'id': 1, 'start': 0, 'duration': 100,
    })
    with pytest.raises(ValueError, match='no audio'):
        clip.mute()


def test_base_clip_media_start_fraction():
    clip = BaseClip({
        '_type': 'UnifiedMedia',
        'id': 1, 'start': 0, 'duration': 100,
        'video': {'start': 0, 'mediaStart': 0},
        'audio': {'start': 0, 'mediaStart': 0},
    })
    clip.media_start = Fraction(1, 3)
    assert clip._data['mediaStart'] == '1/3'
    assert clip._data['video']['mediaStart'] == '1/3'
    clip.media_start = Fraction(10, 1)
    assert clip._data['mediaStart'] == 10


def test_base_clip_is_silent_unified_media():
    clip = BaseClip({
        '_type': 'UnifiedMedia',
        'id': 1, 'start': 0, 'duration': 100,
        'audio': {'attributes': {'gain': 0.0}},
    })
    assert clip.is_silent is True


def test_base_clip_set_start_seconds_unified():
    clip = BaseClip({
        '_type': 'UnifiedMedia',
        'id': 1, 'start': 0, 'duration': 100,
        'video': {'start': 0},
        'audio': {'start': 0},
    })
    clip.set_start_seconds(2.0)
    expected = seconds_to_ticks(2.0)
    assert clip._data['start'] == expected
    assert clip._data['video']['start'] == expected
    assert clip._data['audio']['start'] == expected


# ==================================================================
# UnifiedMedia: effect blocking (from test_clips.py)
# ==================================================================

def _um_data():
    _S10 = seconds_to_ticks(10.0)
    return {
        '_type': 'UnifiedMedia', 'id': 1, 'start': 0, 'duration': _S10,
        'mediaDuration': _S10, 'mediaStart': 0, 'scalar': 1,
        'parameters': {}, 'effects': [],
        'video': {
            '_type': 'ScreenVMFile', 'id': 2, 'src': 5, 'start': 0,
            'duration': _S10, 'mediaDuration': _S10, 'mediaStart': 0, 'scalar': 1,
            'parameters': {}, 'effects': [], 'attributes': {'ident': 'rec'},
            'trackNumber': 0,
        },
        'audio': {
            '_type': 'AMFile', 'id': 3, 'src': 5, 'start': 0,
            'duration': _S10, 'mediaDuration': _S10, 'mediaStart': 0, 'scalar': 1,
            'attributes': {'gain': 1.0},
        },
    }



class TestUnifiedMediaEffectBlocking:
    def test_add_effect(self):
        um = UnifiedMedia(_um_data())
        with pytest.raises(TypeError):
            um.add_effect({})

    def test_add_drop_shadow(self):
        um = UnifiedMedia(_um_data())
        with pytest.raises(TypeError):
            um.add_drop_shadow()

    def test_add_round_corners(self):
        um = UnifiedMedia(_um_data())
        with pytest.raises(TypeError):
            um.add_round_corners()

    def test_add_glow(self):
        um = UnifiedMedia(_um_data())
        with pytest.raises(TypeError):
            um.add_glow()

    def test_add_glow_timed(self):
        um = UnifiedMedia(_um_data())
        with pytest.raises(TypeError):
            um.add_glow_timed()

    def test_copy_effects_from(self):
        um = UnifiedMedia(_um_data())
        with pytest.raises(TypeError):
            um.copy_effects_from(um)

    def test_set_source(self):
        um = UnifiedMedia(_um_data())
        with pytest.raises(TypeError):
            um.set_source(1)


class TestUnifiedMediaDuplicateEffectsTo:
    def test_duplicate_effects_to_raises(self):
        um = UnifiedMedia(_um_data())
        with pytest.raises(TypeError, match='Cannot duplicate effects from UnifiedMedia'):
            um.duplicate_effects_to(um)


class TestUnifiedMediaEffectReadProperties:
    """UnifiedMedia effect read properties aggregate video + audio sub-clip effects."""

    def test_has_effects_false_when_subclips_empty(self):
        um = UnifiedMedia(_um_data())
        assert um.has_effects is False

    def test_has_effects_true_from_video(self):
        data = _um_data()
        data['video']['effects'] = [{'effectName': 'DropShadow'}]
        um = UnifiedMedia(data)
        assert um.has_effects is True

    def test_has_effects_true_from_audio(self):
        data = _um_data()
        data['audio']['effects'] = [{'effectName': 'AudioCompressor'}]
        um = UnifiedMedia(data)
        assert um.has_effects is True

    def test_effect_count_sums_video_and_audio(self):
        data = _um_data()
        data['video']['effects'] = [{'effectName': 'DropShadow'}, {'effectName': 'Glow'}]
        data['audio']['effects'] = [{'effectName': 'AudioCompressor'}]
        um = UnifiedMedia(data)
        assert um.effect_count == 3

    def test_effect_names_lists_video_then_audio(self):
        data = _um_data()
        data['video']['effects'] = [{'effectName': 'DropShadow'}]
        data['audio']['effects'] = [{'effectName': 'AudioCompressor'}]
        um = UnifiedMedia(data)
        assert um.effect_names == ['DropShadow', 'AudioCompressor']

    def test_remove_all_effects_clears_both_subclips(self):
        data = _um_data()
        data['video']['effects'] = [{'effectName': 'DropShadow'}]
        data['audio']['effects'] = [{'effectName': 'AudioCompressor'}]
        um = UnifiedMedia(data)
        result = um.remove_all_effects()
        assert result is um
        assert data['video']['effects'] == []
        assert data['audio']['effects'] == []


def test_unified_media_not_silent_when_gain_nonzero():
    clip = BaseClip({
        '_type': 'UnifiedMedia', 'id': 1, 'start': 0, 'duration': 100,
        'audio': {'attributes': {'gain': 0.8}},
    })
    assert clip.is_silent is False


# ------------------------------------------------------------------
# Bug fix: UnifiedMedia.audio raises AttributeError instead of KeyError
# ------------------------------------------------------------------

class TestUnifiedMediaAudioMissing:
    def test_audio_raises_attribute_error_when_missing(self):
        data = {
            '_type': 'UnifiedMedia', 'id': 1,
            'start': 0, 'duration': 100,
            'video': {'_type': 'VMFile', 'id': 2, 'src': 1, 'start': 0, 'duration': 100},
        }
        um = UnifiedMedia(data)
        with pytest.raises(AttributeError, match='has no audio child'):
            _ = um.audio

    def test_audio_works_when_present(self, unified_data):
        um = UnifiedMedia(unified_data)
        audio = um.audio
        assert audio.id == 8


# ------------------------------------------------------------------
# Bug 2: media_duration setter must not overwrite sub-clip mediaStart
# ------------------------------------------------------------------

class TestMediaDurationSetterNoMediaStartOverwrite:
    def test_media_duration_preserves_sub_clip_media_start(self):
        data = {
            '_type': 'UnifiedMedia', 'id': 1,
            'start': 0, 'duration': 1000, 'mediaStart': 0,
            'mediaDuration': 500,
            'video': {
                '_type': 'VMFile', 'id': 2, 'src': 1,
                'start': 0, 'duration': 1000,
                'mediaStart': 200, 'mediaDuration': 500,
            },
            'audio': {
                '_type': 'AMFile', 'id': 3, 'src': 1,
                'start': 0, 'duration': 1000,
                'mediaStart': 200, 'mediaDuration': 500,
            },
        }
        clip = BaseClip(data)
        clip.media_duration = 600

        assert data['video']['mediaDuration'] == 600
        assert data['audio']['mediaDuration'] == 600
        # mediaStart must NOT be overwritten
        assert data['video']['mediaStart'] == 200
        assert data['audio']['mediaStart'] == 200
