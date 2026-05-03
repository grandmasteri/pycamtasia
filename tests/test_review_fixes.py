"""Regression tests for review findings (error_handling + edge_cases)."""

from __future__ import annotations

from unittest.mock import patch
import warnings

import pytest

from camtasia.frame_stamp import FrameStamp, _lcm
from camtasia.timing import speed_to_scalar

# === REV-edge_cases-001: FrameStamp rejects non-positive frame_rate ===


class TestFrameStampValidation:
    def test_zero_frame_rate_raises(self) -> None:
        with pytest.raises(ValueError, match="frame_rate must be positive"):
            FrameStamp(frame_number=100, frame_rate=0)

    def test_negative_frame_rate_raises(self) -> None:
        with pytest.raises(ValueError, match="frame_rate must be positive"):
            FrameStamp(frame_number=100, frame_rate=-30)

    def test_positive_frame_rate_ok(self) -> None:
        fs = FrameStamp(frame_number=100, frame_rate=30)
        assert fs.frame_rate == 30


# === REV-edge_cases-002: _lcm rejects zero inputs ===


class TestLcmValidation:
    def test_lcm_zero_first_raises(self) -> None:
        with pytest.raises(ValueError, match="must be positive"):
            _lcm(0, 30)

    def test_lcm_zero_second_raises(self) -> None:
        with pytest.raises(ValueError, match="must be positive"):
            _lcm(30, 0)

    def test_lcm_negative_uses_abs(self) -> None:
        assert _lcm(-30, 60) == 60

    def test_lcm_positive_ok(self) -> None:
        assert _lcm(12, 18) == 36


# === REV-edge_cases-003: speed_to_scalar rejects tiny floats ===


class TestSpeedToScalarTinyFloat:
    def test_very_small_speed_raises(self) -> None:
        with pytest.raises(ValueError, match="too small"):
            speed_to_scalar(1e-10)

    def test_threshold_speed_raises(self) -> None:
        with pytest.raises(ValueError, match="too small"):
            speed_to_scalar(1e-5)

    def test_normal_small_speed_ok(self) -> None:
        result = speed_to_scalar(0.01)
        assert result > 0


# === REV-edge_cases-007: Track.add_clip rejects non-positive duration / negative start ===


class TestAddClipValidation:
    def test_zero_duration_allowed(self, project) -> None:
        track = project.timeline.tracks[0]
        clip = track.add_clip("Callout", None, start=0, duration=0)
        assert clip.duration == 0

    def test_negative_duration_raises(self, project) -> None:
        track = project.timeline.tracks[0]
        with pytest.raises(ValueError, match="duration must be non-negative"):
            track.add_clip("Callout", None, start=0, duration=-100)

    def test_negative_start_raises(self, project) -> None:
        track = project.timeline.tracks[0]
        with pytest.raises(ValueError, match="start must be non-negative"):
            track.add_clip("Callout", None, start=-1, duration=705600000)

    def test_valid_clip_ok(self, project) -> None:
        track = project.timeline.tracks[0]
        clip = track.add_clip("Callout", None, start=0, duration=705600000)
        assert clip.duration == 705600000


# === REV-error_handling-001: _probe_media warns on unexpected pymediainfo errors ===


class TestProbeMediaWarning:
    def test_unexpected_pymediainfo_error_warns(self, tmp_path) -> None:
        from camtasia.project import _probe_media

        dummy = tmp_path / "test.mp4"
        dummy.write_bytes(b"\x00" * 100)

        # Patch pymediainfo.MediaInfo at the import source
        with patch.dict("sys.modules", {"pymediainfo": type("mod", (), {"MediaInfo": type("MediaInfo", (), {"parse": staticmethod(lambda *a, **kw: (_ for _ in ()).throw(AttributeError("API changed")))})})()}):
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                _probe_media(dummy)
            warned = [x for x in w if "pymediainfo" in str(x.message).lower()]
            assert len(warned) >= 1


# === REV-error_handling-002: _probe_media_ffprobe warns on unexpected errors ===


class TestProbeMediaFfprobeWarning:
    def test_unexpected_error_warns(self, tmp_path) -> None:
        from camtasia.project import _probe_media_ffprobe

        dummy = tmp_path / "test.mp4"
        dummy.write_bytes(b"\x00" * 100)

        with patch("camtasia.project._sp.run", side_effect=AttributeError("unexpected")):
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                result = _probe_media_ffprobe(dummy)
            warned = [x for x in w if "ffprobe" in str(x.message).lower()]
            assert len(warned) >= 1
            assert result["_backend"] == "ffprobe"


# === REV-error_handling-003: _parse_with_pymediainfo warns on unexpected errors ===


class TestParseWithPymediainfoWarning:
    def test_unexpected_error_warns(self, tmp_path) -> None:
        from camtasia.media_bin.media_bin import _parse_with_pymediainfo

        dummy = tmp_path / "test.mp4"
        dummy.write_bytes(b"\x00" * 100)

        with patch.dict("sys.modules", {"pymediainfo": type("mod", (), {"MediaInfo": type("MediaInfo", (), {"parse": staticmethod(lambda *a, **kw: (_ for _ in ()).throw(AttributeError("API changed")))})})()}):
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                result = _parse_with_pymediainfo(dummy)
            assert result is None
            warned = [x for x in w if "pymediainfo" in str(x.message).lower()]
            assert len(warned) >= 1


# === REV-error_handling-005: remove_media error includes context ===


class TestRemoveMediaErrorContext:
    def test_error_includes_media_id_and_track(self, project) -> None:
        from camtasia.operations.media_ops import remove_media

        # Add media and a clip referencing it
        track = project.timeline.tracks[0]
        track.add_clip("AMFile", 1, start=0, duration=705600000)

        with pytest.raises(ValueError, match=r"media.*1") as exc_info:
            remove_media(project, 1, clear_tracks=False)
        # Should mention the media_id
        assert "1" in str(exc_info.value)
