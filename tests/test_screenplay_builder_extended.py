"""Extended tests for screenplay builder enhancements."""
from __future__ import annotations

from pathlib import Path
import warnings

from camtasia.builders.screenplay_builder import _find_audio_file, build_from_screenplay
from camtasia.screenplay import PauseMarker, Screenplay, ScreenplaySection, VOBlock

WAV_FIXTURE = Path(__file__).parent / 'fixtures' / 'empty.wav'


def _section(vo_ids, *, title='Test', pauses=None):
    return ScreenplaySection(
        title=title, level=2,
        vo_blocks=[VOBlock(id=vid, text='hello world test words here now', section=title) for vid in vo_ids],
        pauses=[PauseMarker(duration_seconds=d, description='') for d in (pauses or [])],
    )


def _screenplay(*sections):
    return Screenplay(sections=list(sections))


class TestFindAudioFileCaseInsensitive:
    def test_uppercase_vo_prefix(self, tmp_path):
        (tmp_path / 'VO-1.1.wav').write_bytes(b'\x00' * 44)
        assert _find_audio_file(tmp_path, '1.1') is not None

    def test_lowercase_vo_prefix(self, tmp_path):
        (tmp_path / 'vo-1.1.wav').write_bytes(b'\x00' * 44)
        assert _find_audio_file(tmp_path, '1.1') is not None

    def test_mixed_case_vo_prefix(self, tmp_path):
        (tmp_path / 'Vo-2.1.MP3').write_bytes(b'\x00' * 44)
        assert _find_audio_file(tmp_path, '2.1') is not None


class TestFindAudioFileFallbackPatterns:
    def test_id_vo_pattern(self, tmp_path):
        """Matches {id}-VO.ext pattern."""
        (tmp_path / '1.1-VO.wav').write_bytes(b'\x00' * 44)
        result = _find_audio_file(tmp_path, '1.1')
        assert result is not None
        assert result.name == '1.1-VO.wav'

    def test_bare_id_pattern(self, tmp_path):
        """Matches {id}.ext pattern."""
        (tmp_path / '1.1.wav').write_bytes(b'\x00' * 44)
        result = _find_audio_file(tmp_path, '1.1')
        assert result is not None
        assert result.name == '1.1.wav'

    def test_vo_prefix_takes_priority(self, tmp_path):
        """VO-{id} is preferred over {id}-VO and bare {id}."""
        (tmp_path / 'VO-1.1.wav').write_bytes(b'\x00' * 44)
        (tmp_path / '1.1-VO.wav').write_bytes(b'\x00' * 44)
        (tmp_path / '1.1.wav').write_bytes(b'\x00' * 44)
        result = _find_audio_file(tmp_path, '1.1')
        assert result is not None
        assert result.name.lower() == 'vo-1.1.wav'

    def test_id_vo_case_insensitive(self, tmp_path):
        (tmp_path / '3.1-vo.WAV').write_bytes(b'\x00' * 44)
        result = _find_audio_file(tmp_path, '3.1')
        assert result is not None

    def test_nonexistent_dir(self, tmp_path):
        result = _find_audio_file(tmp_path / 'nonexistent', '1.1')
        assert result is None


class TestSectionPause:
    def test_section_pause_overrides_default(self, project, tmp_path):
        wav = WAV_FIXTURE
        (tmp_path / 'VO-1.1.wav').write_bytes(wav.read_bytes())
        (tmp_path / 'VO-2.1.wav').write_bytes(wav.read_bytes())
        sp = _screenplay(
            _section(['1.1'], title='S1'),
            _section(['2.1'], title='S2'),
        )
        result = build_from_screenplay(
            project, sp, tmp_path,
            default_pause=1.0, section_pause=3.0,
            validate_alignment=False,
        )
        assert result['clips_placed'] == 2
        # The section pause of 3.0 should be used between sections
        assert result['pauses_added'] == 1
        # Verify the total duration includes the 3.0s section pause
        # (not the 1.0s default_pause)
        dur_with_section = result['total_duration']

        # Compare with default_pause behavior
        project2 = _reload_project(tmp_path)
        result2 = build_from_screenplay(
            project2, sp, tmp_path,
            default_pause=1.0, section_pause=1.0,
            validate_alignment=False,
        )
        assert dur_with_section > result2['total_duration']

    def test_section_pause_none_uses_default(self, project, tmp_path):
        wav = WAV_FIXTURE
        (tmp_path / 'VO-1.1.wav').write_bytes(wav.read_bytes())
        (tmp_path / 'VO-2.1.wav').write_bytes(wav.read_bytes())
        sp = _screenplay(
            _section(['1.1'], title='S1'),
            _section(['2.1'], title='S2'),
        )
        result = build_from_screenplay(
            project, sp, tmp_path,
            default_pause=2.0, section_pause=None,
            validate_alignment=False,
        )
        assert result['pauses_added'] == 1


