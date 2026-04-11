"""Tests for Project.__eq__."""

import json
from pathlib import Path
from unittest.mock import patch

from camtasia.project import Project


def _make_project(data: dict, path: str = '/fake/project.tscproj') -> Project:
    """Create a Project without touching disk."""
    p = Path(path)
    with patch.object(Path, 'is_dir', return_value=False), \
         patch.object(Path, 'read_text', return_value=json.dumps(data)):
        return Project(p)


def test_project_eq_same_data():
    data = {'timeline': {}, 'sourceBin': [], 'width': 1920}
    p1 = _make_project(data)
    p2 = _make_project(data)
    assert p1 == p2


def test_project_neq():
    p1 = _make_project({'timeline': {}, 'width': 1920})
    p2 = _make_project({'timeline': {}, 'width': 1280})
    assert p1 != p2
    assert p1.__eq__('not a project') is NotImplemented
