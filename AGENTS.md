# pycamtasia — Agent Guide

## What is this library?

A Python library for programmatic manipulation of Camtasia project files (`.cmproj`). Used to assemble demo videos from voiceover audio, diagram images, screen recordings, and title cards without touching the Camtasia GUI.

## Core Development Principles

### Reverse-engineer-first workflow

Any new Camtasia capability follows this pattern:

1. Perform the target action in the Camtasia GUI
2. Snapshot the project JSON before and after: `cp project.tscproj /tmp/before.json` / `after.json`
3. Diff and analyze the changes (dispatch a subagent to write a spec)
4. Implement the feature in pycamtasia based on the findings
5. Expose it as a clean, simple high-level API

**Never guess at the JSON format.** Always reverse-engineer from real Camtasia output.

### Library-first moratorium

No raw `_data` access or direct JSON manipulation in assembly scripts or any consumer code. If pycamtasia doesn't support an operation, **implement it in the library first** with a proper L2 API, then use that API. The assembly script should read like a high-level description of intent, not JSON surgery.

The only acceptable `_data` access is inside the library itself (in `src/camtasia/`).

### High-level API over low-level control

The library exposes two API layers:

- **L2 (high-level)**: What most users need. Clean methods like `clip.fade(0.5, 0.5)`, `track.add_lower_third(title, subtitle, start, duration)`, `proj.import_media(path)`. These hide all JSON complexity.
- **L1 (low-level)**: Direct access to `clip._data` for power users who need control the L2 API doesn't expose. This is an escape hatch, not the default.

When adding features, always add the L2 API. The L1 access already exists by virtue of `_data` being accessible.

## Build & Test

```bash
PYTHONPATH=src python3 -m pytest tests/ -q    # run tests
PYTHONPATH=src python3 -m pytest tests/ --cov=camtasia --cov-report=term-missing  # coverage
```

Coverage target: `fail_under = 100` in pyproject.toml.

## Key Files

- `src/camtasia/project.py` — load/save, import_media, validation, parameter flattening
- `src/camtasia/timeline/clips/base.py` — BaseClip with fade, mute, gain, opacity, speed
- `src/camtasia/timeline/track.py` — Track with add_audio, add_image, add_video, add_callout, add_lower_third, split_clip
- `src/camtasia/media_bin/media_bin.py` — source bin management
- `src/camtasia/templates/lower_third.py` — Right Angle Lower Third JSON template
- `ROADMAP.md` — planned features and completed items

## Camtasia v10 Format Notes

- Opacity fades use 2 keyframes + 2 visual segments (target value pattern, not start/end value pattern)
- `defaultValue: 0.0` for opacity means clip starts invisible
- Callouts on the same track at the same time cause "Collision exception"
- Groups contain internal tracks; `mediaStart`/`mediaDuration` act as a viewing window
- `-Infinity` in JSON crashes the parser; `save()` handles this automatically
- JSON formatting must match Camtasia's style: `" : "` not `": "`, scalar arrays on one line
