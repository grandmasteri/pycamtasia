"""Tests for Track.split_clip()."""
from __future__ import annotations

import pytest

from camtasia.timeline.track import Track
from camtasia.timing import seconds_to_ticks, EDIT_RATE


def _make_track(*medias):
    """Build a Track with the given media dicts."""
    attrs = {'ident': 'test', 'audioMuted': False, 'videoHidden': False}
    data = {'trackIndex': 0, 'medias': list(medias)}
    return Track(attrs, data), data


def _simple_clip(clip_id=1, start_s=10.0, dur_s=10.0):
    """Return a simple VMFile clip dict."""
    return {
        'id': clip_id,
        '_type': 'VMFile',
        'src': 1,
        'trackNumber': 0,
        'start': seconds_to_ticks(start_s),
        'duration': seconds_to_ticks(dur_s),
        'mediaStart': 0,
        'mediaDuration': seconds_to_ticks(dur_s),
        'scalar': 1,
        'metadata': {},
        'parameters': {},
        'effects': [],
        'animationTracks': {},
    }


def _group_clip(clip_id=1, start_s=10.0, dur_s=10.0):
    """Return a Group clip dict with internal tracks."""
    return {
        'id': clip_id,
        '_type': 'Group',
        'trackNumber': 0,
        'start': seconds_to_ticks(start_s),
        'duration': seconds_to_ticks(dur_s),
        'mediaStart': 0,
        'mediaDuration': seconds_to_ticks(dur_s),
        'scalar': '6723/5755',
        'metadata': {},
        'parameters': {},
        'effects': [],
        'animationTracks': {},
        'attributes': {'ident': 'Rev Media'},
        'tracks': [
            {
                'trackIndex': 0,
                'medias': [{
                    'id': 2,
                    '_type': 'VMFile',
                    'src': 1,
                    'trackNumber': 0,
                    'start': 0,
                    'duration': seconds_to_ticks(dur_s),
                    'mediaStart': 0,
                    'mediaDuration': seconds_to_ticks(dur_s),
                    'scalar': 1,
                    'metadata': {},
                    'parameters': {},
                    'effects': [],
                    'animationTracks': {},
                }],
            },
            {
                'trackIndex': 1,
                'medias': [{
                    'id': 3,
                    '_type': 'UnifiedMedia',
                    'video': {
                        'id': 4,
                        '_type': 'ScreenVMFile',
                        'src': 2,
                        'trackNumber': 0,
                        'start': 0,
                        'duration': seconds_to_ticks(dur_s),
                        'mediaStart': 0,
                        'mediaDuration': seconds_to_ticks(dur_s),
                        'scalar': 1,
                    },
                    'audio': {
                        'id': 5,
                        '_type': 'AMFile',
                        'src': 2,
                        'trackNumber': 1,
                    },
                    'effects': [],
                    'start': 0,
                    'duration': seconds_to_ticks(dur_s),
                    'mediaStart': 0,
                    'mediaDuration': seconds_to_ticks(dur_s),
                    'scalar': 1,
                }],
            },
        ],
    }


class TestSplitClip:
    def test_split_creates_two_clips(self):
        track, data = _make_track(_simple_clip())
        track.split_clip(1, 15.0)
        assert len(data['medias']) == 2

    def test_split_durations_add_up(self):
        orig_dur = seconds_to_ticks(10.0)
        track, data = _make_track(_simple_clip())
        left, right = track.split_clip(1, 15.0)
        assert left.duration + right.duration == orig_dur

    def test_split_right_media_start(self):
        track, _ = _make_track(_simple_clip())
        left, right = track.split_clip(1, 15.0)
        expected_offset = seconds_to_ticks(15.0) - seconds_to_ticks(10.0)
        assert right.media_start == expected_offset

    def test_split_preserves_scalar(self):
        track, _ = _make_track(_group_clip())
        left, right = track.split_clip(1, 15.0)
        assert left.scalar == right.scalar

    def test_split_assigns_new_ids(self):
        track, data = _make_track(_group_clip())
        left, right = track.split_clip(1, 15.0)
        # Right half gets a new group ID different from left
        assert right.id != left.id
        # All IDs in right half's internal tracks should be new
        left_ids = _collect_ids(data['medias'][0])
        right_ids = _collect_ids(data['medias'][1])
        assert left_ids.isdisjoint(right_ids)


def _collect_ids(media_dict):
    """Collect all IDs from a media dict including internal tracks."""
    ids = {media_dict['id']}
    for t in media_dict.get('tracks', []):
        for m in t.get('medias', []):
            ids.add(m['id'])
            if 'video' in m:
                ids.add(m['video']['id'])
            if 'audio' in m:
                ids.add(m['audio']['id'])
    return ids
