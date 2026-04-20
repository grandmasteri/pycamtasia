"""Tests for Track.shift_all_clips() and Track.scale_all_durations()."""
from __future__ import annotations

from typing import Any

import pytest

from camtasia.timeline.track import Track
from camtasia.timing import EDIT_RATE, seconds_to_ticks


def _make_track() -> Track:
    attrs: dict[str, Any] = {"ident": "Track 1"}
    data: dict[str, Any] = {"trackIndex": 0, "medias": [], "transitions": []}
    return Track(attrs, data)


class TestShiftAllClipsForward:
    def test_shifts_clips_forward(self):
        track = _make_track()
        track.add_callout("A", 0, 5)
        track.add_callout("B", 5, 5)

        track.shift_all_clips(2.0)

        starts = [m['start'] for m in track._data['medias']]
        assert starts == [seconds_to_ticks(2.0), seconds_to_ticks(7.0)]




class TestShiftAllClipsBackward:
    def test_shifts_clips_backward(self):
        track = _make_track()
        track.add_callout("A", 5, 5)

        track.shift_all_clips(-2.0)

        assert track._data['medias'][0]['start'] == seconds_to_ticks(3.0)

    def test_clamps_to_zero(self):
        track = _make_track()
        track.add_callout("A", 1, 5)

        track.shift_all_clips(-5.0)

        assert track._data['medias'][0]['start'] == 0


class TestShiftAllClipsEmpty:
    def test_empty_track_is_noop(self):
        track = _make_track()
        track.shift_all_clips(10.0)
        assert track._data['medias'] == []


class TestScaleAllDurations:
    def test_doubles_durations(self):
        track = _make_track()
        track.add_callout("A", 0, 5)
        orig_dur = track._data['medias'][0]['duration']
        orig_mdur = track._data['medias'][0]['mediaDuration']

        track.scale_all_durations(2.0)

        assert track._data['medias'][0]['duration'] == int(orig_dur * 2)
        assert track._data['medias'][0]['mediaDuration'] == orig_mdur

    def test_halves_durations(self):
        track = _make_track()
        track.add_callout("A", 0, 10)
        orig_dur = track._data['medias'][0]['duration']

        track.scale_all_durations(0.5)

        assert track._data['medias'][0]['duration'] == int(orig_dur * 0.5)

    def test_scales_start_times_proportionally(self):
        track = _make_track()
        track.add_callout("A", 3, 5)
        orig_start = track._data['medias'][0]['start']

        track.scale_all_durations(2.0)

        assert track._data["medias"][0]["start"] == int(orig_start * 2.0)  # scaled proportionally


class TestScaleAllDurationsValidation:
    def test_zero_factor_raises(self):
        track = _make_track()
        with pytest.raises(ValueError, match="factor must be > 0"):
            track.scale_all_durations(0)

    def test_negative_factor_raises(self):
        track = _make_track()
        with pytest.raises(ValueError, match="factor must be > 0"):
            track.scale_all_durations(-1.0)


class TestScaleAllDurationsEmpty:
    def test_empty_track_is_noop(self):
        track = _make_track()
        track.scale_all_durations(2.0)
        assert track._data['medias'] == []


# ------------------------------------------------------------------
# Bug 12: shift_all_clips removes zero-duration clips
# ------------------------------------------------------------------

class TestShiftAllClipsRemovesZeroDuration:
    def test_removes_fully_clamped_clip(self):
        track = _make_track()
        track.add_callout("Short", 0, 1)  # 1s clip at t=0
        track.shift_all_clips(-5.0)  # shift back 5s — clip fully consumed
        assert len(track._data['medias']) == 0

    def test_keeps_partially_clamped_clip(self):
        track = _make_track()
        track.add_callout("Long", 0, 10)  # 10s clip at t=0
        track.shift_all_clips(-3.0)  # shift back 3s — clip partially survives
        assert len(track._data['medias']) == 1
        assert track._data['medias'][0]['start'] == 0
        assert track._data['medias'][0]['duration'] > 0


