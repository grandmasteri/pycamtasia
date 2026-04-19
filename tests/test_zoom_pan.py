from __future__ import annotations

import pytest

from camtasia.timeline.timeline import Timeline, ZoomPanKeyframe
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


class TestZoomPan:
    def test_add_zoom_pan_creates_keyframe(self):
        tl = Timeline(_make_timeline_data())
        actual_kf = tl.add_zoom_pan(2.0, scale=1.5, center_x=0.3, center_y=0.7)
        assert isinstance(actual_kf, ZoomPanKeyframe)
        assert actual_kf.time_seconds == 2.0
        assert actual_kf.scale == 1.5
        assert actual_kf.center_x == 0.3
        assert actual_kf.center_y == 0.7

    def test_add_zoom_pan_stores_in_data(self):
        data = _make_timeline_data()
        tl = Timeline(data)
        tl.add_zoom_pan(3.0, scale=2.0, center_x=0.1, center_y=0.9)
        actual_stored = data['zoomNPan']
        assert len(actual_stored) == 1
        assert actual_stored[0]['time'] == seconds_to_ticks(3.0)
        assert actual_stored[0]['scale'] == 2.0
        assert actual_stored[0]['centerX'] == 0.1
        assert actual_stored[0]['centerY'] == 0.9

    def test_add_zoom_pan_invalid_scale_raises(self):
        tl = Timeline(_make_timeline_data())
        with pytest.raises(ValueError, match="Scale must be positive"):
            tl.add_zoom_pan(1.0, scale=0)
        with pytest.raises(ValueError, match="Scale must be positive"):
            tl.add_zoom_pan(1.0, scale=-1.0)

    def test_zoom_pan_keyframes_reads_back(self):
        tl = Timeline(_make_timeline_data())
        tl.add_zoom_pan(1.0, scale=1.5, center_x=0.2, center_y=0.8)
        tl.add_zoom_pan(5.0, scale=2.0)
        keyframes = tl.zoom_pan_keyframes
        assert len(keyframes) == 2
        assert keyframes[0].time_seconds == pytest.approx(1.0)
        assert keyframes[0].scale == 1.5
        assert keyframes[1].time_seconds == pytest.approx(5.0)
        assert keyframes[1].scale == 2.0

    def test_clear_zoom_pan(self):
        tl = Timeline(_make_timeline_data())
        tl.add_zoom_pan(1.0, scale=2.0)
        tl.add_zoom_pan(3.0, scale=3.0)
        assert len(tl.zoom_pan_keyframes) == 2
        tl.clear_zoom_pan()
        assert tl.zoom_pan_keyframes == []

    def test_zoom_pan_keyframe_repr(self):
        actual_kf = ZoomPanKeyframe(time_seconds=1.5, scale=2.0, center_x=0.3, center_y=0.7)
        assert repr(actual_kf) == "ZoomPanKeyframe(t=1.50s, scale=2.00, center=(0.30, 0.70))"

    def test_multiple_keyframes_ordered(self):
        tl = Timeline(_make_timeline_data())
        tl.add_zoom_pan(5.0, scale=1.0)
        tl.add_zoom_pan(1.0, scale=2.0)
        tl.add_zoom_pan(3.0, scale=1.5)
        keyframes = tl.zoom_pan_keyframes
        assert len(keyframes) == 3
        assert keyframes[0].time_seconds == pytest.approx(5.0)
        assert keyframes[1].time_seconds == pytest.approx(1.0)
        assert keyframes[2].time_seconds == pytest.approx(3.0)
