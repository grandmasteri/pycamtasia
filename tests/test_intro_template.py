"""Tests for insert_intro_template builder function."""
from __future__ import annotations

from camtasia.builders.video_production import insert_intro_template


class TestInsertIntroTemplate:
    def test_returns_summary(self, project):
        result = insert_intro_template(project)
        assert result == {'template_name': 'default', 'duration': 5.0}

    def test_custom_template_name(self, project):
        result = insert_intro_template(project, 'corporate')
        assert result['template_name'] == 'corporate'

    def test_custom_duration(self, project):
        result = insert_intro_template(project, duration=10.0)
        assert result['duration'] == 10.0

    def test_creates_clip(self, project):
        insert_intro_template(project)
        assert project.clip_count > 0

    def test_records_metadata(self, project):
        insert_intro_template(project, 'fancy')
        assert project.timeline._data['metadata']['pendingIntroTemplate'] == 'fancy'

    def test_import_from_builders(self):
        from camtasia.builders import insert_intro_template as iit
        assert iit is insert_intro_template
