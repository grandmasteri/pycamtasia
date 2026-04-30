"""Tests for template save/import/install and placeholder replacement modes."""
from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

from camtasia.operations.template import (
    TemplateManager,
    _collect_placeholders,
    _read_template,
    export_camtemplate,
    install_camtemplate,
    list_installed_templates,
    new_from_template,
    new_project_from_template,
    replace_placeholder,
    save_as_template,
)
from camtasia.project import load_project
from camtasia.timeline.clips import clip_from_dict
from camtasia.timeline.clips.placeholder import PlaceholderMedia
from camtasia.timing import seconds_to_ticks


# ------------------------------------------------------------------
# save_as_template
# ------------------------------------------------------------------

class TestSaveAsTemplate:
    def test_creates_zip_with_expected_entries(self, project, tmp_path):
        dest = tmp_path / 'out.camtemplate'
        result = save_as_template(project, 'My Template', dest)
        assert result == dest.resolve()
        with zipfile.ZipFile(dest) as zf:
            assert set(zf.namelist()) == {'manifest.json', 'project.tscproj', 'metadata.json'}

    def test_manifest_contains_name_and_format(self, project, tmp_path):
        dest = tmp_path / 'out.camtemplate'
        save_as_template(project, 'Demo', dest)
        with zipfile.ZipFile(dest) as zf:
            manifest = json.loads(zf.read('manifest.json'))
        assert manifest['name'] == 'Demo'
        assert manifest['format'] == 'pycamtasia-template'
        assert manifest['version'] == 1

    def test_manifest_lists_placeholders(self, project, tmp_path):
        track = project.timeline.get_or_create_track('V')
        track.add_placeholder(0.0, 5.0, title='Intro', note='opening shot')
        dest = tmp_path / 'out.camtemplate'
        save_as_template(project, 'T', dest)
        with zipfile.ZipFile(dest) as zf:
            manifest = json.loads(zf.read('manifest.json'))
        assert manifest['placeholders'] == [{'title': 'Intro', 'subtitle': 'opening shot'}]

    def test_metadata_contains_dimensions(self, project, tmp_path):
        dest = tmp_path / 'out.camtemplate'
        save_as_template(project, 'T', dest)
        with zipfile.ZipFile(dest) as zf:
            meta = json.loads(zf.read('metadata.json'))
        assert meta['width'] == project._data['width']
        assert meta['height'] == project._data['height']

    def test_project_tscproj_is_valid_json(self, project, tmp_path):
        dest = tmp_path / 'out.camtemplate'
        save_as_template(project, 'T', dest)
        with zipfile.ZipFile(dest) as zf:
            data = json.loads(zf.read('project.tscproj'))
        assert 'timeline' in data


# ------------------------------------------------------------------
# export_camtemplate (alias)
# ------------------------------------------------------------------

class TestExportCamtemplate:
    def test_uses_project_title_as_name(self, project, tmp_path):
        project._data['title'] = 'My Video'
        dest = tmp_path / 'out.camtemplate'
        export_camtemplate(project, dest)
        with zipfile.ZipFile(dest) as zf:
            manifest = json.loads(zf.read('manifest.json'))
        assert manifest['name'] == 'My Video'

    def test_falls_back_to_stem_when_no_title(self, project, tmp_path):
        project._data['title'] = ''
        dest = tmp_path / 'fallback.camtemplate'
        export_camtemplate(project, dest)
        with zipfile.ZipFile(dest) as zf:
            manifest = json.loads(zf.read('manifest.json'))
        assert manifest['name'] == 'fallback'


# ------------------------------------------------------------------
# new_from_template
# ------------------------------------------------------------------

class TestNewFromTemplate:
    def test_creates_project_from_template(self, project, tmp_path):
        tpl = tmp_path / 'tpl.camtemplate'
        save_as_template(project, 'T', tpl)
        dest = tmp_path / 'new_proj.cmproj'
        proj = new_from_template(tpl, dest)
        assert dest.exists()
        assert proj._data['width'] == project._data['width']

    def test_clears_placeholder_titles(self, project, tmp_path):
        track = project.timeline.get_or_create_track('V')
        track.add_placeholder(0.0, 5.0, title='Fill Me', note='note')
        tpl = tmp_path / 'tpl.camtemplate'
        save_as_template(project, 'T', tpl)
        dest = tmp_path / 'new_proj.cmproj'
        proj = new_from_template(tpl, dest)
        placeholders = [c for t in proj.timeline.tracks for c in t if c.is_placeholder]
        assert len(placeholders) == 1
        assert placeholders[0].title == ''
        assert placeholders[0].subtitle == ''

    def test_raises_on_existing_dest(self, project, tmp_path):
        tpl = tmp_path / 'tpl.camtemplate'
        save_as_template(project, 'T', tpl)
        dest = tmp_path / 'existing.cmproj'
        dest.mkdir()
        with pytest.raises(FileExistsError):
            new_from_template(tpl, dest)

    def test_raises_on_invalid_template(self, tmp_path):
        bad = tmp_path / 'bad.camtemplate'
        with zipfile.ZipFile(bad, 'w') as zf:
            zf.writestr('junk.txt', 'not a template')
        with pytest.raises(ValueError, match='Not a valid'):
            new_from_template(bad, tmp_path / 'out.cmproj')


