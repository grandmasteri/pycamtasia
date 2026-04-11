"""Tests verifying the Marker class consolidation."""
from __future__ import annotations

from camtasia.timeline.markers import EDIT_RATE, Marker


def test_marker_has_time_seconds_property():
    m = Marker(name='intro', time=EDIT_RATE * 3)
    assert m.time_seconds == 3.0


def test_marker_repr_shows_seconds():
    m = Marker(name='intro', time=EDIT_RATE * 3)
    assert repr(m) == "Marker(name='intro', time_seconds=3.00)"


def test_marker_importable_from_marker_module():
    from camtasia.timeline.marker import Marker as MarkerCompat
    assert MarkerCompat is Marker


def test_marker_importable_from_markers_module():
    from camtasia.timeline.markers import Marker as MarkerDirect
    assert MarkerDirect is Marker
