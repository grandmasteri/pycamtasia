# Changelog

All notable changes to pycamtasia are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased] — 2026-04-09

### Added
- Comprehensive library rewrite with full timeline manipulation support
- L2 convenience API for high-level project manipulation
- UnifiedMedia clip type for screen recordings with audio
- `is_screen_recording` and `is_camera` properties on UnifiedMedia
- Gain/mute API and audio clip attributes
- Glow effect, time-bounded effects, and StitchedMedia sourceEffect
- Text behaviors, animation tracks, and new callout shapes
- Full Camtasia v10 compatibility from integration test findings
- Sphinx documentation with GitHub Pages deployment
- Tutorial guides for key workflows
- L2 convenience API guide
- Camtasia Rev guide for working with screen recordings
- ROADMAP.md for planned features
- Comprehensive test suite with 788 tests at 100% coverage
- Integration tests with real project fixture
- GitHub Actions test workflow

### Fixed
- Probe audio/video duration with ffprobe for correct source range
- Rewrite fade animations to match Camtasia v10 format
- Preserve extreme float values and match Camtasia JSON formatting
- Update new project template to v10 format (Camtasia 2026)
- Clean polluted project template and add v10 timeline fields
- Strip punctuation in transcript phrase matching
- `plan_sync` now accepts Word objects instead of dicts
- Remove deprecated license classifier
- Correct license, readme path, unused imports, and test assertions

### Changed
- Upgrade test fixture B to v10 format
- Update workflow branches to main
- Opt into Node.js 24 for GitHub Actions
- Remove Codecov integration
- Fix coding standards violations in tests and source
- Replace legacy tests with self-contained modern tests
