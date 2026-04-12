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
- Speed changes with rational-precision scalars
- Transform helpers (move, scale, crop, rotation)
- Keyframe animation (fade in/out, opacity, custom keyframes)
- Visual effects (drop shadow, round corners, glow)
- Cursor effects (motion blur, shadow, physics, click scaling)
- Track reordering and clip search across the timeline
- Word-level transcript parsing from Audiate and WhisperX
- High-level operations: project rescaling, audio-video sync, templates
- Full timing system with tick↔seconds conversion
- Audio gain control and mute API
- Auto-detect image dimensions and audio duration via ffprobe
- Camtasia v10 compatible JSON formatting (NSJSONSerialization style)
- Python protocols (`__eq__`, `__hash__`, `__len__`, `__repr__`) on all major types
- Input validation on crop, opacity, speed, gain, and clip type
- Timeline search: `clips_in_range()`, `clips_of_type()`, `audio_clips`, `image_clips`, `video_clips`
- Track operations: `mute()`/`unmute()`, `hide()`/`show()`, `duplicate_clip()`, `move_clip()`
- Layout operations: `pack_track()`, `ripple_insert()`, `ripple_delete()`, `snap_to_grid()`
- Batch operations: `apply_to_clips()`, `fade_all()`, `scale_all()`, `move_all()`
- Project cleanup: `remove_orphaned_media()`, `remove_empty_tracks()`, `compact_project()`
- Project diff: `diff_projects()` for comparing two projects
- Export: SRT subtitles, project reports (JSON/Markdown), timeline JSON
- Builders: `TimelineBuilder` for cursor-based assembly, `CalloutBuilder` for styled text
- Project introspection: `summary()`, `statistics()`, `validate()`
- 1306 tests

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

### Transforms

```python
clip.move_to(x=100, y=200)       # reposition on canvas
clip.scale_to(1.5)               # uniform scale
clip.scale_to_xy(1.5, 1.0)       # non-uniform scale
clip.crop(left=0.1, top=0.1, right=0.1, bottom=0.1)
clip.rotation = 45.0             # degrees
```

### Animation & Opacity

```python
clip.fade_in(0.5)                # 0.5s fade in
clip.fade_out(0.5)               # 0.5s fade out
clip.fade(0.5, 0.5)              # combined fade in + out
clip.set_opacity(0.8)            # static opacity

clip.add_keyframe(time=1.0, value=0.5)   # custom keyframe
clip.clear_keyframes()
```

### Effects

```python
clip.add_drop_shadow(offset=15.0, blur=25.0, opacity=0.2)
clip.add_round_corners(radius=16.0)
clip.add_glow()
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

## Track & Timeline Operations

```python
# Track
track.clear()                    # remove all clips
track.add_lower_third("Title", "Subtitle", start_seconds=0, duration_seconds=5,
                      font_weight="bold", scale=1.2, template_ident="custom")
track.add_screen_recording(media, start_seconds=0, duration_seconds=30)
track.add_group(clips, start_seconds=0)
track.find_clip(clip_id)

# Timeline
timeline.move_track(from_index, to_index)
timeline.reorder_tracks([2, 0, 1])
timeline.move_track_to_front(track_index)
timeline.move_track_to_back(track_index)
timeline.find_clip(clip_id)
timeline.next_clip_id()
```

## Project Properties

```python
proj.width                       # project canvas width
proj.height                      # project canvas height
proj.import_shader('path/to/shader.tscshadervid')
```

## Group Clips

```python
group.is_screen_recording        # True if group wraps a .trec
group.internal_media_src          # source path of internal media
group.set_internal_segment_speeds([(0, 1.0), (5.0, 2.0)])  # per-segment speeds
```

## Media Bin

```python
for media in proj.media_bin:
    print(media.source, media.duration_seconds)
```

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

```python
from fractions import Fraction
from camtasia.operations import rescale_project

proj = camtasia.load_project('project.cmproj')
rescale_project(proj._data, Fraction(11, 10))  # stretch by 10%
proj.save()
```

### Fix Audio Speed

```python
from camtasia.operations import set_audio_speed

proj = camtasia.load_project('project.cmproj')
factor = set_audio_speed(proj._data, target_speed=1.0)
proj.save()
```

### Audio-Video Sync

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

```python
from camtasia.operations import clone_project_structure, replace_media_source

template = clone_project_structure(proj._data)
count = replace_media_source(proj._data, old_source_id=1, new_source_id=2)
```

## Timing System

Camtasia uses an `editRate` of **705,600,000 ticks per second** — chosen to be evenly divisible by common frame rates (30, 60 fps) and audio sample rates (44100, 48000 Hz).

```python
from camtasia.timing import (
    EDIT_RATE, seconds_to_ticks, ticks_to_seconds,
    format_duration, speed_to_scalar, scalar_to_speed,
)