class TestEmitSceneMarkers:
    def test_markers_added_for_each_section(self, project, tmp_path):
        wav = WAV_FIXTURE
        (tmp_path / 'VO-1.1.wav').write_bytes(wav.read_bytes())
        (tmp_path / 'VO-2.1.wav').write_bytes(wav.read_bytes())
        sp = _screenplay(
            _section(['1.1'], title='Intro'),
            _section(['2.1'], title='Main'),
        )
        result = build_from_screenplay(
            project, sp, tmp_path,
            emit_scene_markers=True,
            validate_alignment=False,
        )
        assert result['markers_added'] == 2
        markers = list(project.timeline.markers)
        actual_names = {m.name for m in markers}
        assert actual_names == {'Intro', 'Main'}

    def test_no_markers_when_disabled(self, project, tmp_path):
        sp = _screenplay(_section([], title='Empty'))
        result = build_from_screenplay(project, sp, tmp_path, emit_scene_markers=False)
        assert 'markers_added' not in result


class TestEmitCaptions:
    def test_captions_added_for_vo_blocks(self, project, tmp_path):
        wav = WAV_FIXTURE
        (tmp_path / 'VO-1.1.wav').write_bytes(wav.read_bytes())
        (tmp_path / 'VO-1.2.wav').write_bytes(wav.read_bytes())
        sp = Screenplay(sections=[ScreenplaySection(
            title='S1', level=2,
            vo_blocks=[
                VOBlock(id='1.1', text='First line', section='S1'),
                VOBlock(id='1.2', text='Second line', section='S1'),
            ],
        )])
        result = build_from_screenplay(
            project, sp, tmp_path,
            emit_captions=True,
            validate_alignment=False,
        )
        assert result['captions_added'] == 2

    def test_no_captions_when_disabled(self, project, tmp_path):
        sp = _screenplay(_section([], title='Empty'))
        result = build_from_screenplay(project, sp, tmp_path, emit_captions=False)
        assert 'captions_added' not in result

    def test_caption_for_missing_audio_uses_default_duration(self, project, tmp_path):
        """When audio is missing, caption still gets placed with a default duration."""
        sp = Screenplay(sections=[ScreenplaySection(
            title='S1', level=2,
            vo_blocks=[VOBlock(id='99.99', text='Missing audio', section='S1')],
        )])
        with warnings.catch_warnings(record=True):
            warnings.simplefilter('always')
            result = build_from_screenplay(
                project, sp, tmp_path,
                emit_captions=True,
                validate_alignment=False,
            )
        assert result['captions_added'] == 1


class TestValidateAlignment:
    def test_warns_on_duration_mismatch(self, project, tmp_path):
        wav = WAV_FIXTURE
        (tmp_path / 'VO-1.1.wav').write_bytes(wav.read_bytes())
        # The empty.wav is very short; text with many words should trigger warning
        sp = Screenplay(sections=[ScreenplaySection(
            title='S1', level=2,
            vo_blocks=[VOBlock(
                id='1.1',
                text='This is a long sentence with many words that should take much longer to speak than the audio duration',
                section='S1',
            )],
        )])
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            build_from_screenplay(project, sp, tmp_path, validate_alignment=True)
        alignment_warnings = [x for x in w if 'differs from estimated' in str(x.message)]
        assert len(alignment_warnings) >= 1

    def test_no_warning_when_disabled(self, project, tmp_path):
        wav = WAV_FIXTURE
        (tmp_path / 'VO-1.1.wav').write_bytes(wav.read_bytes())
        sp = Screenplay(sections=[ScreenplaySection(
            title='S1', level=2,
            vo_blocks=[VOBlock(
                id='1.1',
                text='This is a long sentence with many words that should take much longer',
                section='S1',
            )],
        )])
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            build_from_screenplay(project, sp, tmp_path, validate_alignment=False)
        alignment_warnings = [x for x in w if 'differs from estimated' in str(x.message)]
        assert alignment_warnings == []

    def test_no_warning_for_empty_text(self, project, tmp_path):
        wav = WAV_FIXTURE
        (tmp_path / 'VO-1.1.wav').write_bytes(wav.read_bytes())
        sp = Screenplay(sections=[ScreenplaySection(
            title='S1', level=2,
            vo_blocks=[VOBlock(id='1.1', text='', section='S1')],
        )])
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            build_from_screenplay(project, sp, tmp_path, validate_alignment=True)
        alignment_warnings = [x for x in w if 'differs from estimated' in str(x.message)]
        assert alignment_warnings == []


class TestFromParagraphs:
    def test_creates_numbered_vo_blocks(self):
        section = ScreenplaySection.from_paragraphs(
            ['Hello world', 'Second paragraph', 'Third one'],
            title='My Section',
        )
        assert section.title == 'My Section'
        assert section.level == 2
        assert len(section.vo_blocks) == 3
        assert section.vo_blocks[0].id == '1'
        assert section.vo_blocks[0].text == 'Hello world'
        assert section.vo_blocks[1].id == '2'
        assert section.vo_blocks[2].id == '3'
        assert all(vo.section == 'My Section' for vo in section.vo_blocks)

    def test_empty_paragraphs(self):
        section = ScreenplaySection.from_paragraphs([])
        assert section.vo_blocks == []
        assert section.title == 'Untitled'

    def test_custom_level(self):
        section = ScreenplaySection.from_paragraphs(['text'], level=3)
        assert section.level == 3


def _reload_project(tmp_path):
    """Create a fresh project for comparison tests."""
    import shutil
    resources = Path(__file__).parent.parent / 'src' / 'camtasia' / 'resources'
    dst = tmp_path / 'compare.cmproj'
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(resources / 'new.cmproj', dst)
    from camtasia.project import load_project
    return load_project(dst)