# ------------------------------------------------------------------
# install / list / new_project_from_template
# ------------------------------------------------------------------

class TestInstallAndList:
    def test_install_and_list(self, project, tmp_path, monkeypatch):
        tpl_dir = tmp_path / 'templates'
        monkeypatch.setattr('camtasia.operations.template._TEMPLATES_DIR', tpl_dir)
        tpl = tmp_path / 'demo.camtemplate'
        save_as_template(project, 'Demo', tpl)
        installed = install_camtemplate(tpl)
        assert installed == tpl_dir / 'demo.camtemplate'
        assert installed.exists()
        templates = list_installed_templates()
        assert installed in templates

    def test_list_empty_when_no_dir(self, tmp_path, monkeypatch):
        monkeypatch.setattr('camtasia.operations.template._TEMPLATES_DIR', tmp_path / 'nope')
        assert list_installed_templates() == []

    def test_install_rejects_invalid(self, tmp_path, monkeypatch):
        monkeypatch.setattr('camtasia.operations.template._TEMPLATES_DIR', tmp_path / 'tpl')
        bad = tmp_path / 'bad.camtemplate'
        bad.write_text('not a zip')
        with pytest.raises(Exception):
            install_camtemplate(bad)


class TestNewProjectFromTemplate:
    def test_lookup_by_name(self, project, tmp_path, monkeypatch):
        tpl_dir = tmp_path / 'templates'
        monkeypatch.setattr('camtasia.operations.template._TEMPLATES_DIR', tpl_dir)
        tpl = tmp_path / 'demo.camtemplate'
        save_as_template(project, 'MyDemo', tpl)
        install_camtemplate(tpl)
        dest = tmp_path / 'from_name.cmproj'
        proj = new_project_from_template('MyDemo', dest)
        assert dest.exists()
        assert proj._data['width'] == project._data['width']

    def test_raises_when_not_found(self, tmp_path, monkeypatch):
        monkeypatch.setattr('camtasia.operations.template._TEMPLATES_DIR', tmp_path / 'empty')
        with pytest.raises(FileNotFoundError, match='No installed template'):
            new_project_from_template('nonexistent', tmp_path / 'out.cmproj')


# ------------------------------------------------------------------
# TemplateManager
# ------------------------------------------------------------------

class TestTemplateManager:
    def test_list_rename_delete(self, project, tmp_path):
        tpl_dir = tmp_path / 'mgr_templates'
        tpl_dir.mkdir()
        mgr = TemplateManager(tpl_dir)
        assert mgr.list() == []

        tpl = tmp_path / 'a.camtemplate'
        save_as_template(project, 'A', tpl)
        import shutil
        shutil.copy2(tpl, tpl_dir / 'a.camtemplate')

        assert len(mgr.list()) == 1
        mgr.rename('a.camtemplate', 'b.camtemplate')
        assert (tpl_dir / 'b.camtemplate').exists()
        assert not (tpl_dir / 'a.camtemplate').exists()

        mgr.delete('b.camtemplate')
        assert mgr.list() == []

    def test_rename_missing_raises(self, tmp_path):
        mgr = TemplateManager(tmp_path)
        with pytest.raises(FileNotFoundError):
            mgr.rename('nope.camtemplate', 'new.camtemplate')

    def test_delete_missing_raises(self, tmp_path):
        mgr = TemplateManager(tmp_path)
        with pytest.raises(FileNotFoundError):
            mgr.delete('nope.camtemplate')


# ------------------------------------------------------------------
# replace_placeholder
# ------------------------------------------------------------------

