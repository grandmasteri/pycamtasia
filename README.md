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

**pycamtasia** is a Python library for programmatic access to TechSmith Camtasia project files (`.cmproj` / `.tscproj`). Load projects, manipulate timelines, apply effects, manage media, and save — all from Python. Validated against 86 TechSmith sample assets with 1,752 tests at 100% coverage.

📖 **[Documentation](https://grandmasteri.github.io/pycamtasia/)** · 📦 **[PyPI](https://pypi.org/project/pycamtasia/)** · 🐛 **[Issues](https://github.com/grandmasteri/pycamtasia/issues)**

---

## Installation

```bash
pip install pycamtasia
```

For development:

```bash
git clone https://github.com/grandmasteri/pycamtasia.git
cd pycamtasia
pip install -e ".[dev,test]"
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

# Apply effects
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
- **Builders** — `TimelineBuilder`, `CalloutBuilder`, `ScreenplayBuilder` for fluent assembly
- **Export** — SRT subtitles, EDL, project reports (JSON/Markdown), timeline JSON
- **Project tools** — Diff, merge, cleanup, validation, statistics
- **Camtasia v10 compatible** — NSJSONSerialization-style formatting preserved on save

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

```bash
pytest                                    # 1,752 tests, ~13s
pytest --cov=camtasia --cov-report=term   # with coverage
mypy src/camtasia                         # 0 errors
```

## License

MIT — see [LICENSE](LICENSE) for details.

Originally forked from [sixty-north/python-camtasia](https://github.com/sixty-north/python-camtasia).
