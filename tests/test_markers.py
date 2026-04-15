from __future__ import annotations

import pytest

from camtasia.timeline.markers import EDIT_RATE, Marker, MarkerList


def _make_keyframe(value: str, time: int) -> dict:
    """Build a realistic marker keyframe from the format spec."""
    return {"time": time, "endTime": time, "value": value, "duration": 0}


def _make_data_with_markers(*keyframes: dict) -> dict:
    """Build a parent dict with parameters/toc/keyframes path."""
    return {"parameters": {"toc": {"type": "string", "keyframes": list(keyframes)}}}


class TestMarkerDataclass:
    def test_fields(self):
        actual_result = Marker(name="Selecting a recent batch run", time=116_306_400_000)
        assert actual_result.name == "Selecting a recent batch run"
        assert actual_result.time == 116_306_400_000

    @pytest.mark.parametrize(
        "ticks, expected_seconds",
        [
            (0, 0.0),
            (705_600_000, 1.0),
            (352_800_000, 0.5),
            (116_306_400_000, 116_306_400_000 / EDIT_RATE),
        ],
    )
    def test_time_seconds(self, ticks: int, expected_seconds: float):
        actual_result = Marker(name="M", time=ticks).time_seconds
        assert actual_result == pytest.approx(expected_seconds)


class TestMarkerListIteration:
    def test_empty(self):
        ml = MarkerList(_make_data_with_markers())
        assert list(ml) == []

    def test_iter_yields_markers(self):
        data = _make_data_with_markers(
            _make_keyframe("Selecting a recent batch run", 116_306_400_000),
            _make_keyframe("Navigating to the dashboard", 119_552_160_000),
        )
        actual_result = [(m.name, m.time) for m in MarkerList(data)]
        expected_result = [
            ("Selecting a recent batch run", 116_306_400_000),
            ("Navigating to the dashboard", 119_552_160_000),
        ]
        assert actual_result == expected_result

    def test_len(self):
        data = _make_data_with_markers(
            _make_keyframe("M1", 0),
            _make_keyframe("M2", 705_600_000),
        )
        ml = MarkerList(data)
        # Verify content, not just count
        assert [(m.name, m.time) for m in ml] == [("M1", 0), ("M2", 705_600_000)]


class TestMarkerListAdd:
    def test_add_creates_correct_keyframe(self):
        data = _make_data_with_markers()
        ml = MarkerList(data)
        ml.add("Selecting a recent batch run", 116_306_400_000)

        expected_keyframe = {
            "time": 116_306_400_000,
            "endTime": 116_306_400_000,
            "value": "Selecting a recent batch run",
            "duration": 0,
        }
        assert data["parameters"]["toc"]["keyframes"][0] == expected_keyframe

    def test_add_returns_marker(self):
        ml = MarkerList(_make_data_with_markers())
        actual_result = ml.add("M1", 705_600_000)
        expected_result = Marker(name="M1", time=705_600_000)
        assert actual_result == expected_result

    def test_add_creates_parameters_path_if_missing(self):
        data: dict = {}
        ml = MarkerList(data)
        ml.add("First marker", 0)

        assert data["parameters"]["toc"]["keyframes"] == [
            {"time": 0, "endTime": 0, "value": "First marker", "duration": 0}
        ]

    def test_add_creates_toc_if_only_parameters_exists(self):
        data: dict = {"parameters": {}}
        ml = MarkerList(data)
        ml.add("M", 100)

        assert "toc" in data["parameters"]
        assert data["parameters"]["toc"]["keyframes"] == [
            {"time": 100, "endTime": 100, "value": "M", "duration": 0}
        ]


class TestMarkerListRemoveAt:
    def test_remove_at_removes_correct_marker(self):
        data = _make_data_with_markers(
            _make_keyframe("M1", 100),
            _make_keyframe("M2", 200),
            _make_keyframe("M3", 300),
        )
        ml = MarkerList(data)
        ml.remove_at(200)

        actual_result = [(m.name, m.time) for m in ml]
        expected_result = [("M1", 100), ("M3", 300)]
        assert actual_result == expected_result

    def test_remove_at_raises_key_error_for_missing_time(self):
        data = _make_data_with_markers(_make_keyframe("M1", 100))
        ml = MarkerList(data)
        with pytest.raises(KeyError, match="No marker at time=999"):
            ml.remove_at(999)

    def test_remove_at_removes_all_markers_at_same_time(self):
        data = _make_data_with_markers(
            _make_keyframe("M1", 100),
            _make_keyframe("M2", 100),
        )
        ml = MarkerList(data)
        ml.remove_at(100)
        assert list(ml) == []


class TestMarkerListReplace:
    def test_replace_on_empty(self):
        data: dict = {}
        ml = MarkerList(data)
        ml.replace([("A", 100), ("B", 200)])
        actual_result = [(m.name, m.time) for m in ml]
        assert actual_result == [("A", 100), ("B", 200)]

    def test_replace_clears_existing(self):
        data = _make_data_with_markers(
            _make_keyframe("Old1", 10),
            _make_keyframe("Old2", 20),
        )
        ml = MarkerList(data)
        ml.replace([("New1", 300)])
        actual_result = [(m.name, m.time) for m in ml]
        assert actual_result == [("New1", 300)]

    def test_replace_with_empty_list(self):
        data = _make_data_with_markers(_make_keyframe("M1", 100))
        ml = MarkerList(data)
        ml.replace([])
        assert list(ml) == []


class TestTimelineMarkersReplace:
    def _make_timeline_data(self) -> dict:
        return {
            "parameters": {"toc": {"type": "string", "keyframes": [
                _make_keyframe("Old", 50),
            ]}},
        }

    def test_replace_delegates(self):
        from camtasia.timeline.timeline import _TimelineMarkers
        data = self._make_timeline_data()
        tm = _TimelineMarkers(data)
        tm.replace([("X", 1000), ("Y", 2000)])
        actual_result = [(m.name, m.time) for m in tm]
        assert actual_result == [("X", 1000), ("Y", 2000)]
