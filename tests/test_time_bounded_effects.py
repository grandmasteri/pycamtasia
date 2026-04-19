from __future__ import annotations

import json
from pathlib import Path

import pytest

from camtasia.effects.base import effect_from_dict
from camtasia.effects.visual import Glow
from camtasia.timeline.clips import Group, StitchedMedia

FIXTURES = Path(__file__).parent / "fixtures"


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _param(value, type_: str = "double", interp: str = "linr") -> dict:
    return {"type": type_, "defaultValue": value, "interp": interp}


def _glow_dict(**overrides) -> dict:
    d = {
        "effectName": "Glow",
        "bypassed": False,
        "category": "visual",
        "parameters": {
            "radius": _param(35.0),
            "intensity": _param(0.6),
        },
    }
    d.update(overrides)
    return d


def _time_bounded_effect_dict(
    *,
    left_edge_mods=None,
    right_edge_mods=None,
) -> dict:
    d = {
        "effectName": "Glow",
        "bypassed": False,
        "category": "visual",
        "parameters": {
            "radius": _param(35.0),
            "intensity": _param(0.5),
        },
        "start": 0,
        "duration": 705600000,
    }
    if left_edge_mods is not None:
        d["leftEdgeMods"] = left_edge_mods
    if right_edge_mods is not None:
        d["rightEdgeMods"] = right_edge_mods
    return d


def _edge_mod(
    group: str = "Video",
    duration: int = 282240000,
    parameters: list[dict] | None = None,
) -> dict:
    return {
        "group": group,
        "duration": duration,
        "parameters": parameters
        or [
            {"name": "intensity", "func": "FadeInFunc"},
            {"name": "radius", "func": "FadeInFunc"},
        ],
    }


# ------------------------------------------------------------------
# Glow effect
# ------------------------------------------------------------------


class TestGlowEffect:
    def test_effect_from_dict_dispatches_glow(self):
        actual_effect = effect_from_dict(_glow_dict())
        assert isinstance(actual_effect, Glow)
        assert actual_effect.name == "Glow"

    def test_radius_and_intensity_read(self):
        actual_effect = effect_from_dict(_glow_dict())
        assert actual_effect.radius == 35.0
        assert actual_effect.intensity == 0.6

    def test_radius_and_intensity_write(self):
        data = _glow_dict()
        actual_effect = effect_from_dict(data)
        actual_effect.radius = 50.0
        actual_effect.intensity = 0.8
        assert actual_effect.radius == 50.0
        assert actual_effect.intensity == 0.8

    def test_dict_mutation_passthrough(self):
        data = _glow_dict()
        actual_effect = effect_from_dict(data)
        actual_effect.radius = 99.0
        assert data["parameters"]["radius"]["defaultValue"] == 99.0

    def test_full_round_trip(self):
        """Tier 1: full object comparison for happy path."""
        data = _glow_dict()
        actual_effect = effect_from_dict(data)
        expected_data = _glow_dict()
        assert actual_effect.data == expected_data


# ------------------------------------------------------------------
# Time-bounded effects
# ------------------------------------------------------------------


class TestTimeBoundedEffects:
    def test_with_start_and_duration_is_time_bounded(self):
        actual_effect = effect_from_dict(_time_bounded_effect_dict())
        assert actual_effect.is_time_bounded is True

    def test_without_start_and_duration_is_not_time_bounded(self):
        actual_effect = effect_from_dict(_glow_dict())
        assert actual_effect.is_time_bounded is False

    def test_left_edge_mods_returns_correct_data(self):
        expected_mods = [_edge_mod()]
        actual_effect = effect_from_dict(
            _time_bounded_effect_dict(left_edge_mods=expected_mods)
        )
        assert actual_effect.left_edge_mods == expected_mods

    def test_right_edge_mods_returns_correct_data(self):
        expected_mods = [
            _edge_mod(
                parameters=[
                    {"name": "intensity", "func": "FadeOutFunc"},
                    {"name": "radius", "func": "FadeOutFunc"},
                ]
            )
        ]
        actual_effect = effect_from_dict(
            _time_bounded_effect_dict(right_edge_mods=expected_mods)
        )
        assert actual_effect.right_edge_mods == expected_mods

    def test_empty_left_edge_mods(self):
        actual_effect = effect_from_dict(_time_bounded_effect_dict())
        assert actual_effect.left_edge_mods == []

    def test_empty_right_edge_mods(self):
        actual_effect = effect_from_dict(_time_bounded_effect_dict())
        assert actual_effect.right_edge_mods == []

    def test_edge_mod_structure(self):
        """Verify EdgeMod has group, duration, and parameters with name+func."""
        expected_mod = _edge_mod(
            group="Video",
            duration=282240000,
            parameters=[
                {"name": "intensity", "func": "FadeInFunc"},
                {"name": "radius", "func": "FadeInFunc"},
            ],
        )
        actual_effect = effect_from_dict(
            _time_bounded_effect_dict(left_edge_mods=[expected_mod])
        )
        actual_mod = actual_effect.left_edge_mods[0]
        assert actual_mod == expected_mod

    @pytest.mark.parametrize(
        ("has_start", "has_duration", "expected"),
        [
            (True, True, True),
            (True, False, False),
            (False, True, False),
            (False, False, False),
        ],
        ids=["both", "start-only", "duration-only", "neither"],
    )
    def test_is_time_bounded_boundary_cases(self, has_start, has_duration, expected):
        data = _glow_dict()
        if has_start:
            data["start"] = 0
        if has_duration:
            data["duration"] = 705600000
        actual_effect = effect_from_dict(data)
        assert actual_effect.is_time_bounded is expected