# ------------------------------------------------------------------
# Bug 14: scale_all_durations scales effect timing
# ------------------------------------------------------------------

class TestScaleAllDurationsEffects:
    def test_scales_effect_start_and_duration(self):
        track = _make_track()
        track.add_callout("A", 0, 10)
        track._data['medias'][0]['effects'] = [
            {'effectName': 'Glow', 'start': 100, 'duration': 200},
        ]
        track.scale_all_durations(2.0)
        eff = track._data['medias'][0]['effects'][0]
        assert eff['start'] == 200
        assert eff['duration'] == 400

    def test_effect_without_timing_unchanged(self):
        track = _make_track()
        track.add_callout("A", 0, 10)
        track._data['medias'][0]['effects'] = [
            {'effectName': 'Glow'},
        ]
        track.scale_all_durations(2.0)
        eff = track._data['medias'][0]['effects'][0]
        assert 'start' not in eff
        assert 'duration' not in eff


# ------------------------------------------------------------------
# Bug 12: Timeline.shift_all removes zero-duration clips
# ------------------------------------------------------------------

class TestTimelineShiftAllRemovesZeroDuration:
    def test_removes_fully_consumed_clip(self):
        from camtasia.timeline.timeline import Timeline
        tl_data = {
            'id': 0,
            'sceneTrack': {'scenes': [{'csml': {'tracks': [
                {'trackIndex': 0, 'medias': [
                    {'id': 1, '_type': 'VMFile', 'start': 0, 'duration': seconds_to_ticks(1.0),
                     'mediaStart': 0, 'mediaDuration': seconds_to_ticks(1.0), 'scalar': 1},
                ]},
            ]}}]},
            'trackAttributes': [{'ident': 'A'}],
        }
        tl = Timeline(tl_data)
        tl.shift_all(-5.0)
        assert len(tl_data['sceneTrack']['scenes'][0]['csml']['tracks'][0]['medias']) == 0


class TestShiftAllClipsEffectsOnClamp:
    """Bug 12: shift_all_clips should adjust effects when clips are clamped."""

    def test_clamped_clip_effects_adjusted(self):
        track = _make_track()
        track.add_callout("A", 2.0, 10.0)
        # Add an effect at the start and one later
        m = track._data["medias"][0]
        m["effects"] = [
            {"start": 0, "duration": seconds_to_ticks(3.0), "name": "early"},
            {"start": seconds_to_ticks(5.0), "duration": seconds_to_ticks(3.0), "name": "mid"},
        ]

        track.shift_all_clips(-5.0)  # clamp_amount = 3s (clip was at 2s, shifted -5s)

        m = track._data["medias"][0]
        assert m["start"] == 0
        effects = m["effects"]
        # "early" effect: start=0, dur=3s. After clamp 3s from start:
        # entirely in the trimmed portion? No: clamp_amount = 3s (5-2=3).
        # early: end=3s <= 3s -> removed
        # mid: start=5s, dur=3s. After shift right by 3s: start=2s, dur=3s
        early = [e for e in effects if e.get("name") == "early"]
        assert len(early) == 0, "Effect entirely in clamped region should be removed"
        mid = [e for e in effects if e.get("name") == "mid"]
        assert len(mid) == 1
        assert mid[0]["start"] == seconds_to_ticks(2.0)


# ---------------------------------------------------------------------------
# Bug 8: scale_all_durations must propagate AFTER all fields are updated
# ---------------------------------------------------------------------------

