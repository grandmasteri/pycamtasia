"""Feature-specific Camtasia integration tests.

Each test creates a minimal project, applies ONE operation, saves,
launches Camtasia, and checks stderr for 0 EXCEPTION lines.

Run with: pytest -m integration
"""
from __future__ import annotations

import shutil
import subprocess
import time
from pathlib import Path

import pytest

from camtasia import load_project, new_project, seconds_to_ticks

CAMTASIA_APP = Path('/Applications/Camtasia.app')
CAMTASIA_BIN = CAMTASIA_APP / 'Contents/MacOS/Camtasia'
FIXTURES = Path(__file__).parent / 'fixtures'
EMPTY_WAV = FIXTURES / 'empty.wav'

pytestmark = [
    pytest.mark.skipif(not CAMTASIA_APP.exists(), reason='Camtasia not installed'),
    pytest.mark.integration,
    pytest.mark.timeout(30),  # Integration tests need 15s+ for Camtasia launch
]


def _validate_in_camtasia(project_path: str, timeout: int = 15) -> int:
    """Launch Camtasia, wait, count EXCEPTION lines in stderr."""
    subprocess.run(['pkill', '-f', 'Camtasia'], capture_output=True)
    time.sleep(2)

    lock = Path(project_path) / '~project.tscproj'
    lock.unlink(missing_ok=True)

    log = Path('/tmp/cam_integration_test.log')
    with log.open('w') as log_fh:
        proc = subprocess.Popen(
            [str(CAMTASIA_BIN), project_path],
            stderr=log_fh,
            stdout=subprocess.DEVNULL,
        )
    time.sleep(timeout)
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()

    return log.read_text().count('EXCEPTION') if log.exists() else 0


def _create_test_image(tmp_path: Path) -> Path:
    """Create a minimal 1x1 white PNG."""
    import struct, zlib
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


def _make_project(tmp_path: Path) -> 'Project':
    """Create a fresh project in tmp_path and return it loaded."""
    dst = tmp_path / 'test.cmproj'
    new_project(dst)
    return load_project(dst)


class TestBasicOperations:
    def test_empty_project_opens(self, tmp_path):
        """A fresh project saved by pycamtasia opens without exceptions."""
        proj = _make_project(tmp_path)
        proj.save()
        assert _validate_in_camtasia(str(tmp_path / 'test.cmproj')) == 0

    def test_add_audio_clip_opens(self, tmp_path):
        """Project with an audio clip opens without exceptions."""
        proj = _make_project(tmp_path)
        media = proj.import_media(EMPTY_WAV)
        track = proj.timeline.add_track('Audio')
        track.add_audio(media.id, start_seconds=0.0, duration_seconds=2.0)
        proj.save()
        assert _validate_in_camtasia(str(tmp_path / 'test.cmproj')) == 0

    def test_add_image_clip_opens(self, tmp_path):
        """Project with an image clip opens without exceptions."""
        proj = _make_project(tmp_path)
        img = _create_test_image(tmp_path)
        media = proj.import_media(img)
        track = proj.timeline.add_track('Content')
        track.add_clip('IMFile', media.id, 0, seconds_to_ticks(5))
        proj.save()
        assert _validate_in_camtasia(str(tmp_path / 'test.cmproj')) == 0

    def test_add_and_remove_clip_opens(self, tmp_path):
        """Project after add+remove cycle opens without exceptions."""
        proj = _make_project(tmp_path)
        track = proj.timeline.add_track('Test')
        clip = track.add_clip('AMFile', None, 0, seconds_to_ticks(5))
        track.remove_clip(clip.id)
        proj.save()
        assert _validate_in_camtasia(str(tmp_path / 'test.cmproj')) == 0

    def test_add_transition_opens(self, tmp_path):
        """Project with a transition opens without exceptions."""
        proj = _make_project(tmp_path)
        media = proj.import_media(EMPTY_WAV)
        track = proj.timeline.add_track('Audio')
        c1 = track.add_audio(media.id, start_seconds=0.0, duration_seconds=2.0)
        c2 = track.add_audio(media.id, start_seconds=2.0, duration_seconds=2.0)
        track.transitions.add_fade_through_black(
            c1.id, c2.id, seconds_to_ticks(0.5),
        )
        proj.save()
        assert _validate_in_camtasia(str(tmp_path / 'test.cmproj')) == 0

    def test_add_effect_opens(self, tmp_path):
        """Project with visual effects opens without exceptions."""
        proj = _make_project(tmp_path)
        img = _create_test_image(tmp_path)
        media = proj.import_media(img)
        track = proj.timeline.add_track('Content')
        clip = track.add_clip('IMFile', media.id, 0, seconds_to_ticks(5))
        clip.add_drop_shadow()
        clip.add_round_corners(radius=16.0)
        proj.save()
        assert _validate_in_camtasia(str(tmp_path / 'test.cmproj')) == 0


