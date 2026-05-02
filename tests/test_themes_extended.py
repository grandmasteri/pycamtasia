"""Tests for extended Theme features: logo_path, add_color, ThemeManager, export/import,
annotation-background/stroke-width/stroke-style in apply_theme, and add_annotation_from_theme."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile

import pytest

from camtasia.project import Project
from camtasia.themes import (
    Theme,
    ThemeManager,
    add_annotation_from_theme,
    apply_theme,
    export_theme,
    import_theme,
)

# ---------------------------------------------------------------------------
# Theme.logo_path
# ---------------------------------------------------------------------------

def test_theme_logo_path_default_none():
    t = Theme()
    assert t.logo_path is None


def test_theme_logo_path_set():
    t = Theme(logo_path=Path('/img/logo.png'))
    assert t.logo_path == Path('/img/logo.png')


# ---------------------------------------------------------------------------
# Theme.add_color
# ---------------------------------------------------------------------------

def test_add_color_creates_custom_slot():
    t = Theme()
    t.add_color('accent-3', (0.1, 0.2, 0.3, 1.0))
    assert t.resolve('accent-3') == (0.1, 0.2, 0.3, 1.0)


def test_add_color_overwrites_existing():
    t = Theme()
    t.add_color('accent-3', (0.0, 0.0, 0.0, 1.0))
    t.add_color('accent-3', (1.0, 1.0, 1.0, 1.0))
    assert t.resolve('accent-3') == (1.0, 1.0, 1.0, 1.0)


# ---------------------------------------------------------------------------
# ThemeManager
# ---------------------------------------------------------------------------

def test_manager_create_and_get():
    mgr = ThemeManager()
    t = Theme(name='Dark')
    mgr.create_theme('Dark', t)
    assert mgr.get('Dark') is t


def test_manager_create_duplicate_raises():
    mgr = ThemeManager()
    mgr.create_theme('A', Theme())
    with pytest.raises(KeyError, match='already exists'):
        mgr.create_theme('A', Theme())


def test_manager_get_missing_raises():
    mgr = ThemeManager()
    with pytest.raises(KeyError, match='not found'):
        mgr.get('nope')


def test_manager_rename():
    mgr = ThemeManager()
    mgr.create_theme('old', Theme(name='old'))
    mgr.rename('old', 'new')
    assert mgr.list() == ['new']
    assert mgr.get('new').name == 'new'


def test_manager_rename_missing_raises():
    mgr = ThemeManager()
    with pytest.raises(KeyError, match='not found'):
        mgr.rename('x', 'y')


def test_manager_rename_collision_raises():
    mgr = ThemeManager()
    mgr.create_theme('a', Theme())
    mgr.create_theme('b', Theme())
    with pytest.raises(KeyError, match='already exists'):
        mgr.rename('a', 'b')


def test_manager_delete():
    mgr = ThemeManager()
    mgr.create_theme('x', Theme())
    mgr.delete('x')
    assert mgr.list() == []


def test_manager_delete_missing_raises():
    mgr = ThemeManager()
    with pytest.raises(KeyError, match='not found'):
        mgr.delete('x')


def test_manager_list_sorted():
    mgr = ThemeManager()
    mgr.create_theme('Zebra', Theme())
    mgr.create_theme('Alpha', Theme())
    assert mgr.list() == ['Alpha', 'Zebra']


# ---------------------------------------------------------------------------
# export_theme / import_theme
# ---------------------------------------------------------------------------

def test_export_import_roundtrip(tmp_path):
    t = Theme(
        name='Branded',
        accent_1=(0.1, 0.2, 0.3, 0.4),
        font_1='Courier',
        logo_path=Path('/logos/brand.png'),
    )
    t.add_color('accent-5', (0.5, 0.5, 0.5, 1.0))
    out = tmp_path / 'theme.json'
    export_theme(t, out)
    loaded = import_theme(out)
    assert loaded.name == 'Branded'
    assert loaded.accent_1 == (0.1, 0.2, 0.3, 0.4)
    assert loaded.font_1 == 'Courier'
    assert loaded.logo_path == Path('/logos/brand.png')
    assert loaded.resolve('accent-5') == (0.5, 0.5, 0.5, 1.0)


def test_export_writes_pycamtasia_format(tmp_path):
    out = tmp_path / 'theme.json'
    export_theme(Theme(), out)
    data = json.loads(out.read_text())
    assert data['format'] == 'pycamtasia-theme'
    assert data['version'] == 1


def test_import_rejects_bad_format(tmp_path):
    bad = tmp_path / 'bad.json'
    bad.write_text(json.dumps({'format': 'other'}))
    with pytest.raises(ValueError, match='Not a pycamtasia theme'):
        import_theme(bad)


def test_export_import_no_logo(tmp_path):
    out = tmp_path / 'theme.json'
    export_theme(Theme(logo_path=None), out)
    loaded = import_theme(out)
    assert loaded.logo_path is None


# ---------------------------------------------------------------------------
# apply_theme: annotation-background, stroke-width, stroke-style
# ---------------------------------------------------------------------------

def _make_themed_project(theme_mappings):
    """Helper: create a project with a callout wired to the given themeMappings."""
    td = tempfile.TemporaryDirectory()
    tmp = Path(td.name) / 'test.cmproj'
    proj = Project.new(str(tmp))
    track = proj.timeline.get_or_create_track('T')
    callout = track.add_callout('X', 0.0, 1.0)
    callout._data.setdefault('attributes', {})['assetProperties'] = [
        {
            'type': 1, 'name': 'C', 'objects': [callout.id],
            'themeMappings': theme_mappings,
        },
    ]
    proj._tmp_dir = td  # prevent GC cleanup
    return proj, callout


def test_apply_theme_annotation_background():
    proj, callout = _make_themed_project({'annotation-background': 'background-1'})
    theme = Theme(background_1=(0.2, 0.3, 0.4, 0.5))
    count = apply_theme(proj, theme)
    assert count == 1
    cdef = callout._data['def']
    assert cdef['annotation-bg-color-red'] == 0.2
    assert cdef['annotation-bg-color-green'] == 0.3
    assert cdef['annotation-bg-color-blue'] == 0.4
    assert cdef['annotation-bg-color-opacity'] == 0.5


def test_apply_theme_stroke_width():
    theme = Theme()
    theme.add_color('stroke-w', 3.0)  # store numeric in custom
    proj, callout = _make_themed_project({'stroke-width': 'stroke-w'})
    count = apply_theme(proj, theme)
    assert count == 1
    assert callout._data['def']['stroke-width'] == 3.0


def test_apply_theme_stroke_style():
    theme = Theme()
    theme.custom['stroke-s'] = 'dashed'
    proj, callout = _make_themed_project({'stroke-style': 'stroke-s'})
    count = apply_theme(proj, theme)
    assert count == 1
    assert callout._data['def']['stroke-style'] == 'dashed'


# ---------------------------------------------------------------------------
# add_annotation_from_theme
# ---------------------------------------------------------------------------

def test_add_annotation_from_theme_applies_colors(tmp_path):
    tmp = tmp_path / 'test.cmproj'
    proj = Project.new(str(tmp))
    track = proj.timeline.get_or_create_track('T')
    theme = Theme(
        accent_1=(1.0, 0.0, 0.0, 1.0),
        accent_2=(0.0, 1.0, 0.0, 1.0),
        foreground_1=(0.0, 0.0, 1.0, 1.0),
        font_1='Menlo',
    )
    callout = add_annotation_from_theme(track, theme, 'callout', 'Hi', 0.0, 2.0)
    cdef = callout._data['def']
    assert cdef['stroke-color-red'] == 1.0
    assert cdef['fill-color-green'] == 1.0
    assert cdef['font']['color-blue'] == 1.0
    assert cdef['font']['name'] == 'Menlo'


def test_add_annotation_from_theme_unsupported_type(tmp_path):
    tmp = tmp_path / 'test.cmproj'
    proj = Project.new(str(tmp))
    track = proj.timeline.get_or_create_track('T')
    with pytest.raises(ValueError, match='Unsupported annotation type'):
        add_annotation_from_theme(track, Theme(), 'shape', 'X', 0.0, 1.0)
