"""Tests for SRT/VTT import, SRT export, multilang export, and multilang package."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from camtasia import Project
from camtasia.export.captions import (
    CaptionEntry,
    export_captions_multilang,
    export_captions_srt,
    export_multilang_package,
    import_captions_srt,
    import_captions_vtt,
)


@pytest.fixture
def project_with_subtitles():
    tmp = Path(tempfile.mkdtemp()) / 'test.cmproj'
    proj = Project.new(str(tmp))
    proj.add_subtitle_track([
        (0.0, 2.0, 'Hello world'),
        (2.5, 3.0, 'Second line'),
        (6.0, 1.5, 'Third line'),
    ])
    return proj


@pytest.fixture
def srt_file(tmp_path):
    content = (
        '1\n'
        '00:00:00,000 --> 00:00:02,000\n'
        'Hello world\n'
        '\n'
        '2\n'
        '00:00:02,500 --> 00:00:05,500\n'
        'Second line\n'
        '\n'
        '3\n'
        '00:01:06,000 --> 00:01:07,500\n'
        'Third line\n'
    )
    p = tmp_path / 'test.srt'
    p.write_text(content)
    return p


@pytest.fixture
def vtt_file(tmp_path):
    content = (
        'WEBVTT\n'
        '\n'
        '1\n'
        '00:00:00.000 --> 00:00:02.000\n'
        'Hello world\n'
        '\n'
        '2\n'
        '00:00:02.500 --> 00:00:05.500\n'
        'Second line\n'
        '\n'
        '3\n'
        '00:01:06.000 --> 00:01:07.500\n'
        'Third line\n'
    )
    p = tmp_path / 'test.vtt'
    p.write_text(content)
    return p


class TestImportSrt:
    def test_parses_entries(self, srt_file):
        entries = import_captions_srt(srt_file)
        assert len(entries) == 3
        assert entries[0] == CaptionEntry(start_seconds=0.0, duration_seconds=2.0, text='Hello world')
        assert entries[1] == CaptionEntry(start_seconds=2.5, duration_seconds=3.0, text='Second line')
        assert entries[2] == CaptionEntry(start_seconds=66.0, duration_seconds=1.5, text='Third line')

    def test_empty_file(self, tmp_path):
        p = tmp_path / 'empty.srt'
        p.write_text('')
        assert import_captions_srt(p) == []

    def test_multiline_text(self, tmp_path):
        content = '1\n00:00:00,000 --> 00:00:02,000\nLine one\nLine two\n'
        p = tmp_path / 'multi.srt'
        p.write_text(content)
        entries = import_captions_srt(p)
        assert entries[0].text == 'Line one\nLine two'


class TestImportVtt:
    def test_parses_entries(self, vtt_file):
        entries = import_captions_vtt(vtt_file)
        assert len(entries) == 3
        assert entries[0] == CaptionEntry(start_seconds=0.0, duration_seconds=2.0, text='Hello world')
        assert entries[1] == CaptionEntry(start_seconds=2.5, duration_seconds=3.0, text='Second line')

    def test_empty_file(self, tmp_path):
        p = tmp_path / 'empty.vtt'
        p.write_text('WEBVTT\n')
        assert import_captions_vtt(p) == []

    def test_vtt_without_cue_ids(self, tmp_path):
        content = 'WEBVTT\n\n00:00:01.000 --> 00:00:03.000\nNo cue id\n'
        p = tmp_path / 'nocue.vtt'
        p.write_text(content)
        entries = import_captions_vtt(p)
        assert entries[0].text == 'No cue id'


class TestExportCaptionsSrt:
    def test_roundtrip(self, project_with_subtitles, tmp_path):
        out = tmp_path / 'out.srt'
        export_captions_srt(project_with_subtitles, out)
        entries = import_captions_srt(out)
        assert len(entries) == 3
        assert entries[0].text == 'Hello world'
        assert entries[0].start_seconds == 0.0
        assert entries[0].duration_seconds == 2.0

    def test_raises_on_missing_track(self, project_with_subtitles, tmp_path):
        with pytest.raises(KeyError, match='No track named'):
            export_captions_srt(project_with_subtitles, tmp_path / 'x.srt', track_name='Nope')


class TestExportCaptionsMultilang:
    def test_creates_one_srt_per_language(self, project_with_subtitles, tmp_path):
        paths = export_captions_multilang(
            project_with_subtitles, tmp_path, ['en', 'fr'],
        )
        assert len(paths) == 2
        assert (tmp_path / 'en.srt').exists()
        assert (tmp_path / 'fr.srt').exists()
        # Both should have the same content (fallback mode)
        en_entries = import_captions_srt(tmp_path / 'en.srt')
        fr_entries = import_captions_srt(tmp_path / 'fr.srt')
        assert len(en_entries) == len(fr_entries) == 3


class TestExportMultilangPackage:
    def test_creates_subfolders(self, project_with_subtitles, tmp_path):
        root = export_multilang_package(
            project_with_subtitles, tmp_path / 'pkg', ['en', 'de'],
        )
        assert (root / 'en' / 'captions.srt').exists()
        assert (root / 'de' / 'captions.srt').exists()
        assert (root / 'en' / 'metadata.json').exists()
        meta = json.loads((root / 'en' / 'metadata.json').read_text())
        assert meta['language'] == 'en'
        assert meta['track_name'] == 'Subtitles'

    def test_metadata_per_language(self, project_with_subtitles, tmp_path):
        root = export_multilang_package(
            project_with_subtitles, tmp_path / 'pkg2', ['ja'],
        )
        meta = json.loads((root / 'ja' / 'metadata.json').read_text())
        assert meta['language'] == 'ja'
