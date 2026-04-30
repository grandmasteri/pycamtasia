"""Tests for camtasia.export.audio — audio timeline metadata export."""
from __future__ import annotations

import csv
import json

import pytest

from camtasia.export.audio import export_audio, export_audio_clips
from camtasia.timing import seconds_to_ticks


def _add_audio_clip(project, track_name='Audio', start_seconds=0.0, duration_seconds=5.0, source_id=1):
    """Add an AMFile clip to the named track."""
    track = project.timeline.get_or_create_track(track_name)
    return track.add_audio(source_id, start_seconds=start_seconds, duration_seconds=duration_seconds)


def _add_unified_with_audio(project, track_name='Video', start_seconds=0.0, duration_seconds=5.0):
    """Inject a UnifiedMedia clip with audio sub-clip."""
    track = project.timeline.get_or_create_track(track_name)
    track._data.setdefault('medias', []).append({
        '_type': 'UnifiedMedia', 'id': 900, 'src': 1,
        'start': seconds_to_ticks(start_seconds),
        'duration': seconds_to_ticks(duration_seconds),
        'mediaStart': 0, 'mediaDuration': seconds_to_ticks(duration_seconds),
        'scalar': 1, 'parameters': {}, 'effects': [], 'metadata': {},
        'animationTracks': {}, 'attributes': {'ident': ''},
        'video': {
            '_type': 'ScreenVMFile', 'id': 901, 'src': 1,
            'start': 0, 'duration': seconds_to_ticks(duration_seconds),
            'mediaStart': 0, 'mediaDuration': seconds_to_ticks(duration_seconds),
            'scalar': 1, 'parameters': {}, 'effects': [],
        },
        'audio': {
            '_type': 'AMFile', 'id': 902, 'src': 1,
            'start': 0, 'duration': seconds_to_ticks(duration_seconds),
            'mediaStart': 0, 'mediaDuration': seconds_to_ticks(duration_seconds),
            'scalar': 1, 'attributes': {'gain': 1.0},
        },
    })


class TestExportAudioCsv:
    def test_csv_header(self, project, tmp_path):
        actual_path = export_audio(project, tmp_path / 'audio.csv')
        actual_header = actual_path.read_text().splitlines()[0]
        assert actual_header == 'track_name,track_index,clip_id,clip_type,start_seconds,duration_seconds,end_seconds,source_id,volume,gain,effects'

    def test_csv_with_audio_clip(self, project, tmp_path):
        _add_audio_clip(project, start_seconds=1.0, duration_seconds=3.0)
        actual_path = export_audio(project, tmp_path / 'audio.csv')
        with actual_path.open() as f:
            reader = list(csv.DictReader(f))
        assert len(reader) == 1
        actual_row = reader[0]
        assert actual_row['track_name'] == 'Audio'
        assert actual_row['clip_type'] == 'AMFile'
        assert actual_row['start_seconds'] == '1.0'
        assert actual_row['duration_seconds'] == '3.0'
        assert actual_row['end_seconds'] == '4.0'

    def test_csv_empty_project(self, project, tmp_path):
        actual_path = export_audio(project, tmp_path / 'audio.csv')
        actual_lines = actual_path.read_text().strip().splitlines()
        assert len(actual_lines) == 1  # header only

    def test_csv_excludes_video_only_clips(self, project, tmp_path):
        track = project.timeline.get_or_create_track('Video')
        track.add_clip('VMFile', 1, 0, seconds_to_ticks(5.0))
        actual_path = export_audio(project, tmp_path / 'audio.csv')
        with actual_path.open() as f:
            actual_rows = list(csv.DictReader(f))
        assert actual_rows == []

    def test_csv_includes_unified_with_audio(self, project, tmp_path):
        _add_unified_with_audio(project)
        actual_path = export_audio(project, tmp_path / 'audio.csv')
        with actual_path.open() as f:
            actual_rows = list(csv.DictReader(f))
        assert len(actual_rows) == 1
        assert actual_rows[0]['clip_type'] == 'UnifiedMedia'

    def test_csv_effects_semicolon_separated(self, project, tmp_path):
        clip = _add_audio_clip(project)
        clip._data.setdefault('effects', []).extend([
            {'effectName': 'NoiseRemoval'},
            {'effectName': 'AudioCompression'},
        ])
        actual_path = export_audio(project, tmp_path / 'audio.csv')
        with actual_path.open() as f:
            actual_row = next(iter(csv.DictReader(f)))
        assert actual_row['effects'] == 'NoiseRemoval; AudioCompression'