class TestEffectsAndAnnotations:
    @pytest.mark.integration
    def test_color_adjustment_opens(self, tmp_path):
        proj = _make_project(tmp_path)
        img = _create_test_image(tmp_path)
        media = proj.import_media(img)
        track = proj.timeline.add_track('Content')
        clip = track.add_clip('IMFile', media.id, 0, seconds_to_ticks(5))
        clip.add_color_adjustment(brightness=0.1, contrast=0.2)
        proj.save()
        assert _validate_in_camtasia(str(tmp_path / 'test.cmproj')) == 0

    @pytest.mark.integration
    def test_border_effect_opens(self, tmp_path):
        proj = _make_project(tmp_path)
        img = _create_test_image(tmp_path)
        media = proj.import_media(img)
        track = proj.timeline.add_track('Content')
        clip = track.add_clip('IMFile', media.id, 0, seconds_to_ticks(5))
        clip.add_border(width=4.0, color=(1.0, 0.0, 0.0, 1.0))
        proj.save()
        assert _validate_in_camtasia(str(tmp_path / 'test.cmproj')) == 0

    @pytest.mark.integration
    def test_callout_with_behavior_opens(self, tmp_path):
        proj = _make_project(tmp_path)
        track = proj.timeline.add_track('Callouts')
        callout = track.add_callout('Hello World', start_seconds=0.0, duration_seconds=5.0)
        callout.add_behavior('Reveal')
        proj.save()
        assert _validate_in_camtasia(str(tmp_path / 'test.cmproj')) == 0

    @pytest.mark.integration
    def test_lower_third_opens(self, tmp_path):
        proj = _make_project(tmp_path)
        track = proj.timeline.add_track('Titles')
        track.add_lower_third('Speaker Name', 'Title goes here', start_seconds=0.0, duration_seconds=5.0)
        proj.save()
        assert _validate_in_camtasia(str(tmp_path / 'test.cmproj')) == 0

    @pytest.mark.integration
    def test_multiple_tracks_opens(self, tmp_path):
        proj = _make_project(tmp_path)
        img = _create_test_image(tmp_path)
        media = proj.import_media(img)
        for i in range(5):
            track = proj.timeline.add_track(f'Track {i}')
            track.add_clip('IMFile', media.id, 0, seconds_to_ticks(5))
        proj.save()
        assert _validate_in_camtasia(str(tmp_path / 'test.cmproj')) == 0


