# pycamtasia

*Read, write, and manipulate Camtasia project files with Python.*

[![PyPI version](https://img.shields.io/pypi/v/pycamtasia)](https://pypi.org/project/pycamtasia/)
[![Python versions](https://img.shields.io/pypi/pyversions/pycamtasia)](https://pypi.org/project/pycamtasia/)
[![Tests](https://github.com/grandmasteri/pycamtasia/actions/workflows/tests.yml/badge.svg)](https://github.com/grandmasteri/pycamtasia/actions/workflows/tests.yml)
[![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen)](https://github.com/grandmasteri/pycamtasia/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/grandmasteri/pycamtasia/blob/main/LICENSE)

> ✨ Active development — this is the initial public release. API may evolve before 1.0.0.

---

## Why pycamtasia?

Camtasia projects are opaque bundles of JSON, media, and recordings. **pycamtasia** gives you a clean Python API to create, inspect, and transform them — so you can automate video production pipelines, batch-apply effects, generate projects from scripts, and integrate Camtasia into CI workflows. The library is tested with 4,900+ tests at 100% line coverage across 92 source files, with full mypy and ruff compliance.

## Installation

```bash
pip install pycamtasia
```

Optional extras:

```bash
pip install pycamtasia[cli]    # Command-line interface (pytsc)
pip install pycamtasia[media]  # Media probing via pymediainfo
```

## Quickstart

```python
import camtasia

# Create a new empty project
camtasia.new_project("demo.cmproj")

# Load it
proj = camtasia.load_project("demo.cmproj")

# Add a track and inspect the timeline
track = proj.timeline.add_track("Main")
print(f"Tracks: {len(proj.timeline.tracks)}")

# Set project metadata
proj.title = "My Demo"
proj.author = "pycamtasia"

# Save and print the path
proj.save()
print(f"Saved to {proj.file_path}")
```

## More Examples

### Read a project and print a report

```python
import camtasia

proj = camtasia.load_project("lecture.cmproj")
print(proj.summary())

for track in proj.timeline.tracks:
    print(f"Track {track.index}: {len(track.clips)} clips")
    for clip in track.clips:
        print(f"  {clip.clip_type}: {clip.duration_seconds:.1f}s")
```

### Batch-apply effects to every clip

```python
import camtasia

with camtasia.use_project("tutorial.cmproj") as proj:
    for track in proj.timeline.tracks:
        for clip in track.clips:
            clip.fade_in(0.5)
            clip.add_drop_shadow(blur=25.0)
# Project is saved automatically on exit
```

### Fill a template project with real media

```python
from camtasia import load_project
from camtasia.operations.template import replace_placeholder

proj = load_project("template.cmproj")
for track in proj.timeline.tracks:
    for clip in track.clips:
        if clip.clip_type == "PlaceholderMedia":
            print(f"Placeholder: {clip.name}")
            # Replace with real media using replace_placeholder()
```

## Key Features

- **Project I/O** — Create, load, copy, compact, and save `.cmproj` / `.tscproj` bundles
- **Timeline editing** — Tracks, clips, markers, transitions, split, trim, reorder, ripple insert/delete
- **Effects & animation** — Drop shadow, glow, round corners, keyframes, fade, behaviors, cursor effects
- **Speed control** — Fraction-based lossless scalar arithmetic with audio-video sync
- **Builders** — `TimelineBuilder`, `CalloutBuilder`, `ScreenplayBuilder` for fluent project assembly
- **Undo & redo** — JSON Patch-based change history, persistable across sessions
- **Export** — SRT subtitles, EDL, CSV, project reports (JSON/Markdown), chapter markers
- **Validation** — JSON Schema validation against 93 TechSmith samples; structural and semantic checks
- **Video production helpers** — Background music, lower thirds, progressive disclosure, zoom-to-region, voiceover sequences, and more
- **Audiate integration** — Word-level transcript parsing from Audiate and WhisperX

## Requirements

- **Python 3.10+** (tested on 3.10, 3.11, 3.12, 3.13)
- **Camtasia 2024+** (project format version 10.0)
- No binary dependencies — pure Python with only `jsonpatch` as a runtime requirement

## Links

- 📖 [Documentation](https://grandmasteri.github.io/pycamtasia/)
- 📋 [Changelog](https://github.com/grandmasteri/pycamtasia/blob/main/CHANGELOG.md)
- 🐛 [Issues](https://github.com/grandmasteri/pycamtasia/issues)
- 🤝 [Contributing](https://github.com/grandmasteri/pycamtasia/blob/main/CONTRIBUTING.md)
- 🔒 [Security](https://github.com/grandmasteri/pycamtasia/blob/main/SECURITY.md)

## Contributing

Contributions are welcome — see [CONTRIBUTING.md](CONTRIBUTING.md) for setup and guidelines.

```bash
pytest                                    # 4,900+ tests
pytest --cov=camtasia --cov-report=term   # with coverage (must be 100%)
mypy src/camtasia                         # 0 errors
```

## License

MIT — see [LICENSE](LICENSE) for details.

`SPDX-License-Identifier: MIT`
