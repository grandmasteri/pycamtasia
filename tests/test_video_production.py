"""Tests for video production pipeline features:

- Track.add_freeze_frame
- Project.add_voiceover_sequence_v2
- Project.add_image_sequence
"""
from __future__ import annotations

import struct
import zlib
from pathlib import Path

import pytest

from camtasia.timing import seconds_to_ticks, ticks_to_seconds

FIXTURES = Path(__file__).parent / 'fixtures'
EMPTY_WAV = FIXTURES / 'empty.wav'
EMPTY2_WAV = FIXTURES / 'empty2.wav'


def _make_minimal_png(path: Path) -> None:
    """Write a valid 1x1 white PNG file."""
    signature = b'\x89PNG\r\n\x1a\n'
    ihdr_data = struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0)
    ihdr = _png_chunk(b'IHDR', ihdr_data)
    raw_row = b'\x00\xff\xff\xff'
    idat = _png_chunk(b'IDAT', zlib.compress(raw_row))
    iend = _png_chunk(b'IEND', b'')
    path.write_bytes(signature + ihdr + idat + iend)


def _png_chunk(chunk_type: bytes, data: bytes) -> bytes:
    length = struct.pack('>I', len(data))
    crc = struct.pack('>I', zlib.crc32(chunk_type + data) & 0xFFFFFFFF)
    return length + chunk_type + data + crc


# ── Track.add_freeze_frame ──────────────────────────────────────────


class TestAddFreezeFrame:
    def test_creates_imfile_clip(self, project):
        track = project.timeline.get_or_create_track('Video')
        src = track.add_clip('VMFile', 1, seconds_to_ticks(0), seconds_to_ticks(10))
        assert track.add_freeze_frame(src, at_seconds=5.0, freeze_duration_seconds=2.0).clip_type == 'IMFile'

    def test_freeze_start_position(self, project):
        track = project.timeline.get_or_create_track('Video')
        src = track.add_clip('VMFile', 1, seconds_to_ticks(0), seconds_to_ticks(10))
        freeze = track.add_freeze_frame(src, at_seconds=3.0, freeze_duration_seconds=1.0)
        assert freeze.start == seconds_to_ticks(3.0)

    def test_freeze_duration(self, project):
        track = project.timeline.get_or_create_track('Video')
        src = track.add_clip('VMFile', 1, seconds_to_ticks(0), seconds_to_ticks(10))
        freeze = track.add_freeze_frame(src, at_seconds=5.0, freeze_duration_seconds=3.0)
        assert freeze.duration == seconds_to_ticks(3.0)

    def test_freeze_uses_source_id(self, project):
        track = project.timeline.get_or_create_track('Video')
        src = track.add_clip('VMFile', 42, seconds_to_ticks(0), seconds_to_ticks(10))
        assert track.add_freeze_frame(src, at_seconds=2.0, freeze_duration_seconds=1.0).source_id == 42

    def test_freeze_media_start_offset(self, project):
        track = project.timeline.get_or_create_track('Video')
        src = track.add_clip('VMFile', 1, seconds_to_ticks(2.0), seconds_to_ticks(10))
        freeze = track.add_freeze_frame(src, at_seconds=5.0, freeze_duration_seconds=1.0)
        assert freeze._data['mediaStart'] == seconds_to_ticks(3.0)

    def test_freeze_adds_to_track_clip_count(self, project):
        track = project.timeline.get_or_create_track('Video')
        src = track.add_clip('VMFile', 1, seconds_to_ticks(0), seconds_to_ticks(10))
        initial_count = len(track)
        track.add_freeze_frame(src, at_seconds=5.0, freeze_duration_seconds=2.0)
        assert len(track) == initial_count + 1


# ── Project.add_voiceover_sequence_v2 ───────────────────────────────