# ------------------------------------------------------------------
# StitchedMedia source_effect
# ------------------------------------------------------------------


class TestStitchedMediaSourceEffect:
    def test_with_source_effect_returns_dict(self):
        expected_source_effect = {
            "effectName": "SourceEffect",
            "bypassed": False,
            "category": "",
            "parameters": {},
        }
        data = {
            "_type": "StitchedMedia",
            "id": 1,
            "start": 0,
            "duration": 100,
            "mediaStart": 0,
            "mediaDuration": 100,
            "sourceEffect": expected_source_effect,
        }
        actual_clip = StitchedMedia(data)
        assert actual_clip.source_effect == expected_source_effect

    def test_without_source_effect_returns_none(self):
        data = {
            "_type": "StitchedMedia",
            "id": 1,
            "start": 0,
            "duration": 100,
            "mediaStart": 0,
            "mediaDuration": 100,
        }
        actual_clip = StitchedMedia(data)
        assert actual_clip.source_effect is None


# ------------------------------------------------------------------
# Integration tests with real fixture
# ------------------------------------------------------------------


@pytest.fixture
def test_project_c_data():
    with open(FIXTURES / "test_project_c.tscproj") as f:
        return json.load(f)


def _all_clips(data: dict):
    """Yield all clip dicts from the project, recursively."""
    for track in (
        data.get("timeline", {})
        .get("sceneTrack", {})
        .get("scenes", [{}])[0]
        .get("csml", {})
        .get("tracks", [])
    ):
        yield from _walk_medias(track.get("medias", []))


def _walk_medias(medias: list[dict]):
    for media in medias:
        yield media
        if media.get("_type") == "Group":
            for track in media.get("tracks", []):
                yield from _walk_medias(track.get("medias", []))
        elif media.get("_type") == "StitchedMedia":
            yield from _walk_medias(media.get("medias", []))


class TestProjectCIntegration:
    def test_find_glow_effects(self, test_project_c_data):
        actual_glow_effects = []
        for clip_data in _all_clips(test_project_c_data):
            for eff_data in clip_data.get("effects", []):
                if eff_data.get("effectName") == "Glow":
                    actual_glow_effects.append(effect_from_dict(eff_data))

        assert all(isinstance(e, Glow) for e in actual_glow_effects)
        assert all(e.radius > 0 for e in actual_glow_effects)
        assert all(e.intensity > 0 for e in actual_glow_effects)
        # Verify we found the expected set of intensities
        actual_intensities = {round(e.intensity, 4) for e in actual_glow_effects}
        expected_intensities = {0.3545, 0.6, 0.4352}
        assert actual_intensities == expected_intensities

    def test_find_time_bounded_effects_with_edge_mods(self, test_project_c_data):
        actual_effects_with_left = []
        actual_effects_with_right = []
        for clip_data in _all_clips(test_project_c_data):
            for eff_data in clip_data.get("effects", []):
                eff = effect_from_dict(eff_data)
                if not hasattr(eff, 'left_edge_mods'):
                    continue
                if eff.is_time_bounded:
                    if eff.left_edge_mods:
                        actual_effects_with_left.append(eff)
                    if eff.right_edge_mods:
                        actual_effects_with_right.append(eff)

        # Verify structure of edge mods
        for eff in actual_effects_with_left:
            for mod in eff.left_edge_mods:
                assert {"group", "duration", "parameters"} == set(mod.keys())
                for param in mod["parameters"]:
                    assert {"name", "func"} == set(param.keys())

        for eff in actual_effects_with_right:
            for mod in eff.right_edge_mods:
                assert {"group", "duration", "parameters"} == set(mod.keys())
                for param in mod["parameters"]:
                    assert {"name", "func"} == set(param.keys())

        # Verify we found some
        assert actual_effects_with_left != []
        assert actual_effects_with_right != []

    def test_find_stitched_media_with_source_effect(self, test_project_c_data):
        actual_clips_with_source_effect = []
        for clip_data in _all_clips(test_project_c_data):
            if clip_data.get("_type") == "StitchedMedia" and "sourceEffect" in clip_data:
                actual_clip = StitchedMedia(clip_data)
                actual_clips_with_source_effect.append(actual_clip)

        assert actual_clips_with_source_effect != []
        for clip in actual_clips_with_source_effect:
            actual_se = clip.source_effect
            assert actual_se is not None
            assert "effectName" in actual_se
            assert "parameters" in actual_se

    def test_nested_groups(self, test_project_c_data):
        """Verify Group containing Group works correctly."""
        actual_nested_groups = []
        for clip_data in _all_clips(test_project_c_data):
            if clip_data.get("_type") == "Group":
                group = Group(clip_data)
                for track in group.tracks:
                    for child in track.clips:
                        if isinstance(child, Group):
                            actual_nested_groups.append((group, child))

        assert actual_nested_groups != []
        for parent, child in actual_nested_groups:
            assert isinstance(parent, Group)
            assert isinstance(child, Group)
            assert parent.tracks != []
            assert child.tracks != []
