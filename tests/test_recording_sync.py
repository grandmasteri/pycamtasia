"""Tests for ScreenRecordingSync."""

from __future__ import annotations

from fractions import Fraction

import pytest

from camtasia.operations.recording_sync import ScreenRecordingSync, _find_clip_by_id
from camtasia.timing import EDIT_RATE


def _make_project_data(screen_clip, voice_clip, extra_tracks=None):
    """Build minimal project data with two clips on separate tracks."""
    tracks = [
        {'trackIndex': 0, 'medias': [screen_clip]},
        {'trackIndex': 1, 'medias': [voice_clip]},
    ]
    if extra_tracks:
        tracks.extend(extra_tracks)
    return {
        'sourceBin': [],
        'timeline': {
            'sceneTrack': {
                'scenes': [{
                    'csml': {
                        'tracks': tracks,
                    }
                }]
            },
            'parameters': {},
        },
    }


def _screen_clip(clip_id=5, duration=10 * EDIT_RATE, media_duration=10 * EDIT_RATE):
    return {
        'id': clip_id,
        '_type': 'ScreenVMFile',
        'start': 0,
        'duration': duration,
        'mediaDuration': media_duration,
        'mediaStart': 0,
        'scalar': 1,
        'metadata': {},
        'effects': [],
        'parameters': {},
    }


def _voice_clip(clip_id=10, duration=20 * EDIT_RATE):
    return {
        'id': clip_id,
        '_type': 'AMFile',
        'start': 0,
        'duration': duration,
        'mediaDuration': duration,
        'mediaStart': 0,
        'scalar': 1,
        'metadata': {},
        'effects': [],
        'parameters': {},
    }


def _group_clip(clip_id=5, duration=10 * EDIT_RATE, inner_src=1):
    """Build a Group clip with an internal UnifiedMedia screen recording."""
    inner_dur = duration
    return {
        'id': clip_id,
        '_type': 'Group',
        'start': 0,
        'duration': duration,
        'mediaDuration': duration,
        'mediaStart': 0,
        'scalar': 1,
        'metadata': {},
        'effects': [],
        'parameters': {},
        'attributes': {'ident': 'Screen Recording'},
        'tracks': [{
            'trackIndex': 0,
            'medias': [{
                'id': clip_id + 100,
                '_type': 'UnifiedMedia',
                'start': 0,
                'duration': inner_dur,
                'mediaDuration': inner_dur,
                'mediaStart': 0,
                'scalar': 1,
                'src': inner_src,
                'metadata': {},
                'effects': [],
                'parameters': {},
                'attributes': {'ident': ''},
                'video': {
                    'id': clip_id + 101,
                    '_type': 'ScreenVMFile',
                    'src': inner_src,
                    'start': 0,
                    'duration': inner_dur,
                    'mediaDuration': inner_dur,
                    'mediaStart': 0,
                    'scalar': 1,
                    'trackNumber': 0,
                    'metadata': {},
                    'effects': [],
                    'parameters': {},
                    'attributes': {'ident': ''},
                },
                'audio': {
                    'id': clip_id + 102,
                    '_type': 'AMFile',
                    'src': inner_src,
                    'start': 0,
                    'duration': inner_dur,
                    'mediaDuration': inner_dur,
                    'mediaStart': 0,
                    'scalar': 1,
                    'trackNumber': 1,
                    'metadata': {},
                    'effects': [],
                    'parameters': {},
                    'attributes': {'ident': ''},
                },
            }],
        }],
    }


class FakeProject:
    """Minimal stand-in for Project with _data and timeline."""

    def __init__(self, data):
        self._data = data
        self.timeline = FakeTimeline(data)


class FakeTimeline:
    def __init__(self, data):
        self._data = data

    @property
    def tracks(self):
        return [
            FakeTrack(t)
            for t in self._data['timeline']['sceneTrack']['scenes'][0]['csml']['tracks']
        ]


class FakeTrack:
    def __init__(self, data):
        self._data = data

    @property
    def clips(self):
        from camtasia.timeline.clips import clip_from_dict
        return [clip_from_dict(m) for m in self._data.get('medias', [])]


# ── _find_clip_by_id ──────────────────────────────────────────────

class TestFindClipById:
    def test_finds_top_level_clip(self):
        data = _make_project_data(_screen_clip(5), _voice_clip(10))
        assert _find_clip_by_id(data, 5) is not None
        assert _find_clip_by_id(data, 5)['id'] == 5

    def test_finds_nested_clip_in_group(self):
        group = _group_clip(5)
        data = _make_project_data(group, _voice_clip(10))
        # inner UnifiedMedia has id=105
        found = _find_clip_by_id(data, 105)
        assert found is not None
        assert found['id'] == 105

    def test_returns_none_for_missing(self):
        data = _make_project_data(_screen_clip(5), _voice_clip(10))
        assert _find_clip_by_id(data, 999) is None


