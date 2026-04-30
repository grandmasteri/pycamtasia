"""Tests for export_campackage and export_burned_in_captions_stub."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import zipfile

import pytest

from camtasia import Project
from camtasia.export import export_burned_in_captions_stub, export_campackage


@pytest.fixture
def project_with_subtitles():
    tmp = Path(tempfile.mkdtemp()) / 'test.cmproj'
    proj = Project.new(str(tmp))
    proj.add_subtitle_track([
        (0.0, 2.0, 'Hello world'),
        (2.5, 3.0, 'Second line'),
    ])
    return proj


# --- export_campackage ---


class TestExportCampackage:
    def test_creates_zip_file(self, project, tmp_path):
        assets = [{'name': 'clip1', 'src': 'a.mp4'}]
        result = export_campackage(project, assets, tmp_path / 'out.campackage', package_name='test')
        assert result.exists()
        assert zipfile.is_zipfile(result)

    def test_appends_extension(self, project, tmp_path):
        assets = [{'name': 'clip1'}]
        result = export_campackage(project, assets, tmp_path / 'out', package_name='pkg')
        assert result.suffix == '.campackage'
        assert result.exists()

    def test_manifest_structure(self, project, tmp_path):
        assets = [{'name': 'a'}, {'name': 'b'}]
        result = export_campackage(project, assets, tmp_path / 'out.campackage', package_name='mypkg')
        with zipfile.ZipFile(result) as zf:
            manifest = json.loads(zf.read('manifest.json'))
        assert manifest == {
            'format': 'pycamtasia-campackage',
            'version': '1.0',
            'package_name': 'mypkg',
            'canvas': {'width': project.width, 'height': project.height},
            'asset_count': 2,
            'assets': [
                {'index': 0, 'name': 'a', 'file': 'assets/0.json'},
                {'index': 1, 'name': 'b', 'file': 'assets/1.json'},
            ],
        }

    def test_per_asset_json_files(self, project, tmp_path):
        assets = [{'name': 'x', 'extra': 42}, {'name': 'y', 'tags': ['a']}]
        result = export_campackage(project, assets, tmp_path / 'out.campackage', package_name='p')
        with zipfile.ZipFile(result) as zf:
            asset0 = json.loads(zf.read('assets/0.json'))
            asset1 = json.loads(zf.read('assets/1.json'))
        assert asset0 == {'name': 'x', 'extra': 42}
        assert asset1 == {'name': 'y', 'tags': ['a']}

    def test_emits_user_warning(self, project, tmp_path):
        assets = [{'name': 'a'}]
        with pytest.warns(UserWarning, match='pycamtasia-defined'):
            export_campackage(project, assets, tmp_path / 'out.campackage', package_name='w')

    def test_raises_on_empty_assets(self, project, tmp_path):
        with pytest.raises(ValueError, match='must not be empty'):
            export_campackage(project, [], tmp_path / 'out.campackage', package_name='e')

    def test_raises_on_missing_name_key(self, project, tmp_path):
        with pytest.raises(ValueError, match='missing required "name" key'):
            export_campackage(project, [{'src': 'a.mp4'}], tmp_path / 'x.campackage', package_name='n')

    def test_creates_parent_directories(self, project, tmp_path):
        assets = [{'name': 'a'}]
        deep = tmp_path / 'a' / 'b' / 'c' / 'out.campackage'
        result = export_campackage(project, assets, deep, package_name='deep')
        assert result.exists()

    def test_zip_contains_expected_entries(self, project, tmp_path):
        assets = [{'name': 'a'}, {'name': 'b'}, {'name': 'c'}]
        result = export_campackage(project, assets, tmp_path / 'out.campackage', package_name='p')
        with zipfile.ZipFile(result) as zf:
            assert set(zf.namelist()) == {'manifest.json', 'assets/0.json', 'assets/1.json', 'assets/2.json'}


# --- export_burned_in_captions_stub ---


class TestExportBurnedInCaptionsStub:
    def test_creates_metadata_file(self, project_with_subtitles, tmp_path):
        result = export_burned_in_captions_stub(project_with_subtitles, tmp_path)
        assert result == tmp_path / 'burned_in_captions.json'
        assert result.exists()

    def test_metadata_structure(self, project_with_subtitles, tmp_path):
        result = export_burned_in_captions_stub(project_with_subtitles, tmp_path)
        data = json.loads(result.read_text())
        assert data['format'] == 'pycamtasia-burned-in-stub'
        assert data['version'] == '1.0'
        assert data['track_name'] == 'Subtitles'
        assert data['entry_count'] == 2
        assert data['entries'][0] == {
            'start_seconds': 0.0,
            'duration_seconds': 2.0,
            'text': 'Hello world',
        }
        assert data['entries'][1] == {
            'start_seconds': 2.5,
            'duration_seconds': 3.0,
            'text': 'Second line',
        }

    def test_raises_on_missing_track(self, project_with_subtitles, tmp_path):
        with pytest.raises(KeyError, match='No track named'):
            export_burned_in_captions_stub(project_with_subtitles, tmp_path, track_name='Nope')

    def test_creates_dest_dir(self, project_with_subtitles, tmp_path):
        deep = tmp_path / 'x' / 'y'
        result = export_burned_in_captions_stub(project_with_subtitles, deep)
        assert result.exists()

    def test_empty_track_produces_empty_entries(self, tmp_path):
        proj = Project.new(str(tmp_path / 'empty.cmproj'))
        proj.timeline.get_or_create_track('Subtitles')
        out_dir = tmp_path / 'out'
        result = export_burned_in_captions_stub(proj, out_dir)
        data = json.loads(result.read_text())
        assert data['entries'] == []
        assert data['entry_count'] == 0

    def test_note_field_present(self, project_with_subtitles, tmp_path):
        result = export_burned_in_captions_stub(project_with_subtitles, tmp_path)
        data = json.loads(result.read_text())
        assert 'out of scope' in data['note']
