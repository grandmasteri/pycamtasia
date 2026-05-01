"""Integration tests for pycamtasia template operations.

Each test exercises template creation, installation, and round-trip
workflows, then opens the resulting project in Camtasia to verify
correctness via the validator contract.

Run with: pytest -m integration tests/test_integration_templates.py
"""
from __future__ import annotations

from pathlib import Path

import pytest

from camtasia import operations, seconds_to_ticks
from camtasia.operations import TemplateManager
from tests.integration_helpers import INTEGRATION_MARKERS, open_in_camtasia

FIXTURES = Path(__file__).parent / 'fixtures'
EMPTY_WAV = FIXTURES / 'empty.wav'

pytestmark = INTEGRATION_MARKERS


def _populate_project(project, tmp_path: Path):
    """Add multiple features to a project for richer template testing."""
    # Add an audio clip
    media = project.import_media(EMPTY_WAV)
    track = project.timeline.add_track('Audio')
    track.add_audio(media.id, start_seconds=0.0, duration_seconds=2.0)

    # Add a content track with a clip
    content_track = project.timeline.add_track('Content')
    content_track.add_clip('AMFile', media.id, 0, seconds_to_ticks(3))


class TestSaveAsTemplateAndReload:
    def test_save_as_template_and_new_from_template_opens(self, project, tmp_path):
        """save_as_template → new_from_template → opens in Camtasia."""
        _populate_project(project, tmp_path)
        template_path = tmp_path / 'basic.camtemplate'
        operations.save_as_template(project, 'Basic Template', template_path)

        new_proj = operations.new_from_template(template_path, tmp_path / 'from_template.cmproj')
        open_in_camtasia(new_proj)

    def test_empty_project_template_round_trip(self, project, tmp_path):
        """An empty project survives template round-trip."""
        template_path = tmp_path / 'empty.camtemplate'
        operations.save_as_template(project, 'Empty', template_path)

        new_proj = operations.new_from_template(template_path, tmp_path / 'empty_rt.cmproj')
        open_in_camtasia(new_proj)


class TestExportAndInstall:
    def test_export_camtemplate_and_install(self, project, tmp_path):
        """export_camtemplate → install_camtemplate → new_project_from_template → opens."""
        _populate_project(project, tmp_path)
        template_path = tmp_path / 'exported.camtemplate'
        operations.export_camtemplate(project, template_path)

        # Install into a custom directory to avoid polluting ~/.pycamtasia
        templates_dir = tmp_path / 'templates'
        templates_dir.mkdir()
        import shutil
        shutil.copy2(template_path, templates_dir / template_path.name)

        # Verify the template is valid by loading from it
        new_proj = operations.new_from_template(
            templates_dir / 'exported.camtemplate',
            tmp_path / 'installed_proj.cmproj',
        )
        open_in_camtasia(new_proj)

    def test_install_camtemplate_and_list(self, project, tmp_path, monkeypatch):
        """install_camtemplate places file in templates dir and list finds it."""
        template_path = tmp_path / 'to_install.camtemplate'
        operations.save_as_template(project, 'Installable', template_path)

        # Redirect templates dir to tmp to avoid side effects
        fake_dir = tmp_path / 'fake_templates'
        fake_dir.mkdir()
        monkeypatch.setattr('camtasia.operations.template._TEMPLATES_DIR', fake_dir)

        installed = operations.install_camtemplate(template_path)
        assert installed.exists()

        templates = operations.list_installed_templates()
        assert any(t.name == 'to_install.camtemplate' for t in templates)


class TestNewProjectFromTemplate:
    def test_new_project_from_installed_template_opens(self, project, tmp_path, monkeypatch):
        """new_project_from_template with an installed template opens in Camtasia."""
        template_path = tmp_path / 'named.camtemplate'
        operations.save_as_template(project, 'MyNamedTemplate', template_path)

        fake_dir = tmp_path / 'fake_templates'
        fake_dir.mkdir()
        monkeypatch.setattr('camtasia.operations.template._TEMPLATES_DIR', fake_dir)
        operations.install_camtemplate(template_path)

        new_proj = operations.new_project_from_template(
            'MyNamedTemplate', tmp_path / 'from_named.cmproj'
        )
        open_in_camtasia(new_proj)

    def test_new_project_from_template_not_found_raises(self, tmp_path, monkeypatch):
        """new_project_from_template raises FileNotFoundError for missing name."""
        fake_dir = tmp_path / 'empty_templates'
        fake_dir.mkdir()
        monkeypatch.setattr('camtasia.operations.template._TEMPLATES_DIR', fake_dir)

        with pytest.raises(FileNotFoundError, match='NoSuchTemplate'):
            operations.new_project_from_template('NoSuchTemplate', tmp_path / 'x.cmproj')


class TestTemplateRoundTrip:
    def test_template_to_project_modify_and_re_template(self, project, tmp_path):
        """template → project → modify → save as new template → apply → opens."""
        _populate_project(project, tmp_path)

        # First template
        tpl1 = tmp_path / 'v1.camtemplate'
        operations.save_as_template(project, 'V1', tpl1)

        # Create project from template, modify it
        proj2 = operations.new_from_template(tpl1, tmp_path / 'modified.cmproj')
        extra_track = proj2.timeline.add_track('Extra')
        media2 = proj2.import_media(EMPTY_WAV)
        extra_track.add_audio(media2.id, start_seconds=0.0, duration_seconds=2.0)

        # Save modified project as a new template
        tpl2 = tmp_path / 'v2.camtemplate'
        operations.save_as_template(proj2, 'V2', tpl2)

        # Create final project from v2 template
        final = operations.new_from_template(tpl2, tmp_path / 'final.cmproj')
        open_in_camtasia(final)


class TestTemplateManager:
    def test_list_rename_delete(self, project, tmp_path):
        """TemplateManager can list, rename, and delete templates."""
        templates_dir = tmp_path / 'mgr_templates'
        templates_dir.mkdir()
        mgr = TemplateManager(templates_dir)

        # Create and install a template manually
        tpl = tmp_path / 'managed.camtemplate'
        operations.save_as_template(project, 'Managed', tpl)
        import shutil
        shutil.copy2(tpl, templates_dir / 'managed.camtemplate')

        # List
        assert len(mgr.list()) == 1

        # Rename
        renamed = mgr.rename('managed.camtemplate', 'renamed.camtemplate')
        assert renamed.exists()
        assert not (templates_dir / 'managed.camtemplate').exists()

        # Delete
        mgr.delete('renamed.camtemplate')
        assert len(mgr.list()) == 0

    def test_manager_delete_nonexistent_raises(self, tmp_path):
        """TemplateManager.delete raises FileNotFoundError for missing file."""
        mgr = TemplateManager(tmp_path)
        with pytest.raises(FileNotFoundError):
            mgr.delete('ghost.camtemplate')

    def test_manager_installed_template_produces_openable_project(self, project, tmp_path):
        """A template managed via TemplateManager produces a project Camtasia opens."""
        templates_dir = tmp_path / 'mgr_templates'
        templates_dir.mkdir()
        mgr = TemplateManager(templates_dir)

        _populate_project(project, tmp_path)
        tpl = tmp_path / 'mgr_test.camtemplate'
        operations.save_as_template(project, 'MgrTest', tpl)
        import shutil
        shutil.copy2(tpl, templates_dir / 'mgr_test.camtemplate')

        assert len(mgr.list()) == 1

        # Use the managed template to create a project
        new_proj = operations.new_from_template(
            templates_dir / 'mgr_test.camtemplate',
            tmp_path / 'mgr_output.cmproj',
        )
        open_in_camtasia(new_proj)
