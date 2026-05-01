"""Tests for SRT/VTT import, SRT export, multilang export, and multilang package."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile

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


class TestParseSrtTimeInvalid:
    def test_raises_on_invalid_timecode(self):
        from camtasia.export.captions import _parse_srt_time
        with pytest.raises(ValueError, match='Invalid SRT timecode'):
            _parse_srt_time('not-a-timecode')


class TestImportSrtMalformedTimecode:
    def test_skips_block_with_bad_timecode_line(self, tmp_path):
        content = '1\nNOT_A_TIMECODE\nSome text\n\n2\n00:00:01,000 --> 00:00:02,000\nGood\n'
        p = tmp_path / 'bad_tc.srt'
        p.write_text(content)
        entries = import_captions_srt(p)
        assert entries == [CaptionEntry(start_seconds=1.0, duration_seconds=1.0, text='Good')]


class TestImportVttEdgeCases:
    def test_skips_block_with_bad_timecode_match(self, tmp_path):
        # A block where '-->' is present but regex doesn't match (e.g. no valid times)
        content = 'WEBVTT\n\n-->\nSome text\n\n00:00:01.000 --> 00:00:02.000\nGood\n'
        p = tmp_path / 'bad_vtt.vtt'
        p.write_text(content)
        entries = import_captions_vtt(p)
        assert entries == [CaptionEntry(start_seconds=1.0, duration_seconds=1.0, text='Good')]

    def test_skips_block_with_empty_caption_text(self, tmp_path):
        content = 'WEBVTT\n\n00:00:00.000 --> 00:00:01.000\n\n\n00:00:01.000 --> 00:00:02.000\nReal text\n'
        p = tmp_path / 'empty_text.vtt'
        p.write_text(content)
        entries = import_captions_vtt(p)
        assert entries == [CaptionEntry(start_seconds=1.0, duration_seconds=1.0, text='Real text')]


class TestExportCaptionsSrtBody:
    def test_srt_output_content(self, project_with_subtitles, tmp_path):
        out = tmp_path / 'out.srt'
        result = export_captions_srt(project_with_subtitles, out)
        assert result == out
        text = out.read_text()
        assert '1\n' in text
        assert 'Hello world' in text
        assert '-->' in text

    def test_skips_non_callout_clips(self, project_with_subtitles, tmp_path):
        """Non-Callout clips on the subtitle track are skipped in SRT export."""
        track = project_with_subtitles.timeline.find_track_by_name('Subtitles')
        src_id = project_with_subtitles.media_bin.next_id()
        project_with_subtitles._data.setdefault('sourceBin', []).append({
            '_type': 'IMFile', 'id': src_id, 'src': './media/fake.png',
            'sourceTracks': [{'range': [0, 1], 'type': 0, 'editRate': 30,
                'trackRect': [0, 0, 1, 1], 'sampleRate': 30, 'bitDepth': 24,
                'numChannels': 0, 'integratedLUFS': 100.0, 'peakLevel': -1.0,
                'metaData': '', 'tag': 0}],
            'lastMod': 'X', 'loudnessNormalization': False,
            'rect': [0, 0, 1, 1], 'metadata': {'timeAdded': ''},
        })
        track.add_clip('IMFile', src_id, 0, 705600000)
        out = tmp_path / 'out.srt'
        export_captions_srt(project_with_subtitles, out)
        entries = import_captions_srt(out)
        # Only the 3 callout captions, not the image clip
        assert len(entries) == 3


class TestExportCaptionsMultilangWithByLanguage:
    def test_uses_captions_by_language_when_available(self, tmp_path):
        """When project has captions_by_language attr, use it instead of fallback."""
        project = type('FakeProject', (), {
            'captions_by_language': {
                'en': [CaptionEntry(0.0, 1.0, 'English')],
                'fr': [CaptionEntry(0.0, 1.0, 'Français')],
            },
        })()
        paths = export_captions_multilang(project, tmp_path, ['en', 'fr'])
        assert len(paths) == 2
        en_entries = import_captions_srt(tmp_path / 'en.srt')
        assert en_entries == [CaptionEntry(start_seconds=0.0, duration_seconds=1.0, text='English')]
        fr_entries = import_captions_srt(tmp_path / 'fr.srt')
        assert fr_entries == [CaptionEntry(start_seconds=0.0, duration_seconds=1.0, text='Français')]


class TestExportBurnedInCaptionsStub:
    def test_creates_metadata_file(self, project_with_subtitles, tmp_path):
        from camtasia.export.captions import export_burned_in_captions_stub
        result = export_burned_in_captions_stub(project_with_subtitles, tmp_path)
        assert result == tmp_path / 'burned_in_captions.json'
        data = json.loads(result.read_text())
        assert data['format'] == 'pycamtasia-burned-in-stub'
        assert data['version'] == '1.0'
        assert data['track_name'] == 'Subtitles'
        assert data['entry_count'] == 3
        assert data['entries'][0]['text'] == 'Hello world'

    def test_raises_on_missing_track(self, project_with_subtitles, tmp_path):
        from camtasia.export.captions import export_burned_in_captions_stub
        with pytest.raises(KeyError, match='No track named'):
            export_burned_in_captions_stub(project_with_subtitles, tmp_path, track_name='Nope')

    def test_skips_non_callout_clips(self, project_with_subtitles, tmp_path):
        from camtasia.export.captions import export_burned_in_captions_stub
        track = project_with_subtitles.timeline.find_track_by_name('Subtitles')
        src_id = project_with_subtitles.media_bin.next_id()
        project_with_subtitles._data.setdefault('sourceBin', []).append({
            '_type': 'IMFile', 'id': src_id, 'src': './media/fake.png',
            'sourceTracks': [{'range': [0, 1], 'type': 0, 'editRate': 30,
                'trackRect': [0, 0, 1, 1], 'sampleRate': 30, 'bitDepth': 24,
                'numChannels': 0, 'integratedLUFS': 100.0, 'peakLevel': -1.0,
                'metaData': '', 'tag': 0}],
            'lastMod': 'X', 'loudnessNormalization': False,
            'rect': [0, 0, 1, 1], 'metadata': {'timeAdded': ''},
        })
        track.add_clip('IMFile', src_id, 0, 705600000)
        result = export_burned_in_captions_stub(project_with_subtitles, tmp_path)
        data = json.loads(result.read_text())
        assert data['entry_count'] == 3
