"""Tests for camtasia.canvas_presets module."""

from __future__ import annotations

import pytest

from camtasia.canvas_presets import (
    PRESET_NAMES,
    Platform,
    SafeZone,
    VerticalPreset,
    get_safe_zone,
)


class TestVerticalPreset:
    """Tests for the VerticalPreset enum."""

    def test_all_presets_have_two_element_tuples(self):
        for preset in VerticalPreset:
            w, h = preset.value
            assert isinstance(w, int)
            assert isinstance(h, int)

    def test_nine_by_sixteen_fhd(self):
        assert VerticalPreset.NINE_BY_SIXTEEN_FHD.value == (1080, 1920)

    def test_nine_by_sixteen_hd(self):
        assert VerticalPreset.NINE_BY_SIXTEEN_HD.value == (720, 1280)

    def test_four_by_five(self):
        assert VerticalPreset.FOUR_BY_FIVE.value == (1080, 1350)

    def test_one_by_one(self):
        assert VerticalPreset.ONE_BY_ONE.value == (1080, 1080)

    def test_sixteen_by_nine_fhd(self):
        assert VerticalPreset.SIXTEEN_BY_NINE_FHD.value == (1920, 1080)


class TestPresetNames:
    """Tests for the PRESET_NAMES mapping."""

    def test_all_five_presets_present(self):
        assert set(PRESET_NAMES) == {'9:16_FHD', '9:16_HD', '4:5', '1:1', '16:9_FHD'}

    def test_maps_to_correct_enum(self):
        assert PRESET_NAMES['9:16_FHD'] is VerticalPreset.NINE_BY_SIXTEEN_FHD
        assert PRESET_NAMES['1:1'] is VerticalPreset.ONE_BY_ONE


class TestPlatform:
    """Tests for the Platform enum."""

    def test_members(self):
        assert set(p.value for p in Platform) == {
            'instagram_reels', 'youtube_shorts', 'tiktok',
        }


class TestSafeZone:
    """Tests for the SafeZone dataclass."""

    def test_frozen(self):
        sz = SafeZone(top=10, bottom=20, left=5, right=5, platform=Platform.TIKTOK)
        with pytest.raises(AttributeError):
            sz.top = 99  # type: ignore[misc]

    def test_fields(self):
        sz = SafeZone(top=1, bottom=2, left=3, right=4, platform=Platform.YOUTUBE_SHORTS)
        assert (sz.top, sz.bottom, sz.left, sz.right) == (1, 2, 3, 4)
        assert sz.platform is Platform.YOUTUBE_SHORTS


class TestGetSafeZone:
    """Tests for the get_safe_zone() helper."""

    @pytest.mark.parametrize('platform', list(Platform))
    def test_returns_safe_zone_for_all_platforms(self, platform: Platform):
        sz = get_safe_zone(platform)
        assert isinstance(sz, SafeZone)
        assert sz.platform is platform

    def test_accepts_string(self):
        sz = get_safe_zone('tiktok')
        assert sz.platform is Platform.TIKTOK

    def test_unknown_string_raises(self):
        with pytest.raises(ValueError, match='Unknown platform'):
            get_safe_zone('snapchat')

    def test_instagram_reels_values(self):
        sz = get_safe_zone(Platform.INSTAGRAM_REELS)
        assert sz.top == 250
        assert sz.bottom == 400

    def test_youtube_shorts_values(self):
        sz = get_safe_zone(Platform.YOUTUBE_SHORTS)
        assert sz.top == 200
        assert sz.bottom == 300

    def test_tiktok_values(self):
        sz = get_safe_zone(Platform.TIKTOK)
        assert sz.top == 150
        assert sz.bottom == 350


class TestProjectGetSafeZone:
    """Tests for Project.get_safe_zone() wrapper."""

    def test_delegates_to_module(self, project):
        from camtasia.canvas_presets import Platform as P

        sz = project.get_safe_zone('instagram_reels')
        assert sz.platform is P.INSTAGRAM_REELS

    def test_invalid_platform_raises(self, project):
        with pytest.raises(ValueError):
            project.get_safe_zone('nonexistent')
