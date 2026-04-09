# Quick Start

## Installation

```bash
pip install pycamtasia
```

## Loading a Project

```python
import camtasia

proj = camtasia.load_project("path/to/project.cmproj")

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

## Context Manager (Auto-Save)

```python
with camtasia.use_project("path/to/project.cmproj") as proj:
    proj.timeline.markers.add("Chapter 2", camtasia.seconds_to_ticks(30.0))
```

## Creating a New Project

```python
camtasia.new_project("path/to/new.cmproj")
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

## Speed Changes

Speed is stored as a rational scalar (`Fraction`). A scalar of `1/2` means 2× playback speed.

```python
clip.set_speed(2.0)       # 2× speed — scalar becomes 1/2
clip.set_speed(0.5)       # half speed — scalar becomes 2/1
print(clip.scalar)        # Fraction(1, 2)
```

## Transitions

```python
from camtasia import seconds_to_ticks

track = list(proj.timeline.tracks)[0]
clips = list(track.clips)

track.transitions.add_fade_through_black(
    left_clip_id=clips[0].id,
    right_clip_id=clips[1].id,
    duration_ticks=seconds_to_ticks(0.5),
)
```

## Effects

```python
from camtasia.effects import RoundCorners, DropShadow, CursorPhysics

clip.effects.append(RoundCorners(radius=16.0).data)
clip.effects.append(DropShadow(offset=15.0, blur=25.0, opacity=0.2).data)
clip.effects.append(CursorPhysics(smoothing=0.8).data)
```

## Timing System

Camtasia uses an `editRate` of **705,600,000 ticks per second**.

```python
from camtasia.timing import EDIT_RATE, seconds_to_ticks, ticks_to_seconds, format_duration

seconds_to_ticks(2.5)            # 1_764_000_000
ticks_to_seconds(1_764_000_000)  # 2.5
format_duration(seconds_to_ticks(125.3))  # '2:05.29'
```
