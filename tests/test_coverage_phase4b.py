"""Targeted tests for uncovered lines in phase 4b."""
from __future__ import annotations

import copy
from fractions import Fraction
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


# ── 1. effects/cursor.py — property setters ──────────────────────────

class TestCursorMotionBlurSetter:
    def test_set_intensity(self):
        from camtasia.effects.cursor import CursorMotionBlur
        data = {"effectName": "CursorMotionBlur", "parameters": {"intensity": {"type": "double", "defaultValue": 0.5}}}
        e = CursorMotionBlur(data)
        e.intensity = 0.8
        assert e.intensity == 0.8


class TestCursorShadowSetters:
    def _make(self):
        from camtasia.effects.cursor import CursorShadow
        data = {
            "effectName": "CursorShadow",
            "parameters": {
                "enabled": {"type": "int", "defaultValue": 1},
                "angle": {"type": "double", "defaultValue": 0.5},
                "offset": {"type": "double", "defaultValue": 3.0},
                "blur": {"type": "double", "defaultValue": 2.0},
                "opacity": {"type": "double", "defaultValue": 0.7},
                "color-red": {"type": "double", "defaultValue": 0.0},
                "color-green": {"type": "double", "defaultValue": 0.0},
                "color-blue": {"type": "double", "defaultValue": 0.0},
                "color-alpha": {"type": "double", "defaultValue": 1.0},
            },
        }
        return CursorShadow(data)

    def test_set_enabled(self):
        e = self._make()
        e.enabled = 0
        assert e.enabled == 0

    def test_set_angle(self):
        e = self._make()
        e.angle = 1.5
        assert e.angle == 1.5

    def test_set_offset(self):
        e = self._make()
        e.offset = 5.0
        assert e.offset == 5.0

    def test_set_blur(self):
        e = self._make()
        e.blur = 4.0
        assert e.blur == 4.0

    def test_set_opacity(self):
        e = self._make()
        e.opacity = 0.3
        assert e.opacity == 0.3

    def test_set_color(self):
        e = self._make()
        e.color = (1.0, 0.5, 0.25, 0.8)
        assert e.color == (1.0, 0.5, 0.25, 0.8)


class TestCursorPhysicsSetters:
    def _make(self):
        from camtasia.effects.cursor import CursorPhysics
        return CursorPhysics({
            "effectName": "CursorPhysics",
            "parameters": {
                "intensity": {"type": "double", "defaultValue": 0.5},
                "tilt": {"type": "double", "defaultValue": 0.3},
            },
        })

    def test_set_intensity(self):
        e = self._make()
        e.intensity = 0.9
        assert e.intensity == 0.9

    def test_set_tilt(self):
        e = self._make()
        e.tilt = 0.7
        assert e.tilt == 0.7


class TestLeftClickScalingSetters:
    def _make(self):
        from camtasia.effects.cursor import LeftClickScaling
        return LeftClickScaling({
            "effectName": "LeftClickScaling",
            "parameters": {
                "scale": {"type": "double", "defaultValue": 1.5},
                "speed": {"type": "double", "defaultValue": 1.0},
            },
        })

    def test_set_scale(self):
        e = self._make()
        e.scale = 2.0
        assert e.scale == 2.0

    def test_set_speed(self):
        e = self._make()
        e.speed = 0.5
        assert e.speed == 0.5


# ── 2. effects/behaviors.py — edge cases ─────────────────────────────

