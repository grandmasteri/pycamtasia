"""Tests for cursor-path editing API on ScreenIMFile and ScreenVMFile."""
from __future__ import annotations

import pytest

from camtasia.timeline.clips.screen_recording import ScreenIMFile, ScreenVMFile
from camtasia.timing import seconds_to_ticks

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_screen_im(params: dict | None = None) -> ScreenIMFile:
    """Build a minimal ScreenIMFile from a raw dict."""
    data: dict = {
        '_type': 'ScreenIMFile',
        'id': 1,
        'start': 0,
        'duration': seconds_to_ticks(10.0),
        'mediaDuration': 1,
        'parameters': params or {},
    }
    return ScreenIMFile(data)


def _make_screen_vm(params: dict | None = None) -> ScreenVMFile:
    """Build a minimal ScreenVMFile from a raw dict."""
    data: dict = {
        '_type': 'ScreenVMFile',
        'id': 2,
        'start': 0,
        'duration': seconds_to_ticks(10.0),
        'mediaDuration': seconds_to_ticks(10.0),
        'parameters': params or {},
    }
    return ScreenVMFile(data)


def _cursor_loc_params(keyframes: list[tuple[float, float, float]]) -> dict:
    """Build a cursorLocation parameter dict from (time, x, y) tuples."""
    kfs = []
    for i, (t, x, y) in enumerate(keyframes):
        ticks = seconds_to_ticks(t)
        next_ticks = seconds_to_ticks(keyframes[i + 1][0]) if i + 1 < len(keyframes) else ticks
        kfs.append({
            'endTime': next_ticks,
            'time': ticks,
            'value': [x, y, 0],
            'duration': next_ticks - ticks,
        })
    return {
        'cursorLocation': {
            'type': 'point',
            'keyframes': kfs,
        },
    }


# ===========================================================================
# ScreenIMFile — cursor path editing
# ===========================================================================


class TestAddCursorPoint:
    def test_add_to_empty(self):
        clip = _make_screen_im()
        clip.add_cursor_point(1.0, 100, 200)
        kfs = clip.cursor_location_keyframes
        assert len(kfs) == 1
        assert kfs[0]['value'] == [100, 200, 0]
        assert kfs[0]['time'] == seconds_to_ticks(1.0)

    def test_add_maintains_sort_order(self):
        clip = _make_screen_im()
        clip.add_cursor_point(3.0, 300, 300)
        clip.add_cursor_point(1.0, 100, 100)
        clip.add_cursor_point(2.0, 200, 200)
        kfs = clip.cursor_location_keyframes
        times = [kf['time'] for kf in kfs]
        assert times == sorted(times)
        assert [kf['value'][:2] for kf in kfs] == [[100, 100], [200, 200], [300, 300]]

    def test_add_replaces_existing_at_same_time(self):
        clip = _make_screen_im()
        clip.add_cursor_point(1.0, 100, 200)
        clip.add_cursor_point(1.0, 999, 888)
        kfs = clip.cursor_location_keyframes
        assert len(kfs) == 1
        assert kfs[0]['value'] == [999, 888, 0]

    def test_durations_recomputed(self):
        clip = _make_screen_im()
        clip.add_cursor_point(1.0, 0, 0)
        clip.add_cursor_point(3.0, 0, 0)
        kfs = clip.cursor_location_keyframes
        assert kfs[0]['duration'] == seconds_to_ticks(3.0) - seconds_to_ticks(1.0)
        assert kfs[0]['endTime'] == seconds_to_ticks(3.0)
        assert kfs[1]['duration'] == 0


class TestDeleteCursorPoint:
    def test_delete_exact(self):
        clip = _make_screen_im(_cursor_loc_params([(1.0, 10, 20), (2.0, 30, 40)]))
        clip.delete_cursor_point(1.0)
        kfs = clip.cursor_location_keyframes
        assert len(kfs) == 1
        assert kfs[0]['value'] == [30, 40, 0]

    def test_delete_within_tolerance(self):
        clip = _make_screen_im(_cursor_loc_params([(1.0, 10, 20)]))
        clip.delete_cursor_point(1.0005)
        assert clip.cursor_location_keyframes == []

    def test_delete_outside_tolerance_raises(self):
        clip = _make_screen_im(_cursor_loc_params([(1.0, 10, 20)]))
        with pytest.raises(ValueError, match='No cursor keyframe'):
            clip.delete_cursor_point(5.0)


