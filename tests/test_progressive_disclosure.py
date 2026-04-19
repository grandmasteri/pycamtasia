"""Tests for Project.add_progressive_disclosure()."""
from __future__ import annotations

import struct
from typing import TYPE_CHECKING
import zlib

import pytest

if TYPE_CHECKING:
    from pathlib import Path


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


@pytest.fixture
def images(tmp_path: Path) -> list[Path]:
    paths = [tmp_path / f'step_{i}.png' for i in range(3)]
    for p in paths:
        _make_minimal_png(p)
    return paths


def test_progressive_disclosure_creates_separate_tracks(project, images: list[Path]):
    clips = project.add_progressive_disclosure(images)

    track_names = {t.name for t in project.timeline.tracks}
    assert {'Prog-0', 'Prog-1', 'Prog-2'} <= track_names
    assert all(hasattr(c, 'start_seconds') for c in clips)

    # Each clip lives on a different track
    clip_track_names = set()
    for t in project.timeline.tracks:
        for _c in t:
            clip_track_names.add(t.name)
    assert clip_track_names >= {'Prog-0', 'Prog-1', 'Prog-2'}


def test_progressive_disclosure_images_accumulate(project, images: list[Path]):
    """All previous images remain visible when a new one appears."""
    clips = project.add_progressive_disclosure(
        images, start_seconds=0.0, per_step_seconds=5.0,
    )

    total = 5.0 * 3  # 15 seconds total

    # First image: starts at 0, lasts the full 15s
    assert abs(clips[0].start_seconds - 0.0) < 0.01
    assert abs(clips[0].duration_seconds - total) < 0.01

    # Second image: starts at 5, lasts 10s (visible from 5s to 15s)
    assert abs(clips[1].start_seconds - 5.0) < 0.01
    assert abs(clips[1].duration_seconds - 10.0) < 0.01

    # Third image: starts at 10, lasts 5s (visible from 10s to 15s)
    assert abs(clips[2].start_seconds - 10.0) < 0.01
    assert abs(clips[2].duration_seconds - 5.0) < 0.01

    # At t=12s, all three clips are on screen (accumulation)
    t = 12.0
    visible = [
        c for c in clips
        if c.start_seconds <= t < c.start_seconds + c.duration_seconds
    ]
    visible_starts = sorted(c.start_seconds for c in visible)
    assert abs(visible_starts[0] - 0.0) < 0.01
    assert abs(visible_starts[1] - 5.0) < 0.01
    assert abs(visible_starts[2] - 10.0) < 0.01


def test_progressive_disclosure_timing(project, images: list[Path]):
    clips = project.add_progressive_disclosure(
        images, start_seconds=2.0, per_step_seconds=4.0,
    )

    total = 4.0 * 3  # 12 seconds

    # Clip 0: start=2.0, duration=12.0
    assert abs(clips[0].start_seconds - 2.0) < 0.01
    assert abs(clips[0].duration_seconds - total) < 0.01

    # Clip 1: start=6.0, duration=8.0
    assert abs(clips[1].start_seconds - 6.0) < 0.01
    assert abs(clips[1].duration_seconds - 8.0) < 0.01

    # Clip 2: start=10.0, duration=4.0
    assert abs(clips[2].start_seconds - 10.0) < 0.01
    assert abs(clips[2].duration_seconds - 4.0) < 0.01

    # All clips end at the same time
    end_times = [c.start_seconds + c.duration_seconds for c in clips]
    assert all(abs(e - end_times[0]) < 0.01 for e in end_times)


def test_progressive_disclosure_fade_in(project, images: list[Path]):
    # With fade
    clips = project.add_progressive_disclosure(
        images[:1], fade_in_seconds=0.8,
    )
    clip_data = clips[0]._data
    params = clip_data.get('parameters', {})
    opacity_param = params.get('opacity', {})
    opacity_kfs = opacity_param.get('keyframes', []) if isinstance(opacity_param, dict) else []
    assert opacity_kfs[0].get('value') == 1.0, 'Opacity keyframe should target fully opaque'
    assert opacity_kfs[0].get('duration', 0) == 564480000, 'Opacity keyframe should have a fade duration'


def test_progressive_disclosure_fade_in_disabled(project, images: list[Path]):
    clips = project.add_progressive_disclosure(
        images[:1], fade_in_seconds=0,
    )
    clip_data = clips[0]._data
    params = clip_data.get('parameters', {})
    opacity_param = params.get('opacity', {})
    opacity_kfs = opacity_param.get('keyframes', []) if isinstance(opacity_param, dict) else []
    assert opacity_kfs == [], 'Expected no opacity keyframes when fade_in_seconds=0'


def test_progressive_disclosure_replace_previous_with_fade_out(project, images: list[Path]):
    """Verify replace_previous fade-out creates all clips."""
    clips = project.add_progressive_disclosure(
        images, fade_out_seconds=0.5, replace_previous=True,
    )
    assert [hasattr(c, 'start_seconds') for c in clips] == [True, True, True]


def test_progressive_disclosure_fade_out_without_replace(project, images: list[Path]):
    """Verify fade-out without replace_previous creates all clips."""
    clips = project.add_progressive_disclosure(
        images, fade_out_seconds=0.5, replace_previous=False,
    )
    assert [hasattr(c, 'start_seconds') for c in clips] == [True, True, True]
