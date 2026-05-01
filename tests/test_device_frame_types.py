"""Tests for DeviceFrameType enum, device frame library, and device frame effect."""
from __future__ import annotations

import sys
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from camtasia import Project
from camtasia.builders import (
    DEVICE_FRAME_LIBRARY_URL,
    DeviceFrameAsset,
    DeviceFrameType,
    add_device_frame,
    add_device_frame_effect,
    get_device_frame_asset,
)


@pytest.fixture
def proj_with_clip(tmp_path, monkeypatch):
    """Project with a single image clip on a Content track."""
    mock_mi = MagicMock()
    mock_mi.MediaInfo.parse.return_value = SimpleNamespace(tracks=[
        SimpleNamespace(track_type='Image', width=1920, height=1080),
    ])
    monkeypatch.setitem(sys.modules, 'pymediainfo', mock_mi)
    proj_dir = tmp_path / 'test.cmproj'
    proj = Project.new(str(proj_dir))
    img = tmp_path / 'bg.png'
    img.write_bytes(b'\x89PNG\r\n\x1a\n')
    media = proj.import_media(img)
    track = proj.timeline.get_or_create_track('Content')
    clip = track.add_image(media.id, start_seconds=0.0, duration_seconds=5.0)
    return proj, clip


class TestDeviceFrameType:

    def test_all_members(self):
        expected = {
            'IPHONE', 'IPAD', 'ANDROID_PHONE', 'ANDROID_TABLET',
            'MACBOOK', 'IMAC', 'BROWSER', 'TV', 'WATCH',
        }
        assert {m.name for m in DeviceFrameType} == expected

    def test_values_are_lowercase_strings(self):
        for member in DeviceFrameType:
            assert member.value == member.value.lower()
            assert isinstance(member.value, str)

    def test_is_str_enum(self):
        assert isinstance(DeviceFrameType.IPHONE, str)
        assert DeviceFrameType.IPHONE == 'iphone'


class TestDeviceFrameLibrary:

    def test_library_url_constant(self):
        assert DEVICE_FRAME_LIBRARY_URL == 'https://library.techsmith.com/Camtasia'

    def test_get_asset_returns_dataclass(self):
        asset = get_device_frame_asset(DeviceFrameType.IPHONE)
        assert isinstance(asset, DeviceFrameAsset)

    def test_asset_image_path_is_none(self):
        asset = get_device_frame_asset(DeviceFrameType.MACBOOK)
        assert asset.image_path is None

    def test_asset_has_valid_display_area(self):
        asset = get_device_frame_asset(DeviceFrameType.IPAD, orientation='landscape')
        x, y, w, h = asset.display_area
        assert 0.0 < x < 1.0
        assert 0.0 < y < 1.0
        assert 0.0 < w <= 1.0
        assert 0.0 < h <= 1.0

    def test_portrait_orientation(self):
        asset = get_device_frame_asset(DeviceFrameType.IPHONE, orientation='portrait')
        assert asset.orientation == 'portrait'
        assert asset.type == DeviceFrameType.IPHONE

    def test_invalid_orientation_raises(self):
        with pytest.raises(ValueError, match='orientation'):
            get_device_frame_asset(DeviceFrameType.BROWSER, orientation='diagonal')

    @pytest.mark.parametrize('frame_type', list(DeviceFrameType))
    def test_all_types_have_landscape_asset(self, frame_type):
        asset = get_device_frame_asset(frame_type, orientation='landscape')
        assert asset.type == frame_type
        assert len(asset.display_area) == 4

    @pytest.mark.parametrize('frame_type', list(DeviceFrameType))
    def test_all_types_have_portrait_asset(self, frame_type):
        asset = get_device_frame_asset(frame_type, orientation='portrait')
        assert asset.type == frame_type
        assert asset.orientation == 'portrait'

    def test_asset_is_frozen(self):
        asset = get_device_frame_asset(DeviceFrameType.TV)
        with pytest.raises(AttributeError):
            asset.image_path = '/some/path'  # type: ignore[misc]


class TestAddDeviceFrameWithType:

    def test_frame_type_param_accepted(self, proj_with_clip, tmp_path):
        proj, clip = proj_with_clip
        frame = tmp_path / 'iphone.png'
        frame.write_bytes(b'\x89PNG\r\n\x1a\n')
        result = add_device_frame(
            proj, frame, clip, frame_type=DeviceFrameType.IPHONE,
        )
        assert result.clip_type == 'IMFile'

    def test_orientation_param_accepted(self, proj_with_clip, tmp_path):
        proj, clip = proj_with_clip
        frame = tmp_path / 'ipad.png'
        frame.write_bytes(b'\x89PNG\r\n\x1a\n')
        result = add_device_frame(
            proj, frame, clip, orientation='portrait',
        )
        assert result.start == clip.start

    def test_fit_to_canvas(self, proj_with_clip, tmp_path):
        proj, clip = proj_with_clip
        frame = tmp_path / 'macbook.png'
        frame.write_bytes(b'\x89PNG\r\n\x1a\n')
        result = add_device_frame(proj, frame, clip, fit_to_canvas=True)
        canvas_w = proj.width
        canvas_h = proj.height
        expected_scale = (canvas_w / 1920, canvas_h / 1080)
        assert result.scale == expected_scale


class TestAddDeviceFrameEffect:

    def test_attaches_effect_to_clip(self, proj_with_clip):
        _proj, clip = proj_with_clip
        effect = add_device_frame_effect(clip, DeviceFrameType.IPHONE)
        assert effect.name == 'DeviceFrame'

    def test_effect_has_frame_type_param(self, proj_with_clip):
        _proj, clip = proj_with_clip
        add_device_frame_effect(clip, DeviceFrameType.MACBOOK)
        effects = clip.effects
        df_effects = [e for e in effects if e.get('effectName') == 'DeviceFrame']
        assert len(df_effects) == 1
        assert df_effects[0]['parameters']['frame-type']['defaultValue'] == 'macbook'

    def test_effect_category_is_visual(self, proj_with_clip):
        _proj, clip = proj_with_clip
        effect = add_device_frame_effect(clip, DeviceFrameType.BROWSER)
        assert effect.category == 'categoryVisualEffects'

    def test_effect_not_bypassed(self, proj_with_clip):
        _proj, clip = proj_with_clip
        effect = add_device_frame_effect(clip, DeviceFrameType.TV)
        assert not effect.bypassed

    def test_multiple_effects_allowed(self, proj_with_clip):
        _proj, clip = proj_with_clip
        add_device_frame_effect(clip, DeviceFrameType.IPHONE)
        add_device_frame_effect(clip, DeviceFrameType.IPAD)
        df_effects = [e for e in clip.effects if e.get('effectName') == 'DeviceFrame']
        assert len(df_effects) == 2

    def test_effect_removable_by_name(self, proj_with_clip):
        _proj, clip = proj_with_clip
        add_device_frame_effect(clip, DeviceFrameType.WATCH)
        removed = clip.remove_effect_by_name('DeviceFrame')
        assert removed == 1
        assert not clip.is_effect_applied('DeviceFrame')
