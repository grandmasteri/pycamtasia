# Design Decisions — Intentional Patterns

This document captures design decisions that look like bugs but are
intentional. Reviewers and fixers should consult this file before filing
findings about the listed patterns.

If you believe a design decision here is wrong, file it as a finding
anyway with severity INFO and reference this file — do not silently
change the behavior.

---

## D-001: Two API layers (high-level + low-level)

The library exposes BOTH a high-level convenience API (e.g.
`project.import_media()`, `track.add_audio(media_id, ...)`) AND a
low-level API (e.g. `track.add_clip('AMFile', source_id, ...)` with
raw type strings).

**Why:** high-level is for 80% of users; low-level gives power users
access to features not yet wrapped. This is documented in
`docs/concepts/the-two-api-layers.md`.

**Do not flag:** "redundant API", "confusing two ways to add clips",
"inconsistent naming between layers".

## D-002: Mixed positional and keyword-only arguments

Some APIs take positional args (e.g. `add_callout(text, start_seconds, duration_seconds)`)
and others require keyword-only (`add_audio(media_id, *, start_seconds, duration_seconds)`).

**Why:** callouts are constructed frequently with 3 intuitive args; audio
clips have more configuration and a media_id first arg that benefits from
explicit kwargs for safety. Some risk methods force kwargs. This is not
accidental.

**Do flag:** if the inconsistency is NOT matching this rationale (e.g.
two methods with identical risk profiles using different styles).

## D-003: Validation is advisory, not blocking

`project.validate()` returns a list of issues; it does not raise or
prevent save. `project.save()` always succeeds even on invalid state.

**Why:** users may deliberately create intermediate invalid states
(e.g. constructing a project in stages, importing from a broken
upstream). Forcing validity mid-construction breaks workflows.

**Do not flag:** "save should validate first". The integration tests
use `open_in_camtasia()` which DOES enforce the contract in test
context only.

## D-004: Point-form vs span-form keyframes

- Audio / scalar parameter keyframes: point form (`endTime == time`, `duration == 0`)
- Visual parameter keyframes (scale, opacity, translation): span form (`endTime > time`, `duration > 0`)

**Why:** Camtasia's file format treats these differently. Visual
parameters share animation tracks that need non-overlapping segments;
audio parameters are interpolated point-by-point.

**Do not flag:** "inconsistent keyframe construction", "why isn't
this unified?".

## D-005: ticks (not seconds) is the internal unit

All internal timing uses ticks (`EDIT_RATE = 705600000` per second).
Public APIs take seconds and convert via `seconds_to_ticks()`.

**Why:** matches Camtasia's file format; avoids floating-point
precision loss for frame-aligned operations.

**Do not flag:** "why don't internal APIs take seconds?"

## D-006: Behavior preset "center phase" names differ from preset names

For some BehaviorPreset values (emphasize, jiggle), the center phase
name in the generated JSON differs from the preset name (e.g.
`emphasize` → `pulsate`, `jiggle` → `tremble`). Verified against
Camtasia's own output.

**Do not flag:** "inconsistent naming in behavior_presets.py". These
are the NAMES Camtasia expects; the preset names are pycamtasia's
user-facing abstraction.

## D-007: CLI entry points are lazy-imported

The `camtasia.cli` module uses lazy imports so the library can be
installed without `[cli]` extras and not fail on plain `import camtasia`.

**Do not flag:** "CLI import should be at top of module".

## D-008: Optional dependencies (pymediainfo) degrade gracefully

If `pymediainfo` is not installed, `import_media()` falls back to a
1-second default duration with a warning. This matches the
progressive-enhancement model.

**Do not flag:** "import_media should require pymediainfo".

## D-009: MIT-required attribution to Sixty North AS

The LICENSE includes both `Copyright (c) 2019 Sixty North AS` and
`Copyright (c) 2019-2026 Isaac Douglas`. This is **legally required**
— the repo originated as a fork of
`https://github.com/sixty-north/python-camtasia` under MIT, and MIT
requires preserving the upstream attribution.

**Do not flag:** "remove Sixty North from LICENSE" or "dual copyright
is confusing".

## D-010: Integration tests must run serially

`pytest -m integration` requires `-o "addopts="` to disable xdist.
Integration tests serialize through a filelock to prevent Camtasia
instances from killing each other, but xdist workers waiting on the
lock would trigger pytest-timeout. Documented in
`docs/development/publishing.md`.

**Do not flag:** "why isn't the integration suite parallelized?" or
"filelock is redundant with -o addopts=".
