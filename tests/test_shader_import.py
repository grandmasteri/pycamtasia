"""Tests for Project.import_shader()."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from camtasia.project import Project


def _create_test_shader(tmp_path: Path) -> Path:
    shader = {
        'effectDef': [
            {'name': 'Color0', 'type': 'Color', 'value': '232F3E'},
            {'name': 'Color1', 'type': 'Color', 'value': '05A0D1'},
            {'name': 'MidPointX', 'type': 'double', 'defaultValue': 0.5, 'minValue': 0.0, 'maxValue': 1.0},
            {'name': 'Speed', 'type': 'double', 'defaultValue': 5.0, 'minValue': 0.0, 'maxValue': 10.0},
        ]
    }
    path = tmp_path / 'test.tscshadervid'
    path.write_text(json.dumps(shader))
    return path


def _get_source_entry(proj: Project, media_id: int) -> dict:
    for entry in proj._data['sourceBin']:
        if entry['id'] == media_id:
            return entry
    raise KeyError(media_id)


class TestImportShaderCreatesMedia:
    def test_media_entry_created(self, project, tmp_path: Path):
        shader = _create_test_shader(tmp_path)
        actual_media = project.import_shader(shader)
        assert actual_media.id is not None
        assert actual_media.identity == 'test'


class TestImportShaderEffectDefColors:
    def test_hex_color_parsed_to_rgba(self, project, tmp_path: Path):
        shader = _create_test_shader(tmp_path)
        media = project.import_shader(shader)
        entry = _get_source_entry(project, media.id)
        actual_color0 = entry['effectDef'][0]

        expected_r = 0x23 / 255
        expected_g = 0x2F / 255
        expected_b = 0x3E / 255
        assert actual_color0['name'] == 'Color0'
        assert actual_color0['defaultValue'] == [expected_r, expected_g, expected_b, 1.0]
        assert actual_color0['scalingType'] == 3
        assert actual_color0['unitType'] == 0
        assert actual_color0['userInterfaceType'] == 6

    def test_second_color_parsed(self, project, tmp_path: Path):
        shader = _create_test_shader(tmp_path)
        media = project.import_shader(shader)
        entry = _get_source_entry(project, media.id)
        actual_color1 = entry['effectDef'][1]

        expected_r = 0x05 / 255
        expected_g = 0xA0 / 255
        expected_b = 0xD1 / 255
        assert actual_color1['defaultValue'] == [expected_r, expected_g, expected_b, 1.0]


class TestImportShaderEffectDefNumeric:
    def test_midpoint_has_unit_type_1(self, project, tmp_path: Path):
        shader = _create_test_shader(tmp_path)
        media = project.import_shader(shader)
        entry = _get_source_entry(project, media.id)
        actual_midpoint = entry['effectDef'][2]

        assert actual_midpoint['name'] == 'MidPointX'
        assert actual_midpoint['defaultValue'] == 0.5
        assert actual_midpoint['unitType'] == 1
        assert actual_midpoint['scalingType'] == 0
        assert actual_midpoint['userInterfaceType'] == 0

    def test_speed_has_unit_type_0(self, project, tmp_path: Path):
        shader = _create_test_shader(tmp_path)
        media = project.import_shader(shader)
        entry = _get_source_entry(project, media.id)
        actual_speed = entry['effectDef'][3]

        assert actual_speed['name'] == 'Speed'
        assert actual_speed['defaultValue'] == 5.0
        assert actual_speed['unitType'] == 0


class TestImportShaderSourceFileType:
    def test_source_file_type_appended(self, project, tmp_path: Path):
        shader = _create_test_shader(tmp_path)
        media = project.import_shader(shader)
        entry = _get_source_entry(project, media.id)
        actual_last = entry['effectDef'][-1]

        assert actual_last['name'] == 'sourceFileType'
        assert actual_last['defaultValue'] == 'tscshadervid'
        assert actual_last['type'] == 'string'


class TestImportShaderSourceTracks:
    def test_source_tracks_fixed(self, project, tmp_path: Path):
        shader = _create_test_shader(tmp_path)
        media = project.import_shader(shader)
        entry = _get_source_entry(project, media.id)
        actual_track = entry['sourceTracks'][0]

        assert actual_track['editRate'] == 30
        assert actual_track['sampleRate'] == 30
        assert actual_track['bitDepth'] == 32


class TestImportShaderIdempotent:
    def test_reuses_existing_media(self, project, tmp_path: Path):
        shader = _create_test_shader(tmp_path)
        actual_first = project.import_shader(shader)
        actual_second = project.import_shader(shader)

        assert actual_first.id == actual_second.id
        assert [s.id for s in project.find_media_by_suffix('.tscshadervid')] == [actual_first.id]
