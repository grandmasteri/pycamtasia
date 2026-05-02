#!/usr/bin/env python3
"""Repro for REV-user_docs-002: clip.audio_level is not a real property — should be clip.gain.

Expected: Setting audio_level doesn't raise an error but has no effect on the
project JSON. The correct property is `gain`.
"""
import tempfile
from pathlib import Path

from camtasia import load_project, new_project

with tempfile.TemporaryDirectory() as td:
    path = Path(td) / "test.cmproj"
    new_project(path)
    proj = load_project(path)
    track = proj.timeline.add_track("Test")
    track.add_placeholder(0.0, 5.0, title="Test")
    clip = list(track.clips)[0]

    # The undo-redo guide uses clip.audio_level = 0.5
    # This silently sets an instance attribute that has no effect on the project
    clip.audio_level = 0.5  # type: ignore[attr-defined]
    
    # Verify it's NOT a real property — it doesn't appear in _data
    has_audio_level_in_data = 'audio_level' in str(clip._data)
    print(f"audio_level in _data: {has_audio_level_in_data}")  # False
    
    # The correct property is clip.gain which DOES affect _data
    clip.gain = 0.5
    gain_value = clip._data.get('attributes', {}).get('gain')
    print(f"gain in _data: {gain_value}")  # 0.5
    
    if not has_audio_level_in_data and gain_value == 0.5:
        print("PASS: audio_level is a no-op; gain is the correct property")
    else:
        print("FAIL: unexpected behavior")
