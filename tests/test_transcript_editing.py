"""Tests for Transcript word editing, gaps, and to_dynamic_caption_clip."""
from __future__ import annotations

import pytest

from camtasia.audiate.transcript import Transcript, TranscriptGap, Word
from camtasia.timeline.captions import DynamicCaptionStyle


def _make_words(*specs: tuple[str, float, float]) -> list[Word]:
    """Build Word list from (text, start, end) tuples."""
    return [
        Word(text=t, start=s, end=e, word_id=f"w{i}")
        for i, (t, s, e) in enumerate(specs)
    ]


# ---------------------------------------------------------------------------
# TranscriptGap dataclass
# ---------------------------------------------------------------------------


class TestTranscriptGap:
    def test_fields(self):
        gap = TranscriptGap(time_start=1.0, time_end=2.0)
        assert gap.time_start == 1.0
        assert gap.time_end == 2.0

    def test_equality(self):
        assert TranscriptGap(1.0, 2.0) == TranscriptGap(1.0, 2.0)

    def test_inequality(self):
        assert TranscriptGap(1.0, 2.0) != TranscriptGap(1.0, 3.0)


# ---------------------------------------------------------------------------
# Transcript.add_word
# ---------------------------------------------------------------------------


class TestAddWord:
    def test_inserts_at_correct_position(self):
        words = _make_words(("hello", 0.0, 0.5), ("world", 1.0, 1.5))
        t = Transcript(words)
        new_word = t.add_word("beautiful", 0.6, 0.9)
        assert [w.text for w in t.words] == ["hello", "beautiful", "world"]
        assert new_word.text == "beautiful"

    def test_inserts_at_beginning(self):
        words = _make_words(("world", 1.0, 1.5))
        t = Transcript(words)
        t.add_word("hello", 0.0, 0.5)
        assert t.words[0].text == "hello"

    def test_inserts_at_end(self):
        words = _make_words(("hello", 0.0, 0.5))
        t = Transcript(words)
        t.add_word("world", 1.0, 1.5)
        assert t.words[-1].text == "world"

    def test_empty_transcript(self):
        t = Transcript([])
        t.add_word("first", 0.0, 0.5)
        assert len(t.words) == 1
        assert t.words[0].text == "first"

    def test_word_id_generated(self):
        t = Transcript([])
        word = t.add_word("test", 0.0, 0.5)
        assert word.word_id.startswith("w-add-")


# ---------------------------------------------------------------------------
# Transcript.delete_word
# ---------------------------------------------------------------------------


class TestDeleteWord:
    def test_removes_word(self):
        words = _make_words(("hello", 0.0, 0.5), ("world", 1.0, 1.5))
        t = Transcript(words)
        t.delete_word("w0")
        assert [w.text for w in t.words] == ["world"]

    def test_raises_on_missing_id(self):
        t = Transcript(_make_words(("hello", 0.0, 0.5)))
        with pytest.raises(KeyError, match="no-such-id"):
            t.delete_word("no-such-id")

    def test_delete_last_word(self):
        words = _make_words(("only", 0.0, 0.5))
        t = Transcript(words)
        t.delete_word("w0")
        assert t.words == []


# ---------------------------------------------------------------------------
# Transcript.convert_to_gap
# ---------------------------------------------------------------------------


class TestConvertToGap:
    def test_converts_word_to_empty(self):
        words = _make_words(("hello", 0.0, 0.5), ("world", 1.0, 1.5))
        t = Transcript(words)
        t.convert_to_gap("w0")
        assert t.words[0].text == ""
        assert t.words[0].start == 0.0

    def test_raises_on_missing_id(self):
        t = Transcript(_make_words(("hello", 0.0, 0.5)))
        with pytest.raises(KeyError, match="missing"):
            t.convert_to_gap("missing")

    def test_gap_appears_in_gaps_property(self):
        words = _make_words(("hello", 0.0, 0.5), ("world", 1.0, 1.5))
        t = Transcript(words)
        t.convert_to_gap("w0")
        assert len(t.gaps) == 1
        assert t.gaps[0].time_start == 0.0
        assert t.gaps[0].time_end == 0.5


