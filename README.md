<p align="center">
  <em>Read, write, and manipulate Camtasia project files with Python.</em>
</p>

<p align="center">
<a href="https://github.com/grandmasteri/pycamtasia/actions/workflows/tests.yml"><img src="https://github.com/grandmasteri/pycamtasia/actions/workflows/tests.yml/badge.svg" alt="Tests"></a>
<a href="https://github.com/grandmasteri/pycamtasia/actions/workflows/tests.yml"><img src="https://img.shields.io/badge/coverage-100%25-brightgreen" alt="Coverage"></a>
<a href="https://github.com/grandmasteri/pycamtasia/actions/workflows/tests.yml"><img src="https://img.shields.io/badge/mypy-0%20errors-blue" alt="mypy"></a>
<a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.10+-blue.svg" alt="Python 3.10+"></a>
<a href="https://github.com/grandmasteri/pycamtasia/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License: MIT"></a>
</p>

---

**pycamtasia** is a Python library for programmatic access to TechSmith Camtasia project files (`.cmproj` / `.tscproj`). Load projects, manipulate timelines, apply effects, manage media, and save — all from Python. Validated against 93 TechSmith sample assets (JSON Schema) with 2,312 tests at 100% coverage across 70 source files (0 mypy errors, 0 undocumented public symbols). Hardened through 7 rounds of adversarial code review (63+ bugs fixed). Tested on Python 3.10–3.13 in CI.

📖 **[Documentation](https://grandmasteri.github.io/pycamtasia/)** · 🐛 **[Issues](https://github.com/grandmasteri/pycamtasia/issues)**

---

## Installation

```bash
git clone https://github.com/grandmasteri/pycamtasia.git
cd pycamtasia
pip install -e '.[test]'
```

## Quick Example

```python
import camtasia

# Load a project
proj = camtasia.load_project("my_video.cmproj")

# Iterate tracks and clips
for track in proj.timeline.tracks:
    for clip in track.clips:
        print(f"{clip.clip_type}: {clip.duration_seconds:.1f}s")
        clip.fade_in(0.5)
        clip.add_drop_shadow(blur=25.0)
        clip.set_speed(2.0)

# Save
proj.save()
```

## Features

- **Project I/O** — Load, create, copy, compact, and save `.cmproj` / `.tscproj` bundles
- **Timeline manipulation** — Tracks, clips, markers, transitions, reordering
- **Type-safe clips** — Audio, video, image, screen recording, callout, group
- **Effects & animation** — Drop shadow, glow, round corners, keyframes, fade in/out
- **Speed control** — Rational-precision scalars with audio-video sync
- **Transforms** — Move, scale, crop, rotate with canvas-aware positioning
- **Cursor effects** — Motion blur, shadow, physics, click scaling
- **Audiate integration** — Word-level transcript parsing from Audiate and WhisperX
- **Batch operations** — `apply_to_clips()`, `fade_all()`, `scale_all()`, `move_all()`
- **Layout operations** — `pack_track()`, `ripple_insert()`, `ripple_delete()`, `snap_to_grid()`
- **Builders** — `TimelineBuilder`, `CalloutBuilder`, `build_from_screenplay()` for fluent assembly
- **Undo & redo** — JSON Patch-based change history with `track_changes`, persist across sessions
- **Export** — SRT subtitles, EDL, CSV, project reports (JSON/Markdown), timeline JSON
- **Project tools** — Diff, merge, cleanup, validation, statistics
- **Project introspection** — `Project.summary()`, `statistics()`, `to_markdown_report()`
- **Project repair** — `Project.repair()` auto-fixes stale transitions and broken references
- **Video production helpers** — `add_background_music`, `add_lower_third`, `add_progressive_disclosure`, `add_zoom_to_region`, `add_callout_sequence`, `add_chapter_markers`, `add_title_card`, `add_subtitle_track`, `add_voiceover_sequence`, `add_image_sequence`
- **Group manipulation** — `group_clips()`, `ungroup_clip()`, `Group.add_internal_track()`, nested group support
- **JSON Schema validation** — 93 TechSmith samples validated against schema; structural integrity checks on load/save
- **Camtasia v10 compatible** — NSJSONSerialization-style formatting preserved on save

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

```bash
pytest                                    # 2,312 tests, ~13s
pytest --cov=camtasia --cov-report=term   # with coverage
mypy src/camtasia                         # 0 errors
```

## License

MIT — see [LICENSE](LICENSE) for details.

Originally forked from [sixty-north/python-camtasia](https://github.com/sixty-north/python-camtasia).
