# Getting Started with pycamtasia

A hands-on tutorial for reading, editing, and building Camtasia project timelines with Python.

## 1. Installation

```bash
git clone https://github.com/grandmasteri/pycamtasia.git
cd pycamtasia
pip install -e .
```

ffprobe is required for media import (duration/dimension detection):

```bash
brew install ffmpeg          # macOS
sudo apt install ffmpeg      # Ubuntu/Debian
```

## 2. Loading a Project

```python
import camtasia

# Open an existing project
proj = camtasia.load_project("path/to/project.cmproj")

# Or use a context manager that auto-saves on exit
with camtasia.use_project("path/to/project.cmproj") as proj:
    # ... make changes ...
    pass  # saved automatically

# Create a brand-new empty project
camtasia.new_project("path/to/new.cmproj")
```

## 3. Inspecting the Timeline

### Tracks and clips

```python
for track in proj.timeline.tracks:
    print(f"Track {track.index} '{track.name}': {len(track)} clips")
    for clip in track.clips:
        print(f"  {clip.clip_type}: {clip.start_seconds:.2f}s – "
              f"{clip.start_seconds + clip.duration_seconds:.2f}s")
```

### Type-checking clips

```python
from camtasia import AMFile, VMFile, IMFile

for track in proj.timeline.tracks:
    for clip in track.clips:
        if isinstance(clip, VMFile):
            print(f"Video: {clip.duration_seconds:.1f}s, speed={clip.scalar}")
        elif isinstance(clip, AMFile):
            print(f"Audio: source_id={clip.source_id}")
        elif isinstance(clip, IMFile):
            print(f"Image: {clip.duration_seconds:.1f}s")
```

### Media bin

```python
for media in proj.media_bin:
    print(f"ID={media.id}  {media.source}  ({media.duration_seconds:.1f}s)")
```

### Quick summary

```python
print(proj.summary())
# Project: project.cmproj
# Canvas: 1920x1080
# Duration: 42.5s
# Tracks: 3
# ...
```

## 4. Adding Clips

All `add_*` methods accept seconds — tick conversion is handled internally.

### Import media first

```python
media = proj.import_media("assets/narration.wav")
print(f"Imported: id={media.id}")
```

### Audio

```python
track = proj.timeline.get_or_create_track("Narration")
clip = track.add_audio(media.id, start_seconds=0, duration_seconds=30.0)
```

### Image

```python
img = proj.import_media("assets/slide.png")
track = proj.timeline.get_or_create_track("Slides")
clip = track.add_image(img.id, start_seconds=0, duration_seconds=5.0)
```

### Video

```python
vid = proj.import_media("assets/demo.mp4")
track = proj.timeline.get_or_create_track("Video")
clip = track.add_video(vid.id, start_seconds=0, duration_seconds=15.0)
```

## 5. Adding Effects

Effects are added directly on clip objects. Each method returns the effect (or `self` for chaining).

### Drop shadow

```python
clip.add_drop_shadow(offset=5, blur=10, opacity=0.5)
```

### Rounded corners

```python
clip.add_round_corners(radius=16.0)
```

### Color adjustment

```python
clip.add_color_adjustment(brightness=0.1, contrast=0.2, saturation=1.2)
```

### Combining effects

```python
clip.add_drop_shadow(offset=8, blur=15, opacity=0.3)
clip.add_round_corners(radius=12.0)
clip.add_color_adjustment(saturation=1.4)
```

## 6. Adding Transitions

Transitions live on each track and reference the clips on either side.

### Fade through black

```python
from camtasia import seconds_to_ticks

track = proj.timeline.get_or_create_track("Slides")
clips = list(track.clips)

track.transitions.add_fade_through_black(
    left_clip_id=clips[0].id,
    right_clip_id=clips[1].id,
    duration_ticks=seconds_to_ticks(0.5),
)
```

### Other transition types

```python
# Dissolve
track.transitions.add_dissolve(clips[0], clips[1], duration_seconds=0.5)

# Fade to white
track.transitions.add_fade_to_white(clips[0], clips[1], duration_seconds=0.5)

# Slide (left, right, up, down)
track.transitions.add_slide(clips[0], clips[1], duration_seconds=0.5, direction="left")

# Wipe (left, right, up, down)
track.transitions.add_wipe(clips[0], clips[1], duration_seconds=0.5, direction="right")
```

