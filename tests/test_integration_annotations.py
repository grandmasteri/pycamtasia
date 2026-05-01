"""Integration tests for non-callout annotations.

Covers: countdowns, end cards, chapter markers, freeze frames,
exported frames, audio visualizers, and stacked annotations.
"""
from __future__ import annotations

from pathlib import Path
import struct
import zlib

import pytest

from tests.integration_helpers import CAMTASIA_APP, INTEGRATION_MARKERS, open_in_camtasia

FIXTURES = Path(__file__).parent / 'fixtures'
EMPTY_WAV = FIXTURES / 'empty.wav'

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


class TestCountdown:
    def test_default_countdown_opens(self, project):
        """Default 3-2-1 countdown opens without exceptions."""
        clips = project.add_countdown()
        assert len(clips) == 3
        open_in_camtasia(project)

    def test_countdown_custom_duration(self, project):
        """Countdown with 5 seconds and slower pace opens."""
        clips = project.add_countdown(seconds=5, per_number_seconds=1.5)
        assert len(clips) == 5
        open_in_camtasia(project)

    def test_countdown_single_second(self, project):
        """Minimal 1-second countdown opens."""
        clips = project.add_countdown(seconds=1)
        assert len(clips) == 1
        open_in_camtasia(project)


class TestEndCard:
    def test_default_end_card_opens(self, project):
        """Default end card opens without exceptions."""
        # Need content so end card appears after something
        media = project.import_media(EMPTY_WAV)
        track = project.timeline.add_track('Audio')
        track.add_audio(media.id, start_seconds=0.0, duration_seconds=3.0)
        project.add_end_card()
        open_in_camtasia(project)

    def test_end_card_with_subtitle(self, project):
        """End card with title and subtitle opens."""
        media = project.import_media(EMPTY_WAV)
        track = project.timeline.add_track('Audio')
        track.add_audio(media.id, start_seconds=0.0, duration_seconds=3.0)
        project.add_end_card(
            title_text='Thanks for Watching',
            subtitle_text='Subscribe for more',
            duration_seconds=8.0,
            fade_seconds=2.0,
        )
        open_in_camtasia(project)


class TestChapterMarkers:
    def test_single_chapter_marker(self, project):
        """Single chapter marker opens."""
        media = project.import_media(EMPTY_WAV)
        track = project.timeline.add_track('Audio')
        track.add_audio(media.id, start_seconds=0.0, duration_seconds=10.0)
        count = project.add_chapter_markers([(2.0, 'Introduction')])
        assert count == 1
        open_in_camtasia(project)

    def test_multiple_chapter_markers(self, project):
        """Multiple chapter markers at various positions open."""
        media = project.import_media(EMPTY_WAV)
        track = project.timeline.add_track('Audio')
        track.add_audio(media.id, start_seconds=0.0, duration_seconds=30.0)
        chapters = [
            (0.0, 'Intro'),
            (5.0, 'Setup'),
            (10.0, 'Demo'),
            (20.0, 'Conclusion'),
            (28.0, 'Outro'),
        ]
        count = project.add_chapter_markers(chapters)
        assert count == 5
        open_in_camtasia(project)


class TestFreezeFrame:
    def test_freeze_frame_opens(self, tmp_path, project):
        """Freeze frame from an image clip opens."""
        img = _create_test_image(tmp_path)
        media = project.import_media(img)
        track = project.timeline.add_track('Content')
        clip = track.add_image(media.id, start_seconds=0.0, duration_seconds=5.0)
        track.add_freeze_frame(clip, at_seconds=2.0, freeze_duration_seconds=3.0)
        # Trim source clip to end at freeze start so clips don't overlap
        track.trim_clip(clip.id, trim_end_seconds=3.0)
        open_in_camtasia(project)


class TestExportedFrame:
    def test_exported_frame_opens(self, tmp_path, project):
        """Exported frame placeholder opens."""
        img = _create_test_image(tmp_path)
        media = project.import_media(img)
        track = project.timeline.add_track('Content')
        clip = track.add_image(media.id, start_seconds=0.0, duration_seconds=2.0)
        track.add_exported_frame(clip.id, at_seconds=2.0)
        open_in_camtasia(project)


class TestAudioVisualizer:
    def test_audio_visualizer_opens(self, project):
        """Audio clip with visualizer opens."""
        media = project.import_media(EMPTY_WAV)
        track = project.timeline.add_track('Audio')
        clip = track.add_audio(media.id, start_seconds=0.0, duration_seconds=5.0)
        clip.add_audio_visualizer(type='bars', sensitivity=0.8)
        open_in_camtasia(project)


class TestStackedAnnotations:
    def test_multiple_annotations_on_timeline(self, tmp_path, project):
        """Countdown + content + end card + chapters all coexist."""
        img = _create_test_image(tmp_path)
        media = project.import_media(img)
        # Countdown at start
        project.add_countdown(seconds=3)
        # Content track
        track = project.timeline.add_track('Content')
        track.add_image(media.id, start_seconds=3.0, duration_seconds=10.0)
        # Chapter markers
        project.add_chapter_markers([
            (3.0, 'Start'),
            (8.0, 'Middle'),
        ])
        # End card
        project.add_end_card(title_text='Done', duration_seconds=4.0)
        open_in_camtasia(project)
