from __future__ import annotations
"""Tests for marshmallow-based legacy effect schemas and TrackMediaEffects integration."""

import importlib.util
import pathlib

import pytest

pytest.importorskip("marshmallow")

# Load the legacy module directly to access rgba, rgb, and schema classes
_legacy_path = pathlib.Path(__file__).parent.parent / "src" / "camtasia" / "effects.py"
_spec = importlib.util.spec_from_file_location("camtasia._effects_legacy", str(_legacy_path))
_legacy = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_legacy)

rgba = _legacy.rgba
rgb = _legacy.rgb
ChromaKeyEffect = _legacy.ChromaKeyEffect
ChromaKeyEffectSchema = _legacy.ChromaKeyEffectSchema
EffectSchema = _legacy.EffectSchema

from camtasia.color import RGBA
from camtasia.timeline.track_media import TrackMedia


# -- rgba / rgb functions (effects.py lines 27-37) --

class TestRgba:
    def test_three_channel_hex_appends_alpha(self):
        actual_result = rgba("#ff0000")
        expected_result = (255, 0, 0, 255)
        assert actual_result == expected_result

    def test_four_channel_hex_passes_through(self):
        actual_result = rgba("#ff008080")
        expected_result = (255, 0, 128, 128)
        assert actual_result == expected_result


class TestRgb:
    def test_valid_rgb_with_ff_alpha(self):
        actual_result = rgb("#00ff00ff")
        expected_result = (0, 255, 0)
        assert actual_result == expected_result

    def test_non_ff_alpha_raises(self):
        with pytest.raises(ValueError, match="Alpha argument not 0xFF"):
            rgb("#00ff0080")


# -- ChromaKeyEffectSchema round-trip (effects.py lines 268-289) --

class TestChromaKeyEffectSchema:
    def test_dump_produces_expected_keys(self):
        chroma_key = ChromaKeyEffect()
        schema = ChromaKeyEffectSchema()
        actual_result = schema.dump(chroma_key)
        assert actual_result["category"] == "categoryVisualEffects"
        assert actual_result["parameters"]["tolerance"] == pytest.approx(0.1)
        assert actual_result["parameters"]["softness"] == pytest.approx(0.1)
        assert actual_result["parameters"]["defringe"] == pytest.approx(0.0)
        assert actual_result["parameters"]["invertEffect"] == 0.0
        assert actual_result["parameters"]["clrCompensation"] == pytest.approx(0.0)
        assert actual_result["parameters"]["color-green"] == pytest.approx(1.0)
        assert actual_result["parameters"]["enabled"] == 1

    def test_load_reconstructs_chroma_key_effect(self):
        original_effect = ChromaKeyEffect(tolerance=0.5, softness=0.3, defringe=-0.2,
                                          inverted=True, compensation=0.4,
                                          hue=RGBA(255, 0, 128, 200))
        schema = ChromaKeyEffectSchema()
        dumped = schema.dump(original_effect)
        loaded_effect = schema.load(dumped)
        assert loaded_effect.tolerance == pytest.approx(0.5)
        assert loaded_effect.softness == pytest.approx(0.3)
        assert loaded_effect.defringe == pytest.approx(-0.2)
        assert loaded_effect.inverted is True
        assert loaded_effect.compensation == pytest.approx(0.4)

    def test_round_trip_preserves_defaults(self):
        schema = ChromaKeyEffectSchema()
        original_effect = ChromaKeyEffect()
        loaded_effect = schema.load(schema.dump(original_effect))
        assert loaded_effect.tolerance == original_effect.tolerance
        assert loaded_effect.softness == original_effect.softness
        assert loaded_effect.inverted == original_effect.inverted


# -- EffectSchema (OneOfSchema) round-trip (effects.py lines 292-299) --

class TestEffectSchema:
    def test_dump_includes_effect_name(self):
        schema = EffectSchema()
        actual_result = schema.dump(ChromaKeyEffect())
        assert actual_result["effectName"] == "ChromaKey"
        assert "category" in actual_result

    def test_load_dispatches_to_chroma_key(self):
        schema = EffectSchema()
        dumped = schema.dump(ChromaKeyEffect(tolerance=0.7))
        loaded_effect = schema.load(dumped)
        assert isinstance(loaded_effect, ChromaKeyEffect)
        assert loaded_effect.tolerance == pytest.approx(0.7)

    def test_round_trip(self):
        schema = EffectSchema()
        original_effect = ChromaKeyEffect(softness=0.6, defringe=0.5)
        loaded_effect = schema.load(schema.dump(original_effect))
        assert loaded_effect.softness == pytest.approx(0.6)
        assert loaded_effect.defringe == pytest.approx(0.5)


# -- effects/__init__.py success path (lines 25-26) --

class TestEffectsInitSuccessPath:
    def test_effect_schema_is_real_oneofschema(self):
        """When marshmallow is installed, EffectSchema should be the real OneOfSchema class."""
        from camtasia.effects import EffectSchema as ImportedSchema
        schema_instance = ImportedSchema()
        assert hasattr(schema_instance, "type_schemas")
        assert "ChromaKey" in schema_instance.type_schemas


# -- TrackMediaEffects (track_media.py lines 89-116) --

def _chroma_key_effect_data():
    """Produce serialized ChromaKey effect data that EffectSchema can parse."""
    schema = EffectSchema()
    return schema.dump(ChromaKeyEffect())


def _make_media_data_with_effects(effects=None, metadata=None):
    return {
        "id": 1,
        "start": 0,
        "mediaStart": 0,
        "duration": 1000,
        "effects": effects if effects is not None else [],
        "metadata": metadata if metadata is not None else {},
    }


class TestTrackMediaEffectsGetItem:
    def test_getitem_returns_chroma_key_effect(self):
        effect_data = _chroma_key_effect_data()
        media = TrackMedia(_make_media_data_with_effects(effects=[effect_data]))
        actual_effect = media.effects[0]
        assert actual_effect.name == "ChromaKey"
        assert actual_effect.tolerance == pytest.approx(0.1)


class TestTrackMediaEffectsDelItem:
    def test_delitem_removes_effect_and_metadata(self):
        chroma_key = ChromaKeyEffect()
        effect_data = _chroma_key_effect_data()
        metadata = dict(chroma_key.metadata)
        data = _make_media_data_with_effects(effects=[effect_data], metadata=metadata)
        media = TrackMedia(data)
        del media.effects[0]
        assert data["effects"] == []
        for key in chroma_key.metadata:
            assert key not in data["metadata"]


class TestTrackMediaEffectsSetItem:
    def test_setitem_replaces_effect(self):
        original_data = _chroma_key_effect_data()
        original_ck = ChromaKeyEffect()
        metadata = dict(original_ck.metadata)
        data = _make_media_data_with_effects(effects=[original_data], metadata=metadata)
        media = TrackMedia(data)

        replacement = ChromaKeyEffect(tolerance=0.9)
        media.effects[0] = replacement

        replaced_effect = media.effects[0]
        assert replaced_effect.tolerance == pytest.approx(0.9)
        assert data["metadata"] == dict(replacement.metadata)


class TestTrackMediaEffectsAddEffect:
    def test_add_effect_appends_and_updates_metadata(self):
        data = _make_media_data_with_effects()
        media = TrackMedia(data)
        new_effect = ChromaKeyEffect(softness=0.8)
        media.effects.add_effect(new_effect)

        assert data["effects"] != []
        loaded_effect = media.effects[0]
        assert loaded_effect.softness == pytest.approx(0.8)
        for key in new_effect.metadata:
            assert key in data["metadata"]
