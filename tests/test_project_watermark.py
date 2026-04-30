"""Tests for Project.add_watermark and add_text_watermark."""
from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def watermark_image(tmp_path: Path) -> Path:
    """Create a minimal 1x1 PNG for watermark tests."""
    # Minimal valid PNG (1x1 white pixel)
    import struct
    import zlib
    def _png_chunk(chunk_type: bytes, data: bytes) -> bytes:
        c = chunk_type + data
        return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c) & 0xFFFFFFFF)
    sig = b'\x89PNG\r\n\x1a\n'
    ihdr = _png_chunk(b'IHDR', struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0))
    raw_row = b'\x00\xff\xff\xff'
    idat = _png_chunk(b'IDAT', zlib.compress(raw_row))
    iend = _png_chunk(b'IEND', b'')
    img = tmp_path / 'watermark.png'
    img.write_bytes(sig + ihdr + idat + iend)
    return img


class TestAddWatermark:
    """Tests for the extended add_watermark API."""

    def test_default_params(self, project, watermark_image):
        clip = project.add_watermark(watermark_image)
        assert clip.clip_type == 'IMFile'
        assert clip.opacity == pytest.approx(0.3)
        assert clip.scale == (1.0, 1.0)
        assert clip.translation == (0.0, 0.0)

    def test_custom_scale(self, project, watermark_image):
        clip = project.add_watermark(watermark_image, scale=0.5)
        assert clip.scale == (0.5, 0.5)

    def test_custom_offset(self, project, watermark_image):
        clip = project.add_watermark(watermark_image, x_offset=100.0, y_offset=-50.0)
        assert clip.translation == (100.0, -50.0)

    def test_scale_and_offset_combined(self, project, watermark_image):
        clip = project.add_watermark(
            watermark_image, scale=2.0, x_offset=10.0, y_offset=20.0, opacity=0.1,
        )
        assert clip.scale == (2.0, 2.0)
        assert clip.translation == (10.0, 20.0)
        assert clip.opacity == pytest.approx(0.1)

    def test_position_serialized_in_parameters(self, project, watermark_image):
        clip = project.add_watermark(
            watermark_image, scale=0.75, x_offset=50.0, y_offset=-30.0,
        )
        params = clip._data.get('parameters', {})
        # scale stored as scale0/scale1
        assert params.get('scale0') == 0.75 or (isinstance(params.get('scale0'), dict) and params['scale0']['defaultValue'] == 0.75)
        assert params.get('scale1') == 0.75 or (isinstance(params.get('scale1'), dict) and params['scale1']['defaultValue'] == 0.75)
        # translation stored as translation0/translation1
        assert params.get('translation0') == 50.0 or (isinstance(params.get('translation0'), dict) and params['translation0']['defaultValue'] == 50.0)
        assert params.get('translation1') == -30.0 or (isinstance(params.get('translation1'), dict) and params['translation1']['defaultValue'] == -30.0)

    def test_keyword_only_params(self, project, watermark_image):
        """New params are keyword-only; positional call still works for image_path."""
        clip = project.add_watermark(watermark_image, opacity=0.5)
        assert clip.opacity == pytest.approx(0.5)


class TestAddTextWatermark:
    """Tests for the add_text_watermark method."""

    def test_basic_text_watermark(self, project):
        # Need some duration on the timeline for the watermark to span
        track = project.timeline.get_or_create_track('Content')
        track.add_callout('placeholder', 0.0, 10.0)

        clip = project.add_text_watermark('© 2026 Acme')
        assert clip.clip_type == 'Callout'
        assert clip.text == '© 2026 Acme'
        assert clip.opacity == pytest.approx(0.5)

    def test_text_watermark_custom_font(self, project):
        clip = project.add_text_watermark(
            'DRAFT',
            font_name='Helvetica',
            font_size=72.0,
            font_color=(1.0, 0.0, 0.0, 0.8),
            opacity=0.2,
        )
        assert clip.text == 'DRAFT'
        assert clip.opacity == pytest.approx(0.2)
        font = clip.definition.get('font', {})
        assert font.get('name') == 'Helvetica'
        assert font.get('size') == 72.0

    def test_text_watermark_with_scale_and_offset(self, project):
        clip = project.add_text_watermark(
            'SAMPLE', scale=1.5, x_offset=200.0, y_offset=-100.0,
        )
        assert clip.scale == (1.5, 1.5)
        assert clip.translation == (200.0, -100.0)

    def test_text_watermark_position_serialized(self, project):
        clip = project.add_text_watermark(
            'WM', scale=0.8, x_offset=10.0, y_offset=20.0,
        )
        params = clip._data.get('parameters', {})
        # Verify scale0/scale1 and translation0/translation1 are set
        def _val(key):
            v = params.get(key)
            return v['defaultValue'] if isinstance(v, dict) else v
        assert _val('scale0') == 0.8
        assert _val('scale1') == 0.8
        assert _val('translation0') == 10.0
        assert _val('translation1') == 20.0


class TestVideoProductionBuilderWatermark:
    """Tests for the builder's add_watermark forwarding."""

    def test_builder_forwards_scale_and_offset(self, project, watermark_image):
        from camtasia.builders.video_production import VideoProductionBuilder

        builder = VideoProductionBuilder(project)
        builder.add_watermark(watermark_image, 0.2, scale=0.5, x_offset=30.0, y_offset=-10.0)
        result = builder.build()

        assert result['has_watermark'] is True
        # Find the watermark clip on the Watermark track
        wm_track = project.timeline.find_track_by_name('Watermark')
        assert wm_track is not None
        clips = list(wm_track.clips)
        assert len(clips) == 1
        clip = clips[0]
        assert clip.opacity == pytest.approx(0.2)
        assert clip.scale == (0.5, 0.5)
        assert clip.translation == (30.0, -10.0)
