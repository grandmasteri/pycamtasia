"""Tests for extended Audiate API: smart_scenes, translate, TTS stubs, sync-edits."""
from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path

from camtasia.audiate.project import SUPPORTED_TRANSLATION_LANGUAGES, AudiateProject
from camtasia.audiate.transcript import Transcript
from camtasia.operations.sync import (
    delete_words_from_timeline,
    send_media_to_audiate,
    sync_audiate_edits_to_timeline,
)
from camtasia.timing import EDIT_RATE


def _make_audiate_data(
    *,
    language: str = "en",
    session_id: str = "test-session-uuid",
    smart_scenes: list[dict] | None = None,
    words: list[tuple[str, int]] | None = None,
) -> dict:
    """Build minimal .audiate JSON with optional smart_scenes and custom words."""
    if words is None:
        words = [("hello", 0), ("um", EDIT_RATE), ("world", EDIT_RATE * 2)]
    keyframes = [
        {
            "time": t,
            "endTime": t,
            "value": json.dumps({"id": f"w{i}", "text": text}),
            "duration": 0,
        }
        for i, (text, t) in enumerate(words)
    ]
    metadata: dict = {
        "projectLanguage": language,
        "caiCamtasiaSessionId": session_id,
    }
    if smart_scenes is not None:
        metadata["smartScenes"] = smart_scenes
    return {
        "metadata": metadata,
        "sourceBin": [{"id": 1, "src": "./media/audio.wav"}],
        "timeline": {
            "sceneTrack": {
                "scenes": [{
                    "csml": {
                        "tracks": [{
                            "medias": [{"src": 1, "duration": EDIT_RATE * 10}],
                            "parameters": {
                                "transcription": {"keyframes": keyframes},
                            },
                        }],
                    },
                }],
            },
        },
    }


@pytest.fixture
def audiate_file(tmp_path: Path) -> Path:
    data = _make_audiate_data()
    fp = tmp_path / "test.audiate"
    fp.write_text(json.dumps(data))
    return fp


@pytest.fixture
def audiate_with_scenes(tmp_path: Path) -> Path:
    scenes = [{"start": 0.0, "end": 5.0, "label": "intro"}, {"start": 5.0, "end": 10.0, "label": "body"}]
    data = _make_audiate_data(smart_scenes=scenes)
    fp = tmp_path / "scenes.audiate"
    fp.write_text(json.dumps(data))
    return fp


# ---------------------------------------------------------------------------
# SUPPORTED_TRANSLATION_LANGUAGES
# ---------------------------------------------------------------------------


class TestSupportedTranslationLanguages:
    def test_contains_expected_codes(self):
        expected = {"en", "de", "fr", "es", "it", "ja", "zh", "pt", "ko", "ru", "nl", "sv", "pl", "ar"}
        assert set(SUPPORTED_TRANSLATION_LANGUAGES) == expected

    def test_is_list(self):
        assert isinstance(SUPPORTED_TRANSLATION_LANGUAGES, list)


# ---------------------------------------------------------------------------
# smart_scenes
# ---------------------------------------------------------------------------


class TestSmartScenes:
    def test_returns_scenes_from_metadata(self, audiate_with_scenes: Path):
        proj = AudiateProject(audiate_with_scenes)
        actual = proj.smart_scenes
        assert actual == [
            {"start": 0.0, "end": 5.0, "label": "intro"},
            {"start": 5.0, "end": 10.0, "label": "body"},
        ]

    def test_returns_empty_when_absent(self, audiate_file: Path):
        proj = AudiateProject(audiate_file)
        assert proj.smart_scenes == []


# ---------------------------------------------------------------------------
# apply_suggested_edits
# ---------------------------------------------------------------------------


class TestApplySuggestedEdits:
    def test_removes_fillers_and_counts(self, audiate_file: Path):
        proj = AudiateProject(audiate_file)
        result = proj.apply_suggested_edits()
        assert result["fillers_removed"] == 1  # "um"
        transcript: Transcript = result["transcript"]
        assert "um" not in transcript.full_text

    def test_skip_fillers(self, audiate_file: Path):
        proj = AudiateProject(audiate_file)
        result = proj.apply_suggested_edits(remove_fillers=False)
        assert result["fillers_removed"] == 0
        assert "um" in result["transcript"].full_text

    def test_skip_pauses(self, audiate_file: Path):
        proj = AudiateProject(audiate_file)
        result = proj.apply_suggested_edits(remove_pauses=False)
        assert result["pauses_shortened"] == 0

    def test_returns_transcript_instance(self, audiate_file: Path):
        proj = AudiateProject(audiate_file)
        result = proj.apply_suggested_edits()
        assert isinstance(result["transcript"], Transcript)


# ---------------------------------------------------------------------------
# translate_script
# ---------------------------------------------------------------------------


