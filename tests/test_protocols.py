"""Tests for __eq__, __hash__, and __repr__ protocols."""
from __future__ import annotations

from pathlib import Path

from camtasia.media_bin.media_bin import Media, MediaBin
from camtasia.effects.base import Effect
from camtasia.timeline.markers import MarkerList
from camtasia.timeline.transitions import Transition, TransitionList
from camtasia.timeline.marker import Marker


def _media(id: int) -> Media:
    return Media({
        "id": id, "src": f"./media/file{id}.mp4", "rect": [0, 0, 1920, 1080],
        "lastMod": "20230101T000000",
        "sourceTracks": [{"type": 0, "range": [0, 1000], "editRate": 1000}],
    })


# --- Media ---

def test_media_eq_same_id():
    assert _media(1) == _media(1)

def test_media_neq_different_id():
    assert _media(1) != _media(2)

def test_media_hash_in_set():
    assert {_media(1), _media(1), _media(2)} == {_media(1), _media(2)}

def test_media_repr():
    assert repr(_media(3)) == 'Media(id=3, source="media/file3.mp4")'


def test_media_eq_non_media():
    assert _media(1) != 'not a media'


# --- MediaBin ---

def test_mediabin_repr():
    bin_ = MediaBin([{"id": 1, "src": "./a.mp4", "rect": [0,0,0,0], "lastMod": "20230101T000000", "sourceTracks": [{"type": 0, "range": [0,1], "editRate": 1000}]}], Path("."))
    assert repr(bin_) == 'MediaBin(count=1)'


# --- Effect ---

def test_effect_eq_same_data():
    d = {"effectName": "Blur", "parameters": {}}
    e1, e2 = Effect(d), Effect(d)
    assert e1 == e2

def test_effect_neq_different_data():
    assert Effect({"effectName": "Blur", "parameters": {}}) != Effect({"effectName": "Blur", "parameters": {}})


def test_effect_eq_non_effect():
    assert Effect({"effectName": "Blur", "parameters": {}}) != 'not an effect'

def test_effect_hash():
    d = {"effectName": "Blur", "parameters": {}}
    e1, e2 = Effect(d), Effect(d)
    assert hash(e1) == hash(e2)
    assert {e1, e2} == {e1}


# --- MarkerList ---

def test_markerlist_repr():
    ml = MarkerList({'parameters': {'toc': {'keyframes': [{'time': 0, 'endTime': 0, 'value': 'x', 'duration': 0}]}}})
    assert repr(ml) == 'MarkerList(count=1)'


# --- TransitionList ---

def test_transitionlist_repr():
    tl = TransitionList({'transitions': [{'name': 'Fade', 'duration': 100, 'leftMedia': 1, 'attributes': {}}]})
    assert repr(tl) == 'TransitionList(count=1)'


# --- Transition ---

def test_transition_eq_same_data():
    d = {'name': 'Fade', 'duration': 100, 'leftMedia': 1, 'attributes': {}}
    assert Transition(d) == Transition(d)

def test_transition_neq_different_data():
    d = {'name': 'Fade', 'duration': 100, 'leftMedia': 1, 'attributes': {}}
    assert Transition(d) != Transition(dict(d))


def test_transition_eq_non_transition():
    d = {'name': 'Fade', 'duration': 100, 'leftMedia': 1, 'attributes': {}}
    assert Transition(d) != 'not a transition'

def test_transition_hash():
    d = {'name': 'Fade', 'duration': 100, 'leftMedia': 1, 'attributes': {}}
    t1, t2 = Transition(d), Transition(d)
    assert hash(t1) == hash(t2)
    assert {t1, t2} == {t1}


# --- Marker repr ---

def test_marker_repr_shows_seconds():
    EDIT_RATE = 705_600_000
    m = Marker(name='intro', time=EDIT_RATE * 2)  # 2 seconds
    assert repr(m) == "Marker(name='intro', time_seconds=2.00)"
