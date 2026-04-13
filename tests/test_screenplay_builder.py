"""Tests for screenplay builder."""
from __future__ import annotations
from pathlib import Path

import pytest

from camtasia.builders.screenplay_builder import build_from_screenplay, _find_audio_file
from camtasia.screenplay import Screenplay, ScreenplaySection, VOBlock, PauseMarker


def _make_screenplay(vo_ids, pauses=None):
    section = ScreenplaySection(
        title='Test', level=2,
        vo_blocks=[VOBlock(id=vid, text='test', section='Test') for vid in vo_ids],
        pauses=[PauseMarker(duration_seconds=d, description='') for d in (pauses or [])],
    )
    return Screenplay(sections=[section])


class TestFindAudioFile:
    def test_exact_match(self, tmp_path):
        (tmp_path / '1.1.wav').write_bytes(b'\x00' * 44)
        actual = _find_audio_file(tmp_path, '1.1')
        assert actual is not None
        assert actual.name == '1.1.wav'

    def test_numbered_prefix(self, tmp_path):
        (tmp_path / '01-intro.wav').write_bytes(b'\x00' * 44)
        actual = _find_audio_file(tmp_path, '1.1')
        assert actual is not None
        assert '01-' in actual.name

    def test_not_found(self, tmp_path):
        actual = _find_audio_file(tmp_path, '99.99')
        assert actual is None


class TestBuildFromScreenplay:
    def test_places_clips(self, project, tmp_path):
        wav = Path(__file__).parent / 'fixtures' / 'empty.wav'
        # Copy wav with matching name
        (tmp_path / '1.1.wav').write_bytes(wav.read_bytes())
        sp = _make_screenplay(['1.1'])
        result = build_from_screenplay(project, sp, tmp_path)
        assert result['clips_placed'] == 1

    def test_adds_pauses(self, project, tmp_path):
        sp = _make_screenplay([], pauses=[1.0, 0.5])
        result = build_from_screenplay(project, sp, tmp_path)
        assert result['pauses_added'] == 2

    def test_returns_summary(self, project, tmp_path):
        sp = _make_screenplay([])
        result = build_from_screenplay(project, sp, tmp_path)
        assert 'clips_placed' in result
        assert 'pauses_added' in result
        assert 'total_duration' in result

    def test_custom_resolver(self, project, tmp_path):
        wav = Path(__file__).parent / 'fixtures' / 'empty.wav'
        sp = _make_screenplay(['1.1'])
        result = build_from_screenplay(
            project, sp, tmp_path,
            vo_file_resolver=lambda vo: wav,
        )
        assert result['clips_placed'] == 1
