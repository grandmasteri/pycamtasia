"""Tests for Project.load, Project.from_template, and Project.new classmethods."""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from camtasia.project import Project

RESOURCES = Path(__file__).parent.parent / 'src' / 'camtasia' / 'resources'


# --- Project.load ---

def test_load_returns_project():
    proj = Project.load(RESOURCES / 'new.cmproj')
    assert isinstance(proj, Project)


def test_load_resolves_path():
    proj = Project.load(RESOURCES / 'new.cmproj')
    assert proj.file_path.is_absolute()


# --- Project.from_template ---

def test_from_template_creates_copy(tmp_path):
    src = RESOURCES / 'new.cmproj'
    dst = tmp_path / 'copied.cmproj'
    proj = Project.from_template(src, dst)
    assert dst.exists()
    assert isinstance(proj, Project)


def test_from_template_independent_of_source(tmp_path):
    src = RESOURCES / 'new.cmproj'
    dst = tmp_path / 'copied.cmproj'
    proj = Project.from_template(src, dst)
    original = Project.load(src)
    proj.title = 'Modified'
    assert original.title != 'Modified'


def test_from_template_overwrites_existing(tmp_path):
    src = RESOURCES / 'new.cmproj'
    dst = tmp_path / 'copied.cmproj'
    dst.mkdir()
    (dst / 'sentinel').write_text('old')
    proj = Project.from_template(src, dst)
    assert not (dst / 'sentinel').exists()
    assert isinstance(proj, Project)


# --- Project.new ---

def test_new_creates_project(tmp_path):
    dst = tmp_path / 'brand_new.cmproj'
    proj = Project.new(dst)
    assert dst.exists()
    assert isinstance(proj, Project)


def test_new_default_settings(tmp_path):
    dst = tmp_path / 'brand_new.cmproj'
    proj = Project.new(dst)
    assert proj.title == 'Untitled'
    assert proj.width == 1920
    assert proj.height == 1080


def test_new_custom_settings(tmp_path):
    dst = tmp_path / 'custom.cmproj'
    proj = Project.new(dst, title='My Video', width=1280, height=720)
    assert proj.title == 'My Video'
    assert proj.width == 1280
    assert proj.height == 720


def test_new_persists_settings(tmp_path):
    dst = tmp_path / 'persist.cmproj'
    Project.new(dst, title='Saved', width=3840, height=2160)
    reloaded = Project.load(dst)
    assert reloaded.title == 'Saved'
    assert reloaded.width == 3840
    assert reloaded.height == 2160


def test_new_overwrites_existing(tmp_path):
    dst = tmp_path / 'overwrite.cmproj'
    dst.mkdir()
    (dst / 'sentinel').write_text('old')
    proj = Project.new(dst)
    assert not (dst / 'sentinel').exists()
    assert isinstance(proj, Project)
