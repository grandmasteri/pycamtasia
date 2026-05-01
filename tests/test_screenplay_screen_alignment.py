"""Tests for screenplay builder screen recording alignment and captions."""
from __future__ import annotations

from pathlib import Path

from camtasia.builders.screenplay_builder import build_from_screenplay
from camtasia.screenplay import Screenplay, ScreenplaySection, VOBlock

FIXTURES = Path(__file__).parent / 'fixtures'


def _make_screenplay(vo_ids: list[str]) -> Screenplay:
    section = ScreenplaySection(
        title='Test', level=2,
        vo_blocks=[VOBlock(id=vid, text='hello world', section='Test') for vid in vo_ids],
    )
    return Screenplay(sections=[section])


class TestScreenRecordingAlignment:
    def test_screen_recording_placed_on_separate_track(self, project, tmp_path):
        wav = FIXTURES / 'empty.wav'
        (tmp_path / '1.1.wav').write_bytes(wav.read_bytes())
        sp = _make_screenplay(['1.1'])
        # Use the wav as a stand-in for a screen recording
        build_from_screenplay(
            project, sp, tmp_path,
            screen_recording_path=wav,
        )
        sr_track = project.timeline.find_track_by_name('Screen Recording')
        assert sr_track is not None
        clips = list(sr_track.clips)
        assert len(clips) == 1
        assert clips[0]._data['_type'] == 'ScreenVMFile'

    def test_screen_recording_starts_at_zero(self, project, tmp_path):
        wav = FIXTURES / 'empty.wav'
        (tmp_path / '1.1.wav').write_bytes(wav.read_bytes())
        sp = _make_screenplay(['1.1'])
        build_from_screenplay(
            project, sp, tmp_path,
            screen_recording_path=wav,
        )
        sr_track = project.timeline.find_track_by_name('Screen Recording')
        clips = list(sr_track.clips)
        assert clips[0].start_seconds == 0.0

    def test_no_screen_recording_when_path_is_none(self, project, tmp_path):
        sp = _make_screenplay([])
        build_from_screenplay(project, sp, tmp_path)
        sr_track = project.timeline.find_track_by_name('Screen Recording')
        assert sr_track is None


class TestEmitCaptions:
    def test_captions_emitted_when_enabled(self, project, tmp_path):
        wav = FIXTURES / 'empty.wav'
        (tmp_path / '1.1.wav').write_bytes(wav.read_bytes())
        sp = _make_screenplay(['1.1'])
        result = build_from_screenplay(
            project, sp, tmp_path,
            emit_captions=True,
        )
        assert result['captions_added'] == 1

    def test_captions_not_emitted_by_default(self, project, tmp_path):
        wav = FIXTURES / 'empty.wav'
        (tmp_path / '1.1.wav').write_bytes(wav.read_bytes())
        sp = _make_screenplay(['1.1'])
        result = build_from_screenplay(project, sp, tmp_path)
        assert 'captions_added' not in result