def _make_placeholder(start_ticks: int, duration_ticks: int) -> PlaceholderMedia:
    return PlaceholderMedia({
        '_type': 'PlaceholderMedia', 'id': 1,
        'start': start_ticks, 'duration': duration_ticks,
        'mediaDuration': 1, 'mediaStart': 0, 'scalar': 1,
        'parameters': {}, 'effects': [],
        'metadata': {'placeHolderTitle': 'PH'},
    })


def _make_video_clip(src: int, duration_ticks: int, media_duration: int | None = None) -> object:
    return clip_from_dict({
        '_type': 'VMFile', 'id': 99, 'src': src,
        'start': 0, 'duration': duration_ticks,
        'mediaDuration': media_duration or duration_ticks,
        'mediaStart': 0, 'scalar': 1,
        'trackNumber': 0, 'attributes': {'ident': ''},
        'parameters': {}, 'effects': [],
    })


class TestReplacePlaceholder:
    def test_ripple_mode_adopts_new_duration(self):
        ph = _make_placeholder(0, seconds_to_ticks(5.0))
        media = _make_video_clip(42, seconds_to_ticks(10.0))
        replace_placeholder(ph, media, mode='ripple')
        assert ph._data['src'] == 42
        assert ph._data['_type'] == 'VMFile'
        assert ph._data['duration'] == seconds_to_ticks(10.0)

    def test_clip_speed_mode_keeps_placeholder_duration(self):
        ph_dur = seconds_to_ticks(5.0)
        media_dur = seconds_to_ticks(10.0)
        ph = _make_placeholder(0, ph_dur)
        media = _make_video_clip(42, media_dur)
        replace_placeholder(ph, media, mode='clip_speed')
        assert ph._data['duration'] == ph_dur
        assert ph._data['mediaDuration'] == media_dur

    def test_from_end_mode_trims_start(self):
        ph_dur = seconds_to_ticks(3.0)
        media_dur = seconds_to_ticks(10.0)
        ph = _make_placeholder(0, ph_dur)
        media = _make_video_clip(42, media_dur)
        replace_placeholder(ph, media, mode='from_end')
        assert ph._data['mediaStart'] == media_dur - ph_dur

    def test_from_start_mode_keeps_duration(self):
        ph_dur = seconds_to_ticks(3.0)
        media_dur = seconds_to_ticks(10.0)
        ph = _make_placeholder(0, ph_dur)
        media = _make_video_clip(42, media_dur)
        replace_placeholder(ph, media, mode='from_start')
        assert ph._data['duration'] == ph_dur
        assert ph._data['mediaStart'] == 0

    def test_invalid_mode_raises(self):
        ph = _make_placeholder(0, 100)
        media = _make_video_clip(1, 100)
        with pytest.raises(ValueError, match='Invalid mode'):
            replace_placeholder(ph, media, mode='invalid')

    def test_default_mode_is_ripple(self):
        ph = _make_placeholder(0, seconds_to_ticks(5.0))
        media = _make_video_clip(42, seconds_to_ticks(8.0))
        replace_placeholder(ph, media)
        assert ph._data['duration'] == seconds_to_ticks(8.0)

    def test_from_end_short_media_uses_media_duration(self):
        """When media is shorter than placeholder, from_end uses media duration."""
        ph_dur = seconds_to_ticks(10.0)
        media_dur = seconds_to_ticks(3.0)
        ph = _make_placeholder(0, ph_dur)
        media = _make_video_clip(42, media_dur)
        replace_placeholder(ph, media, mode='from_end')
        assert ph._data['duration'] == media_dur
        assert ph._data['mediaStart'] == 0


# ------------------------------------------------------------------
# _collect_placeholders
# ------------------------------------------------------------------

class TestCollectPlaceholders:
    def test_collects_from_project(self, project):
        track = project.timeline.get_or_create_track('V')
        track.add_placeholder(0.0, 5.0, title='A', note='a-note')
        track.add_placeholder(5.0, 3.0, title='B')
        result = _collect_placeholders(project._data)
        assert result == [
            {'title': 'A', 'subtitle': 'a-note'},
            {'title': 'B', 'subtitle': ''},
        ]


# ------------------------------------------------------------------
# _read_template validation
# ------------------------------------------------------------------

class TestReadTemplate:
    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            _read_template(tmp_path / 'nope.camtemplate')

    def test_wrong_format_raises(self, tmp_path):
        bad = tmp_path / 'bad.camtemplate'
        with zipfile.ZipFile(bad, 'w') as zf:
            zf.writestr('manifest.json', json.dumps({'format': 'wrong'}))
        with pytest.raises(ValueError, match='Not a valid'):
            _read_template(bad)
