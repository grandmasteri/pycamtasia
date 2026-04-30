"""Tests for Track.promote_marker_to_media and Track.demote_marker_to_timeline."""
from __future__ import annotations

import pytest

from camtasia.timeline.track import Track


def _make_track(markers=None, medias=None):
    """Build a minimal Track with optional timeline markers and clips."""
    params = {}
    if markers:
        params['toc'] = {
            'type': 'string',
            'keyframes': [
                {'time': t, 'endTime': t, 'value': n, 'duration': 0}
                for n, t in markers
            ],
        }
    data = {
        'trackIndex': 0,
        'medias': medias or [],
        'parameters': params,
        'transitions': [],
    }
    attrs = {'ident': 'Track 1'}
    return Track(attrs, data)


def _make_clip(clip_id, clip_type='VMFile', media_markers=None):
    """Build a minimal clip dict with optional media markers."""
    clip = {
        'id': clip_id,
        '_type': clip_type,
        'start': 0,
        'duration': 1000,
        'mediaStart': 0,
        'mediaDuration': 1000,
        'scalar': 1,
        'parameters': {},
        'effects': [],
        'metadata': {},
        'animationTracks': {},
    }
    if media_markers:
        clip['parameters']['toc'] = {
            'type': 'string',
            'keyframes': [
                {'time': t, 'endTime': t, 'value': n, 'duration': 0}
                for n, t in media_markers
            ],
        }
    return clip


class TestPromoteMarkerToMedia:
    def test_moves_marker_from_track_to_clip(self):
        clip = _make_clip(10)
        track = _make_track(markers=[('ChapterA', 500)], medias=[clip])
        track.promote_marker_to_media(500, 10)
        assert list(track.markers) == []
        clip_kfs = clip['parameters']['toc']['keyframes']
        assert len(clip_kfs) == 1
        assert clip_kfs[0]['value'] == 'ChapterA'
        assert clip_kfs[0]['time'] == 500

    def test_preserves_other_timeline_markers(self):
        clip = _make_clip(10)
        track = _make_track(markers=[('A', 100), ('B', 200)], medias=[clip])
        track.promote_marker_to_media(100, 10)
        remaining = [(m.name, m.time) for m in track.markers]
        assert remaining == [('B', 200)]

    def test_raises_on_missing_marker(self):
        clip = _make_clip(10)
        track = _make_track(markers=[], medias=[clip])
        with pytest.raises(KeyError, match='No timeline marker at time=999'):
            track.promote_marker_to_media(999, 10)

    def test_raises_on_missing_clip(self):
        track = _make_track(markers=[('A', 100)])
        with pytest.raises(KeyError, match='No clip with id=99'):
            track.promote_marker_to_media(100, 99)

    def test_appends_to_existing_media_markers(self):
        clip = _make_clip(10, media_markers=[('Existing', 50)])
        track = _make_track(markers=[('New', 200)], medias=[clip])
        track.promote_marker_to_media(200, 10)
        clip_kfs = clip['parameters']['toc']['keyframes']
        assert [(kf['value'], kf['time']) for kf in clip_kfs] == [
            ('Existing', 50),
            ('New', 200),
        ]

    def test_creates_toc_structure_when_absent(self):
        clip = _make_clip(10)
        clip['parameters'] = {}
        track = _make_track(markers=[('M', 300)], medias=[clip])
        track.promote_marker_to_media(300, 10)
        assert clip['parameters']['toc']['keyframes'][0]['value'] == 'M'


class TestDemoteMarkerToTimeline:
    def test_moves_marker_from_clip_to_track(self):
        clip = _make_clip(10, media_markers=[('MediaM', 400)])
        track = _make_track(medias=[clip])
        track.demote_marker_to_timeline(10, 400)
        clip_kfs = clip['parameters']['toc']['keyframes']
        assert clip_kfs == []
        track_kfs = track._data['parameters']['toc']['keyframes']
        assert len(track_kfs) == 1
        assert track_kfs[0]['value'] == 'MediaM'

    def test_raises_on_missing_clip(self):
        track = _make_track()
        with pytest.raises(KeyError, match='No clip with id=99'):
            track.demote_marker_to_timeline(99, 100)

    def test_raises_on_missing_media_marker(self):
        clip = _make_clip(10)
        track = _make_track(medias=[clip])
        with pytest.raises(KeyError, match='No media marker at time=999'):
            track.demote_marker_to_timeline(10, 999)

    def test_roundtrip_promote_then_demote(self):
        clip = _make_clip(10)
        track = _make_track(markers=[('RT', 600)], medias=[clip])
        track.promote_marker_to_media(600, 10)
        assert list(track.markers) == []
        track.demote_marker_to_timeline(10, 600)
        assert [(m.name, m.time) for m in track.markers] == [('RT', 600)]
        assert clip['parameters']['toc']['keyframes'] == []

    def test_preserves_other_media_markers(self):
        clip = _make_clip(10, media_markers=[('Keep', 100), ('Remove', 200)])
        track = _make_track(medias=[clip])
        track.demote_marker_to_timeline(10, 200)
        clip_kfs = clip['parameters']['toc']['keyframes']
        assert [(kf['value'], kf['time']) for kf in clip_kfs] == [('Keep', 100)]

    def test_creates_track_toc_when_absent(self):
        clip = _make_clip(10, media_markers=[('M', 300)])
        track = _make_track(medias=[clip])
        track._data['parameters'] = {}
        track.demote_marker_to_timeline(10, 300)
        assert track._data['parameters']['toc']['keyframes'][0]['value'] == 'M'
