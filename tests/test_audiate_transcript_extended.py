"""Tests for Transcript editing helpers and SRT export."""
from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from camtasia.audiate.project import AudiateProject
from camtasia.audiate.transcript import Transcript, Word, _format_srt_time
from camtasia.timing import EDIT_RATE

if TYPE_CHECKING:
    from pathlib import Path


def _make_words(*specs: tuple[str, float, float | None]) -> list[Word]:
    """Build Word list from (text, start, end) tuples."""
    return [
        Word(text=t, start=s, end=e, word_id=f"w{i}")
        for i, (t, s, e) in enumerate(specs)
    ]


# ---------------------------------------------------------------------------
# SRT time formatting
# ---------------------------------------------------------------------------


class TestFormatSrtTime:
    @pytest.mark.parametrize(
        ("seconds", "expected"),
        [
            (0.0, "00:00:00,000"),
            (1.5, "00:00:01,500"),
            (61.123, "00:01:01,123"),
            (3661.001, "01:01:01,001"),
            (-1.0, "00:00:00,000"),
        ],
    )
    def test_formatting(self, seconds: float, expected: str):
        assert _format_srt_time(seconds) == expected


# ---------------------------------------------------------------------------
# to_srt
# ---------------------------------------------------------------------------


class TestToSrt:
    def test_basic_output(self):
        words = _make_words(("hello", 0.0, 0.5), ("world", 0.6, 1.2))
        transcript = Transcript(words)
        srt = transcript.to_srt()
        lines = srt.split("\n")
        assert lines[0] == "1"
        assert lines[1] == "00:00:00,000 --> 00:00:00,500"
        assert lines[2] == "hello"
        assert lines[3] == ""
        assert lines[4] == "2"
        assert lines[5] == "00:00:00,600 --> 00:00:01,200"
        assert lines[6] == "world"

    def test_none_end_uses_next_start(self):
        words = _make_words(("a", 0.0, None), ("b", 1.0, 1.5))
        transcript = Transcript(words)
        srt = transcript.to_srt()
        assert "00:00:00,000 --> 00:00:01,000" in srt

    def test_last_word_none_end_uses_fallback(self):
        words = _make_words(("only", 2.0, None))
        transcript = Transcript(words)
        srt = transcript.to_srt()
        assert "00:00:02,000 --> 00:00:02,500" in srt

    def test_writes_file(self, tmp_path: Path):
        words = _make_words(("hi", 0.0, 0.3))
        transcript = Transcript(words)
        out = tmp_path / "out.srt"
        result = transcript.to_srt(out)
        assert out.read_text() == result

    def test_empty_transcript(self):
        assert Transcript([]).to_srt() == ""


# ---------------------------------------------------------------------------
# detect_filler_words
# ---------------------------------------------------------------------------


class TestDetectFillerWords:
    def test_finds_fillers(self):
        words = _make_words(
            ("so", 0.0, 0.2),
            ("um", 0.3, 0.5),
            ("yeah", 0.6, 0.8),
            ("like", 0.9, 1.1),
        )
        actual = Transcript(words).detect_filler_words()
        assert [w.text for w in actual] == ["um", "like"]

    def test_case_insensitive(self):
        words = _make_words(("UM", 0.0, 0.2), ("Uh", 0.3, 0.5))
        actual = Transcript(words).detect_filler_words()
        assert [w.text for w in actual] == ["UM", "Uh"]

    def test_custom_fillers(self):
        words = _make_words(("well", 0.0, 0.2), ("so", 0.3, 0.5))
        actual = Transcript(words).detect_filler_words(fillers={"well"})
        assert [w.text for w in actual] == ["well"]

    def test_no_fillers(self):
        words = _make_words(("hello", 0.0, 0.5))
        assert Transcript(words).detect_filler_words() == []

    def test_empty_transcript(self):
        assert Transcript([]).detect_filler_words() == []


# ---------------------------------------------------------------------------
# remove_filler_words
# ---------------------------------------------------------------------------


class TestRemoveFillerWords:
    def test_removes_fillers(self):
        words = _make_words(
            ("I", 0.0, 0.1),
            ("um", 0.2, 0.3),
            ("think", 0.4, 0.6),
        )
        result = Transcript(words).remove_filler_words()
        assert [w.text for w in result.words] == ["I", "think"]

    def test_returns_new_transcript(self):
        words = _make_words(("um", 0.0, 0.2), ("ok", 0.3, 0.5))
        original = Transcript(words)
        result = original.remove_filler_words()
        assert len(original.words) == 2
        assert len(result.words) == 1

    def test_custom_fillers(self):
        words = _make_words(("well", 0.0, 0.2), ("ok", 0.3, 0.5))
        result = Transcript(words).remove_filler_words(fillers={"well"})
        assert [w.text for w in result.words] == ["ok"]

    def test_empty_transcript(self):
        result = Transcript([]).remove_filler_words()
        assert result.words == []


# ---------------------------------------------------------------------------
# detect_pauses
# ---------------------------------------------------------------------------