EDIT_RATE                        # 705_600_000
seconds_to_ticks(2.5)            # 1_764_000_000
ticks_to_seconds(1_764_000_000)  # 2.5
format_duration(seconds_to_ticks(125.3))  # '2:05.29'

speed_to_scalar(2.0)             # Fraction(1, 2)
scalar_to_speed(Fraction(1, 2))  # 2.0
```

## API Reference

The public API is available directly from `import camtasia`:

- **Project**: `load_project()`, `new_project()`, `use_project()`, `Project`, `ValidationIssue`
  - `project.width`, `project.height`, `project.import_shader()`
  - `project.summary()`, `project.statistics()`, `project.validate()`
- **Timeline**: `Timeline`, `Track`, `Marker`, `MarkerList`, `Transition`, `TransitionList`
  - `timeline.move_track()`, `reorder_tracks()`, `move_track_to_front()`, `move_track_to_back()`, `find_clip()`, `find_track()`, `next_clip_id()`, `remove_empty_tracks()`
  - `timeline.clips_in_range()`, `clips_of_type()`, `audio_clips`, `image_clips`, `video_clips`
  - `track.clear()`, `track.mute()`, `track.unmute()`, `track.hide()`, `track.show()`
  - `track.duplicate_clip()`, `track.move_clip()`, `track.find_clip()`
  - `track.add_lower_third()`, `track.add_screen_recording()`, `track.add_group()`
- **Clips**: `BaseClip`, `AMFile`, `VMFile`, `IMFile`, `ScreenVMFile`, `ScreenIMFile`, `StitchedMedia`, `Group`, `Callout`
  - Transforms: `move_to()`, `scale_to()`, `scale_to_xy()`, `crop()`, `rotation`
  - Animation: `fade_in()`, `fade_out()`, `fade()`, `set_opacity()`, `add_keyframe()`, `clear_keyframes()`
  - Effects: `add_drop_shadow()`, `add_round_corners()`, `add_glow()`
  - Audio: `AMFile.is_muted`, `set_gain()`, `normalize_gain()`
  - Group: `is_screen_recording`, `internal_media_src`, `set_internal_segment_speeds()`
  - Media: `media.duration_seconds`
- **Effects**: `Effect`, `Glow`, `RoundCorners`, `DropShadow`, `CursorPhysics`, `CursorMotionBlur`, `CursorShadow`, `LeftClickScaling`, `SourceEffect`
- **Audiate**: `AudiateProject`, `Transcript`, `Word`
- **Timing**: `EDIT_RATE`, `seconds_to_ticks()`, `ticks_to_seconds()`, `format_duration()`, `speed_to_scalar()`, `scalar_to_speed()`
- **Operations** (`camtasia.operations`):
  - Layout: `pack_track()`, `ripple_insert()`, `ripple_delete()`, `snap_to_grid()`
  - Batch: `apply_to_clips()`, `apply_to_track()`, `apply_to_all_tracks()`, `set_opacity_all()`, `fade_all()`, `scale_all()`, `move_all()`
  - Cleanup: `remove_orphaned_media()`, `remove_empty_tracks()`, `compact_project()`
  - Diff: `diff_projects()`, `ProjectDiff`
  - Speed: `rescale_project()`, `set_audio_speed()`
  - Sync: `plan_sync()`, `match_marker_to_transcript()`, `SyncSegment`
  - Template: `clone_project_structure()`, `replace_media_source()`, `duplicate_project()`
- **Export** (`camtasia.export`):
  - `export_markers_as_srt()` — SRT subtitle export
  - `export_project_report()` — JSON or Markdown project reports
  - `export_timeline_json()`, `load_timeline_json()` — portable timeline JSON
- **Builders** (`camtasia.builders`):
  - `TimelineBuilder` — cursor-based fluent API for video assembly
  - `CalloutBuilder` — fluent API for styled text callouts
- **Protocols**: `__eq__`, `__hash__`, `__len__`, `__repr__` on all major types

See the [full API documentation](https://grandmasteri.github.io/pycamtasia/) for detailed parameter docs, examples, and type signatures.

## Contributing

Contributions are welcome. Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

Run tests and view coverage:

```bash
PYTHONPATH=src pytest tests/
PYTHONPATH=src pytest tests/ --cov=camtasia --cov-report=term-missing

# Run tests in parallel
python -m pytest -n auto
```

The library uses thin wrappers over the underlying JSON dicts — mutations go directly to the dict, so `project.save()` always writes the current state. See `ARCHITECTURE.md` for design details.

## Known Limitations

- `.trec` screen recordings cannot be imported into new projects — start from the existing Camtasia Rev project
- Audio source metadata from ffprobe is approximate — Camtasia corrects values on open

## License

BSD-2-Clause. Originally forked from [sixty-north/python-camtasia](https://github.com/sixty-north/python-camtasia).
