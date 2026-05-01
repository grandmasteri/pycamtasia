"""Tests for add_intro template_name and library_asset parameters."""
from __future__ import annotations

from camtasia.builders.video_production import VideoProductionBuilder


class TestAddIntroTemplateName:
    def test_template_name_recorded_in_metadata(self, project):
        builder = VideoProductionBuilder(project)
        builder.add_intro(title='Hello', template_name='corporate')
        builder.build()
        meta = project.timeline._data.get('metadata', {})
        assert meta['introTemplateName'] == 'corporate'

    def test_library_asset_recorded_in_metadata(self, project):
        builder = VideoProductionBuilder(project)
        builder.add_intro(title='Hello', library_asset='intro-v2.camlib')
        builder.build()
        meta = project.timeline._data.get('metadata', {})
        assert meta['introLibraryAsset'] == 'intro-v2.camlib'

    def test_both_template_and_asset(self, project):
        builder = VideoProductionBuilder(project)
        builder.add_intro(
            title='Hello',
            template_name='fancy',
            library_asset='fancy.camlib',
        )
        builder.build()
        meta = project.timeline._data.get('metadata', {})
        assert meta['introTemplateName'] == 'fancy'
        assert meta['introLibraryAsset'] == 'fancy.camlib'

    def test_no_template_no_metadata(self, project):
        builder = VideoProductionBuilder(project)
        builder.add_intro(title='Hello')
        builder.build()
        meta = project.timeline._data.get('metadata', {})
        assert 'introTemplateName' not in meta
        assert 'introLibraryAsset' not in meta

    def test_still_creates_title_card(self, project):
        builder = VideoProductionBuilder(project)
        builder.add_intro(title='Hello', template_name='corporate')
        result = builder.build()
        assert result['has_intro'] is True
        assert project.clip_count > 0

    def test_fluent_chaining_with_template(self, project):
        builder = VideoProductionBuilder(project)
        ret = builder.add_intro(title='X', template_name='t')
        assert ret is builder