### Iterating and removing

```python
for t in track.transitions:
    print(f"{t.name}: {t.duration_seconds:.2f}s")

track.transitions.remove(0)  # remove by index
```

## 7. Adding Title Cards (Lower Third)

The `add_lower_third` method creates a styled title/subtitle overlay from a built-in template.

```python
track = proj.timeline.get_or_create_track("Titles")
group = track.add_lower_third(
    "Speaker Name",
    "Job Title — Company",
    start_seconds=2.0,
    duration_seconds=5.0,
)
```

### Customizing appearance

```python
group = track.add_lower_third(
    "Speaker Name",
    "Job Title — Company",
    start_seconds=2.0,
    duration_seconds=5.0,
    title_color=(255, 255, 255, 255),       # RGBA 0-255
    accent_color=(0.2, 0.6, 1.0),           # RGB 0.0-1.0
    font_weight=700,
    scale=1.2,
)
```

### Simple text callout

For a plain text overlay without the lower-third template:

```python
callout = track.add_callout(
    "Chapter 1: Introduction",
    start_seconds=0,
    duration_seconds=3.0,
    font_size=48.0,
)
```

## 8. Saving the Project

```python
proj.save()
```

Or use the context manager for auto-save:

```python
with camtasia.use_project("path/to/project.cmproj") as proj:
    track = proj.timeline.get_or_create_track("Audio")
    media = proj.import_media("narration.wav")
    track.add_audio(media.id, start_seconds=0, duration_seconds=30.0)
# saved automatically on exit
```

## 9. Validating the Output

### Validation

`validate()` checks for common issues — missing source files, orphaned media, zero-range audio, duplicate clip IDs.

```python
issues = proj.validate()
for issue in issues:
    print(f"[{issue.level}] {issue.message}")

if not issues:
    print("Project is clean!")
```

### Statistics

```python
stats = proj.statistics()
print(f"Tracks: {stats['total_tracks']}")
print(f"Clips: {stats['total_clips']}")
print(f"Duration: {stats['duration_seconds']:.1f}s")
print(f"Clips by type: {stats['clips_by_type']}")
```

## 10. Using the TimelineBuilder

`TimelineBuilder` provides a cursor-based API for sequential assembly. The cursor advances automatically after audio clips.

```python
from camtasia.builders import TimelineBuilder

proj = camtasia.load_project("path/to/project.cmproj")
builder = TimelineBuilder(proj)

# Add audio clips sequentially — cursor advances automatically
clip1 = builder.add_audio("assets/intro.wav", track_name="Narration")
builder.add_pause(1.0)  # 1-second gap
clip2 = builder.add_audio("assets/main.wav", track_name="Narration")

# Add visuals at specific positions — cursor does NOT advance
builder.seek(0)
builder.add_image("assets/title-card.png", track_name="Slides", duration=5.0)

# Add a title overlay
builder.add_title("My Presentation", track_name="Titles", duration=5.0)

# Check cursor position
print(f"Timeline ends at {builder.cursor:.1f}s")

proj.save()
```

### Builder methods

| Method | Advances cursor? | Description |
|--------|:-:|---|
| `add_audio(path)` | ✓ | Import and place audio at cursor |
| `add_pause(seconds)` | ✓ | Gap without a clip |
| `add_image(path)` | ✗ | Visual overlay at cursor |
| `add_title(text)` | ✗ | Text callout at cursor |
| `seek(seconds)` | — | Jump to absolute position |
| `advance(seconds)` | ✓ | Move cursor forward |

## Next Steps

- [Convenience API](convenience-api.md) — L2 methods for animations, audio, and batch operations
- [Speed Changes](speed-change.md) — rational-precision speed control
- [Audio-Video Sync](audio-video-sync.md) — marker-to-transcript alignment
- [Template Projects](template-projects.md) — cloning and media replacement
- [Full API Reference](https://grandmasteri.github.io/pycamtasia/)
