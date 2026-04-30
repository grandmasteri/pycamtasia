"""Tests for camtasia.export.toc — table-of-contents export."""
from __future__ import annotations

import json
from xml.etree.ElementTree import fromstring

import pytest

from camtasia.export.toc import export_toc
from camtasia.timing import EDIT_RATE


class TestExportTocSmartPlayer:
    def test_empty_markers(self, project, tmp_path):
        out = export_toc(project, tmp_path / 'toc.xml')
        root = fromstring(out.read_text())
        assert root.tag == 'SmartPlayerTOC'
        assert list(root) == []

    def test_single_marker(self, project, tmp_path):
        project.timeline.add_marker('Intro', 0.0)
        out = export_toc(project, tmp_path / 'toc.xml')
        root = fromstring(out.read_text())
        entries = root.findall('Entry')
        assert len(entries) == 1
        assert entries[0].find('Title').text == 'Intro'
        assert entries[0].find('Time').text == '00:00:00.000'
        assert entries[0].find('Thumbnail') is not None

    def test_multiple_markers_sorted(self, project, tmp_path):
        project.timeline.add_marker('Second', 5.0)
        project.timeline.add_marker('First', 1.0)
        out = export_toc(project, tmp_path / 'toc.xml')
        root = fromstring(out.read_text())
        titles = [e.find('Title').text for e in root.findall('Entry')]
        assert titles == ['First', 'Second']

    def test_returns_path(self, project, tmp_path):
        result = export_toc(project, tmp_path / 'toc.xml')
        assert result == tmp_path / 'toc.xml'
        assert result.exists()


class TestExportTocXml:
    def test_empty_markers(self, project, tmp_path):
        out = export_toc(project, tmp_path / 'toc.xml', format='xml')
        root = fromstring(out.read_text())
        assert root.tag == 'chapters'
        assert list(root) == []

    def test_chapter_attributes(self, project, tmp_path):
        project.timeline.add_marker('Chapter 1', 10.0)
        out = export_toc(project, tmp_path / 'toc.xml', format='xml')
        root = fromstring(out.read_text())
        ch = root.findall('chapter')
        assert len(ch) == 1
        assert ch[0].get('title') == 'Chapter 1'
        assert ch[0].get('time') == '00:00:10.000'


class TestExportTocJson:
    def test_empty_markers(self, project, tmp_path):
        out = export_toc(project, tmp_path / 'toc.json', format='json')
        data = json.loads(out.read_text())
        assert data == {'chapters': []}

    def test_chapter_fields(self, project, tmp_path):
        project.timeline.add_marker('Demo', 2.5)
        out = export_toc(project, tmp_path / 'toc.json', format='json')
        data = json.loads(out.read_text())
        assert len(data['chapters']) == 1
        ch = data['chapters'][0]
        assert ch['title'] == 'Demo'
        assert ch['time_seconds'] == pytest.approx(2.5)
        assert ch['time_ticks'] == pytest.approx(2.5 * EDIT_RATE, abs=1)

    def test_sorted_output(self, project, tmp_path):
        project.timeline.add_marker('B', 3.0)
        project.timeline.add_marker('A', 1.0)
        out = export_toc(project, tmp_path / 'toc.json', format='json')
        data = json.loads(out.read_text())
        titles = [c['title'] for c in data['chapters']]
        assert titles == ['A', 'B']


class TestExportTocErrors:
    def test_invalid_format_raises(self, project, tmp_path):
        with pytest.raises(ValueError, match='Unknown format'):
            export_toc(project, tmp_path / 'toc.txt', format='invalid')
