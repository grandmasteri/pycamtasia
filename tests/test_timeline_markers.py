from __future__ import annotations

import pytest

from camtasia.timeline.markers import Marker, MarkerList


def _make_keyframe(value: str, time: int) -> dict:
    return {"time": time, "endTime": time, "value": value, "duration": 0}


def _make_data(*keyframes: dict) -> dict:
    return {"parameters": {"toc": {"type": "string", "keyframes": list(keyframes)}}}


class TestRename:
    def test_renames_first_match(self):
        ml = MarkerList(_make_data(_make_keyframe("A", 100), _make_keyframe("B", 200)))
        ml.rename("A", "Z")
        assert [(m.name, m.time) for m in ml] == [("Z", 100), ("B", 200)]

    def test_renames_only_first_duplicate(self):
        ml = MarkerList(_make_data(_make_keyframe("A", 100), _make_keyframe("A", 200)))
        ml.rename("A", "Z")
        assert [(m.name, m.time) for m in ml] == [("Z", 100), ("A", 200)]

    def test_raises_for_missing_name(self):
        ml = MarkerList(_make_data(_make_keyframe("A", 100)))
        with pytest.raises(ValueError, match="No marker named 'X'"):
            ml.rename("X", "Y")


class TestMove:
    def test_moves_marker(self):
        ml = MarkerList(_make_data(_make_keyframe("A", 100), _make_keyframe("B", 200)))
        ml.move(100, 500)
        assert [(m.name, m.time) for m in ml] == [("A", 500), ("B", 200)]

    def test_moves_only_first_at_time(self):
        ml = MarkerList(_make_data(_make_keyframe("A", 100), _make_keyframe("B", 100)))
        ml.move(100, 500)
        assert [(m.name, m.time) for m in ml] == [("A", 500), ("B", 100)]

    def test_raises_for_missing_time(self):
        ml = MarkerList(_make_data(_make_keyframe("A", 100)))
        with pytest.raises(ValueError, match="No marker at time=999"):
            ml.move(999, 500)


class TestRemoveByName:
    def test_removes_first_match(self):
        ml = MarkerList(_make_data(
            _make_keyframe("A", 100), _make_keyframe("B", 200), _make_keyframe("A", 300),
        ))
        ml.remove_by_name("A")
        assert [(m.name, m.time) for m in ml] == [("B", 200), ("A", 300)]

    def test_raises_for_missing_name(self):
        ml = MarkerList(_make_data(_make_keyframe("A", 100)))
        with pytest.raises(ValueError, match="No marker named 'X'"):
            ml.remove_by_name("X")

    def test_removes_sole_marker(self):
        ml = MarkerList(_make_data(_make_keyframe("A", 100)))
        ml.remove_by_name("A")
        assert list(ml) == []


class TestNextAfter:
    def test_returns_next(self):
        ml = MarkerList(_make_data(
            _make_keyframe("A", 100), _make_keyframe("B", 200), _make_keyframe("C", 300),
        ))
        result = ml.next_after(150)
        assert result == Marker(name="B", time=200)

    def test_returns_none_when_no_later(self):
        ml = MarkerList(_make_data(_make_keyframe("A", 100)))
        assert ml.next_after(100) is None

    def test_excludes_exact_match(self):
        ml = MarkerList(_make_data(_make_keyframe("A", 100), _make_keyframe("B", 200)))
        result = ml.next_after(100)
        assert result == Marker(name="B", time=200)

    def test_empty_list(self):
        ml = MarkerList(_make_data())
        assert ml.next_after(0) is None


class TestPrevBefore:
    def test_returns_prev(self):
        ml = MarkerList(_make_data(
            _make_keyframe("A", 100), _make_keyframe("B", 200), _make_keyframe("C", 300),
        ))
        result = ml.prev_before(250)
        assert result == Marker(name="B", time=200)

    def test_returns_none_when_no_earlier(self):
        ml = MarkerList(_make_data(_make_keyframe("A", 100)))
        assert ml.prev_before(100) is None

    def test_excludes_exact_match(self):
        ml = MarkerList(_make_data(_make_keyframe("A", 100), _make_keyframe("B", 200)))
        result = ml.prev_before(200)
        assert result == Marker(name="A", time=100)

    def test_empty_list(self):
        ml = MarkerList(_make_data())
        assert ml.prev_before(100) is None
