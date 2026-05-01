"""Integration tests for pycamtasia visual and audio effects.

Each test creates a minimal project, applies ONE effect (or a specific
combination), saves, and opens in Camtasia via the validator-contract helper.

Run with: pytest -m integration tests/test_integration_effects.py
"""
from __future__ import annotations

import struct
import zlib
from pathlib import Path

import pytest

from camtasia import seconds_to_ticks
from camtasia.types import BlendMode, MatteMode

from tests.integration_helpers import INTEGRATION_MARKERS, open_in_camtasia

FIXTURES = Path(__file__).parent / 'fixtures'

pytestmark = INTEGRATION_MARKERS


def _create_test_image(tmp_path: Path) -> Path:
    """Create a minimal 1x1 white PNG."""
    def _chunk(chunk_type, data):
        c = chunk_type + data
        return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c) & 0xffffffff)
    sig = b'\x89PNG\r\n\x1a\n'
    ihdr = _chunk(b'IHDR', struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0))
    idat = _chunk(b'IDAT', zlib.compress(b'\x00\xff\xff\xff'))
    iend = _chunk(b'IEND', b'')
    path = tmp_path / 'test_image.png'
    path.write_bytes(sig + ihdr + idat + iend)
    return path


def _image_clip(project, tmp_path):
    """Helper: import a test image and place it on a track, return the clip."""
    img = _create_test_image(tmp_path)
    media = project.import_media(img)
    track = project.timeline.add_track('Content')
    return track.add_image(media.id, start_seconds=0.0, duration_seconds=5.0)


class TestColorAdjustmentEffects:
    def test_brightness_contrast_opens(self, project, tmp_path):
        clip = _image_clip(project, tmp_path)
        clip.add_color_adjustment(brightness=0.5, contrast=-0.3)
        open_in_camtasia(project)

    def test_saturation_opens(self, project, tmp_path):
        clip = _image_clip(project, tmp_path)
        clip.add_color_adjustment(saturation=2.5)
        open_in_camtasia(project)


class TestDropShadowEffects:
    def test_drop_shadow_default_opens(self, project, tmp_path):
        clip = _image_clip(project, tmp_path)
        clip.add_drop_shadow()
        open_in_camtasia(project)

    def test_drop_shadow_custom_opens(self, project, tmp_path):
        clip = _image_clip(project, tmp_path)
        clip.add_drop_shadow(offset=12, blur=20, opacity=0.8, color=(0.2, 0.0, 0.5))
        open_in_camtasia(project)


class TestGlowEffects:
    def test_glow_opens(self, project, tmp_path):
        clip = _image_clip(project, tmp_path)
        clip.add_glow(radius=50.0, intensity=0.7)
        open_in_camtasia(project)

    def test_glow_timed_opens(self, project, tmp_path):
        clip = _image_clip(project, tmp_path)
        clip.add_glow_timed(
            start_seconds=1.0, duration_seconds=2.0,
            radius=40.0, intensity=0.5,
            fade_in_seconds=0.3, fade_out_seconds=0.6,
        )
        open_in_camtasia(project)


class TestBorderEffect:
    def test_border_red_opens(self, project, tmp_path):
        clip = _image_clip(project, tmp_path)
        clip.add_border(width=8.0, color=(1.0, 0.0, 0.0, 1.0), corner_radius=4.0)
        open_in_camtasia(project)


class TestColorizeEffect:
    def test_colorize_opens(self, project, tmp_path):
        clip = _image_clip(project, tmp_path)
        clip.add_colorize(color=(0.1, 0.6, 0.9), intensity=0.8)
        open_in_camtasia(project)


class TestSpotlightEffect:
    def test_spotlight_opens(self, project, tmp_path):
        clip = _image_clip(project, tmp_path)
        clip.add_spotlight(brightness=0.7, concentration=0.6, opacity=0.5)
        open_in_camtasia(project)


class TestBlendModeEffect:
    def test_blend_mode_multiply_opens(self, project, tmp_path):
        clip = _image_clip(project, tmp_path)
        clip.add_blend_mode(mode=BlendMode.MULTIPLY, intensity=0.9)
        open_in_camtasia(project)

    def test_blend_mode_normal_opens(self, project, tmp_path):
        clip = _image_clip(project, tmp_path)
        clip.add_blend_mode(mode=BlendMode.NORMAL, intensity=0.5)
        open_in_camtasia(project)


class TestMediaMatteEffect:
    def test_media_matte_alpha_opens(self, project, tmp_path):
        img = _create_test_image(tmp_path)
        media = project.import_media(img)
        matte_track = project.timeline.add_track('Matte')
        matte_track.add_image(media.id, start_seconds=0.0, duration_seconds=5.0)
        content_track = project.timeline.add_track('Content')
        clip = content_track.add_image(media.id, start_seconds=0.0, duration_seconds=5.0)
        clip.add_media_matte(matte_mode=MatteMode.ALPHA)
        open_in_camtasia(project)

    def test_media_matte_luminosity_opens(self, project, tmp_path):
        img = _create_test_image(tmp_path)
        media = project.import_media(img)
        matte_track = project.timeline.add_track('Matte')
        matte_track.add_image(media.id, start_seconds=0.0, duration_seconds=5.0)
        content_track = project.timeline.add_track('Content')
        clip = content_track.add_image(media.id, start_seconds=0.0, duration_seconds=5.0)
        clip.add_media_matte(matte_mode=MatteMode.LUMINOSITY, intensity=0.7)
        open_in_camtasia(project)


class TestEmphasizeEffect:
    def test_emphasize_opens(self, project):
        media = project.import_media(FIXTURES / 'empty.wav')
        track = project.timeline.add_track('Audio')
        clip = track.add_audio(media.id, start_seconds=0.0, duration_seconds=2.0)
        clip.add_emphasize(ramp_position='inside', intensity=0.6, ramp_in_seconds=0.2, ramp_out_seconds=0.3)
        open_in_camtasia(project)


class TestGradientBackground:
    def test_gradient_background_opens(self, project):
        project.timeline.add_track('Background')
        project.add_gradient_background(
            duration_seconds=5.0,
            color0=(0.2, 0.0, 0.4, 1.0),
            color1=(0.0, 0.0, 0.1, 1.0),
        )
        open_in_camtasia(project)


class TestMultipleEffectsStacked:
    def test_stacked_effects_opens(self, project, tmp_path):
        clip = _image_clip(project, tmp_path)
        clip.add_drop_shadow(offset=8, blur=12, opacity=0.6)
        clip.add_color_adjustment(brightness=0.2, saturation=1.5)
        clip.add_border(width=3.0, color=(0.0, 0.5, 1.0, 1.0))
        clip.add_glow(radius=20.0, intensity=0.3)
        open_in_camtasia(project)
