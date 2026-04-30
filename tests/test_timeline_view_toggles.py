"""Tests for Timeline markers_view_visible and quiz_view_visible properties."""
from __future__ import annotations

from camtasia.timeline.timeline import Timeline


def _make_timeline_data(**extra) -> dict:
    data = {
        "id": 1,
        "sceneTrack": {"scenes": [{"csml": {"tracks": []}}]},
        "trackAttributes": [],
    }
    data.update(extra)
    return data


class TestMarkersViewVisible:
    def test_default_is_false(self):
        tl = Timeline(_make_timeline_data())
        assert tl.markers_view_visible is False

    def test_set_true(self):
        tl = Timeline(_make_timeline_data())
        tl.markers_view_visible = True
        assert tl.markers_view_visible is True

    def test_roundtrip_false(self):
        tl = Timeline(_make_timeline_data())
        tl.markers_view_visible = True
        tl.markers_view_visible = False
        assert tl.markers_view_visible is False

    def test_stored_in_docprefs(self):
        tl = Timeline(_make_timeline_data())
        tl.markers_view_visible = True
        assert tl._data['docPrefs']['DocPrefMarkersViewVisible'] is True


class TestQuizViewVisible:
    def test_default_is_false(self):
        tl = Timeline(_make_timeline_data())
        assert tl.quiz_view_visible is False

    def test_set_true(self):
        tl = Timeline(_make_timeline_data())
        tl.quiz_view_visible = True
        assert tl.quiz_view_visible is True

    def test_roundtrip_false(self):
        tl = Timeline(_make_timeline_data())
        tl.quiz_view_visible = True
        tl.quiz_view_visible = False
        assert tl.quiz_view_visible is False

    def test_stored_in_docprefs(self):
        tl = Timeline(_make_timeline_data())
        tl.quiz_view_visible = True
        assert tl._data['docPrefs']['DocPrefQuizViewVisible'] is True