class TestAddVoiceoverSequenceV2:
    def test_single_audio_file(self, project):
        placed = project.add_voiceover_sequence_v2([EMPTY_WAV])
        assert len(placed) == 1
        assert placed[0].clip_type == 'AMFile'
        assert placed[0].start == 0

    def test_multiple_audio_files(self, project):
        placed = project.add_voiceover_sequence_v2([EMPTY_WAV, EMPTY2_WAV])
        assert len(placed) == 2
        assert all(c.clip_type == 'AMFile' for c in placed)

    def test_clips_are_sequential(self, project):
        placed = project.add_voiceover_sequence_v2([EMPTY_WAV, EMPTY2_WAV])
        first_end = placed[0].start_seconds + placed[0].duration_seconds
        assert abs(placed[1].start_seconds - first_end) < 0.01

    def test_custom_start_seconds(self, project):
        placed = project.add_voiceover_sequence_v2([EMPTY_WAV], start_seconds=10.0)
        assert abs(placed[0].start_seconds - 10.0) < 0.01

    def test_gap_between_clips(self, project):
        placed = project.add_voiceover_sequence_v2([EMPTY_WAV, EMPTY2_WAV], gap_seconds=2.0)
        first_end = placed[0].start_seconds + placed[0].duration_seconds
        assert abs(placed[1].start_seconds - first_end - 2.0) < 0.01

    def test_custom_track_name(self, project):
        project.add_voiceover_sequence_v2([EMPTY_WAV], track_name='Narration')
        assert len(project.timeline.get_or_create_track('Narration')) == 1

    def test_empty_list_returns_empty(self, project):
        assert project.add_voiceover_sequence_v2([]) == []

    def test_string_paths_accepted(self, project):
        placed = project.add_voiceover_sequence_v2([str(EMPTY_WAV)])
        assert len(placed) == 1
        assert placed[0].clip_type == 'AMFile'


# ── Project.add_image_sequence ──────────────────────────────────────


class TestAddImageSequence:
    @pytest.fixture(autouse=True)
    def _create_test_images(self, tmp_path: Path):
        self.image_a = tmp_path / 'slide_a.png'
        self.image_b = tmp_path / 'slide_b.png'
        _make_minimal_png(self.image_a)
        _make_minimal_png(self.image_b)

    def test_single_image(self, project):
        placed = project.add_image_sequence([self.image_a])
        assert len(placed) == 1
        assert placed[0].clip_type == 'IMFile'
        assert placed[0].start_seconds == pytest.approx(0.0, abs=0.01)

    def test_multiple_images(self, project):
        placed = project.add_image_sequence([self.image_a, self.image_b])
        assert len(placed) == 2
        assert all(c.clip_type == 'IMFile' for c in placed)

    def test_clips_are_sequential(self, project):
        placed = project.add_image_sequence(
            [self.image_a, self.image_b], per_image_seconds=4.0, fade_seconds=0)
        first_end = placed[0].start_seconds + placed[0].duration_seconds
        assert abs(placed[1].start_seconds - first_end) < 0.01

    def test_per_image_duration(self, project):
        placed = project.add_image_sequence([self.image_a], per_image_seconds=7.0, fade_seconds=0)
        assert abs(placed[0].duration_seconds - 7.0) < 0.01

    def test_custom_start_seconds(self, project):
        placed = project.add_image_sequence([self.image_a], start_seconds=5.0)
        assert abs(placed[0].start_seconds - 5.0) < 0.01

    def test_custom_track_name(self, project):
        project.add_image_sequence([self.image_a], track_name='Slides')
        assert len(project.timeline.get_or_create_track('Slides')) == 1

    def test_fade_applied_by_default(self, project):
        placed = project.add_image_sequence([self.image_a], fade_seconds=0.5)
        anim = placed[0]._data.get('animationTracks', {})
        assert 'visual' in anim and len(anim.get('visual', [])) > 0

    def test_no_fade_when_zero(self, project):
        placed = project.add_image_sequence([self.image_a], fade_seconds=0)
        anim = placed[0]._data.get('animationTracks', {})
        assert anim.get('visual', []) == []

    def test_empty_list_returns_empty(self, project):
        assert project.add_image_sequence([]) == []

    def test_string_paths_accepted(self, project):
        placed = project.add_image_sequence([str(self.image_a)])
        assert len(placed) == 1
        assert placed[0].clip_type == 'IMFile'