class TestNewEffects:
    @pytest.mark.integration
    def test_colorize_effect_opens(self, tmp_path):
        proj = _make_project(tmp_path)
        img = _create_test_image(tmp_path)
        media = proj.import_media(img)
        track = proj.timeline.add_track('Content')
        clip = track.add_clip('IMFile', media.id, 0, seconds_to_ticks(5))
        clip.add_colorize(color=(0.2, 0.4, 0.8), intensity=0.5)
        proj.save()
        assert _validate_in_camtasia(str(tmp_path / 'test.cmproj')) == 0

    @pytest.mark.integration
    def test_spotlight_effect_opens(self, tmp_path):
        proj = _make_project(tmp_path)
        img = _create_test_image(tmp_path)
        media = proj.import_media(img)
        track = proj.timeline.add_track('Content')
        clip = track.add_clip('IMFile', media.id, 0, seconds_to_ticks(5))
        clip.add_spotlight(dim_opacity=0.7)
        proj.save()
        assert _validate_in_camtasia(str(tmp_path / 'test.cmproj')) == 0

    @pytest.mark.integration
    def test_multiple_effects_opens(self, tmp_path):
        proj = _make_project(tmp_path)
        img = _create_test_image(tmp_path)
        media = proj.import_media(img)
        track = proj.timeline.add_track('Content')
        clip = track.add_clip('IMFile', media.id, 0, seconds_to_ticks(5))
        clip.add_drop_shadow()
        clip.add_round_corners(radius=16.0)
        clip.add_color_adjustment(brightness=0.1, contrast=0.2)
        proj.save()
        assert _validate_in_camtasia(str(tmp_path / 'test.cmproj')) == 0

    @pytest.mark.integration
    def test_dissolve_transition_opens(self, tmp_path):
        proj = _make_project(tmp_path)
        media = proj.import_media(EMPTY_WAV)
        track = proj.timeline.add_track('Audio')
        c1 = track.add_audio(media.id, start_seconds=0.0, duration_seconds=2.0)
        c2 = track.add_audio(media.id, start_seconds=2.0, duration_seconds=2.0)
        track.transitions.add_dissolve(c1.id, c2.id, seconds_to_ticks(0.5))
        proj.save()
        assert _validate_in_camtasia(str(tmp_path / 'test.cmproj')) == 0


class TestAdvancedOperations:
    @pytest.mark.integration
    @pytest.mark.xfail(reason="split_clip after transition needs investigation")
    def test_split_and_transition_opens(self, tmp_path):
        """Project with split clip and transition opens without exceptions."""
        proj = _make_project(tmp_path)
        media = proj.import_media(EMPTY_WAV)
        track = proj.timeline.add_track('Audio')
        c1 = track.add_audio(media.id, start_seconds=0.0, duration_seconds=4.0)
        c2 = track.add_audio(media.id, start_seconds=4.0, duration_seconds=4.0)
        track.transitions.add_fade_through_black(c1.id, c2.id, seconds_to_ticks(0.5))
        _left, _right = track.split_clip(c1.id, split_at_seconds=2.0)
        proj.save()
        assert _validate_in_camtasia(str(tmp_path / 'test.cmproj')) == 0

    @pytest.mark.integration
    def test_media_matte_opens(self, tmp_path):
        """Project with media matte effect opens without exceptions."""
        proj = _make_project(tmp_path)
        img = _create_test_image(tmp_path)
        media = proj.import_media(img)
        matte_track = proj.timeline.add_track('Matte')
        matte_track.add_image(media.id, start_seconds=0.0, duration_seconds=5.0)
        content_track = proj.timeline.add_track('Content')
        clip = content_track.add_image(media.id, start_seconds=0.0, duration_seconds=5.0)
        clip.add_media_matte()
        proj.save()
        assert _validate_in_camtasia(str(tmp_path / 'test.cmproj')) == 0

    @pytest.mark.integration
    def test_title_card_opens(self, tmp_path):
        """Project with styled lower third title opens without exceptions."""
        proj = _make_project(tmp_path)
        track = proj.timeline.add_track('Titles')
        track.add_lower_third(
            'Presenter Name', 'Senior Engineer',
            start_seconds=0.0, duration_seconds=5.0,
            font_weight=700, scale=1.2,
        )
        proj.save()
        assert _validate_in_camtasia(str(tmp_path / 'test.cmproj')) == 0