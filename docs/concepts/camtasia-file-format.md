# Camtasia File Format

This page provides a brief overview of the `.tscproj` JSON structure. For the
complete field-by-field reference, see the
{doc}`/camtasia-format-reference`.

## The .cmproj bundle

A Camtasia project on disk is a **directory** with the `.cmproj` extension (a
macOS bundle). Inside it:

```
my_video.cmproj/
├── project.tscproj     # the JSON project file
├── media/              # imported media assets
└── recordings/         # screen recordings (.trec files)
```

The `.tscproj` file is a single UTF-8 JSON document containing the entire
project state.

## Top-level JSON structure

```json
{
  "title": "",
  "version": "10.0",
  "editRate": 705600000,
  "width": 1920.0,
  "height": 1080.0,
  "authoringClientName": { ... },
  "sourceBin": [ ... ],
  "timeline": { ... },
  "metadata": { ... }
}
```

### Key sections

**`authoringClientName`** — identifies the Camtasia version that created the
file:

```json
{
  "name": "Camtasia",
  "platform": "Mac",
  "version": "2024.1.0"
}
```

**`sourceBin`** — array of all media assets referenced by the project. Each
entry has a unique integer `id`, a file `src` path, and metadata like
dimensions and duration:

```json
[
  {"id": 1, "src": "media/slide_01.png", "rect": [0, 0, 1920, 1080], ...},
  {"id": 2, "src": "media/narration.m4a", "duration": 42336000000, ...}
]
```

**`timeline`** — the editing timeline. Contains a `sceneTrack` with one scene,
which holds the `tracks` array. Each track contains `medias` (clips),
`transitions`, and other track-level data:

```json
{
  "sceneTrack": {
    "scenes": [{
      "csml": {
        "tracks": [
          {
            "trackIndex": 0,
            "medias": [ ... ],
            "transitions": [ ... ]
          }
        ]
      }
    }]
  },
  "trackAttributes": [ ... ]
}
```

**`metadata`** — arbitrary key-value pairs for project settings (autosave
path, canvas zoom level, UI preferences, etc.).

## Time values

All time values are integers in **edit-rate ticks** where
`editRate = 705,600,000` ticks per second. See {doc}`/concepts/timing` for
details on the timing system.

## Clip structure

Each clip in a track's `medias` array has at minimum:

```json
{
  "_type": "IMFile",
  "id": 42,
  "src": 1,
  "start": 0,
  "duration": 705600000,
  "effects": [ ... ],
  "parameters": { ... }
}
```

The `_type` field determines the clip type — see {doc}`/concepts/clip-ontology`
for the full list.

## Format versioning

The `version` field (e.g., `"6.0"`, `"8.0"`, `"10.0"`) indicates the schema
version. Newer versions add metadata keys and structural requirements. The
validation system accounts for version differences when checking Group clip
metadata.

## See also

- {doc}`/camtasia-format-reference` — complete field-by-field reference
- {doc}`/concepts/project-model` — how pycamtasia loads this format
- {doc}`/concepts/timing` — the edit rate and tick system
- {doc}`/concepts/clip-ontology` — clip types and their `_type` strings
- {doc}`/concepts/validation-model` — validating the JSON structure
