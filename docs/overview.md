# Overview

**pycamtasia** is a Python library for reading, writing, and manipulating
[TechSmith Camtasia](https://www.techsmith.com/camtasia/) project files
(`.cmproj` / `.tscproj`). It gives video producers, developer advocates, and
automation engineers a typed, scriptable API for assembling and transforming
Camtasia projects — replacing manual GUI work with reproducible Python code.

## What you can do

- **Assemble videos from scripts** — combine voiceover audio, slide images,
  screen recordings, and title cards into a finished project without touching
  the Camtasia GUI.
- **Batch-apply effects** — add drop shadows, fades, round corners, or color
  adjustments to every clip in a project with a single loop.
- **Generate projects from templates** — clone a template project and swap
  placeholder media for real assets, producing consistent branded videos at
  scale.
- **Sync audio to visuals** — align slide transitions to transcript timestamps
  or timeline markers using the audio-video sync engine.
- **Export metadata** — extract SRT subtitles, EDL edit lists, CSV timelines,
  chapter markers, and project reports from any Camtasia project.
- **Validate projects** — catch duplicate clip IDs, missing media references,
  and structural issues before opening in Camtasia.
- **Control speed with precision** — use `Fraction`-based lossless scalar
  arithmetic to change playback speed without floating-point drift.
- **Integrate with CI pipelines** — generate or transform projects in automated
  workflows, then hand off to Camtasia for final rendering.

## How it compares

| | Camtasia GUI | ffmpeg / OpenCV scripts | Editing `.tscproj` by hand | **pycamtasia** |
|---|---|---|---|---|
| **Learning curve** | Visual, discoverable | Steep CLI / API | Must reverse-engineer JSON | Typed Python API with docs |
| **Repeatability** | Manual — hard to reproduce | Fully scriptable | Scriptable but fragile | Fully scriptable with validation |
| **Camtasia features** | Full access | None — different tool | Full access but no guardrails | Most features via typed wrappers |
| **Batch operations** | One project at a time | Natural | Possible but error-prone | Natural — loop over clips/tracks |
| **Safety** | Undo in GUI | N/A | Silent corruption risk | Structural validation + undo/redo |
| **Output format** | `.cmproj` for rendering | Final video directly | `.tscproj` JSON | `.cmproj` for rendering in Camtasia |

**Camtasia GUI** is the right choice for one-off editing with full visual
feedback. **ffmpeg/OpenCV** is the right choice when you don't need Camtasia at
all and want to produce final video directly. **pycamtasia** fills the gap when
you need Camtasia's rendering engine but want to automate the project assembly
— or when you need to inspect, transform, or batch-process existing Camtasia
projects.

## Next steps

- [Installation](installation.md) — install pycamtasia and optional extras
- [Quick Start](quickstart.md) — load a project and make your first edit
- [Getting Started Tutorial](guides/getting-started.md) — build a complete
  project from scratch
- [Cookbook](guides/cookbook.md) — 15+ runnable recipes
