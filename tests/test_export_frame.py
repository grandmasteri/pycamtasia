"""Tests for Project.export_frame() and export_frame_and_import()."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from camtasia.project import load_project

RESOURCES = Path(__file__).parent.parent / 'src' / 'camtasia' / 'resources'


@pytest.fixture
def project():
    return load_project(RESOURCES / 'new.cmproj')


@patch('camtasia.project._sp.run')
def test_export_frame_calls_ffmpeg_correctly(mock_run, project):
    mock_run.return_value = MagicMock(returncode=0)
    video = Path('/tmp/demo.mp4')

    project.export_frame(video, 5.0, output_path='/tmp/out.png')

    mock_run.assert_called_once_with(
        ['ffmpeg', '-ss', '5.0', '-i', str(video),
         '-frames:v', '1', '-q:v', '2', '/tmp/out.png'],
        capture_output=True, text=True,
    )


@patch('camtasia.project._sp.run')
def test_export_frame_default_output_path(mock_run, project):
    mock_run.return_value = MagicMock(returncode=0)

    result = project.export_frame('/tmp/clip.mp4', 2.5)

    expected = project.file_path / 'media' / 'clip_frame_2.500s.png'
    assert result == expected


@patch('camtasia.project._sp.run')
def test_export_frame_custom_output_path(mock_run, project):
    mock_run.return_value = MagicMock(returncode=0)

    result = project.export_frame('/tmp/clip.mp4', 1.0, output_path='/custom/frame.png')

    assert result == Path('/custom/frame.png')


@patch('camtasia.project._sp.run')
@patch('camtasia.project._probe_media')
def test_export_frame_and_import_returns_media(mock_probe, mock_run, project):
    mock_run.return_value = MagicMock(returncode=0)
    mock_probe.return_value = {'width': 1920, 'height': 1080}

    # Create the file that export_frame would produce so import_media can find it
    expected_png = project.file_path / 'media' / 'clip_frame_3.000s.png'
    expected_png.parent.mkdir(parents=True, exist_ok=True)
    expected_png.write_bytes(b'\x89PNG')

    try:
        media = project.export_frame_and_import('/tmp/clip.mp4', 3.0)
        assert media is not None
        assert media.source.name.endswith('.png')
    finally:
        expected_png.unlink(missing_ok=True)


@patch('camtasia.project._sp.run')
def test_export_frame_raises_on_ffmpeg_failure(mock_run, project):
    mock_run.return_value = MagicMock(returncode=1, stderr='encode error')

    with pytest.raises(RuntimeError, match='ffmpeg failed'):
        project.export_frame('/tmp/clip.mp4', 0.0, output_path='/tmp/out.png')
