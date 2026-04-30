"""Tests for Timeline.add_zoom_n_pan_rect viewport-rect-based zoom."""
from __future__ import annotations

import pytest

from camtasia.timeline.timeline import Timeline
from camtasia.timing import seconds_to_ticks


def _make_timeline_data(**extra) -> dict:
    data = {
        "id": 1,
        "sceneTrack": {
            "scenes": [{"csml": {"tracks": []}}]
        },
        "trackAttributes": [],
    }
    data.update(extra)
    return data


class TestAddZoomNPanRect:
    def test_basic_rect(self):
        tl = Timeline(_make_timeline_data())
        kf = tl.add_zoom_n_pan_rect(100, 200, 800, 600, time_seconds=1.0)
        assert kf['rect'] == {'x': 100, 'y': 200, 'width': 800, 'height': 600}
        assert kf['time'] == seconds_to_ticks(1.0)
        assert kf['duration'] == seconds_to_ticks(1.0)

    def test_custom_duration(self):
        tl = Timeline(_make_timeline_data())
        kf = tl.add_zoom_n_pan_rect(0, 0, 1920, 1080, time_seconds=0.0, duration_seconds=2.5)
        assert kf['duration'] == seconds_to_ticks(2.5)

    def test_defaults_to_playhead(self):
        tl = Timeline(_make_timeline_data())
        tl.playhead_seconds = 3.0
        kf = tl.add_zoom_n_pan_rect(0, 0, 640, 480)
        assert kf['time'] == seconds_to_ticks(3.0)

    def test_stored_in_zoom_n_pan_array(self):
        data = _make_timeline_data()
        tl = Timeline(data)
        tl.add_zoom_n_pan_rect(10, 20, 300, 200, time_seconds=0.0)
        assert len(data['zoomNPan']) == 1
        assert data['zoomNPan'][0]['rect']['x'] == 10

    def test_multiple_rects(self):
        tl = Timeline(_make_timeline_data())
        tl.add_zoom_n_pan_rect(0, 0, 1920, 1080, time_seconds=0.0)
        tl.add_zoom_n_pan_rect(100, 100, 800, 600, time_seconds=5.0)
        assert len(tl._data['zoomNPan']) == 2

    def test_zero_width_raises(self):
        tl = Timeline(_make_timeline_data())
        with pytest.raises(ValueError, match="Width must be positive"):
            tl.add_zoom_n_pan_rect(0, 0, 0, 100, time_seconds=0.0)

    def test_negative_height_raises(self):
        tl = Timeline(_make_timeline_data())
        with pytest.raises(ValueError, match="Height must be positive"):
            tl.add_zoom_n_pan_rect(0, 0, 100, -50, time_seconds=0.0)

    def test_coexists_with_scale_based_zoom(self):
        tl = Timeline(_make_timeline_data())
        tl.add_zoom_pan(1.0, scale=2.0)
        tl.add_zoom_n_pan_rect(0, 0, 960, 540, time_seconds=3.0)
        assert len(tl._data['zoomNPan']) == 2
        # First is scale-based, second is rect-based
        assert 'scale' in tl._data['zoomNPan'][0]
        assert 'rect' in tl._data['zoomNPan'][1]
