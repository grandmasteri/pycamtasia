"""Tests for video production pipeline features:

- Track.add_freeze_frame
- Project.add_voiceover_sequence_v2
- Project.add_image_sequence
"""
from __future__ import annotations

import struct
from pathlib import Path

import pytest

from camtasia.project import load_project
from camtasia.timing import seconds_to_ticks, ticks_to_seconds

RESOURCES = Path(__file__).parent.parent / 'src' / 'camtasia' / 'resources'
FIXTURES = Path(__file__).parent / 'fixtures'
EMPTY_WAV = FIXTURES / 'empty.wav'
EMPTY2_WAV = FIXTURES / 'empty2.wav'



def _isolated_project():
    """Load template into an isolated temp copy (safe for parallel execution)."""
    import shutil, tempfile
    from camtasia.project import load_project
    tmp = tempfile.mkdtemp()
    dst = Path(tmp) / 'test.cmproj'
    shutil.copytree(RESOURCES / 'new.cmproj', dst)
    return load_project(dst)

def _make_project():
    return _isolated_project()


def _make_minimal_png(path: Path) -> None:
    """Write a valid 1x1 white PNG file."""
    import zlib
    signature = b'\x89PNG\r\n\x1a\n'
    # IHDR: 1x1, 8-bit RGB
    ihdr_data = struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0)
    ihdr = _png_chunk(b'IHDR', ihdr_data)
    # IDAT: single row, filter byte 0, white pixel (255,255,255)
    raw_row = b'\x00\xff\xff\xff'
    idat = _png_chunk(b'IDAT', zlib.compress(raw_row))
    iend = _png_chunk(b'IEND', b'')
    path.write_bytes(signature + ihdr + idat + iend)


def _png_chunk(chunk_type: bytes, data: bytes) -> bytes:
    import zlib
    length = struct.pack('>I', len(data))
    crc = struct.pack('>I', zlib.crc32(chunk_type + data) & 0xFFFFFFFF)
    return length + chunk_type + data + crc


# ── Track.add_freeze_frame ──────────────────────────────────────────


class TestAddFreezeFrame:
    def test_creates_imfile_clip(self):
        proj = _make_project()
        track = proj.timeline.get_or_create_track('Video')
        source_clip = track.add_clip('VMFile', 1, seconds_to_ticks(0), seconds_to_ticks(10))
        freeze = track.add_freeze_frame(source_clip, at_seconds=5.0, freeze_duration_seconds=2.0)
        assert freeze.clip_type == 'IMFile'

    def test_freeze_start_position(self):
        proj = _make_project()
        track = proj.timeline.get_or_create_track('Video')
        source_clip = track.add_clip('VMFile', 1, seconds_to_ticks(0), seconds_to_ticks(10))
        freeze = track.add_freeze_frame(source_clip, at_seconds=3.0, freeze_duration_seconds=1.0)
        assert freeze.start == seconds_to_ticks(3.0)

    def test_freeze_duration(self):
        proj = _make_project()
        track = proj.timeline.get_or_create_track('Video')
        source_clip = track.add_clip('VMFile', 1, seconds_to_ticks(0), seconds_to_ticks(10))
        freeze = track.add_freeze_frame(source_clip, at_seconds=5.0, freeze_duration_seconds=3.0)
        assert freeze.duration == seconds_to_ticks(3.0)

    def test_freeze_uses_source_id(self):
        proj = _make_project()
        track = proj.timeline.get_or_create_track('Video')
        source_clip = track.add_clip('VMFile', 42, seconds_to_ticks(0), seconds_to_ticks(10))
        freeze = track.add_freeze_frame(source_clip, at_seconds=2.0, freeze_duration_seconds=1.0)
        assert freeze.source_id == 42

    def test_freeze_media_start_offset(self):
        proj = _make_project()
        track = proj.timeline.get_or_create_track('Video')
        # Source clip starts at 2s on the timeline
        source_clip = track.add_clip('VMFile', 1, seconds_to_ticks(2.0), seconds_to_ticks(10))
        # Freeze at 5s means 3s into the source
        freeze = track.add_freeze_frame(source_clip, at_seconds=5.0, freeze_duration_seconds=1.0)
        expected_media_start: int = seconds_to_ticks(3.0)
        assert freeze._data['mediaStart'] == expected_media_start

    def test_freeze_adds_to_track_clip_count(self):
        proj = _make_project()
        track = proj.timeline.get_or_create_track('Video')
        source_clip = track.add_clip('VMFile', 1, seconds_to_ticks(0), seconds_to_ticks(10))
        initial_count: int = len(track)
        track.add_freeze_frame(source_clip, at_seconds=5.0, freeze_duration_seconds=2.0)
        assert len(track) == initial_count + 1


# ── Project.add_voiceover_sequence_v2 ───────────────────────────────


