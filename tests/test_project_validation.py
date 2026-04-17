"""Tests for Project.validate() — pre-save validation checks."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from camtasia.project import load_project
from camtasia.validation import ValidationIssue
from camtasia.media_bin import MediaType

RESOURCES = Path(__file__).parent.parent / 'src' / 'camtasia' / 'resources'


# Module-level list to prevent TemporaryDirectory from being GC'd during test
_TEMP_DIRS: list = []

def _isolated_project():
    """Load template into an isolated temp copy (safe for parallel execution)."""
    import shutil, tempfile
    from camtasia.project import load_project
    td = tempfile.TemporaryDirectory()
    _TEMP_DIRS.append(td)  # prevent premature GC
    dst = Path(td.name) / 'test.cmproj'
    shutil.copytree(RESOURCES / 'new.cmproj', dst)
    return load_project(dst)

def project():
    return _isolated_project()


def test_validate_clean_project_returns_no_issues(project):
    actual_issues = project.validate()
    expected_issues = []
    assert actual_issues == expected_issues


def test_validate_detects_zero_range_audio(project):
    project.media_bin.add_media_entry({
        'id': 100,
        'src': './media/test.wav',
        'rect': [0, 0, 0, 0],
        'lastMod': '20260101T000000',
        'sourceTracks': [{'range': [0, 0], 'type': MediaType.Audio.value,
                          'editRate': 44100, 'trackRect': [0, 0, 0, 0],
                          'sampleRate': 44100, 'bitDepth': 16,
                          'numChannels': 2, 'integratedLUFS': 100.0,
                          'peakLevel': -1.0, 'tag': 0, 'metaData': '',
                          'parameters': {}}],
        'metadata': {},
    })

    actual_issues = project.validate()
    expected_issues = [
        ValidationIssue('error', 'Zero-range audio source: media/test.wav', 100),
        ValidationIssue('warning', 'Missing source file: media/test.wav', 100),
        ValidationIssue('warning', 'Orphaned media not used by any clip: media/test.wav', 100),
    ]
    assert actual_issues == expected_issues


def test_validate_detects_zero_dimension_image(project):
    project.media_bin.add_media_entry({
        'id': 200,
        'src': './media/test.png',
        'rect': [0, 0, 0, 0],
        'lastMod': '20260101T000000',
        'sourceTracks': [{'range': [0, 1], 'type': MediaType.Image.value,
                          'editRate': 1000, 'trackRect': [0, 0, 0, 0],
                          'sampleRate': 0, 'bitDepth': 0,
                          'numChannels': 0, 'integratedLUFS': 100.0,
                          'peakLevel': -1.0, 'tag': 0, 'metaData': '',
                          'parameters': {}}],
        'metadata': {},
    })

    actual_issues = project.validate()
    expected_issues = [
        ValidationIssue('error', 'Zero-dimension image source: media/test.png', 200),
        ValidationIssue('warning', 'Missing source file: media/test.png', 200),
        ValidationIssue('warning', 'Orphaned media not used by any clip: media/test.png', 200),
    ]
    assert actual_issues == expected_issues


def test_validate_detects_orphaned_media(project):
    # Add a source bin entry that no clip references
    project._data.setdefault('sourceBin', []).append({
        'id': 300,
        'src': './media/orphaned.mov',
        'rect': [0, 0, 1920, 1080],
        'lastMod': '20260101T000000',
        'sourceTracks': [{'range': [0, 9000], 'type': MediaType.Video.value,
                          'editRate': 30, 'trackRect': [0, 0, 1920, 1080],
                          'sampleRate': 0, 'bitDepth': 0,
                          'numChannels': 0, 'integratedLUFS': 100.0,
                          'peakLevel': -1.0, 'tag': 0, 'metaData': '',
                          'parameters': {}}],
        'metadata': {},
    })

    actual_issues = project.validate()
    orphaned = [i for i in actual_issues if 'Orphaned' in i.message]
    assert len(orphaned) == 1
    assert 'orphaned.mov' in orphaned[0].message


def test_validate_detects_missing_source_file(project):
    project.media_bin.add_media_entry({
        'id': 400,
        'src': './media/nonexistent.mp4',
        'rect': [0, 0, 1920, 1080],
        'lastMod': '20260101T000000',
        'sourceTracks': [{'range': [0, 9000], 'type': MediaType.Video.value,
                          'editRate': 30, 'trackRect': [0, 0, 1920, 1080],
                          'sampleRate': 0, 'bitDepth': 0,
                          'numChannels': 0, 'integratedLUFS': 100.0,
                          'peakLevel': -1.0, 'tag': 0, 'metaData': '',
                          'parameters': {}}],
        'metadata': {},
    })
    # Also place a clip referencing it so it's not orphaned
    project.timeline.tracks[0].add_clip('VMFile', 400, 0, 1000)

    actual_issues = project.validate()
    expected_issues = [
        ValidationIssue('warning', 'Missing source file: media/nonexistent.mp4', 400),
    ]
    assert actual_issues == expected_issues


def test_validate_detects_invalid_clip_reference(project):
    # Add a clip referencing a source ID that doesn't exist in the bin
    project.timeline.tracks[0].add_clip('VMFile', 999, 0, 1000)

    actual_issues = project.validate()
    expected_issues = [
        ValidationIssue('error', 'track[0] clip id=2 src=999 not found in sourceBin', source_id=None),
    ]
    assert actual_issues == expected_issues


def test_save_calls_validate(project, tmp_path):
    import shutil
    # Copy the project to a temp dir so save() can write
    proj_dir = tmp_path / 'test.cmproj'
    shutil.copytree(RESOURCES / 'new.cmproj', proj_dir)
    proj = load_project(proj_dir)

    with patch.object(proj, 'validate', wraps=proj.validate) as mock_validate:
        proj.save()
    mock_validate.assert_called_once()


def test_validate_schema_returns_list(project):
    """validate_schema returns a list of ValidationIssue."""
    result = project.validate_schema()
    assert isinstance(result, list)