class TestMoveCursorPoint:
    def test_move_existing(self):
        clip = _make_screen_im(_cursor_loc_params([(1.0, 10, 20)]))
        clip.move_cursor_point(1.0, 99, 88)
        assert clip.cursor_location_keyframes[0]['value'] == [99, 88, 0]

    def test_move_nonexistent_raises(self):
        clip = _make_screen_im(_cursor_loc_params([(1.0, 10, 20)]))
        with pytest.raises(ValueError, match='No cursor keyframe'):
            clip.move_cursor_point(5.0, 0, 0)


class TestSmoothCursorPath:
    def test_smooth_averages_coordinates(self):
        # 5 points in a zigzag
        pts = [(float(i), float(i * 10), float(i * 10 + (10 if i % 2 else 0)))
               for i in range(5)]
        clip = _make_screen_im(_cursor_loc_params(pts))
        clip.smooth_cursor_path(window=3)
        kfs = clip.cursor_location_keyframes
        # Middle points should be averaged
        assert kfs[1]['value'][0] == pytest.approx((0 + 10 + 20) / 3)
        assert kfs[1]['value'][1] == pytest.approx((0 + 20 + 20) / 3)

    def test_smooth_noop_when_fewer_than_window(self):
        clip = _make_screen_im(_cursor_loc_params([(0.0, 0, 0), (1.0, 10, 10)]))
        clip.smooth_cursor_path(window=3)
        # Should not crash, values unchanged
        assert clip.cursor_location_keyframes[0]['value'][:2] == [0, 0]


class TestStraightenCursorPath:
    def test_removes_intermediate_keyframes(self):
        pts = [(float(i), float(i * 10), float(i * 10)) for i in range(5)]
        clip = _make_screen_im(_cursor_loc_params(pts))
        clip.straighten_cursor_path(0.5, 3.5)
        kfs = clip.cursor_location_keyframes
        # Should keep: 0.0 (outside), 1.0 (first in range), 3.0 (last in range), 4.0 (outside)
        times_s = [kf['time'] / 705_600_000 for kf in kfs]
        assert times_s == pytest.approx([0.0, 1.0, 3.0, 4.0])

    def test_noop_when_two_or_fewer_in_range(self):
        pts = [(1.0, 10, 10), (3.0, 30, 30)]
        clip = _make_screen_im(_cursor_loc_params(pts))
        clip.straighten_cursor_path(0.0, 5.0)
        assert len(clip.cursor_location_keyframes) == 2


class TestRestoreCursorPath:
    def test_removes_cursor_location(self):
        clip = _make_screen_im(_cursor_loc_params([(1.0, 10, 20)]))
        clip.restore_cursor_path()
        assert 'cursorLocation' not in clip.parameters

    def test_noop_when_no_cursor_location(self):
        clip = _make_screen_im()
        clip.restore_cursor_path()  # Should not raise


class TestSplitCursorPath:
    def test_split_inserts_two_keyframes(self):
        pts = [(0.0, 0, 0), (4.0, 40, 40)]
        clip = _make_screen_im(_cursor_loc_params(pts))
        clip.split_cursor_path(2.0)
        kfs = clip.cursor_location_keyframes
        # Original 2 + 2 new = 4
        assert len(kfs) == 4
        split_ticks = seconds_to_ticks(2.0)
        split_kfs = [kf for kf in kfs if kf['time'] == split_ticks]
        assert len(split_kfs) == 2
        # Interpolated position at midpoint
        assert split_kfs[0]['value'][0] == pytest.approx(20.0)
        assert split_kfs[0]['value'][1] == pytest.approx(20.0)

    def test_split_at_existing_keyframe(self):
        pts = [(0.0, 0, 0), (2.0, 20, 20), (4.0, 40, 40)]
        clip = _make_screen_im(_cursor_loc_params(pts))
        clip.split_cursor_path(2.0)
        kfs = clip.cursor_location_keyframes
        # Should have 5 keyframes (3 original + 2 new at t=2.0)
        assert len(kfs) == 5


class TestSetNoCursorAt:
    def test_sets_sentinel_and_adds_point(self):
        clip = _make_screen_im()
        clip.set_no_cursor_at(1.5)
        assert clip.cursor_image_path == 'no_cursor'
        kfs = clip.cursor_location_keyframes
        assert len(kfs) == 1


