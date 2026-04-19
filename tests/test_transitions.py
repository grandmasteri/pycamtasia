from __future__ import annotations

from typing import Any

import pytest

from camtasia.project import Project
from camtasia.timeline.transitions import EDIT_RATE, Transition, TransitionList
from camtasia.timeline.timeline import Timeline
from camtasia.timeline.track import Track


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
        t = Transition({'name': 'FadeThroughBlack', 'duration': 100, 'rightMedia': 1, 'attributes': {}})
        assert t.left_media_id is None


class TestTransitionRepr:
    def test_repr_format(self):
        t = Transition({
            'name': 'FadeThroughBlack', 'duration': 352_800_000,
            'leftMedia': 1, 'rightMedia': 2, 'attributes': {},
        })
        r = repr(t)
        assert 'FadeThroughBlack' in r
        assert 'left=1' in r
        assert 'right=2' in r


# ── Merged from test_coverage_misc.py ────────────────────────────────


class TestTransitionFadeToWhite:
    def test_add_fade_to_white(self):
        data = {'transitions': []}
        tl = TransitionList(data)
        t = tl.add_fade_to_white(left_clip=1, right_clip=2, duration_seconds=0.5)
        assert t.name == 'FadeThroughColor'
        assert t._data['attributes']['Color-red'] == 1.0
        assert t._data['attributes']['Color-green'] == 1.0
        assert t._data['attributes']['Color-blue'] == 1.0


# =========================================================================
# Tests migrated from test_convenience.py
# =========================================================================

def _make_track(medias=None, name='T'):
    """Build a minimal Track from raw dicts."""
    data = {'trackIndex': 0, 'medias': medias or []}
    attrs = {'ident': name}
    return Track(attrs, data)


def _make_timeline(track_specs):
    """Build a Timeline with tracks described as (name, media_list) tuples."""
    tracks = []
    attrs = []
    for i, (name, medias) in enumerate(track_specs):
        tracks.append({'trackIndex': i, 'medias': medias})
        attrs.append({'ident': name})
    data = {
        'sceneTrack': {'scenes': [{'csml': {'tracks': tracks}}]},
        'trackAttributes': attrs,
    }
    return Timeline(data)




# ---------------------------------------------------------------------------
# Timeline.remove_all_transitions
# ---------------------------------------------------------------------------

def test_remove_all_transitions():
    """remove_all_transitions clears transitions from all tracks."""
    tl = _make_timeline([
        ('Track1', [{'id': 1, 'start': 0, 'duration': 100}]),
        ('Track2', [{'id': 2, 'start': 0, 'duration': 100}]),
    ])
    # Inject transitions into raw data
    for track in tl.tracks:
        track._data['transitions'] = [{'type': 'fade'}, {'type': 'dissolve'}]
    count = tl.remove_all_transitions()
    assert count == 4
    for track in tl.tracks:
        assert track._data.get('transitions') == []


def test_add_paint_arcs_transition():
    data = {'trackIndex': 0, 'medias': [
        {'id': 1, '_type': 'AMFile', 'start': 0, 'duration': 705600000},
        {'id': 2, '_type': 'AMFile', 'start': 705600000, 'duration': 705600000},
    ], 'transitions': []}
    t = Track({'ident': 'test'}, data)
    t.transitions.add_paint_arcs(1, 2, 0.5)
    assert len(data['transitions']) == 1
    assert data['transitions'][0]['name'] == 'PaintArcs'


def test_add_spherical_spin_transition():
    data = {'trackIndex': 0, 'medias': [
        {'id': 1, '_type': 'AMFile', 'start': 0, 'duration': 705600000},
        {'id': 2, '_type': 'AMFile', 'start': 705600000, 'duration': 705600000},
    ], 'transitions': []}
    t = Track({'ident': 'test'}, data)
    t.transitions.add_spherical_spin(1, 2, 0.5)
    assert len(data['transitions']) == 1
    assert data['transitions'][0]['name'] == 'SphericalSpin'




# ---------------------------------------------------------------------------
# Project.total_transition_count
# ---------------------------------------------------------------------------

