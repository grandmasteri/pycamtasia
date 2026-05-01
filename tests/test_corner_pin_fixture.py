"""Fixture round-trip test for CornerPin effect."""
from __future__ import annotations

from pathlib import Path
import shutil

from camtasia.effects.base import effect_from_dict
from camtasia.effects.visual import CornerPin
from camtasia.project import load_project

RESOURCES = Path(__file__).parent.parent / "src" / "camtasia" / "resources"


def test_corner_pin_roundtrip(tmp_path: Path) -> None:
    """Add CornerPin to a clip, save, reload — verify effect survives."""
    dst = tmp_path / "test.cmproj"
    shutil.copytree(RESOURCES / "new.cmproj", dst)
    proj = load_project(dst)

    track = next(iter(proj.timeline.tracks))
    clip = track.add_image(source_id=1, start_seconds=0, duration_seconds=5)

    effect = clip.add_effect({
        "effectName": "CornerPin",
        "bypassed": False,
        "category": "categoryVisualEffects",
        "parameters": {
            "topLeftX": {"type": "double", "defaultValue": 0.0, "interp": "linr"},
            "topLeftY": {"type": "double", "defaultValue": 0.0, "interp": "linr"},
            "topRightX": {"type": "double", "defaultValue": 1.0, "interp": "linr"},
            "topRightY": {"type": "double", "defaultValue": 0.0, "interp": "linr"},
            "bottomLeftX": {"type": "double", "defaultValue": 0.0, "interp": "linr"},
            "bottomLeftY": {"type": "double", "defaultValue": 1.0, "interp": "linr"},
            "bottomRightX": {"type": "double", "defaultValue": 1.0, "interp": "linr"},
            "bottomRightY": {"type": "double", "defaultValue": 1.0, "interp": "linr"},
        },
    })
    assert isinstance(effect, CornerPin)
    assert effect.position == (0.5, 0.5)

    proj.save()
    proj2 = load_project(dst)

    track2 = next(iter(proj2.timeline.tracks))
    clip2 = next(iter(track2.clips))
    effects = [effect_from_dict(e) for e in clip2._data.get("effects", [])]
    corner_pins = [e for e in effects if isinstance(e, CornerPin)]
    assert len(corner_pins) == 1

    reloaded = corner_pins[0]
    assert reloaded.name == "CornerPin"
    assert reloaded.top_left == (0.0, 0.0)
    assert reloaded.top_right == (1.0, 0.0)
    assert reloaded.bottom_left == (0.0, 1.0)
    assert reloaded.bottom_right == (1.0, 1.0)
    assert reloaded.position == (0.5, 0.5)
    assert reloaded.skew == 0.0
    assert reloaded.rotation == 0.0