# ── match_duration (basic mode) ───────────────────────────────────

class TestMatchDuration:
    def test_basic_speed_match(self):
        """Screen 10s source → voiceover 20s → scalar should be 2."""
        sc = _screen_clip(5, duration=10 * EDIT_RATE, media_duration=10 * EDIT_RATE)
        vo = _voice_clip(10, duration=20 * EDIT_RATE)
        data = _make_project_data(sc, vo)
        proj = FakeProject(data)

        sync = ScreenRecordingSync(proj)
        result = sync.match_duration(screen_clip_id=5, voiceover_clip_id=10)

        assert result == Fraction(2)
        assert sc['duration'] == 20 * EDIT_RATE
        assert sc['mediaDuration'] == int(Fraction(20 * EDIT_RATE) / Fraction(2))
        assert sc['metadata']['clipSpeedAttribute']['value'] is True

    def test_speed_up(self):
        """Screen 20s source → voiceover 10s → scalar should be 1/2."""
        sc = _screen_clip(5, duration=20 * EDIT_RATE, media_duration=20 * EDIT_RATE)
        vo = _voice_clip(10, duration=10 * EDIT_RATE)
        data = _make_project_data(sc, vo)
        proj = FakeProject(data)

        sync = ScreenRecordingSync(proj)
        result = sync.match_duration(screen_clip_id=5, voiceover_clip_id=10)

        assert result == Fraction(1, 2)
        assert sc['duration'] == 10 * EDIT_RATE

    def test_same_duration_scalar_one(self):
        """When durations match, scalar is 1 and clipSpeedAttribute is False."""
        dur = 15 * EDIT_RATE
        sc = _screen_clip(5, duration=dur, media_duration=dur)
        vo = _voice_clip(10, duration=dur)
        data = _make_project_data(sc, vo)
        proj = FakeProject(data)

        sync = ScreenRecordingSync(proj)
        result = sync.match_duration(screen_clip_id=5, voiceover_clip_id=10)

        assert result == Fraction(1)
        assert sc['scalar'] == 1
        assert sc['metadata']['clipSpeedAttribute']['value'] is False

    def test_propagates_to_unified_children(self):
        """UnifiedMedia children get updated duration, scalar, mediaDuration, mediaStart, and clipSpeedAttribute."""
        sc = _screen_clip(5, duration=10 * EDIT_RATE, media_duration=10 * EDIT_RATE)
        sc['_type'] = 'UnifiedMedia'
        sc['video'] = {'id': 50, '_type': 'ScreenVMFile', 'duration': 10 * EDIT_RATE, 'scalar': 1, 'metadata': {}}
        sc['audio'] = {'id': 51, '_type': 'AMFile', 'duration': 10 * EDIT_RATE, 'scalar': 1, 'metadata': {}}
        vo = _voice_clip(10, duration=20 * EDIT_RATE)
        data = _make_project_data(sc, vo)
        proj = FakeProject(data)

        sync = ScreenRecordingSync(proj)
        sync.match_duration(screen_clip_id=5, voiceover_clip_id=10)

        assert sc['video']['duration'] == 20 * EDIT_RATE
        assert sc['audio']['duration'] == 20 * EDIT_RATE
        # mediaDuration propagated
        assert sc['video']['mediaDuration'] == sc['mediaDuration']
        assert sc['audio']['mediaDuration'] == sc['mediaDuration']
        # mediaStart propagated
        assert sc['video']['mediaStart'] == sc.get('mediaStart', 0)
        assert sc['audio']['mediaStart'] == sc.get('mediaStart', 0)
        # clipSpeedAttribute propagated
        assert sc['video']['metadata']['clipSpeedAttribute']['value'] is True
        assert sc['audio']['metadata']['clipSpeedAttribute']['value'] is True

    def test_missing_screen_clip_raises(self):
        data = _make_project_data(_screen_clip(5), _voice_clip(10))
        proj = FakeProject(data)
        sync = ScreenRecordingSync(proj)
        with pytest.raises(KeyError, match='99'):
            sync.match_duration(screen_clip_id=99, voiceover_clip_id=10)

    def test_missing_voice_clip_raises(self):
        data = _make_project_data(_screen_clip(5), _voice_clip(10))
        proj = FakeProject(data)
        sync = ScreenRecordingSync(proj)
        with pytest.raises(KeyError, match='99'):
            sync.match_duration(screen_clip_id=5, voiceover_clip_id=99)

    def test_zero_voiceover_duration_raises(self):
        sc = _screen_clip(5)
        vo = _voice_clip(10, duration=0)
        data = _make_project_data(sc, vo)
        proj = FakeProject(data)
        sync = ScreenRecordingSync(proj)
        with pytest.raises(ValueError, match='zero duration'):
            sync.match_duration(screen_clip_id=5, voiceover_clip_id=10)


