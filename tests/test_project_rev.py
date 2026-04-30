"""Tests for Project.apply_rev_layout and Project.apply_rev_style."""
from __future__ import annotations

import pytest


# ------------------------------------------------------------------
# apply_rev_layout
# ------------------------------------------------------------------

class TestApplyRevLayout:
    @pytest.mark.parametrize('layout', [
        'picture_in_picture',
        'side_by_side',
        'split_screen',
        'full_screen_camera',
        'full_screen_screen',
    ])
    def test_supported_layouts(self, project, layout):
        project.apply_rev_layout(layout)
        assert project._data['metadata']['pendingRevLayout'] == layout

    def test_invalid_layout_raises(self, project):
        with pytest.raises(ValueError, match='Unknown Rev layout'):
            project.apply_rev_layout('mosaic')

    def test_overwrites_previous_layout(self, project):
        project.apply_rev_layout('side_by_side')
        project.apply_rev_layout('split_screen')
        assert project._data['metadata']['pendingRevLayout'] == 'split_screen'

    def test_metadata_dict_created_if_absent(self, project):
        project._data.pop('metadata', None)
        project.apply_rev_layout('picture_in_picture')
        assert project._data['metadata']['pendingRevLayout'] == 'picture_in_picture'

    def test_preserves_existing_metadata(self, project):
        project._data.setdefault('metadata', {})['custom_key'] = 'value'
        project.apply_rev_layout('side_by_side')
        assert project._data['metadata']['custom_key'] == 'value'
        assert project._data['metadata']['pendingRevLayout'] == 'side_by_side'


# ------------------------------------------------------------------
# apply_rev_style
# ------------------------------------------------------------------

class TestApplyRevStyle:
    @pytest.mark.parametrize('style', [
        'modern',
        'minimal',
        'vibrant',
        'professional',
    ])
    def test_supported_styles(self, project, style):
        project.apply_rev_style(style)
        assert project._data['metadata']['pendingRevStyle'] == style

    def test_invalid_style_raises(self, project):
        with pytest.raises(ValueError, match='Unknown Rev style'):
            project.apply_rev_style('retro')

    def test_overwrites_previous_style(self, project):
        project.apply_rev_style('modern')
        project.apply_rev_style('vibrant')
        assert project._data['metadata']['pendingRevStyle'] == 'vibrant'

    def test_metadata_dict_created_if_absent(self, project):
        project._data.pop('metadata', None)
        project.apply_rev_style('minimal')
        assert project._data['metadata']['pendingRevStyle'] == 'minimal'

    def test_preserves_existing_metadata(self, project):
        project._data.setdefault('metadata', {})['other'] = 42
        project.apply_rev_style('professional')
        assert project._data['metadata']['other'] == 42
        assert project._data['metadata']['pendingRevStyle'] == 'professional'


# ------------------------------------------------------------------
# Combined layout + style
# ------------------------------------------------------------------

class TestRevLayoutAndStyleCombined:
    def test_layout_and_style_coexist(self, project):
        project.apply_rev_layout('picture_in_picture')
        project.apply_rev_style('modern')
        meta = project._data['metadata']
        assert meta['pendingRevLayout'] == 'picture_in_picture'
        assert meta['pendingRevStyle'] == 'modern'

    def test_style_then_layout(self, project):
        project.apply_rev_style('vibrant')
        project.apply_rev_layout('full_screen_camera')
        meta = project._data['metadata']
        assert meta['pendingRevStyle'] == 'vibrant'
        assert meta['pendingRevLayout'] == 'full_screen_camera'
