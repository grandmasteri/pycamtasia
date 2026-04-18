"""Tests for uncovered lines in export/edl.py — UnifiedMedia audio event."""
from __future__ import annotations

import copy
from pathlib import Path

import pytest

from camtasia.export.edl import export_edl


def _inject_unified(project):
    """Add a UnifiedMedia clip to the project's first track."""
    tracks = project._data['timeline']['sceneTrack']['scenes'][0]['csml']['tracks']
    if not tracks:
        tracks.append({'trackIndex': 0, 'medias': []})
    tracks[0]['medias'].append({
        '_type': 'UnifiedMedia', 'id': 50, 'start': 0, 'duration': 705_600_000,
        'mediaStart': 0, 'mediaDuration': 705_600_000, 'scalar': 1,
        'parameters': {}, 'effects': [], 'metadata': {}, 'animationTracks': {},
        'video': {
            '_type': 'ScreenVMFile', 'id': 51, 'src': 999, 'start': 0,
            'duration': 705_600_000, 'mediaStart': 0, 'mediaDuration': 705_600_000,
            'scalar': 1, 'parameters': {}, 'effects': [], 'metadata': {},
        },
        'audio': {
            '_type': 'AMFile', 'id': 52, 'src': 999, 'start': 0,
            'duration': 705_600_000, 'mediaStart': 0, 'mediaDuration': 705_600_000,
            'scalar': 1, 'parameters': {}, 'effects': [], 'metadata': {},
        },
    })


class TestEdlUnifiedMedia:
    def test_unified_media_generates_video_and_audio_events(self, project, tmp_path):
        _inject_unified(project)
        out = export_edl(project, tmp_path / 'out.edl')
        lines = [l for l in out.read_text().splitlines() if l and l[0].isdigit()]
        # UnifiedMedia should produce 2 events: V + A
        assert len(lines) == 2
        assert 'V' in lines[0]
        assert 'A' in lines[1]

    def test_unified_media_source_id_from_video(self, project, tmp_path):
        _inject_unified(project)
        out = export_edl(project, tmp_path / 'out.edl')
        content = out.read_text()
        # Source should be 'AX' since src=999 doesn't exist in media bin
        assert 'AX' in content
