"""Tests for final tutorial gap wrap-up features."""
from __future__ import annotations

import pytest

from camtasia.effects.source import UI_ALIASES, SourceEffect
from camtasia.timeline.captions import extend_dynamic_caption
from camtasia.timeline.clips.audio import AMFile
from camtasia.timeline.clips.base import BaseClip
from camtasia.timeline.track import Track
from camtasia.timing import seconds_to_ticks

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_source_effect(**params: object) -> SourceEffect:
    return SourceEffect({
        'effectName': 'SourceEffect',
        'bypassed': False,
        'category': '',
        'parameters': dict(params),
    })


def _make_track(medias: list[dict] | None = None) -> Track:
    return Track(
        attributes={'ident': 'test'},
        data={'trackIndex': 0, 'medias': medias or [], 'transitions': []},
    )


def _clip(clip_id: int, start_seconds: float, duration_seconds: float, **kw: object) -> dict:
    d: dict = {
        'id': clip_id,
        '_type': kw.pop('_type', 'AMFile'),
        'src': kw.pop('src', 1),
        'start': seconds_to_ticks(start_seconds),
        'duration': seconds_to_ticks(duration_seconds),
        'mediaStart': 0,
        'mediaDuration': seconds_to_ticks(duration_seconds),
        'scalar': 1,
        'metadata': {},
        'animationTracks': {},
        'parameters': {},
        'effects': [],
    }
    d.update(kw)
    return d


# ---------------------------------------------------------------------------
# apply_to_all_animations (item 2 — already exists)
# ---------------------------------------------------------------------------

class TestApplyToAllAnimations:
    """BaseClip.apply_to_all_animations iterates visual animation entries."""

    def test_calls_func_on_each_visual_entry(self) -> None:
        clip = BaseClip({
            'id': 1, '_type': 'VMFile', 'start': 0, 'duration': 100,
            'animationTracks': {'visual': [
                {'endTime': 50, 'duration': 50},
                {'endTime': 100, 'duration': 50},
            ]},
        })
        visited: list[dict] = []
        result = clip.apply_to_all_animations(visited.append)
        assert len(visited) == 2
        assert result is clip  # returns self

    def test_no_animation_tracks(self) -> None:
        clip = BaseClip({'id': 1, '_type': 'VMFile', 'start': 0, 'duration': 100})
        visited: list[dict] = []
        clip.apply_to_all_animations(visited.append)
        assert visited == []

    def test_mutates_entries_in_place(self) -> None:
        clip = BaseClip({
            'id': 1, '_type': 'VMFile', 'start': 0, 'duration': 100,
            'animationTracks': {'visual': [{'endTime': 50, 'duration': 50}]},
        })
        clip.apply_to_all_animations(lambda a: a.update(interp='eioe'))
        assert clip.visual_animations[0]['interp'] == 'eioe'


# ---------------------------------------------------------------------------
# add_media_matte docstring + preset_name (items 3-4 — already done)
# ---------------------------------------------------------------------------

class TestMediaMattePresetName:
    """add_media_matte derives preset_name from matte_mode."""

    @pytest.mark.parametrize(('mode', 'expected'), [
        (1, 'Media Matte Alpha'),
        (3, 'Media Matte Luminosity'),
        (2, 'Media Matte Alpha Invert'),
        (4, 'Media Matte Luminosity Invert'),
    ])
    def test_default_preset_name(self, mode: int, expected: str) -> None:
        clip = BaseClip({
            'id': 1, '_type': 'VMFile', 'start': 0, 'duration': 100,
            'effects': [],
        })
        clip.add_media_matte(matte_mode=mode)
        effect = clip.effects[-1]
        assert effect['metadata']['presetName'] == expected


# ---------------------------------------------------------------------------
# SourceEffect UI aliases (item 5)
# ---------------------------------------------------------------------------

class TestSourceEffectUIAliases:
    """UI_ALIASES dict and set_ui_property/get_ui_property."""

    def test_ui_aliases_keys(self) -> None:
        expected_keys = {
            'Background Color', 'Accent Color', 'Tertiary Color',
            'Quaternary Color', 'Mid Point', 'Mid Point X',
            'Mid Point Y', 'Speed',
        }
        assert set(UI_ALIASES.keys()) == expected_keys

    def test_set_and_get_speed(self) -> None:
        se = _make_source_effect(Speed=5.0)
        se.set_ui_property('Speed', 10.0)
        assert se.get_ui_property('Speed') == 10.0

    def test_set_and_get_mid_point(self) -> None:
        se = _make_source_effect(MidPoint=0.5)
        se.set_ui_property('Mid Point', 0.75)
        assert se.get_ui_property('Mid Point') == 0.75

    def test_set_and_get_color(self) -> None:
        se = _make_source_effect(**{
            'Color0-red': 0.0, 'Color0-green': 0.0,
            'Color0-blue': 0.0, 'Color0-alpha': 1.0,
        })
        new_rgba = (1.0, 0.5, 0.25, 1.0)
        se.set_ui_property('Background Color', new_rgba)
        assert se.get_ui_property('Background Color') == new_rgba

    def test_unknown_label_raises(self) -> None:
        se = _make_source_effect()
        with pytest.raises(KeyError):
            se.get_ui_property('Nonexistent Label')
        with pytest.raises(KeyError):
            se.set_ui_property('Nonexistent Label', 1)


