"""Tests for camtasia.audiate.project — AudiateProject parsing."""
from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from camtasia.audiate.project import AudiateProject
from camtasia.timing import EDIT_RATE

if TYPE_CHECKING:
    from pathlib import Path


def _make_audiate_data(
    *,
    language: str = "en",
    session_id: str = "test-session-uuid",
    media_duration: int = EDIT_RATE * 10,
    src_id: int = 1,
    src_path: str = "./media/audio.wav",
) -> dict:
    return {
        "metadata": {
            "projectLanguage": language,
            "caiCamtasiaSessionId": session_id,
        },
        "sourceBin": [{"id": src_id, "src": src_path}],
        "timeline": {
            "sceneTrack": {
                "scenes": [{
                    "csml": {
                        "tracks": [{
                            "medias": [{"src": src_id, "duration": media_duration}],
                            "parameters": {
                                "transcription": {
                                    "keyframes": [
                                        {"time": 0, "endTime": 0, "value": json.dumps({"id": "w1", "text": "hello"}), "duration": 0},
                                        {"time": EDIT_RATE, "endTime": EDIT_RATE, "value": json.dumps({"id": "w2", "text": "world"}), "duration": 0},
                                    ]
                                }
                            },
                        }]
                    }
                }]
            }
        },
    }


@pytest.fixture
def audiate_file(tmp_path: Path) -> Path:
    data = _make_audiate_data()
    fp = tmp_path / "test.audiate"
    fp.write_text(json.dumps(data))
    return fp


@pytest.fixture
def audiate_dir(tmp_path: Path) -> Path:
    data = _make_audiate_data()
    fp = tmp_path / "recording.audiate"
    fp.write_text(json.dumps(data))
    return tmp_path


class TestAudiateProjectInit:
    def test_load_from_file(self, audiate_file: Path):
        proj = AudiateProject(audiate_file)
        assert repr(proj).startswith("AudiateProject(")

    def test_load_from_directory(self, audiate_dir: Path):
        proj = AudiateProject(audiate_dir)
        assert proj.language == "en"

    def test_directory_without_audiate_raises(self, tmp_path: Path):
        with pytest.raises(FileNotFoundError, match=r"No .audiate file"):
            AudiateProject(tmp_path)


class TestAudiateProjectProperties:
    def test_transcript_words(self, audiate_file: Path):
        proj = AudiateProject(audiate_file)
        actual_words = [w.text for w in proj.transcript.words]
        assert actual_words == ["hello", "world"]

    def test_language(self, audiate_file: Path):
        proj = AudiateProject(audiate_file)
        assert proj.language == "en"

    def test_session_id(self, audiate_file: Path):
        proj = AudiateProject(audiate_file)
        assert proj.session_id == "test-session-uuid"

    def test_audio_duration(self, audiate_file: Path):
        proj = AudiateProject(audiate_file)
        expected_duration = 10.0
        assert proj.audio_duration == expected_duration

    def test_source_audio_path(self, audiate_file: Path):
        proj = AudiateProject(audiate_file)
        actual_path = proj.source_audio_path
        assert actual_path == (audiate_file.parent / "media" / "audio.wav").resolve()

    def test_source_audio_path_missing_raises(self, tmp_path: Path):
        data = _make_audiate_data(src_id=99)
        data["sourceBin"] = []
        fp = tmp_path / "bad.audiate"
        fp.write_text(json.dumps(data))
        proj = AudiateProject(fp)
        with pytest.raises(FileNotFoundError, match="Source with id=99"):
            _ = proj.source_audio_path

    def test_repr(self, audiate_file: Path):
        proj = AudiateProject(audiate_file)
        assert str(audiate_file) in repr(proj)