class TestBehaviorEdgeCases:
    def test_behavior_phase_data_property(self):
        """Line 26: BehaviorPhase.data property."""
        from camtasia.effects.behaviors import BehaviorPhase
        raw = {"attributes": {"name": "reveal"}, "parameters": {}}
        phase = BehaviorPhase(raw)
        assert phase.data is raw

    def test_set_start(self):
        """Line 187: GenericBehaviorEffect.start setter."""
        from camtasia.effects.behaviors import GenericBehaviorEffect
        data = {
            "_type": "GenericBehaviorEffect",
            "effectName": "reveal",
            "start": 0,
            "duration": 100,
            "in": {"attributes": {"name": "reveal"}, "parameters": {}},
            "center": {"attributes": {"name": "none"}, "parameters": {}},
            "out": {"attributes": {"name": "reveal"}, "parameters": {}},
        }
        e = GenericBehaviorEffect(data)
        e.start = 50
        assert e.start == 50

    def test_set_duration(self):
        """Line 197: GenericBehaviorEffect.duration setter."""
        from camtasia.effects.behaviors import GenericBehaviorEffect
        data = {
            "_type": "GenericBehaviorEffect",
            "effectName": "reveal",
            "start": 0,
            "duration": 100,
            "in": {"attributes": {"name": "reveal"}, "parameters": {}},
            "center": {"attributes": {"name": "none"}, "parameters": {}},
            "out": {"attributes": {"name": "reveal"}, "parameters": {}},
        }
        e = GenericBehaviorEffect(data)
        e.duration = 200
        assert e.duration == 200


# ── 3. operations/merge.py — _remap_clip_ids dict assetProperties ────

class TestRemapClipIdsAssetProperties:
    def test_dict_format_objects_in_asset_properties(self):
        """Lines 31-40: dict-format objects in assetProperties."""
        from camtasia.operations.merge import _remap_clip_ids

        clip = {
            "id": 10,
            "attributes": {
                "assetProperties": [
                    {
                        "objects": [
                            {"media": 10, "other": "data"},
                            5,
                        ]
                    }
                ]
            },
        }
        id_counter = [100]
        id_map: dict[int, int] = {}
        src_map: dict[int, int] = {}

        _remap_clip_ids(clip, id_counter, id_map, src_map)

        # id 10 -> 100 in id_map
        assert id_map[10] == 100
        ap = clip["attributes"]["assetProperties"][0]["objects"]
        # dict object: media field remapped 10 -> 100
        assert ap[0]["media"] == 100
        # int object: remapped 5 -> id_map.get(5, 5) = 5 (no mapping)
        assert ap[1] == 5

    def test_int_objects_remapped(self):
        """Int objects in assetProperties are remapped via id_map."""
        from camtasia.operations.merge import _remap_clip_ids

        clip = {
            "id": 20,
            "attributes": {
                "assetProperties": [
                    {"objects": [7]}
                ]
            },
        }
        id_counter = [200]
        id_map: dict[int, int] = {7: 77}
        src_map: dict[int, int] = {}

        _remap_clip_ids(clip, id_counter, id_map, src_map)
        assert clip["attributes"]["assetProperties"][0]["objects"][0] == 77


# ── 4. operations/speed.py — UnifiedMedia audio path + overlap fix ───

def _make_project_data_with_unified_audio(scalar="1/2"):
    """Build minimal project data with a UnifiedMedia clip containing a speed-changed AMFile audio child."""
    return {
        "timeline": {
            "sceneTrack": {
                "scenes": [{
                    "csml": {
                        "tracks": [{
                            "medias": [{
                                "_type": "UnifiedMedia",
                                "start": 0,
                                "duration": 1000,
                                "mediaDuration": 1000,
                                "video": {
                                    "_type": "VMFile",
                                    "start": 0,
                                    "duration": 1000,
                                    "mediaDuration": 1000,
                                    "scalar": 1,
                                },
                                "audio": {
                                    "_type": "AMFile",
                                    "start": 0,
                                    "duration": 1000,
                                    "mediaDuration": 2000,
                                    "scalar": scalar,
                                    "metadata": {
                                        "clipSpeedAttribute": {"type": "bool", "value": True}
                                    },
                                },
                            }],
                        }],
                    }
                }]
            },
            "parameters": {"toc": {"keyframes": []}},
        }
    }