class TestTranslateScript:
    def test_placeholder_translation(self, audiate_file: Path):
        proj = AudiateProject(audiate_file)
        translated = proj.translate_script("de")
        assert all(w.text.startswith("[de:") for w in translated.words)

    def test_preserves_timing(self, audiate_file: Path):
        proj = AudiateProject(audiate_file)
        original = proj.transcript
        translated = proj.translate_script("fr")
        assert [w.start for w in translated.words] == [w.start for w in original.words]

    def test_unsupported_language_raises(self, audiate_file: Path):
        proj = AudiateProject(audiate_file)
        with pytest.raises(ValueError, match="Unsupported language 'xx'"):
            proj.translate_script("xx")


# ---------------------------------------------------------------------------
# generate_audio
# ---------------------------------------------------------------------------


class TestGenerateAudio:
    def test_sets_pending_tts(self, audiate_file: Path):
        proj = AudiateProject(audiate_file)
        proj.generate_audio("en-US-Neural2-F")
        assert proj._data["metadata"]["pendingTTS"] == {
            "voice": "en-US-Neural2-F",
            "language": "en",
            "applyToEntireProject": True,
        }

    def test_partial_project(self, audiate_file: Path):
        proj = AudiateProject(audiate_file)
        proj.generate_audio("en-US-Neural2-F", apply_to_entire_project=False)
        assert proj._data["metadata"]["pendingTTS"]["applyToEntireProject"] is False


# ---------------------------------------------------------------------------
# generate_avatar
# ---------------------------------------------------------------------------


class TestGenerateAvatar:
    def test_sets_pending_avatar(self, audiate_file: Path):
        proj = AudiateProject(audiate_file)
        proj.generate_avatar("avatar-42")
        assert proj._data["metadata"]["pendingAvatar"] == {"avatarId": "avatar-42"}


# ---------------------------------------------------------------------------
# save_as_translation
# ---------------------------------------------------------------------------


class TestSaveAsTranslation:
    def test_writes_translated_copy(self, audiate_file: Path, tmp_path: Path):
        proj = AudiateProject(audiate_file)
        dest = tmp_path / "translated.audiate"
        proj.save_as_translation("de", dest)

        data = json.loads(dest.read_text())
        assert data["metadata"]["projectLanguage"] == "de"
        kf = data["timeline"]["sceneTrack"]["scenes"][0]["csml"]["tracks"][0]["parameters"]["transcription"]["keyframes"]
        first_word = json.loads(kf[0]["value"])["text"]
        assert first_word.startswith("[de:")

    def test_does_not_mutate_original(self, audiate_file: Path, tmp_path: Path):
        proj = AudiateProject(audiate_file)
        proj.save_as_translation("fr", tmp_path / "fr.audiate")
        assert proj.language == "en"
        assert proj.transcript.words[0].text == "hello"

    def test_unsupported_language_raises(self, audiate_file: Path, tmp_path: Path):
        proj = AudiateProject(audiate_file)
        with pytest.raises(ValueError, match="Unsupported language"):
            proj.save_as_translation("xx", tmp_path / "bad.audiate")


# ---------------------------------------------------------------------------
# sync_audiate_edits_to_timeline
# ---------------------------------------------------------------------------


class TestSyncAudiateEditsToTimeline:
    def test_returns_deleted_spans(self, audiate_file: Path, project):
        audiate = AudiateProject(audiate_file)
        spans = sync_audiate_edits_to_timeline(audiate, project)
        # "um" (w1) should be deleted — it's a filler word
        assert len(spans) >= 1
        # Each span is a (start, end) tuple
        assert all(isinstance(s, tuple) and len(s) == 2 for s in spans)


# ---------------------------------------------------------------------------
# send_media_to_audiate
# ---------------------------------------------------------------------------


class TestSendMediaToAudiate:
    def test_returns_pending_stub(self, project):
        track = next(iter(project.timeline.tracks))
        result = send_media_to_audiate(project, track)
        assert result["status"] == "pending"
        assert result["format"] == ".audiate"


# ---------------------------------------------------------------------------
# delete_words_from_timeline
# ---------------------------------------------------------------------------


class TestDeleteWordsFromTimeline:
    def test_deletes_specified_words(self, audiate_file: Path, project):
        audiate = AudiateProject(audiate_file)
        # w1 = "um" at EDIT_RATE ticks, w2 = "world" at EDIT_RATE*2
        spans = delete_words_from_timeline(audiate, project, ["w1"])
        assert len(spans) == 1

    def test_ignores_unknown_ids(self, audiate_file: Path, project):
        audiate = AudiateProject(audiate_file)
        spans = delete_words_from_timeline(audiate, project, ["nonexistent"])
        assert spans == []
