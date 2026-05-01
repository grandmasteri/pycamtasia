"""Tests for per-point bezier/easing on cursor paths."""
from __future__ import annotations

from camtasia.timeline.clips.screen_recording import ScreenIMFile
from camtasia.timing import seconds_to_ticks


def _make_clip(params: dict | None = None) -> ScreenIMFile:
    """Build a minimal ScreenIMFile from a raw dict."""
    return ScreenIMFile({
        '_type': 'ScreenIMFile',
        'id': 1,
        'start': 0,
        'duration': seconds_to_ticks(10.0),
        'mediaDuration': 1,
        'parameters': params or {},
    })


class TestLineTypes:
    def test_straight_sets_linr_interp(self):
        clip = _make_clip()
        clip.set_cursor_location_keyframes(
            [(0.0, 0, 0), (1.0, 10, 10)],
            line_types=['straight', 'straight'],
        )
        kfs = clip.cursor_location_keyframes
        assert kfs[0]['interp'] == 'linr'
        assert kfs[1]['interp'] == 'linr'

    def test_curved_sets_bezi_interp(self):
        clip = _make_clip()
        clip.set_cursor_location_keyframes(
            [(0.0, 0, 0), (1.0, 10, 10)],
            line_types=['curved', 'curved'],
        )
        kfs = clip.cursor_location_keyframes
        assert kfs[0]['interp'] == 'bezi'
        assert kfs[1]['interp'] == 'bezi'

    def test_bezier_alias_sets_bezi_interp(self):
        clip = _make_clip()
        clip.set_cursor_location_keyframes(
            [(0.0, 0, 0)],
            line_types=['bezier'],
        )
        assert clip.cursor_location_keyframes[0]['interp'] == 'bezi'

    def test_mixed_line_types(self):
        clip = _make_clip()
        clip.set_cursor_location_keyframes(
            [(0.0, 0, 0), (1.0, 10, 10), (2.0, 20, 20)],
            line_types=['straight', 'curved', 'straight'],
        )
        kfs = clip.cursor_location_keyframes
        assert [kf['interp'] for kf in kfs] == ['linr', 'bezi', 'linr']


class TestBezierHandles:
    def test_handles_stored_on_keyframes(self):
        clip = _make_clip()
        clip.set_cursor_location_keyframes(
            [(0.0, 0, 0), (1.0, 10, 10)],
            bezier_handles=[
                ((0.1, 0.2), (0.3, 0.4)),
                ((0.5, 0.6), (0.7, 0.8)),
            ],
        )
        kfs = clip.cursor_location_keyframes
        assert kfs[0]['inTangent'] == [0.1, 0.2]
        assert kfs[0]['outTangent'] == [0.3, 0.4]
        assert kfs[1]['inTangent'] == [0.5, 0.6]
        assert kfs[1]['outTangent'] == [0.7, 0.8]

    def test_handles_imply_bezi_interp(self):
        clip = _make_clip()
        clip.set_cursor_location_keyframes(
            [(0.0, 0, 0)],
            bezier_handles=[((1, 2), (3, 4))],
        )
        assert clip.cursor_location_keyframes[0]['interp'] == 'bezi'

    def test_handles_with_fewer_entries_than_keyframes(self):
        clip = _make_clip()
        clip.set_cursor_location_keyframes(
            [(0.0, 0, 0), (1.0, 10, 10)],
            bezier_handles=[((1, 2), (3, 4))],
        )
        kfs = clip.cursor_location_keyframes
        assert 'inTangent' in kfs[0]
        assert 'inTangent' not in kfs[1]


class TestPerPointEasing:
    def test_linear_easing(self):
        clip = _make_clip()
        clip.set_cursor_location_keyframes(
            [(0.0, 0, 0)],
            easing=['linear'],
        )
        assert clip.cursor_location_keyframes[0]['interp'] == 'linr'

    def test_ease_in(self):
        clip = _make_clip()
        clip.set_cursor_location_keyframes(
            [(0.0, 0, 0)],
            easing=['ease-in'],
        )
        assert clip.cursor_location_keyframes[0]['interp'] == 'easi'

    def test_ease_out(self):
        clip = _make_clip()
        clip.set_cursor_location_keyframes(
            [(0.0, 0, 0)],
            easing=['ease-out'],
        )
        assert clip.cursor_location_keyframes[0]['interp'] == 'easo'

    def test_easing_overrides_line_type(self):
        clip = _make_clip()
        clip.set_cursor_location_keyframes(
            [(0.0, 0, 0), (1.0, 10, 10)],
            line_types=['curved', 'curved'],
            easing=['ease-in', 'ease-out'],
        )
        kfs = clip.cursor_location_keyframes
        assert kfs[0]['interp'] == 'easi'
        assert kfs[1]['interp'] == 'easo'

    def test_mixed_easing(self):
        clip = _make_clip()
        clip.set_cursor_location_keyframes(
            [(0.0, 0, 0), (1.0, 10, 10), (2.0, 20, 20)],
            easing=['linear', 'ease-in', 'ease-out'],
        )
        kfs = clip.cursor_location_keyframes
        assert [kf['interp'] for kf in kfs] == ['linr', 'easi', 'easo']


class TestSetCursorLocationWithBezier:
    def test_basic_bezier_path(self):
        clip = _make_clip()
        clip.set_cursor_location_with_bezier([
            (0.0, 0, 0, (0.1, 0.2), (0.3, 0.4)),
            (1.0, 10, 10, (0.5, 0.6), (0.7, 0.8)),
        ])
        kfs = clip.cursor_location_keyframes
        assert len(kfs) == 2
        assert kfs[0]['value'] == [0, 0, 0]
        assert kfs[0]['inTangent'] == [0.1, 0.2]
        assert kfs[0]['outTangent'] == [0.3, 0.4]
        assert kfs[0]['interp'] == 'bezi'
        assert kfs[1]['value'] == [10, 10, 0]
        assert kfs[1]['inTangent'] == [0.5, 0.6]
        assert kfs[1]['outTangent'] == [0.7, 0.8]

    def test_timing_and_duration(self):
        clip = _make_clip()
        clip.set_cursor_location_with_bezier([
            (0.0, 0, 0, (0, 0), (0, 0)),
            (2.0, 20, 20, (0, 0), (0, 0)),
        ])
        kfs = clip.cursor_location_keyframes
        assert kfs[0]['time'] == seconds_to_ticks(0.0)
        assert kfs[0]['endTime'] == seconds_to_ticks(2.0)
        assert kfs[0]['duration'] == seconds_to_ticks(2.0)
        assert kfs[1]['duration'] == 0


class TestNoInterpWithoutOptions:
    def test_no_interp_key_when_no_options(self):
        clip = _make_clip()
        clip.set_cursor_location_keyframes([(0.0, 0, 0), (1.0, 10, 10)])
        kfs = clip.cursor_location_keyframes
        assert 'interp' not in kfs[0]
        assert 'interp' not in kfs[1]


class TestBackwardCompatibility:
    def test_setter_still_works(self):
        clip = _make_clip()
        clip.cursor_location_keyframes = [(0.0, 10, 20), (1.0, 30, 40)]
        kfs = clip.cursor_location_keyframes
        assert len(kfs) == 2
        assert kfs[0]['value'] == [10, 20, 0]
        assert kfs[1]['value'] == [30, 40, 0]

    def test_chaining_returns_self(self):
        clip = _make_clip()
        result = clip.set_cursor_location_keyframes(
            [(0.0, 0, 0)], line_types=['curved'],
        )
        assert result is clip
