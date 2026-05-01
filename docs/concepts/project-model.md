# The Project Model

A `Project` is the central object in pycamtasia. It represents a single Camtasia
video project and provides access to every part of the file: media assets, the
timeline, authoring metadata, and change history.

## What's inside a Project

```{mermaid}
graph TD
    P[Project] --> MB[MediaBin]
    P --> TL[Timeline]
    P --> AC[AuthoringClient]
    P --> CH[ChangeHistory]
    MB --> M1[Media asset]
    MB --> M2[Media asset]
    TL --> T1[Track]
    TL --> T2[Track]
    T1 --> C1[Clip]
    T1 --> C2[Clip]
    C1 --> E1[Effect]
    T1 --> TR[Transition]
    T1 --> MK[Marker]
```

| Component | Purpose |
|-----------|---------|
| **MediaBin** | Registry of all source files (images, audio, video, recordings) referenced by the project. Each entry has a unique integer ID used by clips. |
| **Timeline** | The editing timeline containing an ordered list of tracks. Each track holds clips, transitions, and markers. |
| **AuthoringClient** | Metadata about the Camtasia version that created the file (name, platform, version string). |
| **ChangeHistory** | Optional undo/redo stack storing JSON Patch diffs between project states. |

## The .cmproj bundle on disk

A Camtasia project is a **macOS bundle directory** with the `.cmproj` extension.
Inside it:

```
my_video.cmproj/           # directory, not a single file
├── project.tscproj        # JSON file — the entire project state
├── media/                  # imported media assets
│   ├── slide_01.png
│   ├── narration.m4a
│   └── ...
└── recordings/             # screen recordings (.trec files)
```

The `.tscproj` file is a single JSON document (UTF-8) containing all project
data: canvas dimensions, source bin entries, timeline tracks, clips, effects,
transitions, markers, and metadata. Media files live alongside it in the bundle
directory.

## Loading, creating, and using projects

pycamtasia provides three entry points:

### `load_project` — open an existing project

```python
from camtasia import load_project

project = load_project("my_video.cmproj")
print(project.title)
print(len(list(project.timeline.tracks)))
```

Returns a `Project` instance. Changes are held in memory until you call
`project.save()`.

### `new_project` — create from template

```python
from camtasia import new_project

new_project("fresh.cmproj")  # copies bundled template to disk
project = load_project("fresh.cmproj")
```

Creates a new, empty `.cmproj` bundle from the built-in template. You then
load it to start editing.

### `use_project` — context manager with auto-save

```python
from camtasia import use_project

with use_project("my_video.cmproj") as proj:
    proj.title = "Updated Title"
    # ... make changes ...
# project.save() is called automatically on normal exit
```

`use_project` loads the project, yields it, and saves on normal exit. If an
exception occurs, changes are discarded. Pass `save_on_exit=False` to disable
auto-save.

## Save semantics

`project.save()` writes the current in-memory state back to the `.tscproj`
file. Key details:

- **JSON formatting** matches Camtasia's `NSJSONSerialization` style (space
  before colon) to avoid parser issues with `.trec` screen recordings.
- **Validation** runs automatically before save — errors are emitted as
  warnings but do not block the write.
- **Atomic**: the entire JSON is written in one operation.
- **No auto-save**: changes are only persisted when you explicitly call
  `save()` or use the `use_project` context manager.

All classes (`Timeline`, `Track`, `BaseClip`, `Effect`, etc.) are thin wrappers
over the same in-memory dict tree. Mutations go directly to `_data` — there is
no separate model/serialization step.

## See also

- {doc}`/concepts/camtasia-file-format` — the `.tscproj` JSON structure
- {doc}`/concepts/undo-and-history` — tracking and reverting changes
- {doc}`/concepts/the-two-api-layers` — L1 dict access vs L2 typed API
- {doc}`/api/project` — full API reference
- {doc}`/guides/getting-started` — tutorial walkthrough
