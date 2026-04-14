"""Tests for Project.diff_from and Project.diff_summary."""
from __future__ import annotations

import copy

from camtasia.project import Project


def test_diff_from_identical(project: Project) -> None:
    operations: list[dict[str, object]] = project.diff_from(project)
    assert operations == []


def test_diff_from_with_changes(project: Project) -> None:
    original_title: str = project.title
    project.title = "Modified Title"

    other: Project = Project.__new__(Project)
    other._data = copy.deepcopy(project._data)
    other._data['title'] = original_title

    operations: list[dict[str, object]] = project.diff_from(other)
    assert len(operations) >= 1


def test_diff_summary(project: Project) -> None:
    identical_summary: str = project.diff_summary(project)
    assert identical_summary == 'No differences'

    other: Project = Project.__new__(Project)
    other._data = copy.deepcopy(project._data)
    other._data['title'] = 'Different Title'

    changed_summary: str = project.diff_summary(other)
    assert 'changes:' in changed_summary
