"""Tests for Project.preview_frame and Project.render_canvas_preview."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from camtasia.timing import seconds_to_ticks


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _add_video_clip(project, start_seconds=0.0, duration_seconds=10.0, track_name='Video'):
    """Add a VMFile clip and return its ID."""
    track = project.timeline.get_or_create_track(track_name)
    media_id = project.media_bin.next_id()
    project._data.setdefault('sourceBin', []).append({
        'id': media_id,
        'src': './media/video.mp4',
        'rect': [0, 0, 1920, 1080],
        'sourceTracks': [{'range': [0, 300], 'type': 0, 'editRate': 30,
                          'trackRect': [0, 0, 1920, 1080], 'sampleRate': 48000,
                          'bitDepth': 16, 'numChannels': 2}],
    })
    clip = track.add_video(media_id, start_seconds=start_seconds, duration_seconds=duration_seconds)
    return clip.id


def _add_image_clip_with_effect(project, start_seconds=0.0, duration_seconds=5.0):
    """Add an IMFile clip with a drop shadow effect and return its ID."""
    track = project.timeline.get_or_create_track('Images')
    media_id = project.media_bin.next_id()
    project._data.setdefault('sourceBin', []).append({
        'id': media_id,
        'src': './media/image.png',
        'rect': [0, 0, 1920, 1080],
        'sourceTracks': [{'range': [0, 1], 'type': 2, 'editRate': 1,
                          'trackRect': [0, 0, 1920, 1080]}],
    })
    clip = track.add_image(media_id, start_seconds=start_seconds, duration_seconds=duration_seconds)
    clip.add_drop_shadow()
    return clip.id


# ------------------------------------------------------------------
# preview_frame
# ------------------------------------------------------------------

class TestPreviewFrame:
    def test_empty_project_returns_empty(self, project):
        result = project.preview_frame(0.0)
        assert result == {'clips': [], 'effects': []}

    def test_visible_clip_at_time(self, project):
        clip_id = _add_video_clip(project, start_seconds=0.0, duration_seconds=10.0)
        result = project.preview_frame(5.0)
        assert len(result['clips']) >= 1
        clip_ids = [c['id'] for c in result['clips']]
        assert clip_id in clip_ids

    def test_clip_not_visible_before_start(self, project):
        _add_video_clip(project, start_seconds=5.0, duration_seconds=5.0)
        result = project.preview_frame(2.0)
        assert result['clips'] == []

    def test_clip_not_visible_after_end(self, project):
        _add_video_clip(project, start_seconds=0.0, duration_seconds=5.0)
        result = project.preview_frame(6.0)
        assert result['clips'] == []

    def test_clip_visible_at_start_boundary(self, project):
        clip_id = _add_video_clip(project, start_seconds=2.0, duration_seconds=3.0)
        result = project.preview_frame(2.0)
        clip_ids = [c['id'] for c in result['clips']]
        assert clip_id in clip_ids

    def test_effects_included(self, project):
        clip_id = _add_image_clip_with_effect(project, start_seconds=0.0, duration_seconds=5.0)
        result = project.preview_frame(1.0)
        assert len(result['effects']) >= 1
        assert any(e['clip_id'] == clip_id for e in result['effects'])

    def test_multiple_clips_on_different_tracks(self, project):
        id1 = _add_video_clip(project, start_seconds=0.0, duration_seconds=10.0, track_name='Track A')
        id2 = _add_video_clip(project, start_seconds=0.0, duration_seconds=10.0, track_name='Track B')
        result = project.preview_frame(5.0)
        clip_ids = {c['id'] for c in result['clips']}
        assert {id1, id2} <= clip_ids

    def test_clip_info_contains_track_name(self, project):
        _add_video_clip(project, start_seconds=0.0, duration_seconds=5.0, track_name='MyTrack')
        result = project.preview_frame(1.0)
        tracks = [c['track'] for c in result['clips']]
        assert 'MyTrack' in tracks

    def test_clip_info_contains_type(self, project):
        _add_video_clip(project, start_seconds=0.0, duration_seconds=5.0)
        result = project.preview_frame(1.0)
        types = [c['type'] for c in result['clips']]
        assert 'VMFile' in types


# ------------------------------------------------------------------
# render_canvas_preview
# ------------------------------------------------------------------

class TestRenderCanvasPreview:
    def test_writes_json_file(self, project, tmp_path):
        _add_video_clip(project, start_seconds=0.0, duration_seconds=10.0)
        out = tmp_path / 'preview.json'
        result = project.render_canvas_preview(5.0, out)
        assert result == out
        assert out.exists()
        data = json.loads(out.read_text())
        assert data['time_seconds'] == 5.0

    def test_canvas_dimensions_in_output(self, project, tmp_path):
        out = tmp_path / 'preview.json'
        project.render_canvas_preview(0.0, out)
        data = json.loads(out.read_text())
        assert data['canvas'] == {'width': project.width, 'height': project.height}

    def test_stub_note_present(self, project, tmp_path):
        out = tmp_path / 'preview.json'
        project.render_canvas_preview(0.0, out)
        data = json.loads(out.read_text())
        assert 'Camtasia engine' in data['_note']

    def test_frame_data_matches_preview_frame(self, project, tmp_path):
        _add_video_clip(project, start_seconds=0.0, duration_seconds=10.0)
        out = tmp_path / 'preview.json'
        project.render_canvas_preview(3.0, out)
        data = json.loads(out.read_text())
        expected = project.preview_frame(3.0)
        assert data['frame']['clips'] == expected['clips']
        assert data['frame']['effects'] == expected['effects']

    def test_creates_parent_directories(self, project, tmp_path):
        out = tmp_path / 'nested' / 'dir' / 'preview.json'
        project.render_canvas_preview(0.0, out)
        assert out.exists()

    def test_empty_project_produces_valid_json(self, project, tmp_path):
        out = tmp_path / 'empty.json'
        project.render_canvas_preview(0.0, out)
        data = json.loads(out.read_text())
        assert data['frame'] == {'clips': [], 'effects': []}
