# FAQ

## What is .tscproj vs .cmproj?

A `.tscproj` file is the JSON document that describes a Camtasia project — timeline, clips, effects, and source bin references. A `.cmproj` is a macOS *bundle directory* that contains the `.tscproj` file plus the actual media assets (recordings, images, audio). Think of `.tscproj` as the format and `.cmproj` as the container.

pycamtasia works with both: pass a `.cmproj` directory or a standalone `.tscproj` file to `load_project()`.

## What Python versions are supported?

Python 3.10 and later. The library uses modern syntax features like `match` statements, `X | Y` union types, and `Self` return annotations.

## Which Camtasia versions are supported?

Camtasia 2024 and later. The JSON schema is validated against 93 official TechSmith sample projects from Camtasia 2024+.

## Does this library render video?

No. pycamtasia reads and writes Camtasia project files (`.tscproj` / `.cmproj`). It does not encode, decode, or render video frames. To produce a final video, open the saved project in Camtasia and use its export/produce feature.

## What's the difference between Group and StitchedMedia?

Both are container clip types:

- **Group** represents a Camtasia "group" — multiple clips on internal sub-tracks that play simultaneously (like layers). Screen recordings are stored as Groups with video + cursor + audio sub-tracks.
- **StitchedMedia** represents clips that are joined end-to-end into a single logical clip. The sub-clips play sequentially, not simultaneously.

## How are timings represented internally?

Camtasia uses an `editRate` of **705,600,000 ticks per second**. This value is evenly divisible by common frame rates (24, 25, 30, 60 fps) and audio sample rates (44,100 and 48,000 Hz), avoiding rounding errors.

Convert between ticks and seconds:

```python
from camtasia.timing import seconds_to_ticks, ticks_to_seconds, EDIT_RATE

ticks = seconds_to_ticks(1.5)    # 1058400000
secs = ticks_to_seconds(ticks)   # 1.5
print(EDIT_RATE)                  # 705600000
```

## Can I use this with Camtasia Rev?

Yes. Camtasia Rev projects use the same `.tscproj` format. See the [Camtasia Rev guide](camtasia-rev.md) for details on Rev-specific features and workflows.

## Does this work on Windows?

The Python library itself is cross-platform — it runs on Windows, macOS, and Linux. However, the Camtasia integration tests (which open projects in the Camtasia application) are macOS-specific. The `.cmproj` bundle convention is also macOS-specific; on Windows, Camtasia uses standalone `.tscproj` files.

## Why is my .cmproj a directory?

On macOS, `.cmproj` files are [bundle directories](https://developer.apple.com/library/archive/documentation/CoreFoundation/Conceptual/CFBundles/BundleTypes/BundleTypes.html) — a Finder convention where a directory with a specific extension appears as a single file. Inside the bundle you'll find `project.tscproj` (the JSON project file) plus media assets. This is normal macOS behavior.

## How do I report a bug?

Open an issue on the project's issue tracker. Include:

1. Python version (`python --version`)
2. pycamtasia version (`python -c "import camtasia; print(camtasia.__version__)"`)
3. Minimal reproduction script
4. The error traceback
5. If possible, a minimal `.tscproj` file that triggers the issue
