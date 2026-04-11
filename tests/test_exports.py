from __future__ import annotations

import camtasia


CLIP_TYPES = [
    "UnifiedMedia",
    "GroupTrack",
    "ScreenVMFile",
    "ScreenIMFile",
    "StitchedMedia",
]


def test_all_clip_types_importable():
    for name in CLIP_TYPES:
        assert hasattr(camtasia, name), f"{name} not importable from camtasia"


def test_all_in_all():
    for name in CLIP_TYPES:
        assert name in camtasia.__all__, f"{name} not in camtasia.__all__"