class TestExportAudioJson:
    def test_json_structure(self, project, tmp_path):
        _add_audio_clip(project, start_seconds=2.0, duration_seconds=4.0)
        actual_path = export_audio(project, tmp_path / 'audio.json', format='json')
        actual_data = json.loads(actual_path.read_text())
        assert isinstance(actual_data, list)
        assert len(actual_data) == 1
        actual_clip = actual_data[0]
        assert actual_clip['clip_type'] == 'AMFile'
        assert actual_clip['start_seconds'] == 2.0
        assert actual_clip['duration_seconds'] == 4.0
        assert actual_clip['end_seconds'] == 6.0
        assert isinstance(actual_clip['effects'], list)

    def test_json_empty_project(self, project, tmp_path):
        actual_path = export_audio(project, tmp_path / 'audio.json', format='json')
        assert json.loads(actual_path.read_text()) == []


class TestExportAudioSoloTrack:
    def test_solo_track_filters(self, project, tmp_path):
        _add_audio_clip(project, track_name='Narration', start_seconds=0.0)
        _add_audio_clip(project, track_name='Music', start_seconds=0.0)
        actual_path = export_audio(project, tmp_path / 'audio.json', format='json', solo_track='Narration')
        actual_data = json.loads(actual_path.read_text())
        assert len(actual_data) == 1
        assert actual_data[0]['track_name'] == 'Narration'

    def test_solo_track_no_match(self, project, tmp_path):
        _add_audio_clip(project)
        actual_path = export_audio(project, tmp_path / 'audio.json', format='json', solo_track='Nonexistent')
        assert json.loads(actual_path.read_text()) == []


class TestExportAudioInvalidFormat:
    def test_invalid_format_raises(self, project, tmp_path):
        with pytest.raises(ValueError, match="format must be 'csv' or 'json'"):
            export_audio(project, tmp_path / 'audio.xml', format='xml')


class TestExportAudioVolumeAndGain:
    def test_volume_and_gain_in_output(self, project, tmp_path):
        clip = _add_audio_clip(project)
        clip.volume = 0.5
        clip.gain = 0.8
        actual_path = export_audio(project, tmp_path / 'audio.json', format='json')
        actual_clip = json.loads(actual_path.read_text())[0]
        assert actual_clip['volume'] == 0.5
        assert actual_clip['gain'] == 0.8


class TestExportAudioClips:
    def test_creates_per_clip_files(self, project, tmp_path):
        _add_audio_clip(project, start_seconds=0.0)
        _add_audio_clip(project, track_name='Music', start_seconds=2.0)
        out_dir = tmp_path / 'clips'
        actual_paths = export_audio_clips(project, out_dir)
        assert len(actual_paths) == 2
        for p in actual_paths:
            assert p.exists()
            actual_data = json.loads(p.read_text())
            assert 'clip_id' in actual_data
            assert 'start_seconds' in actual_data

    def test_creates_output_directory(self, project, tmp_path):
        out_dir = tmp_path / 'nested' / 'clips'
        actual_paths = export_audio_clips(project, out_dir)
        assert actual_paths == []
        assert out_dir.exists()

    def test_solo_track_filters(self, project, tmp_path):
        _add_audio_clip(project, track_name='Narration')
        _add_audio_clip(project, track_name='Music')
        out_dir = tmp_path / 'clips'
        actual_paths = export_audio_clips(project, out_dir, solo_track='Music')
        assert len(actual_paths) == 1
        actual_data = json.loads(actual_paths[0].read_text())
        assert actual_data['track_name'] == 'Music'

    def test_file_naming(self, project, tmp_path):
        clip = _add_audio_clip(project)
        out_dir = tmp_path / 'clips'
        actual_paths = export_audio_clips(project, out_dir)
        assert actual_paths[0].name == f'clip_{clip.id}.json'


class TestExportAudioReturnsPath:
    def test_csv_returns_path(self, project, tmp_path):
        expected_path = tmp_path / 'audio.csv'
        actual_path = export_audio(project, expected_path)
        assert actual_path == expected_path

    def test_json_returns_path(self, project, tmp_path):
        expected_path = tmp_path / 'audio.json'
        actual_path = export_audio(project, expected_path, format='json')
        assert actual_path == expected_path
