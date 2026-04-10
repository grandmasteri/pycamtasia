"""Tests for the legacy camtasia/effects.py module — Effect, VisualEffect, ChromaKeyEffect."""

import importlib.util
import pathlib

import pytest

# Load the legacy effects.py directly (same approach as effects/__init__.py)
_legacy_path = pathlib.Path(__file__).parent.parent / "src" / "camtasia" / "effects.py"
_spec = importlib.util.spec_from_file_location("camtasia._effects_legacy", str(_legacy_path))
_legacy = importlib.util.module_from_spec(_spec)

# The file has a broken schema class with newer marshmallow, so exec only the working part
_source = _legacy_path.read_text()
_cut = _source.index("class ChromaKeyEffectParametersSchema")
exec(compile(_source[:_cut], str(_legacy_path), "exec"), _legacy.__dict__)

Effect = _legacy.Effect
VisualEffect = _legacy.VisualEffect
ChromaKeyEffect = _legacy.ChromaKeyEffect
Parameters = _legacy.Parameters
CHROMA_KEY_NAME = _legacy.CHROMA_KEY_NAME
VISUAL_EFFECTS_CATEGORY = _legacy.VISUAL_EFFECTS_CATEGORY

from camtasia.color import RGBA


class TestEffect:
    """Tests for the base Effect class."""

    def test_properties(self):
        effect = Effect(name="test", category="cat")
        assert effect.name == "test"
        assert effect.category == "cat"

    def test_repr(self):
        assert repr(Effect(name="test", category="cat")) == "Effect(name='test', category='cat')"

    def test_equality(self):
        assert Effect(name="a", category="b") == Effect(name="a", category="b")

    def test_inequality(self):
        assert Effect(name="a", category="b") != Effect(name="x", category="b")

    def test_not_equal_to_non_effect(self):
        assert Effect(name="a", category="b") != "not an effect"

    def test_hash_equal_objects(self):
        assert hash(Effect(name="a", category="b")) == hash(Effect(name="a", category="b"))


class TestVisualEffect:
    """Tests for VisualEffect subclass."""

    def test_category_is_visual_effects(self):
        effect = VisualEffect(name="blur")
        assert effect.category == VISUAL_EFFECTS_CATEGORY


class TestChromaKeyEffect:
    """Tests for ChromaKeyEffect construction, defaults, and validation."""

    def test_defaults(self):
        ck = ChromaKeyEffect()
        assert ck.name == CHROMA_KEY_NAME
        assert ck.tolerance == 0.1
        assert ck.softness == 0.1
        assert ck.defringe == 0.0
        assert ck.inverted is False
        assert ck.compensation == 0.0
        assert ck.hue == RGBA(0, 255, 0, 255)

    def test_custom_values(self):
        ck = ChromaKeyEffect(tolerance=0.5, softness=0.3, defringe=-0.5, inverted=True, compensation=0.8)
        assert ck.tolerance == 0.5
        assert ck.softness == 0.3
        assert ck.defringe == -0.5
        assert ck.inverted is True
        assert ck.compensation == 0.8

    def test_hue_from_hex_string(self):
        ck = ChromaKeyEffect(hue="#ff0000")
        assert ck.hue == RGBA(255, 0, 0, 255)

    def test_hue_from_rgba_object(self):
        color = RGBA(100, 100, 100, 200)
        ck = ChromaKeyEffect(hue=color)
        assert ck.hue is color

    def test_color_channel_properties(self):
        ck = ChromaKeyEffect(hue=RGBA(255, 0, 127, 255))
        assert ck.red == 1.0
        assert ck.green == 0.0
        assert ck.blue == pytest.approx(127 / 255)
        assert ck.alpha == 1.0

    @pytest.mark.parametrize("param, value", [
        ("tolerance", -0.1),
        ("tolerance", 1.1),
        ("softness", -0.1),
        ("softness", 1.1),
        ("defringe", -1.1),
        ("defringe", 1.1),
        ("compensation", -0.1),
        ("compensation", 1.1),
    ])
    def test_out_of_range_raises(self, param, value):
        with pytest.raises(ValueError):
            ChromaKeyEffect(**{param: value})

    def test_repr(self):
        actual_result = repr(ChromaKeyEffect())
        assert "ChromaKeyEffect" in actual_result
        assert "tolerance=0.1" in actual_result

    def test_equality(self):
        assert ChromaKeyEffect() == ChromaKeyEffect()

    def test_inequality_different_tolerance(self):
        assert ChromaKeyEffect(tolerance=0.1) != ChromaKeyEffect(tolerance=0.5)

    def test_hash(self):
        assert hash(ChromaKeyEffect()) == hash(ChromaKeyEffect())

    def test_parameters_proxy(self):
        ck = ChromaKeyEffect(tolerance=0.7)
        params = ck.parameters
        assert isinstance(params, Parameters)
        assert params.tolerance == 0.7

    def test_metadata_keys(self):
        ck = ChromaKeyEffect()
        metadata = ck.metadata
        assert f"default-{CHROMA_KEY_NAME}-color" in metadata
        assert f"default-{CHROMA_KEY_NAME}-tolerance" in metadata

    def test_metadata_value_zero(self):
        assert ChromaKeyEffect._metadata_value(0) == "0"

    def test_metadata_value_tuple_no_spaces(self):
        assert ChromaKeyEffect._metadata_value((1, 2, 3)) == "(1,2,3)"
