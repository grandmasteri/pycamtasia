# pycamtasia — Architecture Design

## Overview

A comprehensive Python library for reading, writing, and manipulating TechSmith Camtasia project files (.cmproj/.tscproj) and Audiate files (.audiate). Forked from sixty-north/python-camtasia, extended to cover the full feature set discovered through reverse engineering.

## Package Structure

```
src/camtasia/
├── __init__.py                    # Public API exports
├── project.py                     # Project class (load/save .cmproj bundles)
├── timing.py                      # EditRate, ticks↔seconds, rational scalars
├── media_bin.py                   # SourceBin / Media management
├── timeline/
│   ├── __init__.py
│   ├── timeline.py                # Timeline class
│   ├── track.py                   # Track class + TrackAttributes
│   ├── markers.py                 # Marker class (timeline + per-media)
│   ├── transitions.py             # Transition class (FadeThroughBlack, etc.)
│   └── clips/
│       ├── __init__.py
│       ├── base.py                # BaseClip (shared fields: id, start, duration, etc.)
│       ├── audio.py               # AMFile
│       ├── video.py               # VMFile
│       ├── image.py               # IMFile
│       ├── screen_recording.py    # ScreenVMFile, ScreenIMFile
│       ├── stitched.py            # StitchedMedia
│       ├── group.py               # Group (compound clips)
│       └── callout.py             # Callout (text overlays)
├── effects/
│   ├── __init__.py
│   ├── base.py                    # Effect base class
│   ├── visual.py                  # RoundCorners, DropShadow
│   ├── cursor.py                  # CursorMotionBlur, CursorShadow, CursorPhysics, LeftClickScaling
│   └── source.py                  # SourceEffect (shader parameters)
├── annotations/
│   ├── __init__.py
│   └── callouts.py                # Callout definition builders (text, shapes)
├── audiate/
│   ├── __init__.py
│   ├── project.py                 # Audiate project reader
│   └── transcript.py              # Word-level transcript with timestamps
└── operations/
    ├── __init__.py
    ├── speed.py                   # Speed changes with full re-sync
    ├── sync.py                    # Audio-video sync from transcript + markers
    └── template.py                # Template-based project creation
```

## Key Design Decisions

### 1. Thin wrappers over JSON dicts
Each class wraps a reference to the underlying JSON dict (like the original library).
Mutations go directly to the dict — no separate "model" that needs serialization.
This means `project.save()` always writes the current state.

### 2. Timing as first-class concept
```python
from camtasia.timing import EditRate, Ticks, seconds_to_ticks, ticks_to_seconds

rate = EditRate(705_600_000)
ticks = rate.from_seconds(2.5)       # -> 1764000000
secs = rate.to_seconds(1764000000)   # -> 2.5
```

### 3. Rational scalars via fractions.Fraction
```python
clip.scalar                    # -> Fraction(51, 101)
clip.speed                     # -> 1.98 (human-readable speed multiplier)
clip.set_speed(2.0)            # sets scalar = Fraction(1, 2)
```

### 4. Type-dispatched clip access
```python
for clip in track.clips:           # iterate all clips
    if isinstance(clip, AMFile):   # type-safe
        print(clip.source_id)

track.clips.add_image(media, start=rate.from_seconds(5.0), duration=rate.from_seconds(10.0))
```

### 5. Transitions as track-level objects
```python
track.transitions.add("FadeThroughBlack", left_clip, right_clip, duration=rate.from_seconds(0.5))
for t in track.transitions:
    print(t.name, t.left_clip_id, t.right_clip_id)
```

### 6. Effects as composable objects
```python
from camtasia.effects import RoundCorners, DropShadow, CursorPhysics

clip.effects.add(RoundCorners(radius=16.0))
clip.effects.add(DropShadow(offset=15.0, blur=25.0, opacity=0.2))
```

## Module Responsibilities

### timing.py
- EditRate class with conversion methods
- Rational scalar parsing/formatting (string fractions like "51/101")
- Duration formatting (ticks -> "M:SS.ff")

### media_bin.py
- Refactored from original, add type hints and docstrings
- Media class with type enum (Video=0, Image=1, Audio=2)
- Import media with proper sourceBin entry creation

### timeline/clips/base.py
- BaseClip with: id, start, duration, media_start, media_duration, scalar, effects, metadata
- Property accessors that read/write the underlying dict
- `start_seconds`, `duration_seconds` convenience properties

### timeline/clips/*.py
- One class per clip type, inheriting BaseClip
- Type-specific properties (e.g., ScreenVMFile.cursor_scale, Callout.text)
- Factory function to instantiate correct class from _type field

### timeline/transitions.py
- Transition dataclass: name, duration, left_media_id, right_media_id, attributes
- TransitionList on Track for add/remove/iterate

### effects/
- Effect base with name, category, bypassed, parameters
- Concrete classes for each known effect type
- Parameters as typed properties

### audiate/
- AudiateProject: loads .audiate files (same JSON schema as .tscproj)
- Transcript: parses word-level keyframes into Word(text, start, end) objects

### operations/
- High-level operations that coordinate across multiple clips/tracks
- speed.rescale_project(project, factor) — what we tested successfully
- sync.sync_to_transcript(project, transcript, markers) — V3 workflow
