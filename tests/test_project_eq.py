"""Tests for Project.__eq__."""
from __future__ import annotations

import copy

from camtasia.project import Project


def test_project_eq_same_data(project: Project):
    # Two projects with identical data should be equal
    other = copy.copy(project)
    other._data = copy.deepcopy(project._data)
    assert project == other


def test_project_neq(project: Project):
    other = copy.copy(project)
    other._data = copy.deepcopy(project._data)
    other._data['width'] = project.width + 100
    assert project != other
    assert project.__eq__('not a project') is NotImplemented
