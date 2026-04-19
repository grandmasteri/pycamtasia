"""Tests for BaseClip.summary()."""
from __future__ import annotations

from camtasia.timeline.clips import BaseClip, EDIT_RATE


def _clip(**overrides) -> BaseClip:
    data: dict = {
        "id": 1,
        "_type": "VMFile",
        "src": 3,
        "start": 0,
        "duration": int(10 * EDIT_RATE),
        "mediaStart": 0,
        "mediaDuration": int(10 * EDIT_RATE),
        "scalar": 1,
    }
    data.update(overrides)
    return BaseClip(data)


class TestSummaryBasic:
    def test_basic_summary(self) -> None:
        clip = _clip()
        result = clip.summary()
        assert result.startswith("VMFile(id=1)")
        assert "Time: 0:00 - 0:10" in result
        assert "Duration: 10.00s" in result

    def test_no_speed_line_at_normal(self) -> None:
        clip = _clip()
        assert "Speed" not in clip.summary()

    def test_no_effects_line_when_empty(self) -> None:
        clip = _clip()
        assert "Effects" not in clip.summary()


class TestSummarySpeed:
    def test_speed_shown_when_not_one(self) -> None:
        clip = _clip(scalar="1/2")
        assert "Speed: 2.00x" in clip.summary()

    def test_speed_2x(self) -> None:
        clip = _clip(scalar=2)
        assert "Speed: 0.50x" in clip.summary()


class TestSummaryEffects:
    def test_single_effect(self) -> None:
        clip = _clip(effects=[{"effectName": "DropShadow"}])
        assert "Effects: DropShadow" in clip.summary()

    def test_multiple_effects(self) -> None:
        clip = _clip(effects=[
            {"effectName": "DropShadow"},
            {"effectName": "Glow"},
        ])
        assert "Effects: DropShadow, Glow" in clip.summary()

    def test_missing_effect_name_uses_fallback(self) -> None:
        clip = _clip(effects=[{}])
        assert "Effects: ?" in clip.summary()


class TestSummaryReturnType:
    def test_returns_str(self) -> None:
        assert isinstance(_clip().summary(), str)

    def test_multiline(self) -> None:
        lines = _clip().summary().split("\n")
        assert len(lines) == 3
        assert lines[0] == "VMFile(id=1)"
