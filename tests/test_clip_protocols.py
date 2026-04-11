"""Tests for BaseClip equality, hashing, and input validation."""
from __future__ import annotations

import pytest

from camtasia.timeline.clips.base import BaseClip


def _make_clip(clip_id: int = 1, **overrides) -> BaseClip:
    data: dict = {
        'id': clip_id,
        '_type': 'VMFile',
        'start': 0,
        'duration': 705_600_000,
        'mediaStart': 0,
        'mediaDuration': 705_600_000,
        **overrides,
    }
    return BaseClip(data)


class TestClipEquality:
    def test_clip_eq_same_dict(self) -> None:
        data: dict = {'id': 1, '_type': 'VMFile', 'start': 0, 'duration': 705_600_000,
                       'mediaStart': 0, 'mediaDuration': 705_600_000}
        actual_a = BaseClip(data)
        actual_b = BaseClip(data)
        assert actual_a == actual_b

    def test_clip_eq_same_id(self) -> None:
        actual_a = _make_clip(clip_id=42)
        actual_b = _make_clip(clip_id=42)
        assert actual_a == actual_b

    def test_clip_neq_different_id(self) -> None:
        actual_a = _make_clip(clip_id=1)
        actual_b = _make_clip(clip_id=2)
        assert actual_a != actual_b

    def test_clip_eq_different_type_returns_not_implemented(self) -> None:
        actual = _make_clip(clip_id=1)
        expected = NotImplemented
        assert actual.__eq__('not a clip') is expected


class TestClipHash:
    def test_clip_hash_in_set(self) -> None:
        clip_a = _make_clip(clip_id=7)
        clip_b = _make_clip(clip_id=7)
        actual = len({clip_a, clip_b})
        expected = 1
        assert actual == expected


class TestCropValidation:
    @pytest.mark.parametrize(
        'kwargs, expected_fragment',
        [
            pytest.param({'left': 2.0}, 'Crop left', id='left-too-high'),
            pytest.param({'top': -0.1}, 'Crop top', id='top-negative'),
            pytest.param({'right': 1.1}, 'Crop right', id='right-too-high'),
            pytest.param({'bottom': -1.0}, 'Crop bottom', id='bottom-negative'),
        ],
    )
    def test_crop_out_of_range_raises(self, kwargs: dict, expected_fragment: str) -> None:
        clip = _make_clip()
        with pytest.raises(ValueError, match=expected_fragment):
            clip.crop(**kwargs)

    def test_crop_valid_boundary_values(self) -> None:
        clip = _make_clip()
        actual = clip.crop(left=0.0, top=0.0, right=1.0, bottom=1.0)
        assert actual is clip


class TestSetOpacityValidation:
    @pytest.mark.parametrize(
        'opacity',
        [
            pytest.param(-0.1, id='negative'),
            pytest.param(1.1, id='too-high'),
            pytest.param(2.0, id='way-too-high'),
        ],
    )
    def test_set_opacity_out_of_range_raises(self, opacity: float) -> None:
        clip = _make_clip()
        with pytest.raises(ValueError, match='Opacity must be 0.0-1.0'):
            clip.set_opacity(opacity)

    def test_set_opacity_valid_boundary(self) -> None:
        clip = _make_clip()
        actual_low = clip.set_opacity(0.0)
        assert actual_low is clip
        actual_high = clip.set_opacity(1.0)
        assert actual_high is clip


class TestSetSpeedValidation:
    def test_set_speed_zero_raises(self) -> None:
        clip = _make_clip()
        with pytest.raises(ValueError, match='Speed must be positive'):
            clip.set_speed(0)

    def test_set_speed_negative_raises(self) -> None:
        clip = _make_clip()
        with pytest.raises(ValueError, match='Speed must be positive'):
            clip.set_speed(-1.5)

    def test_set_speed_positive_works(self) -> None:
        clip = _make_clip()
        clip.set_speed(2.0)
        actual = clip.scalar
        expected_numerator = 1
        expected_denominator = 2
        assert actual.numerator == expected_numerator
        assert actual.denominator == expected_denominator