# ===========================================================================
# ScreenIMFile — cursor_location_keyframes setter & cursor_track_level setter
# ===========================================================================


class TestCursorLocationKeyframesSetter:
    def test_setter_writes_keyframes(self):
        clip = _make_screen_im()
        clip.cursor_location_keyframes = [(0.0, 10, 20), (1.0, 30, 40)]
        kfs = clip.cursor_location_keyframes
        assert len(kfs) == 2
        assert kfs[0]['value'] == [10, 20, 0]
        assert kfs[1]['value'] == [30, 40, 0]

    def test_setter_uses_point_type(self):
        clip = _make_screen_im()
        clip.cursor_location_keyframes = [(0.0, 0, 0)]
        loc = clip.parameters['cursorLocation']
        assert loc['type'] == 'point'


class TestCursorTrackLevelSetter:
    def test_set_on_screen_im(self):
        clip = _make_screen_im()
        clip.cursor_track_level = 5.0
        assert clip.cursor_track_level == 5.0

    def test_set_on_screen_vm(self):
        clip = _make_screen_vm()
        clip.cursor_track_level = 3.0
        assert clip.cursor_track_level == 3.0

    def test_updates_existing_dict(self):
        clip = _make_screen_im({
            'cursorTrackLevel': {
                'type': 'double', 'defaultValue': 0.0, 'interp': 'linr',
            },
        })
        clip.cursor_track_level = 7.0
        assert clip.cursor_track_level == 7.0
        # Should update in-place, not replace
        assert clip.parameters['cursorTrackLevel']['interp'] == 'linr'


# ===========================================================================
# ScreenVMFile — cursor keyframe and convenience methods
# ===========================================================================


class TestScreenVMSetCursorScaleKeyframes:
    def test_writes_keyframes(self):
        clip = _make_screen_vm()
        clip.set_cursor_scale_keyframes([(0.0, 1.0), (5.0, 2.5)])
        param = clip.parameters['cursorScale']
        assert param['type'] == 'double'
        assert param['defaultValue'] == 2.5
        kfs = param['keyframes']
        assert len(kfs) == 2
        assert kfs[0]['value'] == 1.0
        assert kfs[1]['value'] == 2.5


class TestScreenVMSetCursorOpacityKeyframes:
    def test_writes_keyframes(self):
        clip = _make_screen_vm()
        clip.set_cursor_opacity_keyframes([(0.0, 1.0), (3.0, 0.0)])
        param = clip.parameters['cursorOpacity']
        assert param['defaultValue'] == 0.0
        kfs = param['keyframes']
        assert len(kfs) == 2
        assert kfs[0]['value'] == 1.0
        assert kfs[1]['value'] == 0.0


class TestScreenVMHideShowCursor:
    def test_hide_sets_opacity_zero(self):
        clip = _make_screen_vm()
        clip.hide_cursor()
        assert clip.cursor_opacity == 0.0

    def test_show_sets_opacity_one(self):
        clip = _make_screen_vm()
        clip.hide_cursor()
        clip.show_cursor()
        assert clip.cursor_opacity == 1.0


class TestScreenVMCursorElevation:
    def test_default_is_zero(self):
        clip = _make_screen_vm()
        assert clip.cursor_elevation == 0.0

    def test_set_and_get(self):
        clip = _make_screen_vm()
        clip.cursor_elevation = 42.0
        assert clip.cursor_elevation == 42.0

    def test_stored_in_metadata(self):
        clip = _make_screen_vm()
        clip.cursor_elevation = 10.0
        assert clip._data['metadata']['cursorElevation'] == 10.0


class TestScreenVMCursorTrackLevelSetter:
    def test_set_creates_dict(self):
        clip = _make_screen_vm()
        clip.cursor_track_level = 2.0
        assert clip.cursor_track_level == 2.0
        param = clip.parameters['cursorTrackLevel']
        assert param['type'] == 'double'

    def test_set_updates_existing(self):
        clip = _make_screen_vm({
            'cursorTrackLevel': {
                'type': 'double', 'defaultValue': 0.0, 'interp': 'linr',
            },
        })
        clip.cursor_track_level = 4.0
        assert clip.cursor_track_level == 4.0
