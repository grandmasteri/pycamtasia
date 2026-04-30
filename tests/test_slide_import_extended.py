"""Tests for extended slide import: import_powerpoint, slide_titles, emit_markers, append."""
from __future__ import annotations

import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from camtasia import Project
from camtasia.builders.slide_import import (
    _extract_slides_as_images,
    import_powerpoint,
    import_slide_images,
)
from camtasia.timing import EDIT_RATE


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
    tmp = Path(tempfile.mkdtemp()) / 'test.cmproj'
    proj = Project.new(str(tmp))
    slides = []
    for i in range(3):
        p = tmp_path / f'slide_{i}.png'
        p.write_bytes(b'\x89PNG\r\n\x1a\n')
        slides.append(p)
    return proj, slides


class TestImportSlideImagesWithTitles:
    """Tests for slide_titles parameter on import_slide_images."""

    def test_emit_markers_with_titles(self, proj_and_slides):
        proj, slides = proj_and_slides
        titles = ['Intro', 'Body', 'Conclusion']
        import_slide_images(
            proj, slides,
            per_slide_seconds=4.0,
            slide_titles=titles,
            emit_markers=True,
        )
        markers = list(proj.timeline.markers)
        assert [(m.name, m.time) for m in markers] == [
            ('Intro', 0),
            ('Body', EDIT_RATE * 4),
            ('Conclusion', EDIT_RATE * 8),
        ]

    def test_emit_markers_without_titles_uses_defaults(self, proj_and_slides):
        proj, slides = proj_and_slides
        import_slide_images(
            proj, slides,
            per_slide_seconds=5.0,
            emit_markers=True,
        )
        markers = list(proj.timeline.markers)
        assert [m.name for m in markers] == ['Slide 1', 'Slide 2', 'Slide 3']

    def test_emit_markers_false_adds_no_markers(self, proj_and_slides):
        proj, slides = proj_and_slides
        import_slide_images(
            proj, slides,
            per_slide_seconds=5.0,
            slide_titles=['A', 'B', 'C'],
            emit_markers=False,
        )
        assert list(proj.timeline.markers) == []

    def test_partial_titles_falls_back_to_default(self, proj_and_slides):
        proj, slides = proj_and_slides
        import_slide_images(
            proj, slides,
            per_slide_seconds=5.0,
            slide_titles=['Only First'],
            emit_markers=True,
        )
        markers = list(proj.timeline.markers)
        assert markers[0].name == 'Only First'
        assert markers[1].name == 'Slide 2'
        assert markers[2].name == 'Slide 3'

    def test_cursor_offset_shifts_clips(self, proj_and_slides):
        proj, slides = proj_and_slides
        placed = import_slide_images(
            proj, slides,
            per_slide_seconds=3.0,
            cursor_offset=10.0,
        )
        starts = [c.start / EDIT_RATE for c in placed]
        assert starts == [10.0, 13.0, 16.0]