class TestScaleAllDurationsPropagationOrder:
    def test_unified_media_sub_clips_get_updated_scalar(self):
        """After scaling, UnifiedMedia sub-clips must have the new scalar, not the old one."""
        from fractions import Fraction

        track = _make_track()
        um_data = {
            'id': 1, '_type': 'UnifiedMedia',
            'start': 0, 'duration': seconds_to_ticks(10.0),
            'mediaStart': 0, 'mediaDuration': seconds_to_ticks(10.0),
            'scalar': 1,
            'video': {
                'id': 2, '_type': 'VMFile', 'src': 1,
                'start': 0, 'duration': seconds_to_ticks(10.0),
                'mediaStart': 0, 'mediaDuration': seconds_to_ticks(10.0),
                'scalar': 1,
            },
            'audio': {
                'id': 3, '_type': 'AMFile', 'src': 1,
                'start': 0, 'duration': seconds_to_ticks(10.0),
                'mediaStart': 0, 'mediaDuration': seconds_to_ticks(10.0),
                'scalar': 1,
            },
            'parameters': {}, 'effects': [], 'metadata': {},
            'animationTracks': {},
        }
        track._data['medias'] = [um_data]

        track.scale_all_durations(2.0)

        # After 2x scale: duration doubles, mediaDuration unchanged, scalar = 2
        wrapper = track._data['medias'][0]
        expected_scalar = Fraction(wrapper['duration']) / Fraction(str(wrapper['mediaDuration']))
        video = wrapper['video']
        audio = wrapper['audio']
        # Sub-clips must have the SAME scalar as the wrapper (propagated after update)
        assert Fraction(str(video['scalar'])) == expected_scalar
        assert Fraction(str(audio['scalar'])) == expected_scalar
        assert video['duration'] == wrapper['duration']
        assert audio['duration'] == wrapper['duration']


class TestShiftAllClipsUnifiedMediaEffects:
    """Bug 8: shift_all_clips must adjust effects on UnifiedMedia sub-clips."""

    def test_unified_media_sub_clip_effects_adjusted(self) -> None:
        from camtasia.timeline.track import Track
        EDIT_RATE = 705_600_000
        data = {
            'trackIndex': 0,
            'medias': [{
                'id': 1, '_type': 'UnifiedMedia',
                'start': EDIT_RATE * 2, 'duration': EDIT_RATE * 10,
                'mediaStart': 0, 'mediaDuration': EDIT_RATE * 10, 'scalar': 1,
                'video': {
                    'id': 2, '_type': 'ScreenVMFile', 'src': 1,
                    'start': EDIT_RATE * 2, 'duration': EDIT_RATE * 10,
                    'mediaStart': 0, 'mediaDuration': EDIT_RATE * 10, 'scalar': 1,
                    'effects': [{'effectName': 'Glow', 'start': EDIT_RATE * 1, 'duration': EDIT_RATE * 5}],
                    'parameters': {}, 'metadata': {}, 'animationTracks': {},
                },
                'audio': {
                    'id': 3, '_type': 'AMFile', 'src': 1,
                    'start': EDIT_RATE * 2, 'duration': EDIT_RATE * 10,
                    'mediaStart': 0, 'mediaDuration': EDIT_RATE * 10, 'scalar': 1,
                    'effects': [{'effectName': 'Emphasize', 'start': EDIT_RATE * 2, 'duration': EDIT_RATE * 3}],
                    'parameters': {}, 'metadata': {}, 'animationTracks': {},
                },
                'effects': [],
                'parameters': {}, 'metadata': {}, 'animationTracks': {},
            }],
            'transitions': [],
        }
        track = Track({'ident': 'T'}, data)
        # Shift back 5s — clip at 2s gets clamped, clamp_amount = 3s
        track.shift_all_clips(-5.0)
        video_eff = data['medias'][0]['video']['effects'][0]
        # Original effect start was 1s. After clamping 3s: start should be max(0, 1s-3s)=0
        # and duration trimmed accordingly
        assert video_eff['start'] == 0
        audio_eff = data['medias'][0]['audio']['effects'][0]
        # Original audio effect start was 2s. After clamping 3s: start should be max(0, 2s-3s)=0
        assert audio_eff['start'] == 0


# Bug 12: scale_all_durations must scale effects inside UnifiedMedia sub-clips

