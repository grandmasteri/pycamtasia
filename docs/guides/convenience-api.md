# High-Level Convenience API

pycamtasia has two layers of API:

- **L1 (low-level)** — thin wrappers around the raw Camtasia JSON. You access `clip._data`, set properties directly, and manage dict structures yourself. Full control, but verbose.
- **L2 (convenience)** — methods that handle the boilerplate for common operations. They accept seconds instead of ticks, construct the correct JSON schemas internally, and return `self` for chaining.

**Use L2** when you're doing standard things: fading clips, adding effects, building slide sequences. **Drop to L1** when you need fine-grained control over a field that L2 doesn't expose.

## Clip animations

Fade and opacity methods live on `BaseClip` — they work on any clip type.

```python
clip.fade_in(0.5)           # 0.5s opacity fade in
clip.fade_out(1.0)          # 1.0s fade out at end
clip.fade(0.5, 1.0)         # both at once
clip.set_opacity(0.8)       # static opacity
clip.clear_animations()     # remove all visual animations
```

All time parameters are in seconds. The methods convert to ticks internally and build the correct `animationTracks.visual` keyframe entries.

## Adding effects

Effect methods construct the full JSON effect dict and append it to the clip's `effects` array.

```python
clip.add_drop_shadow(offset=10, blur=20, opacity=0.3)
clip.add_glow(radius=35, intensity=0.5)
clip.add_round_corners(radius=12)
clip.add_glow_timed(start_seconds=2.0, duration_seconds=5.0)
```

All parameters have sensible defaults — call `clip.add_drop_shadow()` with no arguments for a standard shadow.

To remove effects:

```python
clip.remove_effects('DropShadow')  # remove by name
clip.remove_effects()              # remove all
```

## Image positioning

Transform methods are available on visual clips (`IMFile`, `ScreenVMFile`).

```python
clip.move_to(100, -50)      # translate x, y
clip.scale_to(1.5)          # uniform scale
clip.crop(left=0.1, right=0.1)  # crop edges (fractions 0.0–1.0)
```

## Building tracks

`Track` provides typed, seconds-based methods for adding clips — no need to know `_type` strings or tick math.

```python
track = timeline.get_or_create_track('Slides')
img = track.add_image(source_id=6, start_seconds=0, duration_seconds=20)
track.add_callout('Title Text', start_seconds=0, duration_seconds=5)
```

For slide-deck workflows, `add_image_sequence` places images back-to-back with optional transitions:

```python
clips = track.add_image_sequence(
    [6, 7, 8],
    start_seconds=0,
    duration_per_image_seconds=15,
    transition_seconds=0.5,
)
```

Use `track.end_time_seconds()` to find where the last clip ends — handy for appending.

## Project-level

```python
media = project.import_media(Path('diagram.png'))
project.add_gradient_background(
    duration_seconds=120,
    color0=(0.16, 0.16, 0.16, 1),
    color1=(0, 0, 0, 1),
)
print(f'Duration: {project.total_duration_seconds():.1f}s')
```

`find_media_by_name` and `find_media_by_suffix` search the source bin:

```python
narration = project.find_media_by_name('narration')
pngs = project.find_media_by_suffix('.png')
```

## Method chaining

Clip mutation methods return `self`, so you can chain them:

```python
track.add_image(src, 0, 20).fade_in(0.5).add_drop_shadow().move_to(0, -100)
```

## Dropping to L1

L2 doesn't cover your use case? Access the raw data directly:

```python
clip._data['parameters']['customField'] = {
    'type': 'double',
    'defaultValue': 42.0,
}
```

Every L2 object wraps a dict — `_data` is always available for escape-hatch access.

## Full example

```python
from pathlib import Path
from camtasia import use_project

with use_project("my_video.cmproj") as proj:
    # Import media
    slides = [proj.import_media(Path(f"slide_{i}.png")) for i in range(5)]
    audio = proj.import_media(Path("narration.m4a"))

    # Background
    proj.add_gradient_background(duration_seconds=120.0)

    # Slides with transitions
    track = proj.timeline.get_or_create_track("Slides")
    clips = track.add_image_sequence(
        source_ids=[s.id for s in slides],
        start_seconds=0.0,
        duration_per_image_seconds=20.0,
        transition_seconds=0.5,
    )

    # Style all slides
    clips[0].fade_in(0.5)
    clips[-1].fade_out(0.5)
    for clip in clips:
        clip.add_drop_shadow(offset=10, blur=20, opacity=0.3)
        clip.add_round_corners(radius=12)

    # Audio
    audio_track = proj.timeline.get_or_create_track("Audio")
    audio_track.add_audio(audio.id, start_seconds=0.0, duration_seconds=120.0)

    # Title
    title_track = proj.timeline.get_or_create_track("Titles")
    title = title_track.add_callout(
        "My Presentation", start_seconds=0.0, duration_seconds=5.0,
        font_name="Helvetica Neue", font_weight="Bold", font_size=128.0,
    )
    title.fade(0.5, 0.5)

    print(f"Total duration: {proj.total_duration_seconds():.1f}s")
```
