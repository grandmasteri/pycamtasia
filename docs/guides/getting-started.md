# Getting Started with pycamtasia

Build a complete Camtasia project from scratch using Python.

## Prerequisites

```bash
pip install pycamtasia
brew install ffmpeg    # ffprobe needed for media import (macOS)
```

## 1. Create a New Project

```python
import camtasia

proj = camtasia.new_project("my-video.cmproj")
```

## 2. Import Media

Add files to the media bin. `import_media` auto-detects duration via ffprobe.

```python
narration = proj.import_media("assets/narration.wav")
slides = proj.import_media("assets/slide-01.png")
demo = proj.import_media("assets/demo.mp4")

for media in proj.media_bin:
    print(f"  {media.id}: {media.source}")
```

## 3. Build a Timeline with Clips

Tracks are created on demand. All `add_*` methods accept seconds.

```python
audio_track = proj.timeline.get_or_create_track("Narration")
audio_clip = audio_track.add_audio(narration.id, start_seconds=0, duration_seconds=30.0)

slide_track = proj.timeline.get_or_create_track("Slides")
slide1 = slide_track.add_image(slides.id, start_seconds=0, duration_seconds=10.0)
slide2 = slide_track.add_image(slides.id, start_seconds=10, duration_seconds=10.0)

video_track = proj.timeline.get_or_create_track("Demo")
video_clip = video_track.add_video(demo.id, start_seconds=0, duration_seconds=15.0)
```

Inspect what you've built:

```python
for track in proj.timeline.tracks:
    print(f"Track '{track.name}': {len(track)} clips")
    for clip in track.clips:
        print(f"  {clip.clip_type}: {clip.start_seconds:.1f}–{clip.end_seconds:.1f}s")
```

## 4. Apply Effects and Transitions

### Effects

```python
slide1.add_drop_shadow(offset=5, blur=10, opacity=0.5)
slide1.add_round_corners(radius=12.0)
video_clip.add_color_adjustment(brightness=0.1, contrast=0.2, saturation=1.2)
```

### Transitions

Transitions connect two adjacent clips on the same track.

```python
slide_track.transitions.add_dissolve(slide1, slide2, duration_seconds=0.5)
```

Other types — all accept `(left_clip, right_clip, duration_seconds)`:

```python
slide_track.transitions.add_fade_to_white(slide1, slide2, duration_seconds=0.5)
slide_track.transitions.add_slide(slide1, slide2, duration_seconds=0.5, direction="left")
slide_track.transitions.add_wipe(slide1, slide2, duration_seconds=0.5, direction="right")
```

## 5. Use the TimelineBuilder

Cursor-based API for sequential assembly. The cursor advances after audio
clips but not after images or titles.

```python
from camtasia.builders import TimelineBuilder

proj = camtasia.new_project("builder-demo.cmproj")
builder = TimelineBuilder(proj)

clip1 = builder.add_audio("assets/intro.wav", track_name="Narration")
builder.add_pause(1.0)
clip2 = builder.add_audio("assets/main.wav", track_name="Narration")

builder.seek(0)
builder.add_image("assets/title-card.png", track_name="Slides", duration=5.0)
builder.add_title("My Presentation", track_name="Titles", duration=5.0)

print(f"Timeline ends at {builder.cursor:.1f}s")
```

| Method | Advances cursor? | Description |
|--------|:-:|---|
| `add_audio(path)` | ✓ | Import and place audio at cursor |
| `add_pause(seconds)` | ✓ | Gap without a clip |
| `add_image(path)` | ✗ | Visual overlay at cursor |
| `add_title(text)` | ✗ | Text callout at cursor |
| `seek(seconds)` | — | Jump to absolute position |
| `advance(seconds)` | ✓ | Move cursor forward |

## 6. Validate and Save

### Validate

`validate()` checks for missing sources, orphaned media, and duplicate clip IDs.

```python
issues = proj.validate()
for issue in issues:
    print(f"[{issue.level}] {issue.message}")
```

### Save

```python
proj.save()

# Or auto-save with a context manager:
with camtasia.use_project("my-video.cmproj") as proj:
    proj.timeline.get_or_create_track("Audio")
```

### Export

```python
from camtasia.export import export_markers_as_srt, export_edl, export_csv

export_markers_as_srt(proj, "output/markers.srt")
export_edl(proj, "output/timeline.edl", title="My Video")
export_csv(proj, "output/timeline.csv")

# Or export everything at once:
proj.export_all("output/")
```

## Next Steps

- [Quick Start](../quickstart.md) — cheat-sheet reference
- [Undo & Redo](undo-redo.md) — change history with JSON Patch diffs
- [The Two API Layers](../concepts/the-two-api-layers.md) — L1/L2 architecture and when to use each
- [Speed Changes](speed-change.md) — rational-precision speed control
- [Template Projects](template-projects.md) — cloning and media replacement
