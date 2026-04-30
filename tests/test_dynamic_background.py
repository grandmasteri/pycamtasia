"""Tests for builders.dynamic_background module."""
from __future__ import annotations

from pathlib import Path

import pytest

from camtasia import Project
from camtasia.builders.dynamic_background import (
    DynamicBackgroundAsset,
    add_dynamic_background,
    add_lottie_background,
)
from camtasia.effects.source import SourceEffect
from camtasia.timing import EDIT_RATE


@pytest.fixture
def proj(tmp_path):
    return Project.new(str(tmp_path / 'test.cmproj'))


class TestDynamicBackgroundAssetEnum:
    def test_all_members(self):
        assert set(DynamicBackgroundAsset) == {
            DynamicBackgroundAsset.GRADIENT_FOUR_CORNER,
            DynamicBackgroundAsset.GRADIENT_RADIAL,
            DynamicBackgroundAsset.ABSTRACT_SHAPES,
            DynamicBackgroundAsset.WAVES,
            DynamicBackgroundAsset.BOKEH,
        }

    def test_values_are_strings(self):
        for member in DynamicBackgroundAsset:
            assert isinstance(member.value, str)


class TestAddDynamicBackground:
    def test_gradient_four_corner(self, proj):
        clip = add_dynamic_background(
            proj,
            DynamicBackgroundAsset.GRADIENT_FOUR_CORNER,
            duration_seconds=10.0,
        )
        assert clip is not None
        assert clip._data['_type'] == 'VMFile'

    def test_gradient_radial(self, proj):
        clip = add_dynamic_background(
            proj,
            DynamicBackgroundAsset.GRADIENT_RADIAL,
            duration_seconds=5.0,
        )
        assert clip is not None

    def test_abstract_shapes_creates_source_effect(self, proj):
        clip = add_dynamic_background(
            proj,
            DynamicBackgroundAsset.ABSTRACT_SHAPES,
            duration_seconds=8.0,
            speed=2.0,
        )
        assert clip._data['_type'] == 'VMFile'
        se = SourceEffect(clip._data['sourceEffect'])
        assert se.speed == 2.0

    def test_waves_with_colors(self, proj):
        colors = [
            (0.1, 0.2, 0.3, 1.0),
            (0.4, 0.5, 0.6, 1.0),
        ]
        clip = add_dynamic_background(
            proj,
            DynamicBackgroundAsset.WAVES,
            duration_seconds=6.0,
            colors=colors,
        )
        se = SourceEffect(clip._data['sourceEffect'])
        assert se.color0 == (0.1, 0.2, 0.3, 1.0)
        assert se.color1 == (0.4, 0.5, 0.6, 1.0)

    def test_bokeh_duration(self, proj):
        clip = add_dynamic_background(
            proj,
            DynamicBackgroundAsset.BOKEH,
            duration_seconds=15.0,
        )
        assert clip._data['duration'] / EDIT_RATE == pytest.approx(15.0, abs=0.01)

    def test_string_asset_name(self, proj):
        clip = add_dynamic_background(
            proj,
            'abstract_shapes',
            duration_seconds=5.0,
        )
        assert clip._data['_type'] == 'VMFile'

    def test_invalid_asset_name_raises(self, proj):
        with pytest.raises(ValueError, match='Unknown asset'):
            add_dynamic_background(proj, 'nonexistent', duration_seconds=5.0)

    def test_custom_track_name(self, proj):
        add_dynamic_background(
            proj,
            DynamicBackgroundAsset.WAVES,
            duration_seconds=5.0,
            track_name='MyBG',
        )
        assert proj.timeline.find_track_by_name('MyBG') is not None

    def test_gradient_with_custom_colors(self, proj):
        colors = [(0.5, 0.5, 0.5, 1.0), (0.1, 0.1, 0.1, 1.0)]
        clip = add_dynamic_background(
            proj,
            DynamicBackgroundAsset.GRADIENT_FOUR_CORNER,
            duration_seconds=5.0,
            colors=colors,
        )
        assert clip is not None


class TestAddLottieBackground:
    def test_creates_clip_with_padded_color_keys(self, tmp_path, proj):
        lottie = tmp_path / 'anim.json'
        lottie.write_text('{"v":"5.0"}')

        clip = add_lottie_background(proj, lottie, duration_seconds=10.0)

        assert clip._data['_type'] == 'VMFile'
        params = clip._data['sourceEffect']['parameters']
        assert 'Color000-red' in params
        assert 'Color001-red' in params
        # Verify padded keys, not short keys
        assert 'Color0-red' not in params

    def test_lottie_duration(self, tmp_path, proj):
        lottie = tmp_path / 'anim.json'
        lottie.write_text('{"v":"5.0"}')

        clip = add_lottie_background(proj, lottie, duration_seconds=7.5)
        assert clip._data['duration'] / EDIT_RATE == pytest.approx(7.5, abs=0.01)

    def test_lottie_custom_track(self, tmp_path, proj):
        lottie = tmp_path / 'anim.json'
        lottie.write_text('{"v":"5.0"}')

        add_lottie_background(proj, lottie, duration_seconds=5.0, track_name='Lottie BG')
        assert proj.timeline.find_track_by_name('Lottie BG') is not None

    def test_lottie_source_bin_entry_created(self, tmp_path, proj):
        lottie = tmp_path / 'anim.json'
        lottie.write_text('{"v":"5.0"}')

        add_lottie_background(proj, lottie, duration_seconds=5.0)
        sources = [s for s in proj._data['sourceBin'] if 'anim.json' in str(s.get('src', ''))]
        assert len(sources) == 1
