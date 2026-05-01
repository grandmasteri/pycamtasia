# The Two API Layers

pycamtasia has two layers of API for interacting with project data. Understanding
when to use each is key to working effectively with the library.

## L1: Raw dict access

Every pycamtasia object is a thin wrapper around a JSON dict. The underlying
dict is always accessible via `._data`:

```python
clip._data                    # the raw JSON dict for this clip
clip._data["start"]           # start time in ticks (integer)
clip._data["parameters"]      # raw parameter dict
clip._data["effects"]         # raw effects array
```

L1 gives you full control over every field in the Camtasia JSON. It's verbose
and requires knowledge of the exact key names and value formats, but nothing is
hidden.

### When to use L1

- Accessing a field that L2 doesn't expose yet
- Debugging — inspecting the exact JSON that will be saved
- Bulk operations on raw data structures
- Working with newly discovered Camtasia features before pycamtasia adds
  typed support

## L2: Typed Python API

L2 methods handle the boilerplate: they accept seconds instead of ticks,
construct correct JSON schemas internally, and return `self` for chaining.

```python
clip.fade_in(0.5)           # 0.5s opacity fade in
clip.fade_out(1.0)          # 1.0s fade out at end
clip.set_opacity(0.8)       # static opacity
clip.add_drop_shadow()      # sensible defaults
clip.mute()                 # set gain to 0
```

Track-level methods create clips with the right `_type` and structure:

```python
track.add_image(source_id=6, start_seconds=0, duration_seconds=20)
track.add_callout("Title", start_seconds=0, duration_seconds=5)
track.add_audio(source_id=3, start_seconds=0, duration_seconds=60)
```

### When to use L2

- Standard operations: adding clips, applying effects, fading, muting
- Any time the method exists — L2 is safer and more readable
- Building slide sequences, adding transitions, importing media

## Worked example: the escape hatch

Suppose you need to set a custom parameter that L2 doesn't expose. Drop to L1
for just that field:

```python
from camtasia import use_project

with use_project("my_video.cmproj") as proj:
    track = list(proj.timeline.tracks)[0]
    clip = list(track.clips)[0]

    # L2 for standard operations
    clip.fade_in(0.5)
    clip.add_drop_shadow(offset=10)

    # L1 escape hatch for a custom field
    clip._data["parameters"]["customField"] = {
        "type": "double",
        "defaultValue": 42.0,
    }
```

Every L2 object wraps a dict — `_data` is always available. The two layers
coexist: L2 methods read and write the same `_data` dict, so changes made
through either layer are immediately visible to the other.

## Design rationale

The two-layer design follows from pycamtasia's architecture: all classes are
thin wrappers over the JSON dict tree. There is no separate model or
serialization step. `project.save()` writes the current dict state directly.

This means:

- **L2 is sugar, not a barrier.** It doesn't hide the data — it just makes
  common operations convenient.
- **L1 is always available.** You never hit a wall where the library can't do
  something — the raw JSON is right there.
- **No sync issues.** Both layers operate on the same dict, so there's no
  risk of L1 and L2 getting out of sync.

## The library-first principle

While L1 is available as an escape hatch, the project convention is
**library-first**: if you find yourself using `_data` access repeatedly for the
same operation, that's a signal to add an L2 method to the library. Consumer
scripts should use L2 wherever possible.

## See also

- {doc}`/concepts/project-model` — the Project object and its components
- {doc}`/concepts/clip-ontology` — clip types and BaseClip
- {doc}`/concepts/effect-system` — effect parameter access
- {doc}`/concepts/the-two-api-layers` — full L2 method reference
- {doc}`/api/clips` — clip API reference
