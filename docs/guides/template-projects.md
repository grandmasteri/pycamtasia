# Template-Based Project Creation

You want to create new Camtasia projects that follow the same structure as an existing one — same tracks, project settings, and canvas dimensions — but with different media. This guide shows how to use `clone_project_structure()` and `replace_media_source()`.

## Cloning a project structure

`clone_project_structure()` deep-copies a project and strips out all media-specific content:

```python
import json
from camtasia.operations import clone_project_structure

with open('template.tscproj') as f:
    template = json.load(f)

new_project = clone_project_structure(template)

with open('new_project.tscproj', 'w') as f:
    json.dump(new_project, f, indent=2)
```

### What gets preserved

- Project settings (canvas size, frame rate, edit rate)
- Track structure (number of tracks, track names, track order)
- Project metadata

### What gets cleared

- Source bin (emptied — no media references)
- All clips on all tracks
- All transitions
- Timeline markers

The result is a clean skeleton you can populate with new media.

## Replacing media sources

If you want to keep the clip structure but swap out the underlying media, use `replace_media_source()`. This walks all clips — including nested clips inside `StitchedMedia` and `Group` containers — and replaces `src` references:

```python
from camtasia.operations import replace_media_source

# After adding new media to the sourceBin with id=100,
# replace all clips that referenced old source id=3
count = replace_media_source(new_project, old_source_id=3, new_source_id=100)
print(f"Replaced {count} media references")
```

This is useful when you have a project with the right clip layout and timing, but need to point it at different recordings.

## Typical workflow

1. Set up a "golden" project in Camtasia with your preferred track layout, effects, and settings
2. Save it as your template `.tscproj`
3. For each new video:

```python
import json
from camtasia.operations import clone_project_structure, replace_media_source

with open('template.tscproj') as f:
    template = json.load(f)

project = clone_project_structure(template)

# Add new media to the source bin
project['sourceBin'].append({
    'id': 1,
    'src': 'new_recording.mp4',
    'rect': [0, 0, 1920, 1080],
    'lastMod': '20260409T143000',
})

# Now add clips to tracks referencing src=1, or use replace_media_source
# if you started from a non-empty clone

with open('episode_42.tscproj', 'w') as f:
    json.dump(project, f, indent=2)
```
