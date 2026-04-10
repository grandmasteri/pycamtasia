# pycamtasia

[![Documentation](https://img.shields.io/badge/docs-GitHub%20Pages-blue)](https://grandmasteri.github.io/pycamtasia/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests](https://github.com/grandmasteri/pycamtasia/actions/workflows/tests.yml/badge.svg)](https://github.com/grandmasteri/pycamtasia/actions/workflows/tests.yml)

A Python library for reading, writing, and manipulating TechSmith Camtasia project files (`.cmproj` / `.tscproj`) and Audiate transcripts.

Forked from [sixty-north/python-camtasia](https://github.com/sixty-north/python-camtasia), extended with full timeline manipulation, effects, speed changes, audio-video sync, and Audiate integration.

📖 **[Full API Documentation](https://grandmasteri.github.io/pycamtasia/)**

## Features

- Load, edit, and save Camtasia project bundles
- Iterate tracks, clips, markers, and transitions
- Type-safe clip access (audio, video, image, screen recording, callout, group)
- Speed changes with rational-precision scalars (roadmap)
- Add/remove transitions between clips
- Cursor and visual effects (drop shadow, round corners, motion blur)
- Word-level transcript parsing from Audiate and WhisperX
- High-level operations: project rescaling, audio-video sync, templates
- Full timing system with tick↔seconds conversion
- Audio gain control and mute API
- Auto-detect image dimensions and audio duration via ffprobe
- Camtasia v10 compatible JSON formatting (NSJSONSerialization style)
- 100% test coverage with 788 tests

## Installation

```bash
git clone https://github.com/grandmasteri/pycamtasia.git
cd pycamtasia
pip install -e .
```

> Requires ffmpeg/ffprobe: `brew install ffmpeg`

> Optional: `brew install mediainfo && pip install pymediainfo` for enhanced media metadata

## Quick Start

```python
import camtasia

# Load a project
proj = camtasia.load_project('path/to/project.cmproj')

# Browse media in the bin
for media in proj.media_bin:
    print(media.source)

# Iterate tracks and clips
for track in proj.timeline.tracks:
    print(track.name)
    for clip in track.clips:
        print(f"  {clip.clip_type}: {clip.start_seconds:.2f}s, {clip.duration_seconds:.2f}s")

# Read timeline markers
for marker in proj.timeline.markers:
    print(f"{marker.name} at {marker.time_seconds:.1f}s")

# Save changes
proj.save()
```

Create a new empty project:

```python
camtasia.new_project('path/to/new.cmproj')
```

## Working with Clips

Clips are type-dispatched — each clip type has its own class:

| Class | Description |
|-------|-------------|
| `AMFile` | Audio clip |
| `VMFile` | Video clip |
| `IMFile` | Image/still clip |
| `ScreenVMFile` | Screen recording (video) |
| `ScreenIMFile` | Screen recording (image) |
| `StitchedMedia` | Compound media with sub-clips |
| `Group` | Grouped clips across internal tracks |
| `Callout` | Text overlay / annotation |

```python
from camtasia import AMFile, VMFile

for track in proj.timeline.tracks:
    for clip in track.clips:
        if isinstance(clip, VMFile):
            print(f"Video: {clip.duration_seconds:.1f}s, scalar={clip.scalar}")
        elif isinstance(clip, AMFile):
            print(f"Audio: source_id={clip.source_id}")
```

### Speed Changes

Speed is stored as a rational scalar (`Fraction`). A scalar of `1/2` means 2× playback speed.

```python
clip.set_speed(2.0)       # 2× speed — scalar becomes 1/2
clip.set_speed(0.5)       # half speed — scalar becomes 2/1
print(clip.scalar)        # Fraction(1, 2)
```

## Transitions

Transitions live on each track and reference the clips on either side:

```python
from camtasia import seconds_to_ticks

track = list(proj.timeline.tracks)[0]

# Add a fade between two clips
clips = list(track.clips)
track.transitions.add_fade_through_black(
    left_clip_id=clips[0].id,
    right_clip_id=clips[1].id,
    duration_ticks=seconds_to_ticks(0.5),
)

# Iterate transitions
for t in track.transitions:
    print(f"{t.name}: {t.duration_seconds:.2f}s")

# Remove by index
track.transitions.remove(0)
```

## Effects

Add visual and cursor effects to clips:

```python
from camtasia.effects import RoundCorners, DropShadow, CursorPhysics

# Visual effects
clip.effects.append(RoundCorners(radius=16.0).data)
clip.effects.append(DropShadow(offset=15.0, blur=25.0, opacity=0.2).data)

# Cursor effects (for screen recordings)
clip.effects.append(CursorPhysics(smoothing=0.8).data)
```

Available effect classes:

- `RoundCorners` — rounded corner radius
- `DropShadow` — shadow with offset, blur, opacity
- `CursorMotionBlur` — motion blur on cursor movement
- `CursorShadow` — drop shadow under cursor
- `CursorPhysics` — smooth/elastic cursor movement
- `LeftClickScaling` — visual pulse on left click

## Audiate Integration

Parse word-level transcripts from Audiate projects or WhisperX output:

```python
from camtasia.audiate import AudiateProject, Transcript

# From an Audiate file
audiate = AudiateProject('recording.audiate')
transcript = Transcript.from_audiate_keyframes(audiate.keyframes)

# From WhisperX
transcript = Transcript.from_whisperx_result(whisperx_result)

# Query the transcript
print(transcript.full_text)
print(f"Duration: {transcript.duration:.1f}s")

# Find a phrase
word = transcript.find_phrase("click the submit button")
if word:
    print(f"Found at {word.start:.2f}s")

# Get words in a time range
segment = transcript.words_in_range(10.0, 20.0)
for w in segment:
    print(f"  {w.start:.2f}s: {w.text}")
```

## Operations

High-level operations that coordinate changes across the entire project.

### Rescale Project

Stretch or compress all timing values by a factor:

```python
from fractions import Fraction
from camtasia.operations import rescale_project

proj = camtasia.load_project('project.cmproj')

# Stretch everything by 10% (slow down)
rescale_project(proj._data, Fraction(11, 10))
proj.save()
```

### Fix Audio Speed

Correct audio that was recorded at the wrong speed:

```python
from camtasia.operations import set_audio_speed

proj = camtasia.load_project('project.cmproj')
factor = set_audio_speed(proj._data, target_speed=1.0)
print(f"Applied stretch factor: {float(factor):.4f}")
proj.save()
```

### Audio-Video Sync

Align video segments with audio using transcript markers:

```python
from camtasia.operations import plan_sync

markers = [("Introduction", 0), ("Demo starts", 352_800_000)]
words = [{"word": "Introduction", "start": 0.0, "end": 1.0},
         {"word": "Demo", "start": 5.2, "end": 5.5},
         {"word": "starts", "start": 5.5, "end": 5.9}]

segments = plan_sync(markers, words)
for seg in segments:
    print(f"Video {seg.video_start_ticks}–{seg.video_end_ticks}: scalar={seg.scalar}")
```

### Templates

Clone a project's structure for reuse, or swap media sources:

```python
from camtasia.operations import clone_project_structure, replace_media_source

# Create an empty template from an existing project
template = clone_project_structure(proj._data)

# Replace all references to one media source with another
count = replace_media_source(proj._data, old_source_id=1, new_source_id=2)
print(f"Updated {count} clips")
```

## Timing System

Camtasia uses an `editRate` of **705,600,000 ticks per second** — chosen to be evenly divisible by common frame rates (30, 60 fps) and audio sample rates (44100, 48000 Hz). This avoids floating-point rounding in timeline positioning.

```python
from camtasia.timing import (
    EDIT_RATE,
    seconds_to_ticks,
    ticks_to_seconds,
    format_duration,
    speed_to_scalar,
    scalar_to_speed,
)

EDIT_RATE                        # 705_600_000
seconds_to_ticks(2.5)            # 1_764_000_000
ticks_to_seconds(1_764_000_000)  # 2.5
format_duration(seconds_to_ticks(125.3))  # '2:05.29'

speed_to_scalar(2.0)             # Fraction(1, 2)
scalar_to_speed(Fraction(1, 2))  # 2.0
```

Speed scalars are stored as `fractions.Fraction` for exact rational arithmetic — no floating-point drift when composing speed changes.

## API Reference

The public API is available directly from `import camtasia`:

- **Project management**: `load_project()`, `new_project()`, `Project`
- **Timeline**: `Timeline`, `Track`, `Marker`, `MarkerList`, `Transition`, `TransitionList`
- **Clips**: `BaseClip`, `AMFile`, `VMFile`, `IMFile`, `ScreenVMFile`, `ScreenIMFile`, `StitchedMedia`, `Group`, `Callout`
- **Effects**: `Effect`, `RoundCorners`, `DropShadow`, `CursorPhysics`, `CursorMotionBlur`, `CursorShadow`, `LeftClickScaling`
- **Audiate**: `AudiateProject`, `Transcript`, `Word`
- **Timing**: `EDIT_RATE`, `seconds_to_ticks()`, `ticks_to_seconds()`, `format_duration()`, `speed_to_scalar()`, `scalar_to_speed()`
- **Operations**: `rescale_project()`, `set_audio_speed()`, `plan_sync()`, `clone_project_structure()`, `replace_media_source()`

See the [full API documentation](https://grandmasteri.github.io/pycamtasia/) for detailed parameter docs, examples, and type signatures.

## Contributing

Contributions are welcome. Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

Run tests and view coverage:

```bash
# Run tests
PYTHONPATH=src pytest tests/

# Run tests with coverage report
PYTHONPATH=src pytest tests/ --cov=camtasia --cov-report=term-missing

# Generate HTML coverage report (browse locally)
PYTHONPATH=src pytest tests/ --cov=camtasia --cov-report=html
open htmlcov/index.html
```

The library uses thin wrappers over the underlying JSON dicts — mutations go directly to the dict, so `project.save()` always writes the current state. See `ARCHITECTURE.md` for design details.

## Known Limitations

- `.trec` screen recordings cannot be imported into new projects — start from the existing Camtasia Rev project
- `set_speed()` not yet implemented
- Audio source metadata from ffprobe is approximate — Camtasia corrects values on open

## License

BSD-2-Clause. Originally forked from [sixty-north/python-camtasia](https://github.com/sixty-north/python-camtasia).
