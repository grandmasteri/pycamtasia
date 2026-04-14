# Type Safety

pycamtasia ships with `py.typed`, comprehensive enums, and TypedDicts so your
editor and mypy can catch mistakes before runtime.

## Enums for string constants

Instead of passing raw strings, use the typed enums from `camtasia.types`:

```python
from camtasia.types import ClipType, EffectName, TransitionType

# Filter clips by type
videos = [c for c in track.clips if c.clip_type == ClipType.VIDEO]

# Add an effect by name
clip.add_effect(EffectName.DROP_SHADOW)

# Set a transition
clip.set_transition(TransitionType.DISSOLVE, duration=30)
```

Your editor will autocomplete the valid values and mypy will flag typos like
`EffectName.DROPSHADOW` at check time.

## Available enums

| Enum | Purpose | Examples |
|------|---------|----------|
| `ClipType` | Clip media types | `VIDEO`, `AUDIO`, `IMAGE`, `CALLOUT`, `GROUP` |
| `EffectName` | Visual/audio effects | `DROP_SHADOW`, `BLUR_REGION`, `COLOR_ADJUSTMENT` |
| `TransitionType` | Transition styles | `DISSOLVE`, `FADE`, `SLIDE_LEFT`, `GLITCH` |
| `BehaviorPreset` | Animation presets | Motion behaviors for clips |
| `BlendMode` | Layer blend modes | Compositing modes |
| `MaskShape` | Mask geometries | Shape options for mask effects |
| `CalloutShape` | Callout shapes | Arrow, rectangle, etc. |
| `ValidationLevel` | Validation severity | Levels for project health checks |
| `MediaType` | Media categories | Audio, video, image classification |

## TypedDicts for structured data

When functions return or accept structured dictionaries, pycamtasia defines
TypedDicts so you get key-completion and type checking:

```python
from camtasia.types import DropShadowParams, ClipSummary

# TypedDict gives you autocomplete on keys
params: DropShadowParams = {
    "color": {"red": 0, "green": 0, "blue": 0, "alpha": 200},
    "angle": 315,
    "offset": 5,
    "blur": 10,
}

# ClipSummary from export functions
summary: ClipSummary  # has .name, .start, .duration, .clip_type, etc.
```

## Literal types

Some parameters use `Literal` types for constrained values:

```python
from camtasia.types import Alignment, ReportFormat

# Alignment: 0 (left), 1 (center), 2 (right)
caption.alignment: Alignment = 1

# ReportFormat: 'markdown' or 'json'
export_project_report(project, format="markdown")
```

## Running mypy

pycamtasia is fully mypy-clean. Add it to your checks:

```bash
mypy --strict your_script.py
```

The `py.typed` marker means mypy will automatically pick up pycamtasia's
type information — no stubs needed.
