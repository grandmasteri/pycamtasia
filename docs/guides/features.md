## Feature tour

This page tours the main feature areas of pycamtasia. For a concise reference,
see the [quickstart](../quickstart.md) and the [cookbook](cookbook.md).

---

### Cursor & click effects

33 new effect classes for cursor visualization, touch gestures, and screen
recording enhancements.

```python
from camtasia import Project
from camtasia.effects.cursor import CursorPathCreator
from camtasia.effects.visual import GestureTap, Hotspot, ZoomNPan

proj = Project.load("demo.cmproj")
clip = proj.timeline.tracks[0].clips[0]

# Add a cursor path creator effect
clip.add_cursor_path_creator()

# Replace the cursor in a screen recording
from camtasia.timeline.clips.screen_recording import ScreenIMFile
# screen_clip.replace_cursor("custom_cursor.png")
```

---

### Visual effects

New visual effects including background removal, device frames, and freeze
regions.

```python
clip.add_background_removal()
clip.fit_to_canvas(mode="cover")
```

---

### Audio effects

`AudioVisualizer` and `Equalizer` effects, plus `mix_to_mono()` on audio clips.

```python
from camtasia.effects.audio_visualizer import AudioVisualizer

audio_clip = proj.timeline.tracks[1].clips[0]
audio_clip.add_audio_visualizer()
audio_clip.mix_to_mono = True
```

---

### Audiate & transcript editing

Word-level transcript editing, `active_word_at()` lookup, and Audiate
translate/TTS stubs.

```python
from camtasia.audiate import AudiateProject

audiate = AudiateProject("recording.audiate")
transcript = audiate.transcript
for word in transcript.words:
    print(f"{word.text} @ {word.start:.2f}s")
```

---

### Dynamic captions

`DynamicCaptionStyle` presets with save/load/list support, plus caption
anchoring and accessibility validation.

```python
from camtasia.timeline.captions import (
    DynamicCaptionStyle,
    apply_dynamic_style,
    save_dynamic_caption_preset,
    list_dynamic_caption_presets,
)
from camtasia.validation import validate_caption_accessibility

style = DynamicCaptionStyle(
    name="my_style",
    font_name="Montserrat",
    font_size=48,
    highlight_color=(255, 255, 0, 255),
)
save_dynamic_caption_preset(style)
print(list_dynamic_caption_presets())
```

---

### Library module

New `Library` class with asset management and `.libzip` import/export.

```python
from camtasia.library import Library
from camtasia.library.libzip import import_libzip, export_libzip
from pathlib import Path

lib = Library("my_library")
lib.add_asset(clip._data, name="intro_clip")
for asset in lib.assets:
    print(asset.name)

# Export/import library archives
export_libzip(lib, Path("my_library.libzip"))
```

---

### Canvas presets & safe zones

Vertical canvas presets for social media, plus platform-specific safe zones.

```python
from camtasia.canvas_presets import VerticalPreset, get_safe_zone

# Set canvas to 9:16 for Instagram Reels
w, h = VerticalPreset.NINE_BY_SIXTEEN_FHD.value
proj.width = w
proj.height = h

# Check safe zone for TikTok
zone = get_safe_zone("tiktok")
print(f"Top inset: {zone.top}px, Bottom inset: {zone.bottom}px")
```

---

### Templates

Save, install, and create projects from templates with placeholder replacement.

```python
from camtasia.operations.template import (
    save_as_template,
    install_camtemplate,
    new_project_from_template,
    list_installed_templates,
)

# Save current project as a reusable template
save_as_template(proj, "my_template", "templates/my_template.camtemplate")

# Create a new project from an installed template
new_proj = new_project_from_template("my_template", "output/new_project.cmproj")
print(list_installed_templates())
```

---

### Exports

New export formats: `.campackage`, table of contents, YouTube chapters, and
SRT/VTT caption import.

```python
from camtasia.export.toc import export_toc
from camtasia.export.chapters import export_chapters
from camtasia.export.campackage import export_campackage
from camtasia.export.captions import import_captions_srt
from pathlib import Path

export_toc(proj, Path("output/toc.xml"), format="xml")
export_chapters(proj, Path("output/chapters.vtt"), format="webvtt")

entries = import_captions_srt(Path("subtitles.srt"))
```

---

### Annotations

Sketch-motion callouts, new shapes (line, ellipse, triangle), and annotation
favorites.

```python
from camtasia.annotations.callouts import (
    sketch_motion_callout,
    save_as_favorite,
    load_favorite,
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

---

### General API improvements

#### Project introspection

```python
# Human-readable summary
print(proj.summary())

# Detailed statistics dict
stats = proj.statistics()
print(f"Tracks: {stats['track_count']}, Clips: {stats['clip_count']}")

# Markdown report
report = proj.to_markdown_report()

# Export full report to file
proj.export_project_report("project-report.md")
```

#### Audio utilities

```python
# Normalize audio levels across the project
proj.normalize_audio(target_gain=1.0)

# Mute a clip
clip.mute()

# Solo a track (mutes all other tracks)
track = proj.timeline.tracks[0]
track.solo = True

# Convert audio to WAV (staticmethod on Project)
wav_path = Project.convert_audio_to_wav("narration.m4a", "narration.wav")
```

#### Validation

```python
from camtasia.validation import validate_all

# Validate via Project method
issues = proj.validate()
for issue in issues:
    print(f"[{issue.level}] {issue.message}")

# Or use the standalone function on raw project data
issues = validate_all(proj.to_dict())
```

#### Groups

```python
# Group clips on a single track
group = track.group_clips([clip_a.id, clip_b.id])

# Ungroup
clips = track.ungroup_clip(group.id)

# Iterate internal tracks and clips
for gt in group.tracks:
    for c in gt.clips:
        print(f"  {c.clip_type}: {c.start_seconds:.1f}s")

# Merge adjacent clips
merged = track.merge_adjacent_clips(clip_a.id, clip_b.id)
```

#### Track features

```python
# Magnetic tracks auto-pack clips
track.magnetic = True

# Selection, cut, copy
track.set_selection(0.0, 5.0)
cut_data = track.cut_selection()

# Ripple replace media
track.ripple_replace_media(clip.id, new_media_dict)
```

#### SmartFocus & animation

```python
from camtasia.timeline.clips.base import Animation

# Structured keyframe animation
anim = Animation(
    start_seconds=0.0,
    end_seconds=1.0,
    position=(100, 50),
    opacity=0.5,
    easing="eioe",
)
```

