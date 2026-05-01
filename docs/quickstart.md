# Quick Start

## Install

```bash
pip install pycamtasia
```

## Load a Project

```python
import camtasia

proj = camtasia.load_project("path/to/project.cmproj")
```

## Inspect Tracks, Clips, and Media

Iterate the timeline to see what's in the project.

```python
for track in proj.timeline.tracks:
    print(f"Track {track.index}: {track.name} ({len(track)} clips)")
    for clip in track.clips:
        print(f"  {clip.clip_type}: {clip.start_seconds:.1f}–{clip.end_seconds:.1f}s")

for media in proj.media_bin:
    print(f"  {media.id}: {media.source}")
```

## Add a Clip with an Effect

Import media, place it on a track, then add a drop shadow.

```python
media = proj.import_media("assets/intro.png")
track = proj.timeline.get_or_create_track("Slides")
clip = track.add_image(media.id, start_seconds=0, duration_seconds=5.0)

clip.add_drop_shadow(offset=5, blur=10, opacity=0.5)
clip.add_round_corners(radius=12.0)
```

## Add a Transition

Transitions go between two adjacent clips on the same track.

```python
clips = list(track.clips)
track.transitions.add_dissolve(clips[0], clips[1], duration_seconds=0.5)
```

## Undo a Change

Wrap edits in `track_changes` to make them undoable.

```python
with proj.track_changes("add shadow"):
    clip.add_drop_shadow()

proj.undo()   # reverts "add shadow"
proj.redo()   # re-applies it
```

## Save

```python
proj.save()
```

Or auto-save with a context manager:

```python
with camtasia.use_project("path/to/project.cmproj") as proj:
    proj.timeline.get_or_create_track("Audio")
```

## Export

Export markers as SRT subtitles, the timeline as EDL or CSV, or everything at once.

```python
from camtasia.export import export_markers_as_srt, export_edl, export_csv

export_markers_as_srt(proj, "markers.srt")
export_edl(proj, "timeline.edl", title="My Project")
export_csv(proj, "timeline.csv")

# Or export all formats in one call:
proj.export_all("output/")
```

## Next Steps

- [Getting Started Tutorial](guides/getting-started.md) — build a complete project from scratch
- [Undo & Redo](guides/undo-redo.md) — change history and persistence
- [The Two API Layers](concepts/the-two-api-layers.md) — L1/L2 architecture and when to use each
