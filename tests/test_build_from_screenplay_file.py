"""Tests for Project.build_from_screenplay_file()."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from camtasia.project import load_project
from camtasia.screenplay import Screenplay, ScreenplaySection, VOBlock


FIXTURES = Path(__file__).parent / 'fixtures'


def _make_screenplay(*vo_ids: str) -> Screenplay:
    section = ScreenplaySection(
        title='Intro', level=2,
        vo_blocks=[VOBlock(id=vid, text='hello', section='Intro') for vid in vo_ids],
    )
    return Screenplay(sections=[section])


class TestBuildFromScreenplayFile:
    """Tests for the build_from_screenplay_file convenience method."""

    def test_places_matching_audio_clips(self, project, tmp_path):
        """Clips are placed for each VO block that has a matching .wav file."""
        sp = _make_screenplay('1.1', '1.2')
        audio_dir = tmp_path / 'audio'
        audio_dir.mkdir()
        wav = FIXTURES / 'empty.wav'
        (audio_dir / '1.1.wav').write_bytes(wav.read_bytes())
        (audio_dir / '1.2.wav').write_bytes(wav.read_bytes())

        screenplay_md = tmp_path / 'script.md'
        screenplay_md.write_text('## Intro\n[VO-1.1] **Narrator:** "Hello"\n[VO-1.2] **Narrator:** "World"\n')

        with patch('camtasia.screenplay.parse_screenplay', return_value=sp):
            result = project.build_from_screenplay_file(screenplay_md, audio_dir)

        assert [c.clip_type for c in result['clips']] == ['AMFile', 'AMFile']
        assert result['total_duration'] == 3.0
        assert result['sections'][0].title == 'Intro'

    def test_skips_missing_audio(self, project, tmp_path):
        """VO blocks without a matching .wav are silently skipped."""
        sp = _make_screenplay('1.1', '1.2')
        audio_dir = tmp_path / 'audio'
        audio_dir.mkdir()
        wav = FIXTURES / 'empty.wav'
        (audio_dir / '1.1.wav').write_bytes(wav.read_bytes())
        # 1.2.wav intentionally missing

        screenplay_md = tmp_path / 'script.md'
        screenplay_md.write_text('## Intro\n')

        with patch('camtasia.screenplay.parse_screenplay', return_value=sp):
            result = project.build_from_screenplay_file(screenplay_md, audio_dir)

        assert [c.clip_type for c in result['clips']] == ['AMFile']

    def test_empty_screenplay(self, project, tmp_path):
        """An empty screenplay produces no clips."""
        sp = Screenplay(sections=[])
        screenplay_md = tmp_path / 'script.md'
        screenplay_md.write_text('# Empty\n')

        with patch('camtasia.screenplay.parse_screenplay', return_value=sp):
            result = project.build_from_screenplay_file(screenplay_md, tmp_path)

        assert result['clips'] == []
        assert result['total_duration'] == 0.0
        assert result['sections'] == []

    def test_custom_track_name(self, project, tmp_path):
        """The track_name parameter controls which track clips land on."""
        sp = _make_screenplay('1.1')
        audio_dir = tmp_path / 'audio'
        audio_dir.mkdir()
        (audio_dir / '1.1.wav').write_bytes((FIXTURES / 'empty.wav').read_bytes())

        screenplay_md = tmp_path / 'script.md'
        screenplay_md.write_text('## Intro\n')

        with patch('camtasia.screenplay.parse_screenplay', return_value=sp):
            project.build_from_screenplay_file(screenplay_md, audio_dir, track_name='VO Track')

        assert any(t.name == 'VO Track' for t in project.timeline.tracks)

    def test_gap_seconds_affects_cursor(self, project, tmp_path):
        """Clips are spaced apart by gap_seconds."""
        sp = _make_screenplay('1.1', '1.2')
        audio_dir = tmp_path / 'audio'
        audio_dir.mkdir()
        wav = FIXTURES / 'empty.wav'
        (audio_dir / '1.1.wav').write_bytes(wav.read_bytes())
        (audio_dir / '1.2.wav').write_bytes(wav.read_bytes())

        screenplay_md = tmp_path / 'script.md'
        screenplay_md.write_text('## Intro\n')

        with patch('camtasia.screenplay.parse_screenplay', return_value=sp):
            r1 = project.build_from_screenplay_file(screenplay_md, audio_dir, gap_seconds=0.0)

        # Reload project for a clean slate
        proj2 = load_project(project.file_path)
        with patch('camtasia.screenplay.parse_screenplay', return_value=sp):
            r2 = proj2.build_from_screenplay_file(screenplay_md, audio_dir, gap_seconds=2.0)

        # With a larger gap, total_duration should be greater
        assert r2['total_duration'] > r1['total_duration']

    def test_returns_sections(self, project, tmp_path):
        """The returned dict includes parsed screenplay sections."""
        section = ScreenplaySection(title='Chapter 1', level=2, vo_blocks=[])
        sp = Screenplay(sections=[section])

        screenplay_md = tmp_path / 'script.md'
        screenplay_md.write_text('## Chapter 1\n')

        with patch('camtasia.screenplay.parse_screenplay', return_value=sp):
            result = project.build_from_screenplay_file(screenplay_md, tmp_path)

        assert result['sections'][0].title == 'Chapter 1'