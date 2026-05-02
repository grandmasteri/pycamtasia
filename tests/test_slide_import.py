"""Tests for builders.slide_import.import_slide_images."""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from camtasia import Project
from camtasia.builders import import_slide_images


@pytest.fixture
def mock_pymediainfo(monkeypatch):
    import sys
    mock_mi = MagicMock()
    mock_mi.MediaInfo.parse.return_value = SimpleNamespace(tracks=[
        SimpleNamespace(track_type='Image', width=1920, height=1080),
    ])
    monkeypatch.setitem(sys.modules, 'pymediainfo', mock_mi)
    return mock_mi


@pytest.fixture
def proj_and_slides(tmp_path, mock_pymediainfo):
    tmp = tmp_path / 'test.cmproj'
    proj = Project.new(str(tmp))
    slides = []
    for i in range(3):
        p = tmp_path / f'slide_{i}.png'
        p.write_bytes(b'\x89PNG\r\n\x1a\n')
        slides.append(p)
    return proj, slides


def test_import_slide_images_places_clips_in_order(proj_and_slides):
    proj, slides = proj_and_slides
    placed = import_slide_images(proj, slides, per_slide_seconds=3.0)
    assert len(placed) == 3
    # Each clip should be 3s long
    starts_seconds = [c.start / 705600000 for c in placed]
    assert starts_seconds == [0.0, 3.0, 6.0]


def test_import_slide_images_custom_track(proj_and_slides):
    proj, slides = proj_and_slides
    import_slide_images(proj, slides, track_name='Deck')
    assert proj.timeline.find_track_by_name('Deck') is not None


def test_import_slide_images_with_transitions_overlaps_and_fades(proj_and_slides):
    proj, slides = proj_and_slides
    placed = import_slide_images(
        proj, slides, per_slide_seconds=3.0, transition_seconds=0.5,
    )
    # With 0.5s transition, cursor advances by 2.5s each step
    starts = [c.start / 705600000 for c in placed]
    assert starts == [0.0, 2.5, 5.0]
    # First clip has fade_out but no fade_in; last has fade_in but no fade_out
    assert placed[0]._data['parameters'].get('opacity') is not None  # fade applied
