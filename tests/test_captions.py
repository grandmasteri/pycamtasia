"""Tests for CaptionAttributes API."""
from __future__ import annotations

import pytest

from camtasia.timeline.captions import CaptionAttributes


def test_caption_attributes_defaults():
    attrs = CaptionAttributes({})
    assert attrs.enabled is True
    assert attrs.font_name == 'Arial'
    assert attrs.font_size == 32
    assert attrs.background_color == [0, 0, 0, 204]
    assert attrs.foreground_color == [255, 255, 255, 255]
    assert attrs.lang == 'en'
    assert attrs.alignment == 0
    assert attrs.opacity == 0.5
    assert attrs.background_enabled is True


def test_caption_attributes_setters():
    data = {}
    attrs = CaptionAttributes(data)

    attrs.enabled = False
    attrs.font_name = 'Helvetica'
    attrs.font_size = 48
    attrs.background_color = [10, 20, 30, 128]
    attrs.foreground_color = [200, 200, 200, 255]
    attrs.lang = 'fr'
    attrs.alignment = 1
    attrs.opacity = 0.8
    attrs.background_enabled = False

    assert attrs.enabled is False
    assert attrs.font_name == 'Helvetica'
    assert attrs.font_size == 48
    assert attrs.background_color == [10, 20, 30, 128]
    assert attrs.foreground_color == [200, 200, 200, 255]
    assert attrs.lang == 'fr'
    assert attrs.alignment == 1
    assert attrs.opacity == 0.8
    assert attrs.background_enabled is False

    # Verify mutations hit the backing dict
    assert data['enabled'] is False
    assert data['fontName'] == 'Helvetica'
    assert data['fontSize'] == 48


def test_caption_attributes_repr():
    attrs = CaptionAttributes({'fontName': 'Courier', 'fontSize': 24, 'lang': 'de'})
    assert repr(attrs) == "CaptionAttributes(font='Courier', size=24, lang='de')"


def test_timeline_caption_attributes_property(project):
    tl = project.timeline
    ca = tl.caption_attributes

    assert isinstance(ca, CaptionAttributes)
    # setdefault should create the key in timeline data
    assert 'captionAttributes' in tl._data
    # Mutations through the property should persist
    ca.font_name = 'Impact'
    assert tl.caption_attributes.font_name == 'Impact'


def test_caption_alignment_validation():
    attrs = CaptionAttributes({})
    for valid in (0, 1, 2):
        attrs.alignment = valid
        assert attrs.alignment == valid
    with pytest.raises(ValueError, match='alignment must be 0'):
        attrs.alignment = 3
    with pytest.raises(ValueError, match='alignment must be 0'):
        attrs.alignment = -1


def test_caption_opacity_validation():
    attrs = CaptionAttributes({})
    attrs.opacity = 0.0
    assert attrs.opacity == 0.0
    attrs.opacity = 1.0
    assert attrs.opacity == 1.0
    with pytest.raises(ValueError, match='opacity must be 0.0-1.0'):
        attrs.opacity = -0.1
    with pytest.raises(ValueError, match='opacity must be 0.0-1.0'):
        attrs.opacity = 1.1


def test_caption_font_size_validation():
    attrs = CaptionAttributes({})
    attrs.font_size = 1
    assert attrs.font_size == 1
    with pytest.raises(ValueError, match='font_size must be >= 1'):
        attrs.font_size = 0
    with pytest.raises(ValueError, match='font_size must be >= 1'):
        attrs.font_size = -5
