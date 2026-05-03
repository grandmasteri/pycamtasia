# Cookbook

Short, runnable recipes for common pycamtasia tasks.

## Create a project from scratch

```python
from camtasia import new_project, load_project

new_project("my-video.cmproj")
proj = load_project("my-video.cmproj")
proj.title = "My Video"
print(proj)  # My Video (0:00, 0 tracks, 0 clips)
proj.save()
```

## Add a voiceover track

```python
from camtasia import load_project

proj = load_project("my-video.cmproj")
audio = proj.import_media("narration.wav")
track = proj.timeline.get_or_create_track("Voiceover")
clip = track.add_audio(audio.id, start_seconds=0, duration_seconds=30.0)
proj.save()
```

## Add slide images as a sequence

```python
from camtasia import load_project

proj = load_project("my-video.cmproj")
ids = [proj.import_media(f"slide_{i}.png").id for i in range(1, 4)]
track = proj.timeline.get_or_create_track("Slides")
track.add_image_sequence(
    ids, start_seconds=0, duration_per_image_seconds=5.0,
    transition_seconds=0.5, transition_name="FadeThroughBlack",
)
proj.save()
```

## Insert a transition between clips

```python
from camtasia import load_project

proj = load_project("my-video.cmproj")
track = proj.timeline.tracks[0]
clip_a, clip_b = track.clips[0], track.clips[1]
track.add_transition("FadeThroughBlack", clip_a, clip_b, duration_seconds=0.5)
proj.save()
```

## Apply a drop shadow to a clip

```python
from camtasia import load_project

proj = load_project("my-video.cmproj")
clip = proj.timeline.tracks[0].clips[0]
clip.add_drop_shadow(offset=5, blur=10, opacity=0.5)
proj.save()
```

## Change clip playback speed

```python
from camtasia import load_project

proj = load_project("my-video.cmproj")
clip = proj.timeline.tracks[0].clips[0]
clip.set_speed(2.0)   # 2× playback
print(clip.duration_seconds)
proj.save()
```

## Add closed captions from an SRT file

```python
from camtasia import load_project
from camtasia.export import import_captions_srt

proj = load_project("my-video.cmproj")
entries = import_captions_srt("subtitles.srt")
proj.add_subtitle_track(
    [(e.start_seconds, e.duration_seconds, e.text) for e in entries],
    track_name="Subtitles",
)
proj.save()
```

## Export a project report (markdown/JSON)

```python
from camtasia import load_project
from camtasia.export import export_project_report

proj = load_project("my-video.cmproj")
export_project_report(proj, "report.md", format="markdown")
export_project_report(proj, "report.json", format="json")
```

## Create a vertical (9:16) video canvas

```python
from camtasia import new_project
from camtasia.canvas_presets import VerticalPreset

preset = VerticalPreset.NINE_BY_SIXTEEN_FHD
proj = new_project("vertical.cmproj", title="Reel")
proj.set_canvas_size(*preset.value)  # 1080×1920
proj.save()
```

## Save a project as a template

```python
from camtasia import Project

# Copy an existing project as a starting point
proj = Project.from_template("golden.cmproj", "episode_42.cmproj")
proj.title = "Episode 42"
proj.save()
```

## Apply a theme to annotations

```python
from camtasia import load_project, Theme, apply_theme

theme = Theme(
    name="Brand",
    accent_1=(0.2, 0.6, 1.0, 1.0),
    accent_2=(1.0, 0.4, 0.1, 1.0),
    font_1="Montserrat",
)
proj = load_project("my-video.cmproj")
count = apply_theme(proj, theme)
print(f"Applied {count} theme mutations")
proj.save()
```

## Remove unused media from the bin

```python
from camtasia import load_project
from camtasia.operations.cleanup import remove_orphaned_media

proj = load_project("my-video.cmproj")
removed = remove_orphaned_media(proj)
print(f"Removed {len(removed)} orphaned media entries: {removed}")
proj.save()
```

## Batch-fade all clips on a track

```python
from camtasia import load_project
from camtasia.operations.batch import fade_all

proj = load_project("my-video.cmproj")
track = proj.timeline.tracks[0]
count = fade_all(track.clips, fade_in=0.3, fade_out=0.3)
print(f"Faded {count} clips")
proj.save()
```

## Use undo/redo

```python
from camtasia import load_project

proj = load_project("my-video.cmproj")
with proj.track_changes("add shadow"):
    proj.timeline.tracks[0].clips[0].add_drop_shadow()

proj.undo()   # reverts "add shadow"
proj.redo()   # re-applies it
print(proj.history.descriptions)
```

## Validate a project before saving

```python
from camtasia import load_project

proj = load_project("my-video.cmproj")
issues = proj.validate()
for issue in issues:
    print(f"[{issue.level}] {issue.message}")
if not issues:
    proj.save()
```

## Add an audio visualizer effect

```python
from camtasia import load_project

proj = load_project("my-video.cmproj")
audio_clip = proj.timeline.tracks[1].clips[0]
audio_clip.add_audio_visualizer()
audio_clip.mix_to_mono = True
proj.save()
```

## Iterate Audiate transcript words

```python
from camtasia.audiate import AudiateProject

audiate = AudiateProject("recording.audiate")
for word in audiate.transcript.words:
    print(f"{word.text} @ {word.start:.2f}s")
```

## Save and list dynamic caption presets

```python
from camtasia.timeline.captions import (
    DynamicCaptionStyle,
    save_dynamic_caption_preset,
    list_dynamic_caption_presets,
)

style = DynamicCaptionStyle(
    name="my_style",
    font_name="Montserrat",
    font_size=48,
    highlight_color=(255, 255, 0, 255),
)
save_dynamic_caption_preset(style)
print(list_dynamic_caption_presets())
```

## Create a sketch-motion callout and save as favorite

```python
from camtasia.annotations.callouts import (
    sketch_motion_callout,
    save_as_favorite,
    list_favorites,
)

callout = sketch_motion_callout(
    shape="circle",
    color=(1, 0, 0, 1),
    stroke_width=4.0,
    draw_time_seconds=1.0,
)
save_as_favorite(callout, "red_circle")
print(list_favorites())
```

## Export a library archive

```python
from camtasia.library import Library
from camtasia.library.libzip import export_libzip
from pathlib import Path

lib = Library("my_library")
lib.add_asset(clip._data, name="intro_clip")
export_libzip(lib, Path("my_library.libzip"))
```