# ── match_duration_with_markers (advanced mode) ──────────────────

class TestMatchDurationWithMarkers:
    def test_too_few_markers_raises(self):
        group = _group_clip(5)
        vo = _voice_clip(10)
        data = _make_project_data(group, vo)
        proj = FakeProject(data)
        sync = ScreenRecordingSync(proj)
        with pytest.raises(ValueError, match='at least 2'):
            sync.match_duration_with_markers(5, 10, [(0, 0)])

    def test_missing_screen_raises(self):
        group = _group_clip(5)
        vo = _voice_clip(10)
        data = _make_project_data(group, vo)
        proj = FakeProject(data)
        sync = ScreenRecordingSync(proj)
        with pytest.raises(KeyError, match='99'):
            sync.match_duration_with_markers(99, 10, [(0, 0), (EDIT_RATE, EDIT_RATE)])

    def test_missing_voice_raises(self):
        group = _group_clip(5)
        vo = _voice_clip(10)
        data = _make_project_data(group, vo)
        proj = FakeProject(data)
        sync = ScreenRecordingSync(proj)
        with pytest.raises(KeyError, match='99'):
            sync.match_duration_with_markers(5, 99, [(0, 0), (EDIT_RATE, EDIT_RATE)])

    def test_returns_segments(self):
        """Two markers produce one segment with correct source/timeline durations."""
        group = _group_clip(5, duration=10 * EDIT_RATE)
        vo = _voice_clip(10, duration=20 * EDIT_RATE)
        data = _make_project_data(group, vo)
        proj = FakeProject(data)
        sync = ScreenRecordingSync(proj)

        markers = [
            (0, 0),
            (5 * EDIT_RATE, 10 * EDIT_RATE),
        ]
        segments = sync.match_duration_with_markers(5, 10, markers)

        assert len(segments) == 1
        src_start, src_end, tl_dur = segments[0]
        assert src_start == pytest.approx(0.0)
        assert src_end == pytest.approx(5.0)
        assert tl_dur == pytest.approx(10.0)

    def test_multiple_segments(self):
        """Three markers produce two segments."""
        group = _group_clip(5, duration=10 * EDIT_RATE)
        vo = _voice_clip(10, duration=20 * EDIT_RATE)
        data = _make_project_data(group, vo)
        proj = FakeProject(data)
        sync = ScreenRecordingSync(proj)

        markers = [
            (0, 0),
            (3 * EDIT_RATE, 6 * EDIT_RATE),
            (8 * EDIT_RATE, 18 * EDIT_RATE),
        ]
        segments = sync.match_duration_with_markers(5, 10, markers)

        assert len(segments) == 2
        # First segment: 3s source → 6s timeline
        assert segments[0][2] == pytest.approx(6.0)
        # Second segment: 5s source → 12s timeline
        assert segments[1][2] == pytest.approx(12.0)

    def test_non_group_screen_clip_raises(self):
        """match_duration_with_markers requires a Group clip on the timeline."""
        sc = _screen_clip(5, duration=10 * EDIT_RATE)
        vo = _voice_clip(10, duration=20 * EDIT_RATE)
        data = _make_project_data(sc, vo)
        proj = FakeProject(data)
        sync = ScreenRecordingSync(proj)

        with pytest.raises(KeyError, match='not a Group'):
            sync.match_duration_with_markers(
                5, 10, [(0, 0), (5 * EDIT_RATE, 10 * EDIT_RATE)]
            )


class TestMatchDurationZeroMediaDuration:
    """Cover recording_sync.py line 78: mediaDuration <= 0 fallback."""

    def test_zero_media_duration_falls_back_to_duration(self):
        screen = _screen_clip(media_duration=0)
        voice = _voice_clip(duration=20 * EDIT_RATE)
        data = _make_project_data(screen, voice)

        class FakeProject:
            _data = data

        sync = ScreenRecordingSync(FakeProject())  # type: ignore[arg-type]
        result = sync.match_duration(5, 10)
        # Should have used screen['duration'] (10*EDIT_RATE) as fallback
        assert result == Fraction(20 * EDIT_RATE, 10 * EDIT_RATE)