# ---------------------------------------------------------------------------
# extend_dynamic_caption (item 6)
# ---------------------------------------------------------------------------

class TestExtendDynamicCaption:
    """extend_dynamic_caption rescales word timings."""

    def test_rescales_word_timings(self) -> None:
        words = [
            {'start': 0.0, 'end': 1.0, 'text': 'hello'},
            {'start': 1.0, 'end': 2.0, 'text': 'world'},
        ]
        callout = {
            'id': 1, '_type': 'Callout',
            'duration': seconds_to_ticks(2.0),
        }
        extend_dynamic_caption(callout, 4.0, transcript=words)
        assert words[0]['start'] == pytest.approx(0.0)
        assert words[0]['end'] == pytest.approx(2.0)
        assert words[1]['start'] == pytest.approx(2.0)
        assert words[1]['end'] == pytest.approx(4.0)
        assert callout['duration'] == seconds_to_ticks(4.0)

    def test_reads_from_metadata(self) -> None:
        words = [{'start': 0.0, 'end': 1.0, 'text': 'hi'}]
        callout = {
            'id': 1, '_type': 'Callout',
            'duration': seconds_to_ticks(1.0),
            'metadata': {'dynamicCaptionTranscription': {'words': words}},
        }
        extend_dynamic_caption(callout, 2.0)
        assert words[0]['end'] == pytest.approx(2.0)

    def test_zero_duration_noop(self) -> None:
        callout = {'id': 1, '_type': 'Callout', 'duration': 0}
        extend_dynamic_caption(callout, 5.0)
        assert callout['duration'] == 0

    def test_no_transcript_noop(self) -> None:
        callout = {
            'id': 1, '_type': 'Callout',
            'duration': seconds_to_ticks(2.0),
        }
        extend_dynamic_caption(callout, 4.0)
        assert callout['duration'] == seconds_to_ticks(4.0)


# ---------------------------------------------------------------------------
# AMFile.dynamic_caption_transcription (item 7)
# ---------------------------------------------------------------------------

class TestDynamicCaptionTranscription:
    """AMFile.dynamic_caption_transcription getter/setter."""

    def test_getter_returns_none_when_absent(self) -> None:
        clip = AMFile({'id': 1, '_type': 'AMFile', 'start': 0, 'duration': 100})
        assert clip.dynamic_caption_transcription is None

    def test_setter_stores_in_metadata(self) -> None:
        clip = AMFile({'id': 1, '_type': 'AMFile', 'start': 0, 'duration': 100})
        data = {'words': [{'text': 'hello', 'start': 0.0, 'end': 0.5}]}
        clip.dynamic_caption_transcription = data
        assert clip.dynamic_caption_transcription is data
        assert clip._data['metadata']['dynamicCaptionTranscription'] is data

    def test_setter_clears_with_none(self) -> None:
        clip = AMFile({
            'id': 1, '_type': 'AMFile', 'start': 0, 'duration': 100,
            'metadata': {'dynamicCaptionTranscription': {'words': []}},
        })
        clip.dynamic_caption_transcription = None
        assert clip.dynamic_caption_transcription is None
        assert 'dynamicCaptionTranscription' not in clip._data['metadata']


# ---------------------------------------------------------------------------
# auto_stitch_on_track (item 8)
# ---------------------------------------------------------------------------

class TestAutoStitchOnTrack:
    """auto_stitch_on_track stitches adjacent same-source clips."""

    def test_stitches_adjacent_same_source(self) -> None:
        from camtasia.operations.stitch import auto_stitch_on_track
        track = _make_track([
            _clip(1, 0.0, 2.0, src=10),
            _clip(2, 2.0, 3.0, src=10),
        ])
        results = auto_stitch_on_track(track)
        assert len(results) == 1
        assert results[0].clip_type == 'StitchedMedia'

    def test_skips_different_sources(self) -> None:
        from camtasia.operations.stitch import auto_stitch_on_track
        track = _make_track([
            _clip(1, 0.0, 2.0, src=10),
            _clip(2, 2.0, 3.0, src=20),
        ])
        results = auto_stitch_on_track(track)
        assert results == []

    def test_skips_non_adjacent(self) -> None:
        from camtasia.operations.stitch import auto_stitch_on_track
        track = _make_track([
            _clip(1, 0.0, 2.0, src=10),
            _clip(2, 5.0, 3.0, src=10),
        ])
        results = auto_stitch_on_track(track)
        assert results == []

    def test_empty_track(self) -> None:
        from camtasia.operations.stitch import auto_stitch_on_track
        track = _make_track([])
        assert auto_stitch_on_track(track) == []

    def test_single_clip(self) -> None:
        from camtasia.operations.stitch import auto_stitch_on_track
        track = _make_track([_clip(1, 0.0, 2.0)])
        assert auto_stitch_on_track(track) == []

    def test_import_from_operations(self) -> None:
        from camtasia.operations import auto_stitch_on_track as fn
        assert callable(fn)
