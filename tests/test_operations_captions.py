"""Tests for operations/captions.py stubs and CaptionAttributes.default_duration_seconds."""
from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from camtasia import Project
from camtasia.operations.captions import (
    TrimRange,
    generate_captions_from_audio,
    sync_script_to_captions,
    trim_silences,
)
from camtasia.timeline.captions import CaptionAttributes


class TestGenerateCaptionsFromAudio:
    def test_raises_not_implemented(self):
        proj = MagicMock()
        clip = MagicMock()
        with pytest.raises(NotImplementedError, match='Audiate'):
            generate_captions_from_audio(proj, clip)


class TestSyncScriptToCaptions:
    def test_raises_not_implemented(self):
        proj = MagicMock()
        with pytest.raises(NotImplementedError, match='Windows'):
            sync_script_to_captions(proj, 'hello world', [(0.0, 1.0)])


class TestTrimSilences:
    def test_raises_not_implemented(self):
        clip = MagicMock()
        with pytest.raises(NotImplementedError, match='audio analysis'):
            trim_silences(clip)

    def test_raises_with_custom_params(self):
        clip = MagicMock()
        with pytest.raises(NotImplementedError):
            trim_silences(clip, threshold_db=-40, min_silence_ms=500)


class TestTrimRange:
    def test_dataclass_fields(self):
        tr = TrimRange(start_seconds=1.0, end_seconds=2.5)
        assert tr.start_seconds == 1.0
        assert tr.end_seconds == 2.5


class TestDefaultDurationSeconds:
    def test_default_value(self):
        attrs = CaptionAttributes({})
        assert attrs.default_duration_seconds == 4.0

    def test_setter(self):
        data: dict = {}
        attrs = CaptionAttributes(data)
        attrs.default_duration_seconds = 5.5
        assert attrs.default_duration_seconds == 5.5
        assert data['defaultDurationSeconds'] == 5.5

    def test_reads_from_data(self):
        attrs = CaptionAttributes({'defaultDurationSeconds': 3.0})
        assert attrs.default_duration_seconds == 3.0

    def test_validation_rejects_zero(self):
        attrs = CaptionAttributes({})
        with pytest.raises(ValueError, match='must be > 0'):
            attrs.default_duration_seconds = 0

    def test_validation_rejects_negative(self):
        attrs = CaptionAttributes({})
        with pytest.raises(ValueError, match='must be > 0'):
            attrs.default_duration_seconds = -1.0