class TestSetAudioSpeedUnifiedMedia:
    def test_unified_media_audio_path(self):
        """Lines 213-215: set_audio_speed finds AMFile inside UnifiedMedia."""
        from camtasia.operations.speed import set_audio_speed
        data = _make_project_data_with_unified_audio("1/2")
        factor = set_audio_speed(data, target_speed=1.0)
        assert factor == Fraction(2)
        audio = data["timeline"]["sceneTrack"]["scenes"][0]["csml"]["tracks"][0]["medias"][0]["audio"]
        assert audio["scalar"] == 1
        assert audio["metadata"]["clipSpeedAttribute"]["value"] is False

    def test_set_audio_speed_negative_raises(self):
        """Line 203: negative target_speed raises ValueError."""
        from camtasia.operations.speed import set_audio_speed
        data = _make_project_data_with_unified_audio("1/2")
        with pytest.raises(ValueError, match="positive"):
            set_audio_speed(data, target_speed=-1.0)

    def test_set_audio_speed_non_unity_target(self):
        """Lines 233-234: non-unity target_speed sets scalar and speed attr True."""
        from camtasia.operations.speed import set_audio_speed
        data = _make_project_data_with_unified_audio("1/2")
        factor = set_audio_speed(data, target_speed=0.5)
        audio = data["timeline"]["sceneTrack"]["scenes"][0]["csml"]["tracks"][0]["medias"][0]["audio"]
        assert audio["metadata"]["clipSpeedAttribute"]["value"] is True
        assert audio["scalar"] != 1


class TestProcessClipStitchedUnified:
    def test_stitched_media_with_unified_child(self):
        """Lines 93-96: UnifiedMedia inside StitchedMedia gets recursively processed."""
        from camtasia.operations.speed import rescale_project
        data = {
            "timeline": {
                "sceneTrack": {
                    "scenes": [{
                        "csml": {
                            "tracks": [{
                                "medias": [{
                                    "_type": "StitchedMedia",
                                    "start": 0,
                                    "duration": 1000,
                                    "mediaStart": 0,
                                    "mediaDuration": 1000,
                                    "medias": [{
                                        "_type": "UnifiedMedia",
                                        "start": 0,
                                        "duration": 500,
                                        "mediaStart": 0,
                                        "mediaDuration": 500,
                                        "video": {
                                            "_type": "VMFile",
                                            "start": 0,
                                            "duration": 500,
                                            "mediaDuration": 500,
                                            "scalar": 1,
                                        },
                                        "audio": {
                                            "_type": "AMFile",
                                            "start": 0,
                                            "duration": 500,
                                            "mediaDuration": 500,
                                            "scalar": 1,
                                        },
                                    }],
                                }],
                            }],
                        }
                    }]
                },
                "parameters": {"toc": {"keyframes": []}},
            }
        }
        rescale_project(data, Fraction(2))
        inner = data["timeline"]["sceneTrack"]["scenes"][0]["csml"]["tracks"][0]["medias"][0]["medias"][0]
        # UnifiedMedia child's video/audio should be scaled
        assert inner["video"]["duration"] == 1000
        assert inner["audio"]["duration"] == 1000


