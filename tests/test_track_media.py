"""Tests for camtasia.timeline.track_media — TrackMedia, TrackMediaEffects, _Markers."""

import pytest
from camtasia.timeline.track_media import TrackMedia
from camtasia.timeline.marker import Marker


def _make_media_data(**overrides):
    """Create minimal media data dict for TrackMedia."""
    data = {
        "id": 1,
        "start": 0,
        "mediaStart": 0,
        "duration": 1000,
        "effects": [],
        "metadata": {},
    }
    data.update(overrides)
    return data


class TestTrackMediaProperties:
    """Tests for TrackMedia basic property access."""

    def test_id(self):
        media = TrackMedia(_make_media_data(id=42))
        assert media.id == 42

    def test_start(self):
        media = TrackMedia(_make_media_data(start=100))
        assert media.start == 100

    def test_media_start(self):
        media = TrackMedia(_make_media_data(mediaStart=50))
        assert media.media_start == 50

    def test_duration(self):
        media = TrackMedia(_make_media_data(duration=500))
        assert media.duration == 500

    def test_source_present(self):
        media = TrackMedia(_make_media_data(src="media-bin-1"))
        assert media.source == "media-bin-1"

    def test_source_absent(self):
        media = TrackMedia(_make_media_data())
        assert media.source is None

    def test_repr(self):
        media = TrackMedia(_make_media_data(start=10, duration=200))
        assert repr(media) == "Media(start=10, duration=200)"


class TestTrackMediaMarkers:
    """Tests for _Markers collection on TrackMedia."""

    def test_iterate_markers(self):
        data = _make_media_data(
            start=100,
            mediaStart=50,
            parameters={"toc": {"keyframes": [
                {"time": 75, "value": "intro"},
            ]}},
        )
        media = TrackMedia(data)
        actual_markers = list(media.markers)
        # timeline position = start + (marker_time - media_start) = 100 + (75 - 50) = 125
        assert actual_markers == [Marker(name="intro", time=125)]

    def test_no_keyframes(self):
        media = TrackMedia(_make_media_data())
        assert list(media.markers) == []

    def test_add_marker(self):
        data = _make_media_data(start=100, mediaStart=50)
        media = TrackMedia(data)
        media.markers.add("new-marker", 150)
        actual_markers = list(media.markers)
        assert actual_markers == [Marker(name="new-marker", time=150)]

    def test_add_duplicate_marker_raises(self):
        data = _make_media_data(
            start=0,
            mediaStart=0,
            parameters={"toc": {"keyframes": [
                {"time": 100, "value": "existing", "endTime": 100, "duration": 0},
            ]}},
        )
        media = TrackMedia(data)
        with pytest.raises(ValueError, match="marker already exists"):
            media.markers.add("dup", 100)


class TestTrackMediaEffects:
    """Tests for TrackMediaEffects len and effects property access."""

    def test_effects_initially_empty(self):
        data = _make_media_data()
        media = TrackMedia(data)
        assert len(media.effects) == 0

    def test_effects_with_raw_data(self):
        effect_data = {"effectName": "SomeEffect", "category": "cat", "parameters": {}}
        data = _make_media_data(effects=[effect_data])
        media = TrackMedia(data)
        assert len(media.effects) == 1
