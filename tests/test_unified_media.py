from __future__ import annotations

import json
from pathlib import Path

import pytest

from camtasia.timeline.clips import clip_from_dict, UnifiedMedia
from camtasia.timeline.clips.audio import AMFile
from camtasia.timeline.clips.screen_recording import ScreenVMFile


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