class TestOverlapFix:
    def test_overlap_fix_shrinks_duration(self):
        """Lines 150-158: overlap fix shrinks clip A duration and recalculates mediaDuration."""
        from camtasia.operations.speed import rescale_project
        data = {
            "timeline": {
                "sceneTrack": {
                    "scenes": [{
                        "csml": {
                            "tracks": [{
                                "medias": [
                                    {"_type": "AMFile", "start": 0, "duration": 100, "mediaDuration": 100, "scalar": 1},
                                    {"_type": "AMFile", "start": 99, "duration": 100, "mediaDuration": 100, "scalar": 1},
                                ],
                            }],
                        }
                    }]
                },
                "parameters": {"toc": {"keyframes": []}},
            }
        }
        # Factor of 1 won't change timing but will trigger overlap check
        # Use a factor that creates overlap via rounding
        rescale_project(data, Fraction(3, 2))
        medias = data["timeline"]["sceneTrack"]["scenes"][0]["csml"]["tracks"][0]["medias"]
        # After rescale by 3/2: clip A start=0, dur=150; clip B start=148 (99*3/2=148.5 rounds to 148)
        # overlap = 150 - 148 = 2, so clip A duration shrinks by 2
        a_end = medias[0]["start"] + medias[0]["duration"]
        b_start = medias[1]["start"]
        assert a_end <= b_start

    def test_overlap_fix_with_non_unity_scalar(self):
        """Overlap fix recalculates mediaDuration with non-unity scalar."""
        from camtasia.operations.speed import rescale_project
        data = {
            "timeline": {
                "sceneTrack": {
                    "scenes": [{
                        "csml": {
                            "tracks": [{
                                "medias": [
                                    {
                                        "_type": "AMFile",
                                        "start": 0,
                                        "duration": 100,
                                        "mediaDuration": 200,
                                        "scalar": "1/2",
                                        "metadata": {"clipSpeedAttribute": {"type": "bool", "value": True}},
                                    },
                                    {
                                        "_type": "AMFile",
                                        "start": 99,
                                        "duration": 100,
                                        "mediaDuration": 100,
                                        "scalar": 1,
                                    },
                                ],
                            }],
                        }
                    }]
                },
                "parameters": {"toc": {"keyframes": []}},
            }
        }
        rescale_project(data, Fraction(3, 2))
        medias = data["timeline"]["sceneTrack"]["scenes"][0]["csml"]["tracks"][0]["medias"]
        a_end = medias[0]["start"] + medias[0]["duration"]
        b_start = medias[1]["start"]
        assert a_end <= b_start


# ── 5. media_bin/media_bin.py — import_media edge cases ──────────────

class TestImportMediaSampleRateConversion:
    def test_non_int_sample_rate_converted(self, project, tmp_path):
        """Lines 309-312: sample_rate that is a string float gets converted to int."""
        wav = tmp_path / "test.wav"
        wav.write_bytes(b"\x00" * 100)

        mock_track = {
            "kind_of_stream": "Audio",
            "sampling_rate": "44100.0",  # string float, not int
            "duration": 1000,
            "bit_depth": 16,
            "channel_s": 2,
        }
        with patch("camtasia.media_bin.media_bin._parse_with_pymediainfo", return_value=mock_track):
            media = project.media_bin.import_media(wav)
            assert media is not None

    def test_non_int_sample_rate_invalid_becomes_none(self, project, tmp_path):
        """Lines 310-312: sample_rate that can't be converted becomes None."""
        wav = tmp_path / "test.wav"
        wav.write_bytes(b"\x00" * 100)

        mock_track = {
            "kind_of_stream": "Audio",
            "sampling_rate": "invalid",
            "duration": 1000,
            "bit_depth": 16,
            "channel_s": 2,
        }
        with patch("camtasia.media_bin.media_bin._parse_with_pymediainfo", return_value=mock_track):
            media = project.media_bin.import_media(wav)
            assert media is not None


