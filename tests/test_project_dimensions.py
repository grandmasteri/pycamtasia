"""Tests for Project.width and Project.height properties."""
from __future__ import annotations

from camtasia.project import Project


class TestWidth:
    def test_default_is_1920(self, project: Project):
        assert project.width == 1920

    def test_setter(self, project: Project):
        project.width = 3840
        assert project.width == 3840


class TestTitle:
    def test_default_empty(self, project: Project):
        assert project.title == ''

    def test_setter(self, project: Project):
        project.title = 'My Project'
        assert project.title == 'My Project'


class TestDescription:
    def test_default_empty(self, project: Project):
        assert project.description == ''

    def test_setter(self, project: Project):
        project.description = 'D'
        assert project.description == 'D'


class TestAuthor:
    def test_default_empty(self, project: Project):
        assert project.author == ''

    def test_setter(self, project: Project):
        project.author = 'A'
        assert project.author == 'A'


class TestTargetLoudness:
    def test_default(self, project: Project):
        assert project.target_loudness == -18.0

    def test_setter(self, project: Project):
        project.target_loudness = -24.0
        assert project.target_loudness == -24.0


class TestFrameRate:
    def test_default(self, project: Project):
        assert project.frame_rate == 30

    def test_setter(self, project: Project):
        project.frame_rate = 60
        assert project.frame_rate == 60


class TestSampleRate:
    def test_default(self, project: Project):
        assert project.sample_rate == 44100

    def test_setter(self, project: Project):
        project.sample_rate = 48000
        assert project.sample_rate == 48000


class TestHeight:
    def test_default_is_1080(self, project: Project):
        assert project.height == 1080

    def test_setter(self, project: Project):
        project.height = 2160
        assert project.height == 2160
