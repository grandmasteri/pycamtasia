"""Tests for apply_dynamic_style and save/load/list dynamic caption presets."""
from __future__ import annotations

import json

import pytest

from camtasia.timeline.captions import (
    DynamicCaptionStyle,
    apply_dynamic_style,
    list_dynamic_caption_presets,
    load_dynamic_caption_preset,
    save_dynamic_caption_preset,
)
from camtasia.timeline.clips.callout import Callout


def _make_callout() -> Callout:
    """Build a minimal Callout clip dict."""
    return Callout({
        '_type': 'Callout',
        'id': 1,
        'start': 0,
        'duration': 705_600_000,
        'mediaStart': 0,
        'mediaDuration': 705_600_000,
        'scalar': 1,
        'parameters': {},
        'effects': [],
        'def': {
            'kind': 'remix',
            'shape': 'text',
            'style': 'basic',
            'text': 'Hello',
            'font': {'name': 'Arial', 'size': 36.0, 'weight': 'Regular'},
            'fill-color-red': 1.0,
            'fill-color-green': 1.0,
            'fill-color-blue': 1.0,
            'fill-color-opacity': 1.0,
            'stroke-color-red': 0.0,
            'stroke-color-green': 0.0,
            'stroke-color-blue': 0.0,
            'stroke-color-opacity': 1.0,
            'width': 400.0,
            'height': 100.0,
        },
    })


# ---------------------------------------------------------------------------
# apply_dynamic_style
# ---------------------------------------------------------------------------


class TestApplyDynamicStyle:
    def test_sets_font(self):
        callout = _make_callout()
        style = DynamicCaptionStyle(name='t', font_name='Courier', font_size=24)
        apply_dynamic_style(callout, style)
        assert callout.text_properties['font_name'] == 'Courier'
        assert callout.text_properties['font_size'] == 24.0

    def test_sets_fill_color(self):
        callout = _make_callout()
        style = DynamicCaptionStyle(name='t', fill_color=(128, 0, 255, 200))
        apply_dynamic_style(callout, style)
        r, g, b, a = callout.fill_color
        assert pytest.approx(r, abs=0.01) == 128 / 255
        assert pytest.approx(b, abs=0.01) == 1.0
        assert pytest.approx(a, abs=0.01) == 200 / 255

    def test_sets_stroke_color(self):
        callout = _make_callout()
        style = DynamicCaptionStyle(name='t', stroke_color=(10, 20, 30, 40))
        apply_dynamic_style(callout, style)
        r, g, b, a = callout.stroke_color
        assert pytest.approx(r, abs=0.01) == 10 / 255
        assert pytest.approx(a, abs=0.01) == 40 / 255

    def test_sets_background_color(self):
        callout = _make_callout()
        style = DynamicCaptionStyle(name='t', background_color=(50, 60, 70, 80))
        apply_dynamic_style(callout, style)
        r, g, b, a = callout.background_color
        assert pytest.approx(r, abs=0.01) == 50 / 255
        assert pytest.approx(b, abs=0.01) == 70 / 255


# ---------------------------------------------------------------------------
# save / load / list presets
# ---------------------------------------------------------------------------


class TestSaveLoadPreset:
    def test_save_creates_file(self, tmp_path):
        style = DynamicCaptionStyle(name='my_preset')
        path = save_dynamic_caption_preset(style, 'my_preset', presets_dir=tmp_path)
        assert path.exists()
        assert path.name == 'my_preset.json'

    def test_roundtrip(self, tmp_path):
        style = DynamicCaptionStyle(
            name='roundtrip',
            font_name='Courier',
            font_size=20,
            fill_color=(10, 20, 30, 40),
            highlight_color=(200, 100, 50, 255),
        )
        save_dynamic_caption_preset(style, 'roundtrip', presets_dir=tmp_path)
        loaded = load_dynamic_caption_preset('roundtrip', presets_dir=tmp_path)
        assert loaded == style

    def test_load_missing_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_dynamic_caption_preset('nonexistent', presets_dir=tmp_path)

    def test_save_overwrites(self, tmp_path):
        style1 = DynamicCaptionStyle(name='v1', font_size=10)
        style2 = DynamicCaptionStyle(name='v2', font_size=99)
        save_dynamic_caption_preset(style1, 'preset', presets_dir=tmp_path)
        save_dynamic_caption_preset(style2, 'preset', presets_dir=tmp_path)
        loaded = load_dynamic_caption_preset('preset', presets_dir=tmp_path)
        assert loaded.font_size == 99

    def test_saved_json_is_valid(self, tmp_path):
        style = DynamicCaptionStyle(name='check')
        save_dynamic_caption_preset(style, 'check', presets_dir=tmp_path)
        data = json.loads((tmp_path / 'check.json').read_text())
        assert data['name'] == 'check'
        assert data['font_name'] == 'Arial'


class TestListPresets:
    def test_empty_directory(self, tmp_path):
        assert list_dynamic_caption_presets(presets_dir=tmp_path) == []

    def test_nonexistent_directory(self, tmp_path):
        assert list_dynamic_caption_presets(presets_dir=tmp_path / 'nope') == []

    def test_lists_saved_presets(self, tmp_path):
        for name in ('beta', 'alpha', 'gamma'):
            save_dynamic_caption_preset(
                DynamicCaptionStyle(name=name), name, presets_dir=tmp_path,
            )
        assert list_dynamic_caption_presets(presets_dir=tmp_path) == ['alpha', 'beta', 'gamma']
