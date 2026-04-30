"""Tests for camtasia.export.chapters — chapter export in multiple formats."""
from __future__ import annotations

from xml.etree.ElementTree import fromstring

import pytest

from camtasia.export.chapters import export_chapters


class TestExportChaptersWebVTT:
    def test_empty_markers(self, project, tmp_path):
        out = export_chapters(project, tmp_path / 'ch.vtt')
        text = out.read_text()
        assert text.startswith('WEBVTT')
        # Only header, no cues
        assert text.strip() == 'WEBVTT'

    def test_single_marker(self, project, tmp_path):
        project.timeline.add_marker('Intro', 0.0)
        out = export_chapters(project, tmp_path / 'ch.vtt')
        text = out.read_text()
        assert '1\n' in text
        assert '00:00:00.000 --> 00:00:01.000' in text
        assert 'Intro' in text

    def test_two_markers_end_time(self, project, tmp_path):
        project.timeline.add_marker('A', 0.0)
        project.timeline.add_marker('B', 5.0)
        out = export_chapters(project, tmp_path / 'ch.vtt')
        text = out.read_text()
        # First cue ends at second marker start
        assert '00:00:00.000 --> 00:00:05.000' in text
        # Second cue ends at +1s
        assert '00:00:05.000 --> 00:00:06.000' in text

    def test_returns_path(self, project, tmp_path):
        result = export_chapters(project, tmp_path / 'ch.vtt')
        assert result == tmp_path / 'ch.vtt'
        assert result.exists()


class TestExportChaptersMp4:
    def test_empty_markers(self, project, tmp_path):
        out = export_chapters(project, tmp_path / 'ch.xml', format='mp4')
        root = fromstring(out.read_text())
        assert root.tag == 'Chapters'
        assert list(root) == []

    def test_chapter_atom_structure(self, project, tmp_path):
        project.timeline.add_marker('Scene 1', 10.0)
        out = export_chapters(project, tmp_path / 'ch.xml', format='mp4')
        root = fromstring(out.read_text())
        atoms = root.findall('ChapterAtom')
        assert len(atoms) == 1
        assert atoms[0].find('ChapterTimeStart').text == '00:00:10.000'
        assert atoms[0].find('ChapterString').text == 'Scene 1'

    def test_multiple_atoms_sorted(self, project, tmp_path):
        project.timeline.add_marker('B', 20.0)
        project.timeline.add_marker('A', 5.0)
        out = export_chapters(project, tmp_path / 'ch.xml', format='mp4')
        root = fromstring(out.read_text())
        names = [a.find('ChapterString').text for a in root.findall('ChapterAtom')]
        assert names == ['A', 'B']


class TestExportChaptersYouTube:
    def test_empty_markers(self, project, tmp_path):
        out = export_chapters(project, tmp_path / 'ch.txt', format='youtube')
        assert out.read_text() == ''

    def test_format_minutes_seconds(self, project, tmp_path):
        project.timeline.add_marker('Intro', 0.0)
        project.timeline.add_marker('Main', 90.0)
        out = export_chapters(project, tmp_path / 'ch.txt', format='youtube')
        lines = out.read_text().strip().split('\n')
        assert lines == ['0:00 Intro', '1:30 Main']

    def test_format_hours(self, project, tmp_path):
        project.timeline.add_marker('Long', 3661.0)
        out = export_chapters(project, tmp_path / 'ch.txt', format='youtube')
        assert out.read_text().strip() == '1:01:01 Long'

    def test_sorted_output(self, project, tmp_path):
        project.timeline.add_marker('Z', 10.0)
        project.timeline.add_marker('A', 0.0)
        out = export_chapters(project, tmp_path / 'ch.txt', format='youtube')
        lines = out.read_text().strip().split('\n')
        assert lines == ['0:00 A', '0:10 Z']


class TestExportChaptersErrors:
    def test_invalid_format_raises(self, project, tmp_path):
        with pytest.raises(ValueError, match='Unknown format'):
            export_chapters(project, tmp_path / 'ch.txt', format='invalid')