class TestScaleAllDurationsUnifiedMediaEffects:
    def test_scales_sub_clip_effects(self):
        from camtasia.timing import EDIT_RATE
        data = {
            'trackIndex': 0,
            'medias': [{
                'id': 1, '_type': 'UnifiedMedia',
                'start': 0, 'duration': EDIT_RATE * 10,
                'mediaStart': 0, 'mediaDuration': EDIT_RATE * 10, 'scalar': 1,
                'video': {
                    'id': 2, '_type': 'VMFile', 'src': 1,
                    'start': 0, 'duration': EDIT_RATE * 10,
                    'mediaStart': 0, 'mediaDuration': EDIT_RATE * 10, 'scalar': 1,
                    'effects': [{'effectName': 'Glow', 'start': EDIT_RATE * 2, 'duration': EDIT_RATE * 4}],
                    'parameters': {}, 'metadata': {}, 'animationTracks': {},
                },
                'audio': {
                    'id': 3, '_type': 'AMFile', 'src': 1,
                    'start': 0, 'duration': EDIT_RATE * 10,
                    'mediaStart': 0, 'mediaDuration': EDIT_RATE * 10, 'scalar': 1,
                    'effects': [{'effectName': 'Fade', 'start': EDIT_RATE * 1, 'duration': EDIT_RATE * 3}],
                    'parameters': {}, 'metadata': {}, 'animationTracks': {},
                },
                'effects': [],
                'parameters': {}, 'metadata': {}, 'animationTracks': {},
            }],
            'transitions': [],
        }
        track = Track({'ident': 'T'}, data)
        track.scale_all_durations(2.0)

        video_eff = data['medias'][0]['video']['effects'][0]
        assert video_eff['start'] == EDIT_RATE * 4
        assert video_eff['duration'] == EDIT_RATE * 8

        audio_eff = data['medias'][0]['audio']['effects'][0]
        assert audio_eff['start'] == EDIT_RATE * 2
        assert audio_eff['duration'] == EDIT_RATE * 6


# ---------------------------------------------------------------------------
# Bug 9: shift_all_clips must use int(round(...)) consistently
# ---------------------------------------------------------------------------

class TestShiftAllClipsRoundConsistency:
    def test_clamped_duration_uses_round(self):
        """When clamping, duration must use int(round()) not int() then round() separately."""
        track = _make_track()
        # Add a clip at start=1s, duration=3s
        track._data['medias'].append({
            '_type': 'VMFile', 'id': 1, 'src': 1,
            'start': seconds_to_ticks(1.0),
            'duration': seconds_to_ticks(3.0),
            'mediaStart': 0, 'mediaDuration': seconds_to_ticks(3.0), 'scalar': 1,
            'parameters': {}, 'effects': [], 'metadata': {}, 'animationTracks': {},
        })
        # Shift backward by 1.5s — clip at 1s gets clamped
        track.shift_all_clips(-1.5)
        m = track._data['medias'][0]
        # New start should be 0, duration should be 3s - 0.5s = 2.5s
        assert m['start'] == 0
        expected_dur = seconds_to_ticks(2.5)
        assert m['duration'] == expected_dur


# ---------------------------------------------------------------------------
# Bug 11: scale_all_durations must scale transition start
# ---------------------------------------------------------------------------

class TestScaleAllDurationsTransitionStart:
    def test_transition_start_is_scaled(self):
        """scale_all_durations must scale transition 'start' field, not just 'duration'."""
        data: dict[str, Any] = {
            'trackIndex': 0,
            'medias': [{
                '_type': 'VMFile', 'id': 1, 'src': 1,
                'start': 0, 'duration': EDIT_RATE * 10,
                'mediaStart': 0, 'mediaDuration': EDIT_RATE * 10, 'scalar': 1,
                'parameters': {}, 'effects': [], 'metadata': {}, 'animationTracks': {},
            }],
            'transitions': [
                {'start': EDIT_RATE * 2, 'duration': EDIT_RATE * 1, 'leftMedia': 1, 'rightMedia': None},
            ],
        }
        track = Track({'ident': 'T'}, data)
        track.scale_all_durations(2.0)
        t = data['transitions'][0]
        assert t['start'] == EDIT_RATE * 4
        assert t['duration'] == EDIT_RATE * 2
