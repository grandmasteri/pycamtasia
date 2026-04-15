# What's New in 7.1

pycamtasia 7.1 is the most thoroughly tested and feature-rich release to date.
Every feature below went through 7 rounds of adversarial code review, resulting
in 63+ bugs caught and fixed before release. The result: a library you can trust
with your production Camtasia workflows.

## Reliability you can verify

This release was validated against **93 real-world Camtasia project files** from
TechSmith's own sample library. Every project loads, round-trips, and saves
without data loss.

- **2,446 tests** with **100% code coverage**
- **34 Hypothesis property-based invariants** that stress-test edge cases no human would write by hand
- **JSON Schema validation** ensures every project file pycamtasia produces is structurally correct
- **Python 3.10, 3.11, 3.12, and 3.13** are all fully supported and tested in CI

## Group manipulation

Work with grouped clips the same way Camtasia's UI does — but from code.

```python
# Group clips together
group = track.group_clips([clip_a, clip_b, clip_c])

# Ungroup back to individual clips
clips = track.ungroup(group)

# Merge adjacent clips into one
merged = track.merge(clip_a, clip_b)
```

Groups are first-class objects. You can nest them, iterate their children,
and apply effects to the entire group at once:

```python
for child in group.children:
    print(f"  {child.clip_type}: {child.start_seconds:.1f}s")

group.fade_in(0.5)          # fades the whole group
group.add_drop_shadow()      # shadow on the composite
group.mute()                 # silence all audio in the group
```

## Video production helpers

10+ new methods for common video production tasks — things that previously
required dozens of lines of manual JSON manipulation.

```python
# Build a slide deck with transitions in one call
clips = track.add_image_sequence(
    source_ids=[s.id for s in slides],
    start_seconds=0.0,
    duration_per_image_seconds=15.0,
    transition_seconds=0.5,
)

# Position and style clips
clip.move_to(100, -50)
clip.scale_to(1.5)
clip.crop(left=0.1, right=0.1)

# Animate
clip.fade(0.5, 1.0)         # fade in 0.5s, fade out 1.0s
clip.set_opacity(0.8)

# Effects
clip.add_drop_shadow(offset=10, blur=20, opacity=0.3)
clip.add_glow(radius=35, intensity=0.5)
clip.add_round_corners(radius=12)

# Transitions between clips
track.transitions.add_dissolve(clip_a, clip_b, duration_seconds=0.5)
```

All time parameters are in seconds. All methods return `self` for chaining:

```python
track.add_image(src, 0, 20).fade_in(0.5).add_drop_shadow().move_to(0, -100)
```

## Project introspection

Understand what's in a project without opening Camtasia.

```python
# Quick summary
print(proj.summary())
# → "My Project: 3 tracks, 12 clips, 47.5s duration"

# Detailed statistics
stats = proj.statistics()
print(f"Tracks: {stats['track_count']}")
print(f"Clips: {stats['clip_count']}")
print(f"Media files: {stats['media_count']}")
print(f"Duration: {stats['duration_seconds']:.1f}s")

# Full report (Markdown or JSON)
report = proj.report(format="markdown")
Path("project-report.md").write_text(report)
```

Use these for CI checks, documentation generation, or just getting your
bearings in an unfamiliar project.

## Audio utilities

Dedicated tools for the audio side of video production.

```python
# Normalize audio levels across clips
track.normalize_audio()

# Mute / solo individual clips
clip.mute()                  # silence this clip
clip.solo()                  # mute everything except this clip

# Convert audio formats
from camtasia.audio import convert_audio_to_wav
convert_audio_to_wav("narration.m4a", "narration.wav")
```

`mute()` and gain control work on any clip type, including Group clips — handy
for silencing the mic track in a screen recording while keeping system audio.

## JSON Schema validation

Every project file pycamtasia writes is validated against a JSON Schema derived
from TechSmith's format. This catches structural errors at save time, not when
you open the file in Camtasia and see a blank timeline.

```python
from camtasia.validation import validate_project

errors = validate_project(proj)
if errors:
    for e in errors:
        print(f"  {e.path}: {e.message}")
else:
    print("Project is valid ✓")
```

Validation runs automatically on `save()`. You can also run it manually to
check a project before committing changes.

## Upgrading

```bash
pip install --upgrade pycamtasia
```

pycamtasia 7.1 is a drop-in replacement for 7.0. No API changes are required —
all new features are additive.