class TestAddVoiceoverSequenceV2:
    def test_single_audio_file(self):
        proj = _make_project()
        placed_clips = proj.add_voiceover_sequence_v2([EMPTY_WAV])
        assert len(placed_clips) == 1
        assert placed_clips[0].clip_type == 'AMFile'

    def test_multiple_audio_files(self):
        proj = _make_project()
        placed_clips = proj.add_voiceover_sequence_v2([EMPTY_WAV, EMPTY2_WAV])
        assert len(placed_clips) == 2

    def test_clips_are_sequential(self):
        proj = _make_project()
        placed_clips = proj.add_voiceover_sequence_v2([EMPTY_WAV, EMPTY2_WAV])
        first_end: float = placed_clips[0].start_seconds + placed_clips[0].duration_seconds
        second_start: float = placed_clips[1].start_seconds
        assert abs(second_start - first_end) < 0.01

    def test_custom_start_seconds(self):
        proj = _make_project()
        placed_clips = proj.add_voiceover_sequence_v2([EMPTY_WAV], start_seconds=10.0)
        assert abs(placed_clips[0].start_seconds - 10.0) < 0.01

    def test_gap_between_clips(self):
        proj = _make_project()
        placed_clips = proj.add_voiceover_sequence_v2(
            [EMPTY_WAV, EMPTY2_WAV], gap_seconds=2.0,
        )
        first_end: float = placed_clips[0].start_seconds + placed_clips[0].duration_seconds
        second_start: float = placed_clips[1].start_seconds
        assert abs(second_start - first_end - 2.0) < 0.01

    def test_custom_track_name(self):
        proj = _make_project()
        proj.add_voiceover_sequence_v2([EMPTY_WAV], track_name='Narration')
        track = proj.timeline.get_or_create_track('Narration')
        assert len(track) == 1

    def test_empty_list_returns_empty(self):
        proj = _make_project()
        placed_clips = proj.add_voiceover_sequence_v2([])
        assert placed_clips == []

    def test_string_paths_accepted(self):
        proj = _make_project()
        placed_clips = proj.add_voiceover_sequence_v2([str(EMPTY_WAV)])
        assert len(placed_clips) == 1


# ── Project.add_image_sequence ──────────────────────────────────────


class TestAddImageSequence:
    @pytest.fixture(autouse=True)
    def _create_test_images(self, tmp_path: Path):
        self.image_a = tmp_path / 'slide_a.png'
        self.image_b = tmp_path / 'slide_b.png'
        _make_minimal_png(self.image_a)
        _make_minimal_png(self.image_b)

    def test_single_image(self):
        proj = _make_project()
        placed_clips = proj.add_image_sequence([self.image_a])
        assert len(placed_clips) == 1
        assert placed_clips[0].clip_type == 'IMFile'

    def test_multiple_images(self):
        proj = _make_project()
        placed_clips = proj.add_image_sequence([self.image_a, self.image_b])
        assert len(placed_clips) == 2

    def test_clips_are_sequential(self):
        proj = _make_project()
        placed_clips = proj.add_image_sequence(
            [self.image_a, self.image_b], per_image_seconds=4.0, fade_seconds=0,
        )
        first_end: float = placed_clips[0].start_seconds + placed_clips[0].duration_seconds
        second_start: float = placed_clips[1].start_seconds
        assert abs(second_start - first_end) < 0.01

    def test_per_image_duration(self):
        proj = _make_project()
        placed_clips = proj.add_image_sequence(
            [self.image_a], per_image_seconds=7.0, fade_seconds=0,
        )
        assert abs(placed_clips[0].duration_seconds - 7.0) < 0.01

    def test_custom_start_seconds(self):
        proj = _make_project()
        placed_clips = proj.add_image_sequence(
            [self.image_a], start_seconds=5.0,
        )
        assert abs(placed_clips[0].start_seconds - 5.0) < 0.01

    def test_custom_track_name(self):
        proj = _make_project()
        proj.add_image_sequence([self.image_a], track_name='Slides')
        track = proj.timeline.get_or_create_track('Slides')
        assert len(track) == 1

    def test_fade_applied_by_default(self):
        proj = _make_project()
        placed_clips = proj.add_image_sequence([self.image_a], fade_seconds=0.5)
        clip_data = placed_clips[0]._data
        # Fade creates opacity keyframes in animationTracks
        anim_tracks = clip_data.get('animationTracks', {})
        has_opacity: bool = any(
            'opacity' in str(v).lower()
            for v in anim_tracks.values()
        ) or 'visual' in anim_tracks
        assert has_opacity or len(anim_tracks) > 0

    def test_no_fade_when_zero(self):
        proj = _make_project()
        placed_clips = proj.add_image_sequence(
            [self.image_a], fade_seconds=0,
        )
        clip_data = placed_clips[0]._data
        anim_tracks = clip_data.get('animationTracks', {})
        # No opacity keyframes should be added
        visual = anim_tracks.get('visual', {})
        opacity_kfs = visual.get('opacity', {}).get('keyframes', []) if isinstance(visual, dict) else []
        assert len(opacity_kfs) == 0

    def test_empty_list_returns_empty(self):
        proj = _make_project()
        placed_clips = proj.add_image_sequence([])
        assert placed_clips == []

    def test_string_paths_accepted(self):
        proj = _make_project()
        placed_clips = proj.add_image_sequence([str(self.image_a)])
        assert len(placed_clips) == 1
