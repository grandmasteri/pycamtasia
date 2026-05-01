# Timing and Edit Rate

All time values in a Camtasia project are integers measured in **ticks**. One
second equals 705,600,000 ticks. Understanding this timing system is essential
for any programmatic editing.

## The edit rate

```python
from camtasia import EDIT_RATE

print(EDIT_RATE)  # 705600000
```

`EDIT_RATE = 705_600_000` is the universal time base for every Camtasia project.
Clip start times, durations, marker positions, and transition lengths are all
stored as integer tick counts.

### Why this number?

705,600,000 was chosen because it divides evenly by all common frame rates and
audio sample rates:

| Divisor | Result | Use case |
|---------|--------|----------|
| 30 | 23,520,000 | 30 fps video |
| 60 | 11,760,000 | 60 fps video |
| 24 | 29,400,000 | 24 fps film |
| 44,100 | 16,000 | CD audio sample rate |
| 48,000 | 14,700 | Professional audio sample rate |

This means frame and sample boundaries always land on exact integer tick values
— no rounding errors accumulate over long timelines.

## Converting between seconds and ticks

pycamtasia provides two conversion functions:

```python
from camtasia import seconds_to_ticks, ticks_to_seconds

ticks = seconds_to_ticks(5.0)       # 3528000000
seconds = ticks_to_seconds(ticks)   # 5.0
```

`seconds_to_ticks` multiplies by `EDIT_RATE` and rounds to the nearest integer.
`ticks_to_seconds` divides by `EDIT_RATE` and returns a float.

The L2 convenience API accepts seconds directly — you rarely need to call these
yourself:

```python
track.add_image(source_id=6, start_seconds=0, duration_seconds=20)
clip.fade_in(0.5)  # 0.5 seconds
```

## Why Fraction arithmetic, not floats

Speed and scalar values use Python's `Fraction` type for exact rational
arithmetic. Floating-point math introduces drift that compounds across
operations:

```python
# Float drift example
speed = 1/3
result = speed * 3  # 0.9999999999999999, not 1.0

# Fraction is exact
from fractions import Fraction
speed = Fraction(1, 3)
result = speed * 3  # Fraction(1, 1) — exactly 1
```

pycamtasia uses `Fraction` throughout the speed/scalar system to ensure that
round-trip conversions (speed → scalar → JSON → scalar → speed) are lossless.

## The scalar concept

Camtasia stores playback speed as a **scalar**, which is the inverse of the
human-readable speed multiplier:

```
scalar = 1 / speed
```

| Human speed | Scalar | Meaning |
|-------------|--------|---------|
| 1× (normal) | `1` | Timeline duration equals source duration |
| 2× (fast) | `1/2` | Timeline uses half the source duration |
| 0.5× (slow) | `2` | Timeline uses double the source duration |

Convert between the two representations:

```python
from camtasia import speed_to_scalar, scalar_to_speed

scalar = speed_to_scalar(2.0)   # Fraction(1, 2)
speed = scalar_to_speed(scalar) # 2.0
```

Scalars are serialized to JSON as string fractions (`"1/2"`) or integer `1`.
Use `parse_scalar` to read them and `scalar_to_string` to write them:

```python
from camtasia import parse_scalar, scalar_to_string

scalar = parse_scalar("51/101")     # Fraction(51, 101)
json_val = scalar_to_string(scalar) # "51/101"
```

## Formatting durations

`format_duration` converts ticks to a human-readable `M:SS.ff` string:

```python
from camtasia.timing import format_duration

print(format_duration(seconds_to_ticks(125.5)))  # "2:05.50"
```

## See also

- {doc}`/concepts/clip-ontology` — clip types that use timing
- {doc}`/guides/speed-change` — practical speed change guide
- {doc}`/api/timing` — full API reference
- {doc}`/concepts/camtasia-file-format` — how timing is stored in JSON
