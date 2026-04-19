from __future__ import annotations

import pytest

from camtasia.timeline.transitions import EDIT_RATE, Transition, TransitionList


def _make_track_data(*transitions: dict) -> dict:
    """Build a minimal track dict with a transitions array."""
    return {"transitions": list(transitions)}


def _fade_through_black_record(
    left: int = 33, right: int | None = 34, duration: int = 352_800_000
) -> dict:
    """Realistic FadeThroughBlack transition from the format spec."""
    record = {
        "name": "FadeThroughBlack",
        "duration": duration,
        "leftMedia": left,
        "attributes": {
            "Color-blue": 0.0,
            "Color-green": 0.0,
            "Color-red": 0.0,
            "bypass": False,
            "reverse": False,
            "trivial": False,
            "useAudioPreRoll": True,
            "useVisualPreRoll": True,
        },
    }
    if right is not None:
        record["rightMedia"] = right
    return record


class TestTransitionProperties:
    def test_name(self):
        actual_result = Transition(_fade_through_black_record()).name
        assert actual_result == "FadeThroughBlack"

    def test_duration_ticks(self):
        actual_result = Transition(_fade_through_black_record()).duration
        assert actual_result == 352_800_000

    def test_duration_seconds(self):
        actual_result = Transition(_fade_through_black_record()).duration_seconds
        assert actual_result == 352_800_000 / EDIT_RATE  # 0.5s

    def test_left_media_id(self):
        actual_result = Transition(_fade_through_black_record()).left_media_id
        assert actual_result == 33

    def test_right_media_id(self):
        actual_result = Transition(_fade_through_black_record()).right_media_id
        assert actual_result == 34

    def test_right_media_id_none_for_fade_out(self):
        record = _fade_through_black_record(right=None)
        actual_result = Transition(record).right_media_id
        assert actual_result is None

    def test_bypassed_false_by_default(self):
        actual_result = Transition(_fade_through_black_record()).bypassed
        assert actual_result is False

    def test_color(self):
        actual_result = Transition(_fade_through_black_record()).color
        assert actual_result == (0.0, 0.0, 0.0)


class TestTransitionListIteration:
    def test_len_empty(self):
        tl = TransitionList({"transitions": []})
        assert list(tl) == []

    def test_iter_yields_transitions(self):
        data = _make_track_data(
            _fade_through_black_record(left=33, right=34),
            _fade_through_black_record(left=34, right=35),
        )
        actual_result = [(t.left_media_id, t.right_media_id) for t in TransitionList(data)]
        expected_result = [(33, 34), (34, 35)]
        assert actual_result == expected_result

    def test_getitem(self):
        data = _make_track_data(
            _fade_through_black_record(left=33, right=34),
            _fade_through_black_record(left=34, right=35),
        )
        tl = TransitionList(data)
        assert tl[1].left_media_id == 34

    def test_getitem_out_of_range(self):
        tl = TransitionList({"transitions": []})
        with pytest.raises(IndexError):
            tl[0]


class TestTransitionListAdd:
    def test_add_creates_correct_json(self):
        data: dict = {"transitions": []}
        tl = TransitionList(data)
        tl.add("FadeThroughBlack", 33, 34, 352_800_000, bypass=False)

        expected_result = {
            "name": "FadeThroughBlack",
            "duration": 352_800_000,
            "leftMedia": 33,
            "rightMedia": 34,
            "attributes": {
                "bypass": False,
                "reverse": False,
                "trivial": False,
                "useAudioPreRoll": True,
                "useVisualPreRoll": True,
            },
        }
        assert data["transitions"][0] == expected_result

    def test_add_without_right_clip_omits_right_media(self):
        data: dict = {"transitions": []}
        tl = TransitionList(data)
        tl.add("FadeThroughBlack", 80, None, 705_600_000)

        actual_record = data["transitions"][0]
        assert "rightMedia" not in actual_record
        assert actual_record["leftMedia"] == 80

    def test_add_returns_transition(self):
        tl = TransitionList({"transitions": []})
        actual_result = tl.add("FadeThroughBlack", 33, 34, 352_800_000)
        assert isinstance(actual_result, Transition)
        assert actual_result.name == "FadeThroughBlack"

    def test_add_fade_through_black_default_attributes(self):
        data: dict = {"transitions": []}
        tl = TransitionList(data)
        tl.add_fade_through_black(33, 34, 352_800_000)

        expected_attrs = {
            "Color-blue": 0.0,
            "Color-green": 0.0,
            "Color-red": 0.0,
            "bypass": False,
            "reverse": False,
            "trivial": False,
            "useAudioPreRoll": True,
            "useVisualPreRoll": True,
        }
        assert data["transitions"][0]["attributes"] == expected_attrs


class TestTransitionListRemove:
    def test_remove_deletes_by_index(self):
        data = _make_track_data(
            _fade_through_black_record(left=33, right=34),
            _fade_through_black_record(left=34, right=35),
        )
        tl = TransitionList(data)
        tl.remove(0)
        assert tl[0].left_media_id == 34
        assert list(data["transitions"]) == [_fade_through_black_record(left=34, right=35)]

    def test_remove_out_of_range(self):
        tl = TransitionList({"transitions": []})
        with pytest.raises(IndexError):
            tl.remove(0)


class TestDictMutationPassthrough:
    def test_mutations_reflect_in_underlying_data(self):
        data: dict = {"transitions": []}
        tl = TransitionList(data)
        tl.add("FadeThroughBlack", 33, 34, 352_800_000)
        # Mutate the underlying dict directly
        data["transitions"][0]["duration"] = 705_600_000
        assert tl[0].duration == 705_600_000

    def test_setdefault_creates_transitions_key(self):
        data: dict = {}
        tl = TransitionList(data)
        tl.add("FadeThroughBlack", 33, 34, 352_800_000)
        assert "transitions" in data
        assert tl[0].name == "FadeThroughBlack"


class TestTransitionMissingLeftMedia:
    def test_left_media_id_none_when_missing(self):
        from camtasia.timeline.transitions import Transition
        t = Transition({'name': 'FadeThroughBlack', 'duration': 100, 'rightMedia': 1, 'attributes': {}})
        assert t.left_media_id is None


class TestTransitionRepr:
    def test_repr_format(self):
        from camtasia.timeline.transitions import Transition
        t = Transition({
            'name': 'FadeThroughBlack', 'duration': 352_800_000,
            'leftMedia': 1, 'rightMedia': 2, 'attributes': {},
        })
        r = repr(t)
        assert 'FadeThroughBlack' in r
        assert 'left=1' in r
        assert 'right=2' in r