def test_total_transition_count():
    track_data_a: dict[str, Any] = {
        'trackIndex': 0,
        'medias': [
            {'id': 1, 'start': 0, 'duration': 100},
            {'id': 2, 'start': 100, 'duration': 100},
        ],
        'transitions': [
            {'start': 50, 'end': 150, 'duration': 100},
        ],
    }
    track_data_b: dict[str, Any] = {
        'trackIndex': 1,
        'medias': [],
        'transitions': [],
    }
    data: dict[str, Any] = {
        'timeline': {
            'id': 'test',
            'sceneTrack': {'scenes': [{'csml': {'tracks': [track_data_a, track_data_b]}}]},
            'trackAttributes': [{'ident': 'A'}, {'ident': 'B'}],
            'parameters': {},
            'authoringClientName': 'test',
        },
    }
    timeline = Timeline(data['timeline'])

    project = Project.__new__(Project)
    object.__setattr__(project, '_timeline', timeline)
    object.__setattr__(project, '_data', data)
    object.__setattr__(project, '_path', None)
    assert project.total_transition_count == 1




# ---------------------------------------------------------------------------
# Track.total_transition_duration_seconds
# ---------------------------------------------------------------------------

def test_total_transition_duration_seconds_empty():
    """total_transition_duration_seconds is 0.0 when no transitions exist."""
    track = _make_track()
    assert track.total_transition_duration_seconds == 0.0


def test_total_transition_duration_seconds_single():
    """total_transition_duration_seconds converts a single transition correctly."""
    duration_ticks: int = EDIT_RATE * 2  # 2 seconds
    data: dict = {'trackIndex': 0, 'medias': [], 'transitions': [{'duration': duration_ticks}]}
    attrs: dict = {'ident': 'T'}
    track = Track(attrs, data)
    assert track.total_transition_duration_seconds == pytest.approx(2.0)


def test_total_transition_duration_seconds_multiple():
    """total_transition_duration_seconds sums multiple transitions."""
    transitions: list[dict] = [
        {'duration': EDIT_RATE},      # 1 second
        {'duration': EDIT_RATE * 3},   # 3 seconds
    ]
    data: dict = {'trackIndex': 0, 'medias': [], 'transitions': transitions}
    attrs: dict = {'ident': 'T'}
    track = Track(attrs, data)
    assert track.total_transition_duration_seconds == pytest.approx(4.0)



# ── Convenience add methods (card_flip, glitch, linear_blur, stretch, paint_arcs, spherical_spin) ──


class TestTransitionConvenienceAdds:
    def _tl(self) -> TransitionList:
        return TransitionList({"transitions": []})

    def test_add_card_flip(self):
        tl = self._tl()
        t = tl.add_card_flip(1, 2)
        assert isinstance(t, Transition)
        assert t.name == "CardFlip"

    def test_add_glitch(self):
        tl = self._tl()
        t = tl.add_glitch(1, 2)
        assert isinstance(t, Transition)
        assert t.name == "Glitch3"

    def test_add_linear_blur(self):
        tl = self._tl()
        t = tl.add_linear_blur(1, 2)
        assert isinstance(t, Transition)
        assert t.name == "LinearBlur"

    def test_add_stretch(self):
        tl = self._tl()
        t = tl.add_stretch(1, 2)
        assert isinstance(t, Transition)
        assert t.name == "Stretch"

    def test_add_paint_arcs(self):
        tl = self._tl()
        t = tl.add_paint_arcs(1, 2)
        assert isinstance(t, Transition)
        assert t.name == "PaintArcs"

    def test_add_spherical_spin(self):
        tl = self._tl()
        t = tl.add_spherical_spin(1, 2)
        assert isinstance(t, Transition)
        assert t.name == "SphericalSpin"


class TestTransitionListClear:
    def test_clear_removes_all(self):
        data = {"transitions": [_fade_through_black_record(), _fade_through_black_record()]}
        tl = TransitionList(data)
        tl.clear()
        assert len(tl) == 0


class TestTransitionBothNone:
    def test_add_transition_both_none_raises(self):
        tl = TransitionList([])
        with pytest.raises(ValueError, match='At least one'):
            tl.add('Fade', duration_ticks=352_800_000, left_clip_id=None, right_clip_id=None)
