"""Tests for uncovered lines in operations/template.py — _walk_clips UnifiedMedia."""
from __future__ import annotations

from camtasia.operations.template import _walk_clips


class TestWalkClipsUnifiedMedia:
    def test_yields_unified_media_children(self):
        tracks = [{
            'medias': [{
                '_type': 'UnifiedMedia', 'id': 1,
                'video': {'_type': 'VMFile', 'id': 2, 'src': 10},
                'audio': {'_type': 'AMFile', 'id': 3, 'src': 10},
            }],
        }]
        clips = list(_walk_clips(tracks))
        ids = [c.get('id') for c in clips]
        assert 1 in ids  # parent
        assert 2 in ids  # video child
        assert 3 in ids  # audio child

    def test_unified_media_without_audio(self):
        tracks = [{
            'medias': [{
                '_type': 'UnifiedMedia', 'id': 1,
                'video': {'_type': 'VMFile', 'id': 2, 'src': 10},
            }],
        }]
        clips = list(_walk_clips(tracks))
        ids = [c.get('id') for c in clips]
        assert 2 in ids
        assert len(ids) == 2  # parent + video only
