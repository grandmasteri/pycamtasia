# Installation

## Requirements

- **Python 3.10+** (tested on 3.10, 3.11, 3.12, and 3.13)
- **Camtasia 2024+** (project format version 10)

pycamtasia is pure Python with a single runtime dependency (`jsonpatch`). No
compiler or binary build tools are needed.

## Install from PyPI

```bash
pip install pycamtasia
```

## Optional extras

pycamtasia ships two optional extras that pull in additional dependencies:

| Extra | Install command | What it enables |
|---|---|---|
| `cli` | `pip install pycamtasia[cli]` | The `pytsc` command-line interface for inspecting and validating projects from the terminal |
| `media` | `pip install pycamtasia[media]` | Media probing via `pymediainfo` — auto-detects duration, dimensions, and codec info when importing media |

Install both at once:

```bash
pip install pycamtasia[cli,media]
```

## Platform-specific notes

The `media` extra depends on `pymediainfo`, which requires a native MediaInfo
library. Install it for your platform:

**macOS**

```bash
brew install ffmpeg
```

**Ubuntu / Debian**

```bash
sudo apt install libmediainfo0v5
```

**Windows**

```bash
choco install mediainfo-cli
```

If you don't need media probing, skip the `media` extra entirely — the core
library works without it.

## WhisperX (optional)

For local speech-to-text transcription (used by the transcript and audio-video
sync features), install [WhisperX](https://github.com/m-bain/whisperX)
separately:

```bash
pip install whisperx
```

WhisperX is not a pycamtasia dependency — it runs independently and produces
transcript files that pycamtasia can consume.

## Verify the installation

```bash
python -c "import camtasia; print(camtasia.__version__)"
```

You should see the installed version number (e.g. `0.1.0`).

## Troubleshooting

### `ModuleNotFoundError: No module named 'camtasia'`

The package is installed as `pycamtasia` but imported as `camtasia`:

```bash
# Install
pip install pycamtasia

# Import
python -c "import camtasia"
```

If the error persists, check that you're using the same Python environment
where you ran `pip install`:

```bash
pip show pycamtasia
python -c "import sys; print(sys.executable)"
```

### `pymediainfo` cannot find the native library

If `pymediainfo` raises an `OSError` about a missing shared library, the
native MediaInfo library is not installed. See the
platform-specific notes above.

On macOS, `brew install ffmpeg` provides the libraries that `pymediainfo`
needs. On Linux, install `libmediainfo0v5` (or `libmediainfo-dev` on older
distributions). On Windows, `choco install mediainfo-cli` places the DLL on
your PATH.

## Next steps

- [Quick Start](quickstart.md) — load a project and make your first edit
- [Getting Started Tutorial](guides/getting-started.md) — build a complete
  project from scratch
