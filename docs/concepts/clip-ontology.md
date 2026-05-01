# Clip Ontology

Every piece of content on a Camtasia timeline is a **clip**. pycamtasia models
10 distinct clip types, all inheriting from a shared `BaseClip` base class.

## The clip type table

| `_type` string | Python class | What it represents |
|----------------|-------------|-------------------|
| `AMFile` | `AMFile` | Audio file (MP3, WAV, M4A, etc.) |
| `VMFile` | `VMFile` | Video file (MP4, MOV, etc.) |
| `IMFile` | `IMFile` | Still image (PNG, JPG, etc.) |
| `Callout` | `Callout` | Text overlay / annotation |
| `Group` | `Group` | Compound clip with nested internal tracks |
| `StitchedMedia` | `StitchedMedia` | Multiple clips joined end-to-end as one unit |
| `UnifiedMedia` | `UnifiedMedia` | Audio+video pair linked as a single clip |
| `ScreenVMFile` | `ScreenVMFile` | Screen recording video (from `.trec` files) |
| `ScreenIMFile` | `ScreenIMFile` | Screen recording still frame |
| `PlaceholderMedia` | `PlaceholderMedia` | Placeholder for media not yet imported |

### When to use which

- **AMFile / VMFile / IMFile** — standard imported media. Most projects use
  these for voiceover audio, video clips, and slide images.
- **Callout** — text overlays, titles, lower thirds. Created via
  `track.add_callout()` or `CalloutBuilder`.
- **Group** — compound clips that contain their own internal tracks. Screen
  recordings from Camtasia are typically Groups containing a `ScreenVMFile`
  (video), an `AMFile` (mic audio), and cursor data. Also used for manually
  grouped clips.
- **StitchedMedia** — clips joined into a single unit on the timeline. Created
  when Camtasia stitches segments together (e.g., after splitting and
  rearranging).
- **UnifiedMedia** — a linked audio+video pair. The `video` and `audio`
  sub-clips share timing and move together.
- **ScreenVMFile / ScreenIMFile** — screen recording variants that carry
  cursor path data and cursor effects.
- **PlaceholderMedia** — a stand-in for media that will be replaced later.
  Useful in template workflows.

## The BaseClip base class

All clip types inherit from `BaseClip`, which provides the shared interface:

```python
clip.id            # unique integer ID
clip.start         # start time in ticks
clip.duration      # duration in ticks
clip.type_name     # the _type string ("AMFile", "VMFile", etc.)
clip.effects       # list of Effect objects
clip.scalar        # playback speed as Fraction

# L2 convenience methods (available on all clip types)
clip.fade_in(0.5)
clip.fade_out(1.0)
clip.set_opacity(0.8)
clip.mute()
clip.add_drop_shadow()
clip.remove_effects("DropShadow")
```

`BaseClip` wraps a raw dict (`clip._data`) — see
{doc}`/concepts/the-two-api-layers` for when to use the dict directly.

## The clip_from_dict factory

When loading a project, pycamtasia needs to create the right Python class from
a raw JSON dict. The `clip_from_dict` factory handles this dispatch:

```python
from camtasia import clip_from_dict

raw = {"_type": "IMFile", "id": 42, "start": 0, "duration": 705600000, ...}
clip = clip_from_dict(raw)
type(clip)  # <class 'camtasia.timeline.clips.image.IMFile'>
```

Internally, `clip_from_dict` uses a `_TYPE_MAP` dictionary that maps `_type`
strings to Python classes:

```python
_TYPE_MAP = {
    'AMFile': AMFile,
    'VMFile': VMFile,
    'IMFile': IMFile,
    'ScreenVMFile': ScreenVMFile,
    'ScreenIMFile': ScreenIMFile,
    'StitchedMedia': StitchedMedia,
    'Group': Group,
    'Callout': Callout,
    'UnifiedMedia': UnifiedMedia,
    'PlaceholderMedia': PlaceholderMedia,
}
```

If the `_type` is unrecognized, `clip_from_dict` returns a generic `BaseClip`
instance — the data is preserved, just without type-specific methods.

## Clip hierarchy

```
BaseClip
├── AMFile          (audio)
├── VMFile          (video)
├── IMFile          (image)
├── ScreenVMFile    (screen recording video)
├── ScreenIMFile    (screen recording image)
├── Callout         (text overlay)
├── Group           (compound clip)
├── StitchedMedia   (joined segments)
├── UnifiedMedia    (linked audio+video)
└── PlaceholderMedia (template placeholder)
```

Each subclass adds type-specific properties and methods. For example, `Group`
exposes internal tracks, `Callout` has text content and font properties, and
`ScreenVMFile` provides cursor path data.

## See also

- {doc}`/concepts/effect-system` — effects attached to clips
- {doc}`/concepts/the-two-api-layers` — L1 vs L2 access patterns
- {doc}`/concepts/timing` — how clip start/duration are measured
- {doc}`/api/clips` — full clip API reference
- {doc}`/guides/convenience-api` — L2 clip methods
