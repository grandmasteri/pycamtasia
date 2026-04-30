"""Tests for EffectName enum coverage of BackgroundRemoval and MediaMatte, plus schema alignment."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from camtasia.types import EffectName, MatteMode

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "src" / "camtasia" / "resources" / "camtasia-project-schema.json"


def _load_schema_effect_enum() -> list[str]:
    schema = json.loads(SCHEMA_PATH.read_text())
    return schema["definitions"]["effect"]["properties"]["effectName"]["enum"]


class TestEffectNameEnumMembers:
    """Verify BACKGROUND_REMOVAL and MEDIA_MATTE exist with correct values."""

    def test_background_removal_exists(self):
        assert EffectName.BACKGROUND_REMOVAL.value == "BackgroundRemoval"

    def test_media_matte_exists(self):
        assert EffectName.MEDIA_MATTE.value == "MediaMatte"

    def test_background_removal_str_comparison(self):
        assert EffectName.BACKGROUND_REMOVAL == "BackgroundRemoval"

    def test_media_matte_str_comparison(self):
        assert EffectName.MEDIA_MATTE == "MediaMatte"


class TestSchemaEffectNameEnum:
    """Verify the JSON schema accepts BackgroundRemoval and MediaMatte."""

    def test_background_removal_in_schema(self):
        assert "BackgroundRemoval" in _load_schema_effect_enum()

    def test_media_matte_in_schema(self):
        assert "MediaMatte" in _load_schema_effect_enum()

    def test_schema_enum_sorted(self):
        enum_list = _load_schema_effect_enum()
        assert enum_list == sorted(enum_list)


class TestMatteModeCompleteness:
    """Verify MatteMode covers all 4 documented modes."""

    @pytest.mark.parametrize(
        ("member", "value"),
        [
            ("ALPHA", 1),
            ("ALPHA_INVERT", 2),
            ("LUMINOSITY", 3),
            ("LUMINOSITY_INVERT", 4),
        ],
    )
    def test_matte_mode_member(self, member: str, value: int):
        assert MatteMode[member] == value

    def test_matte_mode_count(self):
        assert set(MatteMode) == {
            MatteMode.ALPHA,
            MatteMode.ALPHA_INVERT,
            MatteMode.LUMINOSITY,
            MatteMode.LUMINOSITY_INVERT,
        }
