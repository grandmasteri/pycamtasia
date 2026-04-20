"""Tests for Project.validate() — pre-save validation checks."""
from __future__ import annotations

from pathlib import Path
import shutil
from unittest.mock import patch

from camtasia.media_bin import MediaType
from camtasia.project import load_project
from camtasia.validation import ValidationIssue

RESOURCES = Path(__file__).parent.parent / 'src' / 'camtasia' / 'resources'


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
        ValidationIssue('warning', 'Missing source file: media/test.wav', 100),
        ValidationIssue('error', 'Zero-range audio source: media/test.wav', 100),
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
        ValidationIssue('warning', 'Missing source file: media/test.png', 200),
        ValidationIssue('error', 'Zero-dimension image source: media/test.png', 200),
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
    assert result == []


def test_validate_does_not_use_bin_ids_variable(project):
    """Bug 4: validate() should not populate an unused bin_ids set."""
    import ast
    import inspect
    import textwrap
    source = textwrap.dedent(inspect.getsource(project.validate))
    tree = ast.parse(source)
    names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
    assert 'bin_ids' not in names


def test_validate_unified_media_sub_clip_src_not_orphaned(project):
    """Bug 3: validate() should not flag media referenced only by UnifiedMedia sub-clips as orphaned."""
    # Add a media entry to the source bin
    project._data.setdefault('sourceBin', []).append({
        'id': 50, 'src': './media/test.mov', 'rect': [0, 0, 100, 100],
        'lastMod': '20260101T000000',
        'sourceTracks': [{'type': 0, 'range': [0, 100], 'editRate': 30,
                          'trackRect': [0, 0, 100, 100], 'sampleRate': 30,
                          'bitDepth': 24, 'numChannels': 0,
                          'integratedLUFS': 100.0, 'peakLevel': -1.0,
                          'tag': 0, 'metaData': '', 'parameters': {}}],
    })
    media_id = 50
    track = project.timeline.add_track('V')
    # Add a UnifiedMedia clip where only the video child references the media
    track._data['medias'] = [{
        'id': 100, '_type': 'UnifiedMedia',
        'start': 0, 'duration': 1000, 'mediaStart': 0, 'mediaDuration': 1000,
        'scalar': 1, 'metadata': {}, 'parameters': {}, 'effects': [],
        'attributes': {}, 'animationTracks': {},
        'video': {
            'id': 101, '_type': 'VMFile', 'src': media_id,
            'start': 0, 'duration': 1000, 'mediaStart': 0, 'mediaDuration': 1000,
            'scalar': 1, 'metadata': {}, 'parameters': {}, 'effects': [],
            'attributes': {}, 'animationTracks': {},
        },
        'audio': {
            'id': 102, '_type': 'AMFile', 'src': media_id,
            'start': 0, 'duration': 1000, 'mediaStart': 0, 'mediaDuration': 1000,
            'scalar': 1, 'metadata': {}, 'parameters': {}, 'effects': [],
            'attributes': {}, 'animationTracks': {},
        },
    }]

    issues = project.validate()
    orphan_issues = [i for i in issues if 'Orphaned media' in i.message]
    assert len(orphan_issues) == 0, f"Unexpected orphan issues: {orphan_issues}"


# ── Bug 1: validate() uses self.all_clips (recurses into Groups) ────


def test_validate_does_not_report_orphaned_media_referenced_by_group_child(project):
    """Media referenced only by a nested Group child should not be orphaned."""
    # Add media entry
    project.media_bin.add_media_entry({
        'id': 50,
        'src': './media/nested.mov',
        'rect': [0, 0, 1920, 1080],
        'lastMod': '20260101T000000',
        'sourceTracks': [{'range': [0, 5000], 'type': 0, 'editRate': 30,
                          'trackRect': [0, 0, 1920, 1080], 'sampleRate': 30,
                          'bitDepth': 24, 'numChannels': 0,
                          'integratedLUFS': 100.0, 'peakLevel': -1.0,
                          'tag': 0, 'metaData': '', 'parameters': {}}],
        'metadata': {},
    })
    # Create a Group clip whose inner child references media 50
    from camtasia.timing import seconds_to_ticks
    track = project.timeline.tracks[0]
    group_data = {
        'id': 99, '_type': 'Group',
        'start': 0, 'duration': seconds_to_ticks(5.0),
        'mediaStart': 0, 'mediaDuration': seconds_to_ticks(5.0),
        'scalar': 1, 'metadata': {}, 'parameters': {},
        'effects': [], 'attributes': {'ident': ''},
        'animationTracks': {},
        'tracks': [{'medias': [{
            'id': 100, '_type': 'VMFile', 'src': 50,
            'start': 0, 'duration': seconds_to_ticks(5.0),
            'mediaStart': 0, 'mediaDuration': seconds_to_ticks(5.0),
            'scalar': 1, 'metadata': {}, 'parameters': {},
            'effects': [], 'attributes': {}, 'animationTracks': {},
        }]}],
    }
    track._data.setdefault('medias', []).append(group_data)

    issues = project.validate()
    orphan_messages = [i.message for i in issues if 'Orphaned' in i.message and 'nested.mov' in i.message]
    assert orphan_messages == [], f'Media 50 falsely reported as orphaned: {orphan_messages}'
