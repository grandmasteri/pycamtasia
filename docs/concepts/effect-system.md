# The Effect System

Effects modify how clips look and sound on the timeline. pycamtasia models
effects as thin Python wrappers over the raw JSON dicts stored in each clip's
`effects` array.

## Effect categories

Effects are organized into five categories:

| Category | Examples | Purpose |
|----------|----------|---------|
| **visual** | `DropShadow`, `Glow`, `RoundCorners`, `Mask`, `ChromaKey`, `ColorAdjustment` | Modify the visual appearance of a clip |
| **audio** | `NoiseRemoval`, `Equalizer`, `AudioCompression`, `Pitch` | Process clip audio |
| **source** | `SourceEffect` | Shader-level parameters (gradients, colors) |
| **cursor** | `CursorShadow`, `CursorMotionBlur`, `CursorPhysics`, `LeftClickScaling` | Modify cursor appearance in screen recordings |
| **behavior** | `GenericBehaviorEffect` | Text animation behaviors (entrance, emphasis, exit) |

## The base Effect class

Every effect wraps a dict with this structure:

```python
{
    "effectName": "DropShadow",
    "category": "visual",
    "bypassed": False,
    "parameters": {
        "shadow-offset": {"type": "double", "defaultValue": 16.0, "interp": "linr"},
        "shadow-blur":   {"type": "double", "defaultValue": 10.0, "interp": "linr"},
        "shadow-opacity": {"type": "double", "defaultValue": 0.5, "interp": "linr"},
    }
}
```

The `Effect` base class provides access to these fields:

```python
effect = clip.effects[0]
effect.name          # "DropShadow"
effect.category      # "visual"
effect.bypassed      # False

# Read/write parameters
effect.get_parameter("shadow-offset")       # 16.0
effect.set_parameter("shadow-offset", 20.0)
```

## The parameter model

Effect parameters are flat dicts with three standard keys:

| Key | Type | Meaning |
|-----|------|---------|
| `type` | string | Data type: `"double"`, `"int"`, `"bool"`, `"color"` |
| `defaultValue` | varies | The current value of the parameter |
| `interp` | string | Interpolation mode: `"linr"` (linear), `"hold"` (step), `"eCuI"` (ease in), etc. |

Parameter keys use **hyphens**, not underscores — this matches Camtasia's JSON
format. For example: `shadow-offset`, `mask-shape`, `top-left`.

## Keyframed animations

Parameters can be animated over time by adding a `keyframes` array:

```python
{
    "type": "double",
    "defaultValue": 0.0,
    "interp": "linr",
    "keyframes": [
        {"time": 0, "value": 0.0, "interp": "linr"},
        {"time": 352800000, "value": 1.0, "interp": "linr"},
    ]
}
```

Each keyframe specifies a `time` (in ticks), a `value`, and an `interp` mode.
The effect interpolates between keyframes during playback.

## The effect registry

pycamtasia uses a registry pattern to map `effectName` strings to Python
classes. Each subclass is registered with the `@register_effect` decorator:

```python
from camtasia.effects.base import register_effect, Effect

@register_effect("DropShadow")
class DropShadow(Effect):
    @property
    def offset(self) -> float:
        return self.get_parameter("shadow-offset")
    ...
```

The registry lives in `_EFFECT_REGISTRY` — a dict mapping effect name strings
to their Python classes.

## The effectName string vs Python class

The `effectName` is the string identifier stored in JSON (e.g.,
`"DropShadow"`, `"CursorMotionBlur"`, `"VSTEffect-DFN3NoiseRemoval"`). The
Python class is the typed wrapper that provides property access and validation.

Not every `effectName` has a dedicated Python class. The `effect_from_dict`
factory handles this gracefully:

```python
from camtasia import effect_from_dict

data = {"effectName": "DropShadow", "parameters": {...}}
effect = effect_from_dict(data)
type(effect)  # <class 'DropShadow'>

data = {"effectName": "SomeUnknownEffect", "parameters": {...}}
effect = effect_from_dict(data)
type(effect)  # <class 'Effect'> — generic fallback
```

Registered effects get type-specific properties (e.g., `DropShadow.offset`).
Unregistered effects still work through the generic `Effect` interface —
`get_parameter` and `set_parameter` always work.

## Adding effects to clips

The L2 convenience API provides methods on `BaseClip`:

```python
clip.add_drop_shadow(offset=10, blur=20, opacity=0.3)
clip.add_glow(radius=35, intensity=0.5)
clip.add_round_corners(radius=12)
clip.remove_effects("DropShadow")
```

These methods construct the correct JSON dict internally and append it to the
clip's `effects` array.

## See also

- {doc}`/concepts/clip-ontology` — the clips that effects attach to
- {doc}`/concepts/the-two-api-layers` — L1 dict access for custom effects
- {doc}`/api/effects` — full effect API reference
- {doc}`/concepts/the-two-api-layers` — L2 effect methods