class TestImportPowerpoint:
    """Tests for import_powerpoint wrapper."""

    def _setup_pptx_mocks(self, tmp_path, slide_titles, monkeypatch):
        """Set up mocks for pptx and PIL, returning the pptx path."""
        pptx_path = tmp_path / 'deck.pptx'
        pptx_path.write_bytes(b'PK')

        mock_slides = []
        for title in slide_titles:
            shape_title = SimpleNamespace(text=title) if title else None
            mock_slides.append(SimpleNamespace(
                shapes=SimpleNamespace(title=shape_title),
            ))

        mock_prs = SimpleNamespace(
            slides=mock_slides,
            slide_width=SimpleNamespace(inches=10.0),
            slide_height=SimpleNamespace(inches=7.5),
        )

        # Mock pptx
        mock_pptx_mod = MagicMock()
        mock_pptx_mod.Presentation.return_value = mock_prs
        monkeypatch.setitem(__import__('sys').modules, 'pptx', mock_pptx_mod)

        # Mock PIL so Image.save actually writes a PNG file
        real_pil_mod = MagicMock()

        def _fake_new(mode, size, color=None):
            img = MagicMock()

            def _save(path, *a, **kw):
                Path(path).write_bytes(b'\x89PNG\r\n\x1a\n')

            img.save = _save
            return img

        real_pil_mod.Image.new = _fake_new
        monkeypatch.setitem(__import__('sys').modules, 'PIL', real_pil_mod)
        monkeypatch.setitem(__import__('sys').modules, 'PIL.Image', real_pil_mod.Image)
        monkeypatch.setitem(__import__('sys').modules, 'PIL.ImageDraw', real_pil_mod.ImageDraw)

        return pptx_path

    def test_import_powerpoint_basic(self, tmp_path, mock_pymediainfo, monkeypatch):
        proj = Project.new(str(tmp_path / 'test.cmproj'))
        pptx_path = self._setup_pptx_mocks(tmp_path, ['Title 1', 'Title 2'], monkeypatch)

        result = import_powerpoint(proj, pptx_path)

        assert result['slide_count'] == 2
        assert result['titles'] == ['Title 1', 'Title 2']
        assert len(result['clips']) == 2

    def test_import_powerpoint_raises_without_pptx(self, tmp_path, mock_pymediainfo, monkeypatch):
        proj = Project.new(str(tmp_path / 'test.cmproj'))
        pptx_path = tmp_path / 'deck.pptx'
        pptx_path.write_bytes(b'PK')

        monkeypatch.setitem(__import__('sys').modules, 'pptx', None)
        with pytest.raises(ImportError, match='python-pptx is required'):
            import_powerpoint(proj, pptx_path)

    def test_import_powerpoint_with_markers(self, tmp_path, mock_pymediainfo, monkeypatch):
        proj = Project.new(str(tmp_path / 'test.cmproj'))
        pptx_path = self._setup_pptx_mocks(tmp_path, ['Slide A', 'Slide B'], monkeypatch)

        result = import_powerpoint(proj, pptx_path, emit_markers=True)

        markers = list(proj.timeline.markers)
        assert [m.name for m in markers] == ['Slide A', 'Slide B']
        assert result['slide_count'] == 2

    def test_import_powerpoint_append_mode(self, tmp_path, mock_pymediainfo, monkeypatch):
        proj = Project.new(str(tmp_path / 'test.cmproj'))

        # Place an existing slide first
        img = tmp_path / 'existing.png'
        img.write_bytes(b'\x89PNG\r\n\x1a\n')
        import_slide_images(proj, [img], per_slide_seconds=5.0)

        pptx_path = self._setup_pptx_mocks(tmp_path, ['New Slide'], monkeypatch)

        result = import_powerpoint(proj, pptx_path, append=True)

        # The new clip should start after the existing 5s clip
        new_clip = result['clips'][0]
        assert new_clip.start / EDIT_RATE == pytest.approx(5.0, abs=0.01)

    def test_import_powerpoint_custom_duration(self, tmp_path, mock_pymediainfo, monkeypatch):
        proj = Project.new(str(tmp_path / 'test.cmproj'))
        pptx_path = self._setup_pptx_mocks(tmp_path, ['S1'], monkeypatch)

        result = import_powerpoint(proj, pptx_path, per_slide_seconds=10.0)

        clip = result['clips'][0]
        assert clip._data['duration'] / EDIT_RATE == pytest.approx(10.0, abs=0.01)


class TestExtractSlidesAsImages:
    """Tests for _extract_slides_as_images."""

    def test_raises_import_error_without_pptx(self, tmp_path, monkeypatch):
        monkeypatch.setitem(__import__('sys').modules, 'pptx', None)
        with pytest.raises(ImportError, match='python-pptx is required'):
            _extract_slides_as_images(tmp_path / 'deck.pptx', tmp_path)