# ---------------------------------------------------------------------------
# Transcript.set_word_timing
# ---------------------------------------------------------------------------


class TestSetWordTiming:
    def test_updates_timing(self):
        words = _make_words(("hello", 0.0, 0.5))
        t = Transcript(words)
        t.set_word_timing("w0", 0.1, 0.6)
        assert t.words[0].start == 0.1
        assert t.words[0].end == 0.6

    def test_raises_on_missing_id(self):
        t = Transcript(_make_words(("hello", 0.0, 0.5)))
        with pytest.raises(KeyError, match="nope"):
            t.set_word_timing("nope", 0.0, 1.0)


# ---------------------------------------------------------------------------
# Transcript.gaps property
# ---------------------------------------------------------------------------


class TestGapsProperty:
    def test_no_gaps(self):
        words = _make_words(("hello", 0.0, 0.5), ("world", 1.0, 1.5))
        assert Transcript(words).gaps == []

    def test_multiple_gaps(self):
        words = _make_words(
            ("hello", 0.0, 0.5),
            ("um", 0.6, 0.8),
            ("world", 1.0, 1.5),
        )
        t = Transcript(words)
        t.convert_to_gap("w1")
        gaps = t.gaps
        assert len(gaps) == 1
        assert gaps[0] == TranscriptGap(time_start=0.6, time_end=0.8)

    def test_empty_transcript(self):
        assert Transcript([]).gaps == []

    def test_gap_with_none_end(self):
        words = [Word(text="", start=1.0, end=None, word_id="g0")]
        gaps = Transcript(words).gaps
        assert len(gaps) == 1
        assert gaps[0].time_end == 1.0  # falls back to start


# ---------------------------------------------------------------------------
# Transcript.to_dynamic_caption_clip
# ---------------------------------------------------------------------------


class TestToDynamicCaptionClip:
    def test_creates_callout_on_track(self, project):
        words = _make_words(("hello", 0.0, 0.5), ("world", 0.6, 1.0))
        t = Transcript(words)
        clip = t.to_dynamic_caption_clip(project)
        assert clip.text == "hello world"
        assert clip.clip_type == "Callout"

    def test_uses_custom_track_name(self, project):
        words = _make_words(("test", 0.0, 0.5))
        t = Transcript(words)
        t.to_dynamic_caption_clip(project, track_name="MyTrack")
        track_names = [tr.name for tr in project.timeline.tracks]
        assert "MyTrack" in track_names

    def test_uses_custom_style(self, project):
        words = _make_words(("styled", 0.0, 0.5))
        t = Transcript(words)
        style = DynamicCaptionStyle(name='custom', font_name='Courier', font_size=24)
        clip = t.to_dynamic_caption_clip(project, style=style)
        assert clip.font.get('name') == 'Courier'
        assert clip.font.get('size') == 24

    def test_default_style_is_classic(self, project):
        words = _make_words(("default", 0.0, 0.5))
        t = Transcript(words)
        clip = t.to_dynamic_caption_clip(project)
        assert clip.font.get('name') == 'Arial'

    def test_skips_gap_words(self, project):
        words = _make_words(("hello", 0.0, 0.5), ("um", 0.6, 0.8), ("world", 1.0, 1.5))
        t = Transcript(words)
        t.convert_to_gap("w1")
        clip = t.to_dynamic_caption_clip(project)
        assert clip.text == "hello world"

    def test_reuses_existing_track(self, project):
        words = _make_words(("a", 0.0, 0.5))
        t = Transcript(words)
        t.to_dynamic_caption_clip(project, track_name="Subtitles")
        initial_count = len(list(project.timeline.tracks))
        t.to_dynamic_caption_clip(project, track_name="Subtitles")
        assert len(list(project.timeline.tracks)) == initial_count