class TestDetectPauses:
    def test_detects_gap(self):
        words = _make_words(("a", 0.0, 0.5), ("b", 1.5, 2.0))
        actual = Transcript(words).detect_pauses(min_gap_seconds=0.5)
        assert actual == [(0.5, 1.5)]

    def test_ignores_small_gaps(self):
        words = _make_words(("a", 0.0, 0.5), ("b", 0.6, 1.0))
        assert Transcript(words).detect_pauses(min_gap_seconds=0.5) == []

    def test_skips_none_end(self):
        words = _make_words(("a", 0.0, None), ("b", 1.0, 1.5))
        assert Transcript(words).detect_pauses() == []

    def test_multiple_pauses(self):
        words = _make_words(
            ("a", 0.0, 0.5),
            ("b", 1.5, 2.0),
            ("c", 3.0, 3.5),
        )
        actual = Transcript(words).detect_pauses(min_gap_seconds=0.5)
        assert actual == [(0.5, 1.5), (2.0, 3.0)]

    def test_empty_transcript(self):
        assert Transcript([]).detect_pauses() == []

    def test_single_word(self):
        words = _make_words(("a", 0.0, 0.5))
        assert Transcript(words).detect_pauses() == []


# ---------------------------------------------------------------------------
# shorten_pauses
# ---------------------------------------------------------------------------


class TestShortenPauses:
    def test_shortens_long_pause(self):
        words = _make_words(("a", 0.0, 0.5), ("b", 2.0, 2.5))
        result = Transcript(words).shorten_pauses(
            min_gap_seconds=0.5, target_gap_seconds=0.2,
        )
        actual_words = result.words
        assert actual_words[0].start == pytest.approx(0.0)
        assert actual_words[0].end == pytest.approx(0.5)
        # Gap was 1.5s, shortened to 0.2s → shift = 1.3s
        assert actual_words[1].start == pytest.approx(2.0 - 1.3)
        assert actual_words[1].end == pytest.approx(2.5 - 1.3)

    def test_preserves_short_gaps(self):
        words = _make_words(("a", 0.0, 0.5), ("b", 0.6, 1.0))
        result = Transcript(words).shorten_pauses(min_gap_seconds=0.5)
        assert result.words[1].start == pytest.approx(0.6)

    def test_multiple_pauses_accumulate_shift(self):
        words = _make_words(
            ("a", 0.0, 0.5),
            ("b", 2.0, 2.5),
            ("c", 4.0, 4.5),
        )
        result = Transcript(words).shorten_pauses(
            min_gap_seconds=0.5, target_gap_seconds=0.2,
        )
        # First pause: gap=1.5, shift=1.3
        # Second pause: gap=1.5, shift+=1.3 → total shift=2.6
        assert result.words[2].start == pytest.approx(4.0 - 2.6)

    def test_empty_transcript(self):
        result = Transcript([]).shorten_pauses()
        assert result.words == []

    def test_returns_new_transcript(self):
        words = _make_words(("a", 0.0, 0.5), ("b", 2.0, 2.5))
        original = Transcript(words)
        original.shorten_pauses(min_gap_seconds=0.5)
        assert original.words[1].start == 2.0  # unchanged

    def test_none_end_word(self):
        words = _make_words(("a", 0.0, None), ("b", 2.0, 2.5))
        result = Transcript(words).shorten_pauses(min_gap_seconds=0.5)
        # Can't detect pause when prev end is None, so no shift
        assert result.words[1].start == pytest.approx(2.0)
        assert result.words[0].end is None


# ---------------------------------------------------------------------------
# AudiateProject.find_linked_media
# ---------------------------------------------------------------------------


def _make_audiate_data(
    *,
    session_id: str = "test-session-uuid",
) -> dict:
    return {
        "metadata": {
            "projectLanguage": "en",
            "caiCamtasiaSessionId": session_id,
        },
        "sourceBin": [{"id": 1, "src": "./media/audio.wav"}],
        "timeline": {
            "sceneTrack": {
                "scenes": [{
                    "csml": {
                        "tracks": [{
                            "medias": [{"src": 1, "duration": EDIT_RATE * 10}],
                            "parameters": {
                                "transcription": {
                                    "keyframes": [
                                        {
                                            "time": 0,
                                            "endTime": 0,
                                            "value": json.dumps({"id": "w1", "text": "hello"}),
                                            "duration": 0,
                                        },
                                    ]
                                }
                            },
                        }]
                    }
                }]
            }
        },
    }


class TestFindLinkedMedia:
    def test_finds_matching_media(self, tmp_path: Path, project):
        # Set up audiate file
        fp = tmp_path / "test.audiate"
        fp.write_text(json.dumps(_make_audiate_data(session_id="linked-uuid")))
        audiate = AudiateProject(fp)

        # Add a media entry and a clip with matching audiateLinkedSession
        project._data["sourceBin"].append({
            "id": 42,
            "src": "media/audio.wav",
            "rect": [0, 0, 0, 0],
            "lastMod": "20260101T000000",
            "sourceTracks": [],
        })
        track = next(iter(project.timeline.tracks))
        from camtasia.timing import EDIT_RATE as ER
        track.add_clip("AMFile", 42, 0, ER * 2)
        clip = next(iter(track.clips))
        clip._data["audiateLinkedSession"] = "linked-uuid"

        result = audiate.find_linked_media(project)
        assert result is not None
        assert result.id == 42

    def test_returns_none_when_no_match(self, tmp_path: Path, project):
        fp = tmp_path / "test.audiate"
        fp.write_text(json.dumps(_make_audiate_data(session_id="no-match")))
        audiate = AudiateProject(fp)
        assert audiate.find_linked_media(project) is None

    def test_returns_none_for_empty_session(self, tmp_path: Path, project):
        fp = tmp_path / "test.audiate"
        fp.write_text(json.dumps(_make_audiate_data()))
        audiate = AudiateProject(fp)
        assert audiate.find_linked_media(project) is None
