"""Tests for uncovered lines in builders/screenplay_builder.py."""
from __future__ import annotations

import warnings
from pathlib import Path

import pytest

from camtasia.builders.screenplay_builder import build_from_screenplay, _find_audio_file
from camtasia.screenplay import Screenplay, ScreenplaySection, VOBlock, PauseMarker


# ── _find_audio_file: VO- prefix match ──

class TestFindAudioFileVOPrefix:
    def test_vo_prefix_match(self, tmp_path):
        (tmp_path / 'VO-2.1.wav').write_bytes(b'\x00' * 44)
        result = _find_audio_file(tmp_path, '2.1')
        assert result is not None
        assert result.name == 'VO-2.1.wav'

    def test_mp3_extension(self, tmp_path):
        (tmp_path / 'VO-1.1.mp3').write_bytes(b'\x00' * 44)
        result = _find_audio_file(tmp_path, '1.1')
        assert result is not None
        assert result.name == 'VO-1.1.mp3'

    def test_non_numeric_id_returns_none(self, tmp_path):
        """Non-numeric parts in ID skip the numbered prefix search."""
        result = _find_audio_file(tmp_path, 'abc.def')
        assert result is None


# ── build_from_screenplay: missing audio warns, explicit pauses, default pauses ──

class TestBuildFromScreenplayEdgeCases:
    def test_warns_when_audio_file_not_found(self, project, tmp_path):
        sp = Screenplay(sections=[ScreenplaySection(
            title='S1', level=2,
            vo_blocks=[VOBlock(id='99.99', text='missing', section='S1')],
        )])
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            result = build_from_screenplay(project, sp, tmp_path)
        assert result['clips_placed'] == 0
        assert any('No audio file found' in str(x.message) for x in w)

    def test_warns_when_resolved_path_missing(self, project, tmp_path):
        sp = Screenplay(sections=[ScreenplaySection(
            title='S1', level=2,
            vo_blocks=[VOBlock(id='1.1', text='test', section='S1')],
        )])
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            result = build_from_screenplay(
                project, sp, tmp_path,
                vo_file_resolver=lambda vo: tmp_path / 'nonexistent.wav',
            )
        assert result['clips_placed'] == 0
        assert any('Audio file not found' in str(x.message) for x in w)

    def test_explicit_pauses_interleaved(self, project, tmp_path):
        wav = Path(__file__).parent / 'fixtures' / 'empty.wav'
        (tmp_path / 'VO-1.1.wav').write_bytes(wav.read_bytes())
        (tmp_path / 'VO-1.2.wav').write_bytes(wav.read_bytes())
        sp = Screenplay(sections=[ScreenplaySection(
            title='S1', level=2,
            vo_blocks=[
                VOBlock(id='1.1', text='a', section='S1'),
                VOBlock(id='1.2', text='b', section='S1'),
            ],
            pauses=[PauseMarker(duration_seconds=2.0, description='', after_vo_index=0)],
        )])
        result = build_from_screenplay(project, sp, tmp_path)
        assert result['clips_placed'] == 2
        assert result['pauses_added'] == 1

    def test_default_pause_between_vos(self, project, tmp_path):
        wav = Path(__file__).parent / 'fixtures' / 'empty.wav'
        (tmp_path / 'VO-1.1.wav').write_bytes(wav.read_bytes())
        (tmp_path / 'VO-1.2.wav').write_bytes(wav.read_bytes())
        sp = Screenplay(sections=[ScreenplaySection(
            title='S1', level=2,
            vo_blocks=[
                VOBlock(id='1.1', text='a', section='S1'),
                VOBlock(id='1.2', text='b', section='S1'),
            ],
        )])
        result = build_from_screenplay(project, sp, tmp_path, default_pause=0.5)
        assert result['clips_placed'] == 2
        assert result['pauses_added'] == 1  # pause between, not after last

    def test_trailing_pauses(self, project, tmp_path):
        sp = Screenplay(sections=[ScreenplaySection(
            title='S1', level=2,
            vo_blocks=[],
            pauses=[PauseMarker(duration_seconds=1.5, description='', after_vo_index=None)],
        )])
        result = build_from_screenplay(project, sp, tmp_path)
        assert result['pauses_added'] == 1
