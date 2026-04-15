"""Tests for BaseClip.set_source_effect() creation API."""
from __future__ import annotations

import pytest

from camtasia.timeline.clips.base import BaseClip


def _make_clip(**extra) -> BaseClip:
    data = {"_type": "VMFile", "id": 1, "start": 0, "duration": 100,
            "mediaStart": 0, "mediaDuration": 100, **extra}
    return BaseClip(data)


class TestSetSourceEffect:

    def test_creates_structure(self):
        clip = _make_clip()
        clip.set_source_effect(color0=(255, 0, 0))
        se = clip.source_effect
        assert se is not None
        assert se['effectName'] == 'SourceEffect'
        assert se['bypassed'] is False
        assert se['category'] == ''
        assert 'parameters' in se

    def test_converts_rgb_to_float(self):
        clip = _make_clip()
        clip.set_source_effect(color0=(255, 128, 0))
        p = clip.source_effect['parameters']
        assert p['Color0-red'] == pytest.approx(1.0)
        assert p['Color0-green'] == pytest.approx(128 / 255)
        assert p['Color0-blue'] == pytest.approx(0.0)
        assert p['Color0-alpha'] == 1.0

    def test_default_midpoint_and_speed(self):
        clip = _make_clip()
        clip.set_source_effect()
        p = clip.source_effect['parameters']
        assert p['MidPoint'] == 0.5
        assert p['Speed'] == 5.0
        assert p['sourceFileType'] == 'tscshadervid'

    def test_custom_values(self):
        clip = _make_clip()
        clip.set_source_effect(
            color0=(35, 47, 62),
            color1=(5, 160, 209),
            mid_point=(0.3, 0.7),
            speed=3.0,
            source_file_type='custom',
        )
        p = clip.source_effect['parameters']
        assert p['Color0-red'] == pytest.approx(35 / 255)
        assert p['Color1-blue'] == pytest.approx(209 / 255)
        assert p['MidPointX'] == 0.3
        assert p['MidPointY'] == 0.7
        assert p['Speed'] == 3.0
        assert p['sourceFileType'] == 'custom'
        # color2/color3 not set — keys absent
        assert 'Color2-red' not in p
        assert 'Color3-red' not in p

    def test_replaces_existing(self):
        clip = _make_clip()
        clip.set_source_effect(color0=(255, 0, 0), color1=(0, 255, 0))
        clip.set_source_effect(color0=(0, 0, 255))
        p = clip.source_effect['parameters']
        assert p['Color0-blue'] == pytest.approx(1.0)
        assert p['Color0-red'] == pytest.approx(0.0)
        # color1 from first call is gone
        assert 'Color1-red' not in p

    def test_source_effect_property_reads_back(self):
        """The existing source_effect property returns the dict set by set_source_effect."""
        clip = _make_clip()
        assert clip.source_effect is None
        clip.set_source_effect(
            color0=(35, 47, 62),
            color1=(5, 160, 209),
            color2=(35, 47, 62),
            color3=(5, 160, 209),
        )
        se = clip.source_effect
        assert se is not None
        assert se is clip._data['sourceEffect']
        p = se['parameters']
        # All four colors present
        for i in range(4):
            assert f'Color{i}-red' in p
            assert f'Color{i}-alpha' in p