class TestParseWithPymediainfo:
    def test_parse_returns_none_on_import_error(self):
        """Lines 488-489: pymediainfo not installed returns None."""
        from camtasia.media_bin.media_bin import _parse_with_pymediainfo
        from pathlib import Path
        with patch.dict("sys.modules", {"pymediainfo": None}):
            # Force ImportError by removing the module
            import importlib
            import camtasia.media_bin.media_bin as mod
            # Directly test: if pymediainfo raises ImportError
            with patch("builtins.__import__", side_effect=ImportError):
                result = _parse_with_pymediainfo(Path("/fake/file.mp4"))
                assert result is None

    def test_parse_returns_none_on_parse_exception(self):
        """Lines 492-493: pymediainfo parse failure returns None."""
        from camtasia.media_bin.media_bin import _parse_with_pymediainfo
        from pathlib import Path
        mock_mi = MagicMock()
        mock_mi.parse.side_effect = RuntimeError("parse failed")
        with patch.dict("sys.modules", {"pymediainfo": MagicMock(MediaInfo=mock_mi)}):
            result = _parse_with_pymediainfo(Path("/fake/file.mp4"))
            assert result is None

    def test_parse_returns_none_on_too_few_tracks(self):
        """Lines 494-495: fewer than 2 tracks returns None."""
        from camtasia.media_bin.media_bin import _parse_with_pymediainfo
        from pathlib import Path
        mock_mi = MagicMock()
        mock_result = MagicMock()
        mock_result.tracks = [MagicMock()]  # only 1 track
        mock_mi.parse.return_value = mock_result
        with patch.dict("sys.modules", {"pymediainfo": MagicMock(MediaInfo=mock_mi)}):
            result = _parse_with_pymediainfo(Path("/fake/file.mp4"))
            assert result is None

    def test_parse_success_returns_track_data(self):
        """Line 495: successful parse returns track[1].to_data()."""
        from camtasia.media_bin.media_bin import _parse_with_pymediainfo
        from pathlib import Path
        mock_mi = MagicMock()
        mock_result = MagicMock()
        track0 = MagicMock()
        track1 = MagicMock()
        track1.to_data.return_value = {"kind_of_stream": "Video", "width": 1920}
        mock_result.tracks = [track0, track1]
        mock_mi.parse.return_value = mock_result
        with patch.dict("sys.modules", {"pymediainfo": MagicMock(MediaInfo=mock_mi)}):
            result = _parse_with_pymediainfo(Path("/fake/file.mp4"))
            assert result == {"kind_of_stream": "Video", "width": 1920}


# ── 6. operations/template.py — _walk_clips edge cases ───────────────

class TestWalkClipsEdgeCases:
    def test_unified_media_inside_stitched_media(self):
        """Lines 51-54: UnifiedMedia children inside StitchedMedia are yielded."""
        from camtasia.operations.template import _walk_clips

        tracks = [{
            "medias": [{
                "_type": "StitchedMedia",
                "medias": [{
                    "_type": "UnifiedMedia",
                    "video": {"_type": "VMFile", "src": 1},
                    "audio": {"_type": "AMFile", "src": 2},
                }],
            }],
        }]
        clips = list(_walk_clips(tracks))
        types = [c.get("_type") for c in clips]
        assert "StitchedMedia" in types
        assert "UnifiedMedia" in types
        assert "VMFile" in types
        assert "AMFile" in types

    def test_top_level_unified_media(self):
        """Line 57-61: top-level UnifiedMedia children are yielded."""
        from camtasia.operations.template import _walk_clips

        tracks = [{
            "medias": [{
                "_type": "UnifiedMedia",
                "video": {"_type": "VMFile", "src": 1},
                "audio": {"_type": "AMFile", "src": 2},
            }],
        }]
        clips = list(_walk_clips(tracks))
        types = [c.get("_type") for c in clips]
        assert "UnifiedMedia" in types
        assert "VMFile" in types
        assert "AMFile" in types

    def test_duplicate_project_clear_media_with_keyframes(self, tmp_path):
        """Line 126: duplicate_project with clear_media clears toc keyframes."""
        import shutil
        from camtasia.operations.template import duplicate_project
        from camtasia.project import load_project

        src = Path(__file__).parent.parent / "src" / "camtasia" / "resources" / "new.cmproj"
        src_copy = tmp_path / "source.cmproj"
        shutil.copytree(src, src_copy)

        # Add keyframes to the source project's toc
        proj = load_project(src_copy)
        toc = proj._data.setdefault("timeline", {}).setdefault("parameters", {}).setdefault("toc", {})
        toc["keyframes"] = [{"time": 100, "value": "Chapter 1"}]
        proj.save()

        dest = tmp_path / "dest.cmproj"
        result = duplicate_project(src_copy, dest, clear_media=True)
        result_toc = result._data.get("timeline", {}).get("parameters", {}).get("toc", {})
        assert result_toc.get("keyframes") == []
