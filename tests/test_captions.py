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
    with pytest.raises(ValueError, match=r'opacity must be 0\.0-1\.0'):
        attrs.opacity = -0.1
    with pytest.raises(ValueError, match=r'opacity must be 0\.0-1\.0'):
        attrs.opacity = 1.1


def test_caption_font_size_validation():
    attrs = CaptionAttributes({})
    attrs.font_size = 1
    assert attrs.font_size == 1
    with pytest.raises(ValueError, match='font_size must be >= 1'):
        attrs.font_size = 0
    with pytest.raises(ValueError, match='font_size must be >= 1'):
        attrs.font_size = -5


class TestCaptionDefaultDuration:
    def test_getter_default(self):
        attrs = CaptionAttributes({})
        assert attrs.default_duration_seconds == 4.0

    def test_setter_and_getter(self):
        attrs = CaptionAttributes({})
        attrs.default_duration_seconds = 7.5
        assert attrs.default_duration_seconds == 7.5

    def test_setter_rejects_zero(self):
        attrs = CaptionAttributes({})
        with pytest.raises(ValueError, match='default_duration_seconds must be > 0'):
            attrs.default_duration_seconds = 0

    def test_setter_rejects_negative(self):
        attrs = CaptionAttributes({})
        with pytest.raises(ValueError, match='default_duration_seconds must be > 0'):
            attrs.default_duration_seconds = -1.0


class TestCaptionPosition:
    def test_getter_defaults(self):
        attrs = CaptionAttributes({})
        assert attrs.position == {'x': 0.5, 'y': 0.9}

    def test_setter_and_getter(self):
        attrs = CaptionAttributes({})
        attrs.position = {'x': 0.2, 'y': 0.3}
        assert attrs.position == {'x': 0.2, 'y': 0.3}

    def test_getter_with_none_values(self):
        attrs = CaptionAttributes({'positionX': None, 'positionY': None})
        assert attrs.position == {'x': 0.5, 'y': 0.9}


class TestCaptionVerticalAnchor:
    def test_getter_default_bottom(self):
        attrs = CaptionAttributes({})
        assert attrs.vertical_anchor == 'bottom'

    @pytest.mark.parametrize(('anchor', 'expected_y'), [
        ('top', 0.1),
        ('middle', 0.5),
        ('bottom', 0.9),
    ])
    def test_setter_and_roundtrip(self, anchor, expected_y):
        attrs = CaptionAttributes({})
        attrs.vertical_anchor = anchor
        assert attrs.vertical_anchor == anchor
        assert attrs.position['y'] == expected_y

    def test_setter_rejects_invalid(self):
        attrs = CaptionAttributes({})
        with pytest.raises(ValueError, match="vertical_anchor must be"):
            attrs.vertical_anchor = 'center'

    def test_getter_unknown_y_returns_bottom(self):
        attrs = CaptionAttributes({'positionY': 0.75})
        assert attrs.vertical_anchor == 'bottom'


class TestActiveWordAt:
    def test_returns_word_at_time(self):
        attrs = CaptionAttributes({})
        assert attrs.active_word_at(0.0, ['hello', 'world'], 2.0) == 'hello'
        assert attrs.active_word_at(1.5, ['hello', 'world'], 2.0) == 'world'

    def test_returns_none_for_empty_words(self):
        attrs = CaptionAttributes({})
        assert attrs.active_word_at(0.5, [], 2.0) is None

    def test_returns_none_for_zero_duration(self):
        attrs = CaptionAttributes({})
        assert attrs.active_word_at(0.5, ['a'], 0.0) is None

    def test_returns_none_for_negative_time(self):
        attrs = CaptionAttributes({})
        assert attrs.active_word_at(-1.0, ['a'], 2.0) is None

    def test_returns_none_for_time_past_duration(self):
        attrs = CaptionAttributes({})
        assert attrs.active_word_at(3.0, ['a'], 2.0) is None

    def test_clamps_to_last_word_at_boundary(self):
        attrs = CaptionAttributes({})
        assert attrs.active_word_at(2.0, ['a', 'b'], 2.0) == 'b'


class TestExtendDynamicCaption:
    def test_scales_explicit_transcript(self):
        from camtasia.timeline.captions import extend_dynamic_caption
        from camtasia.timing import EDIT_RATE
        data = {'duration': EDIT_RATE * 2}
        words = [{'start': 0.0, 'end': 1.0}, {'start': 1.0, 'end': 2.0}]
        extend_dynamic_caption(data, 4.0, transcript=words)
        assert words[0] == {'start': 0.0, 'end': 2.0}
        assert words[1] == {'start': 2.0, 'end': 4.0}

    def test_reads_words_from_metadata(self):
        from camtasia.timeline.captions import extend_dynamic_caption
        from camtasia.timing import EDIT_RATE
        words = [{'start': 0.0, 'end': 1.0}]
        data = {
            'duration': EDIT_RATE,
            'metadata': {'dynamicCaptionTranscription': {'words': words}},
        }
        extend_dynamic_caption(data, 2.0)
        assert words[0] == {'start': 0.0, 'end': 2.0}

    def test_noop_when_duration_zero(self):
        from camtasia.timeline.captions import extend_dynamic_caption
        data = {'duration': 0}
        extend_dynamic_caption(data, 5.0)
        assert data['duration'] == 0

    def test_noop_when_duration_negative(self):
        from camtasia.timeline.captions import extend_dynamic_caption
        data = {'duration': -100}
        extend_dynamic_caption(data, 5.0)
        assert data['duration'] == -100

    def test_noop_when_old_seconds_underflows_to_zero(self):
        from camtasia.timeline.captions import extend_dynamic_caption
        # 5e-324 is the smallest positive float; dividing by EDIT_RATE underflows to 0.0
        data = {'duration': 5e-324}
        extend_dynamic_caption(data, 5.0)
        assert data['duration'] == 5e-324

    def test_no_words_still_updates_duration(self):
        from camtasia.timeline.captions import extend_dynamic_caption
        from camtasia.timing import EDIT_RATE, seconds_to_ticks
        data = {'duration': EDIT_RATE}
        extend_dynamic_caption(data, 3.0)
        assert data['duration'] == seconds_to_ticks(3.0)
