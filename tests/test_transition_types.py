from __future__ import annotations

import pytest

from camtasia.timeline.transitions import EDIT_RATE, Transition, TransitionList


def _tl() -> TransitionList:
    return TransitionList({"transitions": []})


class TestAddDissolve:
    def test_add_dissolve(self):
        tl = _tl()
        t = tl.add_dissolve(1, 2, 0.5)
        assert t.name == "Fade"
        assert t.left_media_id == 1
        assert t.right_media_id == 2
        assert t.duration == int(0.5 * EDIT_RATE)


class TestAddFadeToWhite:
    def test_add_fade_to_white_sets_color(self):
        tl = _tl()
        t = tl.add_fade_to_white(1, 2)
        assert t.name == "FadeThroughColor"
        assert t.color == (1.0, 1.0, 1.0)


class TestAddSlide:
    @pytest.mark.parametrize("direction,expected_name", [
        ("left", "SlideLeft"),
        ("right", "SlideRight"),
        ("up", "SlideUp"),
        ("down", "SlideDown"),
    ])
    def test_add_slide_directions(self, direction, expected_name):
        tl = _tl()
        t = tl.add_slide(1, 2, direction=direction)
        assert t.name == expected_name

    def test_add_slide_invalid_direction_raises(self):
        tl = _tl()
        with pytest.raises(ValueError, match="Invalid direction"):
            tl.add_slide(1, 2, direction="diagonal")


class TestAddWipe:
    def test_add_wipe_left(self):
        tl = _tl()
        t = tl.add_wipe(1, 2, direction="left")
        assert t.name == "WipeLeft"

    def test_add_wipe_invalid_direction_raises(self):
        tl = _tl()
        with pytest.raises(ValueError, match="Invalid direction"):
            tl.add_wipe(1, 2, direction="diagonal")


class TestAllTransitionsReturnTransitionType:
    @pytest.mark.parametrize("method, args", [
        ("add_dissolve", (1, 2)),
        ("add_fade_to_white", (1, 2)),
        ("add_slide", (1, 2)),
        ("add_wipe", (1, 2)),
    ])
    def test_returns_transition_type(self, method, args):
        tl = _tl()
        result = getattr(tl, method)(*args)
        assert type(result) is Transition
