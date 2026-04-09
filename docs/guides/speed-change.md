# Speed Changes with Visual Re-sync

You have a Camtasia project where the voiceover was sped up — say 1.07× — and you want to slow it back to normal (1.0×) while keeping every visual element in sync. This guide shows how `set_audio_speed()` handles that in one call.

## How Camtasia stores speed

Every clip has a `scalar` field that controls playback speed. The scalar is the ratio of timeline duration to source duration:

```
scalar = timeline_duration / source_duration
```

- `scalar = 1` → normal speed
- `scalar < 1` → faster playback (less timeline per source frame)
- `scalar > 1` → slower playback

For example, audio sped up to 1.07× has a scalar of roughly `1/1.07 ≈ 0.935`. Camtasia stores this as a string fraction like `"51/101"` for exact rational arithmetic.

Clips with a speed change also have `metadata.clipSpeedAttribute.value` set to `true`.

## The solution

`set_audio_speed()` does three things:

1. Finds the audio clip (`AMFile`) that has a speed change
2. Calculates the stretch factor needed to reach the target speed
3. Calls `rescale_project()` to scale **all** timing values proportionally

### What gets scaled

`rescale_project()` walks the entire project and scales:

- Clip `start` and `duration` on every track
- Transition durations
- Timeline markers (time and endTime)
- Nested clips inside `StitchedMedia` (including `mediaStart` / `mediaDuration`)
- Nested clips inside `Group` internal tracks
- Scalars on clips that already have speed changes (adjusted so source alignment is preserved)

## Complete example

```python
import json
from camtasia.operations import set_audio_speed

with open('project.tscproj') as f:
    data = json.load(f)

factor = set_audio_speed(data, target_speed=1.0)
print(f"Stretched by {float(factor):.4f}x")

with open('project.tscproj', 'w') as f:
    json.dump(data, f, indent=2)
```

If the audio was at 1.07× (scalar ≈ `51/101`), this stretches the entire timeline by ~1.07× so everything plays at normal speed. The audio clip's scalar is reset to `1` and its `clipSpeedAttribute` is cleared.

## The math

Given a current scalar `s` and a target speed `t`:

```
target_scalar = 1 / t
factor = target_scalar / s
```

For `s = 51/101` (1.07× speed) and `t = 1.0`:

```
target_scalar = 1/1 = 1
factor = 1 / (51/101) = 101/51 ≈ 1.9804
```

Wait — that's the factor for the *scalar*, not the timeline. The timeline stretch factor is `101/51` because the audio needs to occupy more timeline ticks to play at normal speed, and everything else stretches to match.

## Using rescale_project directly

If you need a custom stretch factor (not tied to audio speed), use `rescale_project()` directly:

```python
from fractions import Fraction
from camtasia.operations import rescale_project

# Stretch everything by 10% (slow down)
rescale_project(data, Fraction(11, 10))

# Compress by 20% (speed up)
rescale_project(data, Fraction(4, 5))
```

The factor is multiplicative: values > 1 stretch (slow down), < 1 compress (speed up).

```{note}
This workflow was validated against a real Camtasia 2026 project — a voiceover recorded at 1.07× was corrected to 1.0× and the project played back correctly on the first try.
```
