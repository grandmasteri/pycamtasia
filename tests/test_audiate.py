from __future__ import annotations

import json

import pytest

from camtasia.audiate.transcript import Transcript, Word
from camtasia.timing import EDIT_RATE


def _make_audiate_keyframe(word_id: str, text: str, time_ticks: int) -> dict:
    """Build a realistic Audiate transcription keyframe from the format spec."""
    return {
        "time": time_ticks,
        "endTime": time_ticks,
        "value": json.dumps({"id": word_id, "text": text}),
        "duration": 0,
    }


# Realistic keyframes from the format spec: "selecting a recent batch run"
AUDIATE_KEYFRAMES = [
    _make_audiate_keyframe("XmbBv2FU", "selecting", 529_200_000),
    _make_audiate_keyframe("Yk9cD3GW", "a", 705_600_000),
    _make_audiate_keyframe("Zn0eE4HX", "recent", 882_000_000),
    _make_audiate_keyframe("Ao1fF5IY", "batch", 1_058_400_000),
    _make_audiate_keyframe("Bp2gG6JZ", "run", 1_234_800_000),
]

# Realistic WhisperX result
WHISPERX_RESULT = {
    "segments": [
        {
            "text": "selecting a recent batch run",
            "words": [
                {"word": "selecting", "start": 0.75, "end": 1.0},
                {"word": "a", "start": 1.0, "end": 1.1},
                {"word": "recent", "start": 1.25, "end": 1.5},
                {"word": "batch", "start": 1.5, "end": 1.75},
                {"word": "run", "start": 1.75, "end": 2.0},
            ],
        }
    ]
}


class TestWordDataclass:
    def test_fields(self):
        actual_result = Word(text="selecting", start=0.75, end=1.0, word_id="XmbBv2FU")
        assert actual_result.text == "selecting"
        assert actual_result.start == 0.75
        assert actual_result.end == 1.0
        assert actual_result.word_id == "XmbBv2FU"

    def test_end_none(self):
        actual_result = Word(text="run", start=1.75, end=None, word_id="Bp2gG6JZ")
        assert actual_result.end is None


class TestTranscriptFromAudiateKeyframes:
    def test_parses_words(self):
        actual_result = Transcript.from_audiate_keyframes(AUDIATE_KEYFRAMES)
        expected_words = [
            Word("selecting", 529_200_000 / EDIT_RATE, 705_600_000 / EDIT_RATE, "XmbBv2FU"),
            Word("a", 705_600_000 / EDIT_RATE, 882_000_000 / EDIT_RATE, "Yk9cD3GW"),
            Word("recent", 882_000_000 / EDIT_RATE, 1_058_400_000 / EDIT_RATE, "Zn0eE4HX"),
            Word("batch", 1_058_400_000 / EDIT_RATE, 1_234_800_000 / EDIT_RATE, "Ao1fF5IY"),
            Word("run", 1_234_800_000 / EDIT_RATE, None, "Bp2gG6JZ"),
        ]
        assert actual_result.words == expected_words

    def test_last_word_end_is_none(self):
        actual_result = Transcript.from_audiate_keyframes(AUDIATE_KEYFRAMES)
        assert actual_result.words[-1].end is None

    def test_empty_keyframes(self):
        actual_result = Transcript.from_audiate_keyframes([])
        assert actual_result.words == []


class TestTranscriptFromWhisperxResult:
    def test_parses_words(self):
        actual_result = Transcript.from_whisperx_result(WHISPERX_RESULT)
        expected_words = [
            Word("selecting", 0.75, 1.0, "wx-0"),
            Word("a", 1.0, 1.1, "wx-1"),
            Word("recent", 1.25, 1.5, "wx-2"),
            Word("batch", 1.5, 1.75, "wx-3"),
            Word("run", 1.75, 2.0, "wx-4"),
        ]
        assert actual_result.words == expected_words

    def test_empty_segments(self):
        actual_result = Transcript.from_whisperx_result({"segments": []})
        assert actual_result.words == []

    def test_word_without_end(self):
        result = {"segments": [{"words": [{"word": "hello", "start": 0.0}]}]}
        actual_result = Transcript.from_whisperx_result(result)
        assert actual_result.words[0].end is None


class TestTranscriptFullText:
    def test_joins_words(self):
        transcript = Transcript.from_whisperx_result(WHISPERX_RESULT)
        actual_result = transcript.full_text
        assert actual_result == "selecting a recent batch run"

    def test_empty(self):
        actual_result = Transcript([]).full_text
        assert actual_result == ""


class TestTranscriptDuration:
    def test_returns_last_word_end(self):
        transcript = Transcript.from_whisperx_result(WHISPERX_RESULT)
        assert transcript.duration == 2.0

    def test_returns_last_word_start_when_end_is_none(self):
        transcript = Transcript.from_audiate_keyframes(AUDIATE_KEYFRAMES)
        # Last word "run" has end=None, so duration = start
        assert transcript.duration == 1_234_800_000 / EDIT_RATE

    def test_empty_transcript(self):
        assert Transcript([]).duration == 0.0


class TestTranscriptFindPhrase:
    def test_finds_single_word(self):
        transcript = Transcript.from_whisperx_result(WHISPERX_RESULT)
        actual_result = transcript.find_phrase("batch")
        expected_result = Word("batch", 1.5, 1.75, "wx-3")
        assert actual_result == expected_result

    def test_finds_multi_word_phrase(self):
        transcript = Transcript.from_whisperx_result(WHISPERX_RESULT)
        actual_result = transcript.find_phrase("recent batch run")
        expected_result = Word("recent", 1.25, 1.5, "wx-2")
        assert actual_result == expected_result

    def test_case_insensitive(self):
        transcript = Transcript.from_whisperx_result(WHISPERX_RESULT)
        actual_result = transcript.find_phrase("SELECTING")
        assert actual_result is not None
        assert actual_result.text == "selecting"

    def test_returns_none_for_no_match(self):
        transcript = Transcript.from_whisperx_result(WHISPERX_RESULT)
        assert transcript.find_phrase("nonexistent") is None

    def test_returns_none_for_empty_phrase(self):
        transcript = Transcript.from_whisperx_result(WHISPERX_RESULT)
        assert transcript.find_phrase("") is None


class TestTranscriptWordsInRange:
    def test_filters_by_time(self):
        transcript = Transcript.from_whisperx_result(WHISPERX_RESULT)
        actual_result = transcript.words_in_range(1.0, 1.5)
        expected_result = [
            Word("a", 1.0, 1.1, "wx-1"),
            Word("recent", 1.25, 1.5, "wx-2"),
            Word("batch", 1.5, 1.75, "wx-3"),
        ]
        assert actual_result == expected_result

    def test_empty_range(self):
        transcript = Transcript.from_whisperx_result(WHISPERX_RESULT)
        assert transcript.words_in_range(10.0, 20.0) == []

    def test_exact_boundary(self):
        transcript = Transcript.from_whisperx_result(WHISPERX_RESULT)
        actual_result = transcript.words_in_range(0.75, 0.75)
        expected_result = [Word("selecting", 0.75, 1.0, "wx-0")]
        assert actual_result == expected_result
