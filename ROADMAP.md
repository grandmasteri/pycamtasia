# pycamtasia Roadmap

## Status

All action-level gaps from the Deep Tutorial Analysis are implemented (325 completed, 1 ongoing refinement). Library is feature-complete for the TechSmith tutorial corpus.

## Pending Bugs

_This section is the authoritative list of bugs reported by adversarial reviewers but not yet fixed. Add entries here immediately upon report. Mark `[verified]` or `[withdrawn: reason]` after verification. Remove entries after the fix is committed and CI is green._

(none currently)

## Pre-release audit findings (2026-05-01)

_Findings from the 17-agent review swarm. Each entry has a stable ID traceable back to the full details in `docs/development/reviews/<aspect>.jsonl`. Mark items as `[x] RESOLVED` when fixed, citing the commit hash._


### CRITICAL

- [x] **REV-ops_readiness-001** (ops_readiness) — Tests CI workflow is failing on main — all 3 most recent runs show 'failure' status. A red main branch means contributors cannot distinguish their own breakage from pre-existing failures, and the badge in README is misleading (it links to a failing workflow). This blocks any confidence in the release pipeline. `.github/workflows/tests.yml:?` (resolved in `9b4558b`)

### HIGH

- [ ] **REV-api_consistency-001** (api_consistency) — Project has both `duration_formatted` (MM:SS only) and `total_duration_formatted` (HH:MM:SS with fallback to M:SS). For durations under 1 hour they produce identical output; for longer durations `duration_formatted` silently produces misleading values like '90:00'. The naming gives no hint which to prefer, and the `total_` prefix is inconsistent with `duration_seconds` (no `total_` prefix). `src/camtasia/project.py:507`
- [ ] **REV-api_consistency-003** (api_consistency) — add_gradient_background is the only Project.add_* method that takes `track_index: int` instead of `track_name: str`. Every other add_* method (add_title_card, add_background_music, add_watermark, add_image_sequence, add_four_corner_gradient, etc.) uses track_name with get_or_create_track(). This makes the API fragile — track indices change when tracks are added or removed. `src/camtasia/project.py:1476`
- [ ] **REV-api_consistency-005** (api_consistency) — Color parameters use three incompatible representations across the API: (1) RGB float 3-tuple in add_title_card/add_subtitle_track/add_caption, (2) RGBA float 4-tuple in add_text_watermark, (3) RGBA int 0-255 4-tuple in Track.add_lower_third's title_color. A user copying a color value between methods will get silently wrong results. `src/camtasia/project.py:2699`
- [ ] **REV-api_consistency-006** (api_consistency) — Project.add_lower_third and Track.add_lower_third share the same method name but have incompatible signatures, different parameter names (title_text/subtitle_text vs title/subtitle), and different return types (BaseClip vs Group). They also produce completely different visual output — Project's version creates a simple callout, Track's version creates a template-based Group with accent lines. `src/camtasia/project.py:2270`
- [ ] **REV-api_consistency-008** (api_consistency) — add_voiceover_sequence and add_voiceover_sequence_v2 coexist as public API with different parameter names (vo_files vs audio_file_paths, pauses vs gap_seconds), different default track names ('Audio' vs 'Voiceover'), and different return types (dict[str, dict] vs list[BaseClip]). The _v2 suffix is an anti-pattern that signals an incomplete API migration. `src/camtasia/project.py:1693`
- [ ] **REV-api_docs-001** (api_docs) — The automodule directive targets `camtasia.media_bin` (the package __init__.py) which only re-exports class names (Media, MediaBin, MediaType). Autodoc does not traverse into the submodule `camtasia.media_bin.media_bin`, so most MediaBin methods (import_folder, import_many, find_by_type, delete_unused, sorted, next_id, add_media_entry, etc.) and most Media properties are invisible in the rendered HTML. The page renders only 1 mention of MediaBin and 0 occurrences of import_folder, find_by_type, delete_unused, or sorted. `docs/api/media_bin.rst:67`
- [ ] **REV-api_docs-002** (api_docs) — The operations.rst decision matrix references `camtasia.operations.media_ops` as the module for 'Add / remove media programmatically', but there is no `.. automodule:: camtasia.operations.media_ops` directive anywhere in the file. The module's two public functions (`add_media_to_track` and `remove_media`) are completely undocumented in the API reference despite being listed in the decision matrix. `docs/api/operations.rst:?`
- [ ] **REV-api_docs-003** (api_docs) — The 'Normalise audio speed' worked example uses `project._data` (a private attribute) to call `set_audio_speed(project._data, target_speed=1.0)`. This exposes internal implementation details in the public API reference and will break if the private attribute is renamed. Additionally, the example uses `camtasia.load_project(...)` without importing `camtasia` — only `from camtasia.operations.speed import set_audio_speed` is imported. The `from fractions import Fraction` import is also unused. `docs/api/operations.rst:55`
- [ ] **REV-concurrency-001** (concurrency) — (no description) `?:?`
- [ ] **REV-docstrings-001** (docstrings) — (no description) `?:?`
- [ ] **REV-edge_cases-001** (edge_cases) — FrameStamp accepts frame_rate=0 without validation. Any subsequent property access (frame_time, time, __str__) raises ZeroDivisionError via divmod(frame_number, 0). Negative frame_rate is also accepted and produces nonsensical results (negative timedelta components). The constructor should reject non-positive frame_rate values. `src/camtasia/frame_stamp.py:18`
- [ ] **REV-edge_cases-002** (edge_cases) — _lcm(0, n) returns 0 instead of raising an error. When FrameStamp._add uses this result, it computes common_frame_rate=0 then does common_frame_rate // frame_rate_1 which raises ZeroDivisionError. The root cause is _lcm not validating its inputs. Additionally, _lcm with negative inputs returns negative values, which is mathematically incorrect (LCM is always non-negative). `src/camtasia/frame_stamp.py:56`
- [ ] **REV-edge_cases-003** (edge_cases) — speed_to_scalar raises ZeroDivisionError for very small positive floats (e.g. 1e-10) instead of ValueError. The speed > 0 check passes, but Fraction(speed).limit_denominator(10_000) rounds to Fraction(0, 1), then Fraction(1,1) / Fraction(0,1) raises ZeroDivisionError. Any float speed < ~1e-4 triggers this. The error message 'Fraction(1, 0)' is confusing and doesn't indicate the actual problem. `src/camtasia/timing.py:100`
- [ ] **REV-edge_cases-007** (edge_cases) — Track.add_clip accepts zero and negative duration values without validation, producing clips that are invisible or have nonsensical timing. A zero-duration clip occupies no timeline space. A negative-duration clip produces invalid JSON. Negative start values are also accepted. While scalar is validated (must be positive), duration and start are not, creating an inconsistency in input validation. `src/camtasia/timeline/track.py:477`
- [ ] **REV-error_handling-001** (error_handling) — (no description) `?:?`
- [ ] **REV-error_handling-002** (error_handling) — (no description) `?:?`
- [ ] **REV-error_handling-003** (error_handling) — (no description) `?:?`
- [ ] **REV-error_handling-005** (error_handling) — (no description) `?:?`
- [ ] **REV-fuzz-001** (fuzz) — Project.__init__ accepts any JSON value without validating the structure. When timeline is a string instead of a dict, load_project succeeds but every subsequent operation (tracks iteration, save, validate) crashes with unhelpful TypeError('string indices must be integers'). No schema validation occurs at load time. `src/camtasia/project.py:192`
- [ ] **REV-fuzz-002** (fuzz) — An empty JSON object {} loads successfully via load_project. Accessing .timeline, calling .validate(), or .save() all crash with bare KeyError('timeline') — an unactionable error that doesn't indicate the project file is structurally invalid. Users processing untrusted .tscproj files get no guidance. `src/camtasia/project.py:192`
- [ ] **REV-fuzz-007** (fuzz) — validate() crashes with TypeError when internal data is corrupted (e.g. tracks=None). The crash occurs in all_clips which iterates timeline.tracks. Since validate()'s purpose is to detect structural problems, it should never crash on malformed data — it should report the problem as a ValidationIssue. `src/camtasia/project.py:901`
- [ ] **REV-fuzz-009** (fuzz) — A .tscproj missing the 'timeline' key loads successfully but crashes with bare KeyError('timeline') on any operation: .timeline, .validate(), .save(). The error message gives no indication that the project file is structurally invalid. This is the same root cause as REV-fuzz-002 but from a different malformation. `src/camtasia/project.py:370`
- [ ] **REV-ops_readiness-002** (ops_readiness) — The CI test workflow does not enforce the 100% coverage gate. The pytest command uses `--cov-report=xml --cov-report=term-missing` but does not pass `--cov-fail-under=100`. While pyproject.toml sets `fail_under = 100` under `[tool.coverage.report]`, this only takes effect if pytest-cov's report phase runs the coverage report check. Without an explicit `--cov-fail-under=100` flag, a coverage regression could slip through if the pyproject.toml config is not picked up correctly. `.github/workflows/tests.yml:22`
- [ ] **REV-packaging-004** (packaging) — (no description) `?:?`
- [ ] **REV-performance-001** (performance) — (no description) `?:?`
- [ ] **REV-performance-002** (performance) — (no description) `?:?`
- [ ] **REV-resources-001** (resource_management) — subprocess.Popen launched without storing the process handle or calling wait/terminate/kill. The Popen object is created at line 52 but never assigned to a variable, so there is no way to reap the child process. Cleanup relies entirely on a subsequent `pkill -f Camtasia` at line 65, which is unreliable (race conditions, permission errors). The Popen object also holds an open file descriptor to stderr_file. Compare with integration_helpers.py _launch_and_scan() which correctly calls proc.terminate(), proc.wait(timeout=5), and proc.kill() as a fallback. `src/camtasia/app_validation.py:52`
- [ ] **REV-resources-002** (resource_management) — Temporary log file created with NamedTemporaryFile(delete=False) is never cleaned up. Each call to camtasia_validate() creates a .log file in the system temp directory via tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) at line 48. The file is read at line 61 (log_path.read_text()) but log_path.unlink() is never called. Repeated integration test runs or programmatic validation calls will accumulate orphaned log files. `src/camtasia/app_validation.py:48`
- [ ] **REV-security-001** (security) — Zip-slip / untrusted path injection in import_libzip. The function reads entry filenames from manifest.json inside the zip archive and passes them to zf.read() without validating they are safe relative paths. More critically, asset_data['thumbnail'] is stored as a Path object verbatim from untrusted JSON, allowing an attacker to set thumbnail_path to any absolute filesystem path (e.g., /etc/passwd). Any downstream code that reads or displays the thumbnail would access arbitrary files. `src/camtasia/library/libzip.py:61`
- [ ] **REV-security-002** (security) — No size or depth limits on project JSON loading. Project.__init__ calls json.loads() on the entire .tscproj file contents with no file size check, no nesting depth limit, and no element count limit. A malicious .tscproj file could contain deeply nested structures (causing stack exhaustion), extremely large arrays (causing OOM), or multi-gigabyte JSON (causing memory exhaustion). Since the library is designed to process .cmproj files from potentially untrusted sources, this is a denial-of-service vector. `src/camtasia/project.py:192`
- [ ] **REV-security-003** (security) — save() follows symlinks blindly, and from_template()/new() call shutil.rmtree() on caller-controlled paths without safety checks. When a project is loaded from a symlinked .cmproj directory, save() follows the symlink and writes to the target. from_template() calls shutil.rmtree(dst) if dst.exists() before copytree — if output_path points to an important directory, it gets deleted. While these are API-level (not file-format-level) attacks, the library processes untrusted .cmproj bundles that could contain symlinks. `src/camtasia/project.py:714`
- [ ] **REV-test_gaps-001** (test_gaps) — The timing roundtrip (seconds_to_ticks then ticks_to_seconds and vice versa) is only tested with 4 parametrized values. A property-based test using Hypothesis would catch floating-point precision edge cases across the full domain (0 to 86400 seconds). Given that D-005 states ticks are the internal unit and precision matters for frame-aligned operations, this is a significant gap. `src/camtasia/timing.py:?`
- [ ] **REV-test_gaps-002** (test_gaps) — Timeline caption index boundary errors (IndexError at lines 1355, 1374, 1403, 1453) are completely untested. These are public API methods that users will call with invalid indices, and the error messages are the only feedback they get. No test verifies that out-of-range indices produce the expected IndexError. `src/camtasia/timeline/timeline.py:1355`
- [ ] **REV-test_gaps-003** (test_gaps) — The validation that at least one of left_clip_id or right_clip_id must be provided (line 136) is not tested. This is a public API guard that prevents creating orphan transitions, and the error path is completely uncovered. `src/camtasia/timeline/transitions.py:136`
- [ ] **REV-test_gaps-004** (test_gaps) — Two validation error paths in base.py are untested: (1) set_crop with negative values (line 1741, 'Crop {name} must be non-negative'), and (2) fit_to_duration with target_duration_seconds <= 0 (line 2678). These are public API methods with input validation that users depend on for clear error messages. `src/camtasia/timeline/clips/base.py:1741`
- [ ] **REV-test_gaps-007** (test_gaps) — Multiple Group clip error paths are untested: (1) line 98 'Internal Group tracks do not support transitions' — accessing transitions on internal tracks, (2) line 178 'Group clips do not have a source ID' — accessing source_id, (3) line 712 'No internal track with UnifiedMedia found' — set_speed_segments on a group without UnifiedMedia, (4) line 759 'segment src_end must be > src_start' — invalid segment range, (5) line 989 'Expected Library, got ...' — passing wrong type to save_to_library. `src/camtasia/timeline/clips/group.py:98`
- [ ] **REV-test_quality-001** (test_quality) — (no description) `?:?`
- [ ] **REV-test_quality-002** (test_quality) — (no description) `?:?`
- [ ] **REV-test_quality-003** (test_quality) — (no description) `?:?`
- [ ] **REV-test_quality-004** (test_quality) — (no description) `?:?`
- [ ] **REV-typing-001** (typing) — (no description) `?:?`
- [ ] **REV-typing-002** (typing) — (no description) `?:?`
- [ ] **REV-typing-003** (typing) — (no description) `?:?`
- [ ] **REV-typing-005** (typing) — (no description) `?:?`
- [ ] **REV-user_docs-001** (user_docs) — (no description) `?:?`
- [ ] **REV-user_docs-002** (user_docs) — (no description) `?:?`

### MEDIUM

- [ ] **REV-api_consistency-002** (api_consistency) — MediaType enum uses PascalCase member names (`Video`, `Image`, `Audio`) while every other enum in types.py uses UPPER_SNAKE_CASE (`AUDIO`, `VIDEO`, `IMAGE` in ClipType; `DROP_SHADOW` in EffectName; `CARD_FLIP` in TransitionType, etc.). This is the only enum that deviates from the project's naming convention. `src/camtasia/types.py:222`
- [ ] **REV-api_consistency-004** (api_consistency) — add_gradient_background returns `-> Any` instead of a concrete clip type. Similarly, import_and_convert_audio (line 2569) returns `-> Any`. All other add_*/import_* methods return specific types (BaseClip, Media, IMFile, etc.). The `Any` return type defeats type checking and IDE autocompletion. `src/camtasia/project.py:1477`
- [ ] **REV-api_consistency-007** (api_consistency) — find_media_by_suffix and find_media_by_extension (line 1466) are near-duplicates with subtly different behavior. find_media_by_suffix does a raw endswith() match (case-sensitive, no dot normalization). find_media_by_extension normalizes case and strips leading dots. Having both creates confusion about which to use and risks silent bugs from case sensitivity differences. `src/camtasia/project.py:1449`
- [ ] **REV-api_consistency-009** (api_consistency) — Track-not-found handling is inconsistent: remove_track_by_name returns False, mute_track returns False, solo_track returns False, but clone_track raises KeyError, swap_tracks raises KeyError, and move_all_clips_to_track raises KeyError. Methods with identical 'find track by name' semantics use different error signaling strategies. `src/camtasia/project.py:446`
- [ ] **REV-api_consistency-011** (api_consistency) — Track has duplicate property pairs for the same state: audio_muted/is_muted, video_hidden/is_hidden, solo/is_solo, magnetic/is_magnetic. The is_* variants are documented as aliases but double the API surface. Users must guess which to use, and both appear in IDE autocompletion. `src/camtasia/timeline/track.py:304`
- [ ] **REV-api_consistency-012** (api_consistency) — Project has six overlapping introspection methods with unclear boundaries: statistics() -> dict, info() -> dict, summary() -> str, describe() -> str, health_check() -> dict, health_report() -> str. The dict-returning methods (statistics vs info) overlap heavily — info() includes everything from statistics() plus a few extra fields. The string-returning methods (summary vs describe vs health_report) have no clear naming convention for their level of detail. `src/camtasia/project.py:1232`
- [ ] **REV-api_consistency-015** (api_consistency) — Batch operation naming is inconsistent: set_opacity_all, fade_all, scale_all, move_all use a verb_all pattern, but the underlying clip methods they call are inconsistent — set_opacity_all calls c.set_opacity(), scale_all calls c.scale_to(), move_all calls c.move_to(). The batch function names don't match the clip method names they delegate to. `src/camtasia/operations/batch.py:45`
- [ ] **REV-api_consistency-017** (api_consistency) — add_title_card uses positional args for text, start_seconds, duration_seconds (all required), while add_caption uses positional for text, start_seconds, duration_seconds then keyword-only (*) for track_name, font_size, font_color. Both methods have identical risk profiles and similar parameter counts, but different positional/keyword patterns. Per D-002, keyword-only should be used when there's configuration risk, but these two methods are inconsistent with each other despite being functionally similar. `src/camtasia/project.py:2032`
- [ ] **REV-api_consistency-020** (api_consistency) — Three validation methods exist with overlapping purposes: validate() returns list[ValidationIssue], validate_schema() returns list[ValidationIssue], and validate_and_report() returns str. The naming convention is inconsistent — validate_and_report suggests it does both validation AND reporting, but validate() alone also validates. validate_schema() is a separate validation pass with no way to combine results with validate(). `src/camtasia/project.py:940`
- [ ] **REV-api_docs-004** (api_docs) — Five public methods on VideoProductionBuilder lack docstrings: add_intro (line 44), add_section (line 59), add_outro (line 75), add_background_music (line 83), and add_watermark (line 91). Since autodoc is configured with `undoc-members: True` in the rst file, these methods appear in the rendered docs but with empty descriptions — users see the signature but no explanation of what the method does or what the parameters mean. `src/camtasia/builders/video_production.py:44`
- [ ] **REV-api_docs-005** (api_docs) — The `RGBA.to_hex()` method has no docstring. Every other public method on RGBA (from_hex, from_floats, red, green, blue, alpha, to_floats, as_tuple) has a docstring. Since conf.py sets `undoc-members: False` by default but the color.rst overrides with `:undoc-members:`, the method appears in docs without description. `src/camtasia/color.py:113`
- [ ] **REV-api_docs-006** (api_docs) — The second worked example ('Pack a track end-to-end') uses `camtasia.load_project(...)` without importing `camtasia`. Only `from camtasia.operations.layout import pack_track` is imported. The example would raise a NameError if copy-pasted and run. `docs/api/operations.rst:65`
- [ ] **REV-api_docs-007** (api_docs) — The media_bin.rst narrative text references `MediaBin.add_to_library` as a bridge to the Library, but the automodule directive (targeting the package __init__) does not render this method. Users reading the narrative are told about a method they cannot find in the autodoc output below. This is a consequence of REV-api_docs-001 but specifically misleading because the narrative explicitly calls out the method. `docs/api/media_bin.rst:?`
- [ ] **REV-api_docs-008** (api_docs) — The media_bin.rst does not document the `trec_probe` submodule (`camtasia.media_bin.trec_probe`), which contains the public function `probe_trec()` with a docstring. This function is used for probing .trec recording files and is part of the media import workflow, but users cannot discover it through the API reference. `docs/api/media_bin.rst:?`
- [ ] **REV-concurrency-004** (concurrency) — (no description) `?:?`
- [ ] **REV-concurrency-005** (concurrency) — (no description) `?:?`
- [ ] **REV-docstrings-002** (docstrings) — (no description) `?:?`
- [ ] **REV-docstrings-003** (docstrings) — (no description) `?:?`
- [ ] **REV-docstrings-005** (docstrings) — (no description) `?:?`
- [ ] **REV-docstrings-006** (docstrings) — (no description) `?:?`
- [ ] **REV-docstrings-012** (docstrings) — (no description) `?:?`
- [ ] **REV-docstrings-013** (docstrings) — (no description) `?:?`
- [ ] **REV-docstrings-015** (docstrings) — (no description) `?:?`
- [ ] **REV-docstrings-017** (docstrings) — (no description) `?:?`
- [ ] **REV-docstrings-020** (docstrings) — (no description) `?:?`
- [ ] **REV-edge_cases-004** (edge_cases) — RGBA.from_floats raises OverflowError for inf and ValueError for NaN inputs instead of clamping or providing a clear error. The _clamp helper does max(0, min(255, round(channel * 255))), but round(inf * 255) overflows before the clamp can take effect. Since from_floats is documented as accepting 0.0-1.0 floats, out-of-range values > 1.0 are already clamped, but inf/NaN bypass the clamp. `src/camtasia/color.py:50`
- [ ] **REV-edge_cases-005** (edge_cases) — TransitionList.add and all convenience methods (add_dissolve, add_fade_through_black, etc.) accept zero and negative duration_ticks without validation. A zero-duration transition is meaningless, and a negative-duration transition produces invalid project JSON that Camtasia cannot load. The same clip ID can also be used for both left and right sides of a transition (self-transition), which is nonsensical. `src/camtasia/timeline/transitions.py:107`
- [ ] **REV-edge_cases-006** (edge_cases) — MarkerList.add accepts negative time_ticks, empty string names, and names containing null bytes without any validation. Negative-time markers produce invalid project JSON. Empty-name markers are invisible in Camtasia's UI. Null bytes in marker names may cause issues with JSON serialization or Camtasia's parser. The move() method also allows moving markers to negative times. `src/camtasia/timeline/markers.py:68`
- [ ] **REV-edge_cases-008** (edge_cases) — extend_dynamic_caption accepts zero and negative new_duration_seconds without validation. Zero duration collapses all word timings to 0.0 and sets clip duration to 0 ticks. Negative duration produces negative word timings and negative tick durations, creating deeply invalid project state. NaN crashes with an unhelpful ValueError from seconds_to_ticks. The function should validate new_duration_seconds > 0. `src/camtasia/timeline/captions.py:349`
- [ ] **REV-error_handling-004** (error_handling) — (no description) `?:?`
- [ ] **REV-error_handling-007** (error_handling) — (no description) `?:?`
- [ ] **REV-error_handling-010** (error_handling) — (no description) `?:?`
- [ ] **REV-error_handling-012** (error_handling) — (no description) `?:?`
- [ ] **REV-error_handling-014** (error_handling) — (no description) `?:?`
- [ ] **REV-fuzz-003** (fuzz) — A project with ~500 levels of JSON nesting loads successfully but crashes in save() with RecursionError. The crash occurs in copy.deepcopy() which save() calls to avoid mutating the live data. This is a denial-of-service vector: a malicious .tscproj can be loaded but never saved, breaking any load-modify-save pipeline. `src/camtasia/project.py:1000`
- [ ] **REV-fuzz-004** (fuzz) — When a .tscproj contains NaN in a numeric field (e.g. width), save() silently replaces NaN with 0.0. This changes project dimensions from NaN to 0×0 — a lossy transformation. While a warning is emitted, the save proceeds and the original value is permanently lost. A project that was merely 'odd' becomes 'broken'. `src/camtasia/project.py:1020`
- [ ] **REV-fuzz-005** (fuzz) — Track.add_clip() accepts negative duration, negative start, and zero duration without raising an error. Negative-duration clips create invalid project state that Camtasia cannot render. While validate() warns about these, the D-003 design decision says validation is advisory — so users who don't call validate() will silently produce corrupt projects. `src/camtasia/timeline/track.py:477`
- [ ] **REV-license_compliance-004** (license_compliance) — (no description) `src/camtasia/**/*.py`
- [ ] **REV-license_compliance-005** (license_compliance) — (no description) `tests/fixtures/techsmith_*.tscproj`
- [ ] **REV-license_compliance-006** (license_compliance) — (no description) `src/camtasia/resources/new.cmproj/`
- [ ] **REV-ops_readiness-003** (ops_readiness) — The docs deploy workflow sets the environment URL to `${{ github.event.repository.html_url }}` which resolves to the GitHub repository URL (e.g., https://github.com/grandmasteri/pycamtasia), not the actual GitHub Pages URL (https://grandmasteri.github.io/pycamtasia/). This means the 'View deployment' link in the GitHub Actions UI points to the repo instead of the deployed docs site. `.github/workflows/docs.yml:47`
- [ ] **REV-ops_readiness-004** (ops_readiness) — The Coverage badge is a static shield.io badge hardcoded to '100%' (`https://img.shields.io/badge/coverage-100%25-brightgreen`). It does not reflect actual coverage from CI. If coverage drops, the badge will still show 100%. Other projects use Codecov or Coveralls to generate dynamic badges from CI coverage reports. `README.md:5`
- [ ] **REV-ops_readiness-005** (ops_readiness) — The tests workflow does not upload coverage artifacts or cache pip dependencies. Each matrix run (4 Python versions) re-downloads and installs all dependencies from scratch. Adding pip caching would reduce CI time. Additionally, the coverage XML report is generated but never uploaded as an artifact or to a coverage service, making it impossible to track coverage trends over time. `.github/workflows/tests.yml:?`
- [ ] **REV-ops_readiness-008** (ops_readiness) — The publishing guide documents a manual pre-release checklist that includes running integration tests, but there is no CI workflow or GitHub Action that automates any part of the pre-release verification beyond the basic tests.yml. The release.yml workflow triggers on tag push and builds+publishes, but does not run tests first. A maintainer could tag and push a broken commit, and the release would proceed to PyPI without any test gate. `docs/development/publishing.md:?`
- [ ] **REV-ops_readiness-013** (ops_readiness) — The coverage configuration in pyproject.toml omits 5 source files from coverage measurement: cli.py, frame_stamp.py, effects.py, track_media.py, and trec_probe.py. While the project claims '100% line coverage', these omissions mean the actual coverage is less than 100% of the codebase. The omitted files could contain untested bugs. This is not documented in CONTRIBUTING.md or the README's coverage claims. `pyproject.toml:?`
- [ ] **REV-packaging-001** (packaging) — (no description) `?:?`
- [ ] **REV-packaging-002** (packaging) — (no description) `?:?`
- [ ] **REV-packaging-007** (packaging) — (no description) `?:?`
- [ ] **REV-performance-003** (performance) — (no description) `?:?`
- [ ] **REV-performance-004** (performance) — (no description) `?:?`
- [ ] **REV-performance-005** (performance) — (no description) `?:?`
- [ ] **REV-performance-007** (performance) — (no description) `?:?`
- [ ] **REV-performance-009** (performance) — (no description) `?:?`
- [ ] **REV-resources-003** (resource_management) — Widespread use of tempfile.mkdtemp() without cleanup across ~30 test locations in 13 test files. Each call creates a temporary directory containing a .cmproj bundle (with subdirectories and files) that is never removed. Affected files include test_caption_accessibility.py (5), test_themes.py (5), test_invariants_property.py (4), test_themes_extended.py (3), test_captions_export.py (2), test_timeline_operations.py (2), and 7 more. Many other tests in the same project correctly use pytest's tmp_path fixture, which auto-cleans. `tests/test_caption_accessibility.py:20`
- [ ] **REV-resources-004** (resource_management) — Intermediate WAV file created by convert_audio_to_wav() is never cleaned up after import. import_and_convert_audio() calls convert_audio_to_wav() which creates a .wav file adjacent to the input file (input_p.with_suffix('.wav')), then imports it. The WAV file persists on disk after import. For a 10-minute MP3 at 48kHz/16-bit, the WAV file is ~110MB. Users calling this method in a loop (e.g., batch importing a podcast series) will accumulate large intermediate files. `src/camtasia/project.py:2592`
- [ ] **REV-resources-005** (resource_management) — Converted media file created by _validate_media_format(auto_convert=True) is never cleaned up. When auto_convert=True and a format mismatch is detected, ffmpeg creates a file at file_path.with_suffix(f'.converted{ext}') (e.g., 'video.converted.mp4'). This file is returned and presumably used by the caller, but there is no mechanism to clean it up afterward. The original file also remains. `src/camtasia/media_bin/media_bin.py:677`
- [ ] **REV-resources-006** (resource_management) — save() creates a full deep copy of the entire project data dict for JSON serialization. For large projects (the .tscproj JSON can be 10-50MB+), this temporarily doubles memory usage. The deep copy at line 1002 (save_data = copy.deepcopy(self._data)) plus the subsequent json.dumps() string representation means peak memory during save is roughly 3x the project data size (original dict + deep copy + serialized string). `src/camtasia/project.py:1002`
- [ ] **REV-security-004** (security) — Subprocess calls pass user-controlled file paths without flag-injection protection. Multiple functions (ffprobe, ffmpeg calls in media_bin.py and project.py) pass file paths via str(file_path) as the last argument to subprocess.run() in list form. While list-form prevents shell injection, a filename starting with '-' (e.g., '-version.mp4') could be interpreted as a command-line flag by ffprobe/ffmpeg. The timeout=10 mitigates some abuse but doesn't prevent flag interpretation. `src/camtasia/media_bin/media_bin.py:609`
- [ ] **REV-security-005** (security) — Media.source property returns unsanitized paths from project JSON. The 'src' field in sourceBin entries is read directly from the .tscproj JSON and returned as a Path object. A malicious .tscproj could set src to '../../etc/passwd' or '/etc/shadow'. Any code that reads or copies files based on Media.source would access arbitrary filesystem locations. The import_media method properly constructs relative paths, but loading an existing project trusts whatever is in the JSON. `src/camtasia/media_bin/media_bin.py:44`
- [ ] **REV-test_gaps-006** (test_gaps) — The 'Unsupported media stream type' ValueError (line 730) is never triggered by any test. This error path handles the case where pymediainfo returns a stream type that isn't 'video' or 'audio' (e.g., 'subtitle', 'data'). Without a test, a regression could silently swallow unknown stream types. `src/camtasia/media_bin/media_bin.py:730`
- [ ] **REV-test_gaps-008** (test_gaps) — Two Library error paths are untested: (1) line 247 RuntimeError('No libraries exist') when accessing .default on empty Libraries, and (2) line 267 KeyError('Library not found') when accessing a non-existent library by name. These are the primary error feedback for library users. `src/camtasia/library/library.py:247`
- [ ] **REV-test_gaps-010** (test_gaps) — No end-to-end test creates a complex project with multiple features (tracks, clips, markers, captions, effects), saves it, reloads from disk, and validates the reloaded project. Individual features are tested in isolation, but the combined roundtrip is not. This matters because save() formatting, JSON serialization edge cases, and cross-feature interactions could produce valid-looking but semantically broken files. `tests/:?`
- [ ] **REV-test_gaps-011** (test_gaps) — The TypeError guards on set_source for ScreenVMFile (line 36, 'Cannot change source on screen recording video clips') and ScreenIMFile (line 234, 'Cannot change source on cursor overlay clips') are not tested. These are important API contract guards — screen recordings are immutable sources. `src/camtasia/timeline/clips/screen_recording.py:36`
- [ ] **REV-test_gaps-012** (test_gaps) — Callout.source_id raises TypeError('Callout clips do not have a source ID') but no test verifies this. This is a type-system contract — callouts are generated content, not media-bin references. `src/camtasia/timeline/clips/callout.py:103`
- [ ] **REV-test_quality-005** (test_quality) — (no description) `?:?`
- [ ] **REV-test_quality-006** (test_quality) — (no description) `?:?`
- [ ] **REV-test_quality-007** (test_quality) — (no description) `?:?`
- [ ] **REV-test_quality-008** (test_quality) — (no description) `?:?`
- [ ] **REV-test_quality-009** (test_quality) — (no description) `?:?`
- [ ] **REV-test_quality-010** (test_quality) — (no description) `?:?`
- [ ] **REV-test_quality-011** (test_quality) — (no description) `?:?`
- [ ] **REV-test_quality-012** (test_quality) — (no description) `?:?`
- [ ] **REV-test_quality-013** (test_quality) — (no description) `?:?`
- [ ] **REV-test_quality-014** (test_quality) — (no description) `?:?`
- [ ] **REV-typing-006** (typing) — (no description) `?:?`
- [ ] **REV-typing-007** (typing) — (no description) `?:?`
- [ ] **REV-typing-008** (typing) — (no description) `?:?`
- [ ] **REV-typing-009** (typing) — (no description) `?:?`
- [ ] **REV-typing-010** (typing) — (no description) `?:?`
- [ ] **REV-user_docs-003** (user_docs) — (no description) `?:?`
- [ ] **REV-user_docs-004** (user_docs) — (no description) `?:?`
- [ ] **REV-user_docs-005** (user_docs) — (no description) `?:?`
- [ ] **REV-user_docs-012** (user_docs) — (no description) `?:?`
- [ ] **REV-user_docs-013** (user_docs) — (no description) `?:?`
- [ ] **REV-user_docs-014** (user_docs) — (no description) `?:?`
- [ ] **REV-user_docs-018** (user_docs) — (no description) `?:?`
- [ ] **REV-user_docs-020** (user_docs) — (no description) `?:?`
- [ ] **REV-user_docs-022** (user_docs) — (no description) `?:?`

### LOW

- [ ] **REV-api_consistency-010** (api_consistency) — Project.duration_seconds is a property that delegates to self.total_duration_seconds(), which is a regular method. Having both a property and a method that return the same value is redundant and confusing. The property shadows the method in typical usage, making the method appear unnecessary. `src/camtasia/project.py:503`
- [ ] **REV-api_consistency-013** (api_consistency) — Project.remove_orphaned_media() returns int (count), but the underlying operations.cleanup.remove_orphaned_media() returns list[int] (list of removed IDs). The Project method wraps with len(), discarding useful information. Other removal methods like remove_all_effects() and strip_audio() also return int counts, so the pattern is consistent at the Project level, but the information loss is unnecessary. `src/camtasia/project.py:2801`
- [ ] **REV-api_consistency-014** (api_consistency) — Project has three diff methods with confusing naming: diff(other) returns a simple dict of changed fields, diff_from(other) returns RFC 6902 JSON Patch operations, and diff_summary(other) returns a human-readable string. The names don't convey the output format — 'diff' vs 'diff_from' suggests a directionality difference, not a format difference. `src/camtasia/project.py:1319`
- [ ] **REV-api_consistency-016** (api_consistency) — Track.add_callout uses font_size default of 96.0, but Project.add_title_card uses 72.0, add_subtitle_track uses 36.0, add_callout_sequence uses 24.0, and add_section_divider uses 48.0. While different defaults for different use cases is reasonable, the base add_callout default of 96.0 is unusually large and inconsistent with the most common use case (subtitles/captions at 36.0). `src/camtasia/project.py:794`
- [ ] **REV-api_consistency-019** (api_consistency) — add_section_divider uses `at_seconds` as its time parameter, while every other method in the codebase uses `start_seconds`. This is the only method with the `at_` prefix for a time parameter. `src/camtasia/project.py:2310`
- [ ] **REV-api_docs-009** (api_docs) — The frame_stamp.rst, authoring_client.rst, app_validation.rst, extras.rst, themes.rst, color.rst, history.rst, validation.rst, and screenplay.rst pages are bare stubs with only a title and automodule directive — no narrative introduction, no usage examples, no seealso links. While the autodoc output provides the raw API, users have no context for when or why to use these modules. Compare with the rich narrative in project.rst, timeline.rst, clips.rst, effects.rst, etc. `docs/api/frame_stamp.rst:?`
- [ ] **REV-api_docs-010** (api_docs) — The design-decisions.md and integration-findings-2026-05-01.md files generate Sphinx warnings because they are not included in any toctree. While these are development-internal documents, the warnings pollute the build output and could mask real issues. `docs/development/design-decisions.md:?`
- [ ] **REV-api_docs-011** (api_docs) — The clips.rst clip type table lists 10 clip types but the `__init__.py` of `camtasia.timeline.clips` also exports `clip_from_dict` factory function. The table does not mention `GroupTrack` which is exported from `camtasia.timeline.__init__` and is a distinct type used for tracks within Group clips. Users looking for GroupTrack in the clips documentation won't find it. `docs/api/clips.rst:?`
- [ ] **REV-api_docs-012** (api_docs) — The annotations.rst narrative mentions 'Favourite annotations can be saved and loaded for reuse across projects' but does not reference any specific function or class for this feature. The `annotations/__init__.py` exports `AnnotationFavorites` and `save_annotation_favorite` but these are not called out in the narrative or linked with cross-references. `docs/api/annotations.rst:?`
- [ ] **REV-api_docs-013** (api_docs) — The effects.rst narrative references `:class:`~camtasia.effects.cursor.CursorSmoothing`` and 'click visualisations' but does not mention the 24+ click effect classes (LeftClickBurst1-4, LeftClickRings, LeftClickRipple, etc.) that are exported from `camtasia.effects.__init__`. Users reading the narrative get no hint that these exist. The automodule for `camtasia.effects.cursor` will render them, but the narrative overview is incomplete. `docs/api/effects.rst:?`
- [ ] **REV-api_docs-018** (api_docs) — The export.rst format support matrix lists 11 formats but omits several exported functions: `export_captions_as_srt` (alias), `export_captions` (generic), `import_captions_srt`, `import_captions` (generic), `export_captions_multilang`, `export_multilang_package`, `export_burned_in_captions_stub`, `export_audio_clips`, and `load_timeline_json`. Users who want these functions must discover them by reading the autodoc output rather than the decision matrix. `docs/api/export.rst:?`
- [ ] **REV-concurrency-006** (concurrency) — (no description) `?:?`
- [ ] **REV-docstrings-004** (docstrings) — (no description) `?:?`
- [ ] **REV-docstrings-007** (docstrings) — (no description) `?:?`
- [ ] **REV-docstrings-008** (docstrings) — (no description) `?:?`
- [ ] **REV-docstrings-009** (docstrings) — (no description) `?:?`
- [ ] **REV-docstrings-010** (docstrings) — (no description) `?:?`
- [ ] **REV-docstrings-011** (docstrings) — (no description) `?:?`
- [ ] **REV-docstrings-014** (docstrings) — (no description) `?:?`
- [ ] **REV-docstrings-018** (docstrings) — (no description) `?:?`
- [ ] **REV-docstrings-019** (docstrings) — (no description) `?:?`
- [ ] **REV-docstrings-021** (docstrings) — (no description) `?:?`
- [ ] **REV-docstrings-022** (docstrings) — (no description) `?:?`
- [ ] **REV-edge_cases-009** (edge_cases) — save_dynamic_caption_preset accepts an empty string as the preset name, creating a hidden file '.json' in the presets directory. While path traversal is blocked by the OS (parent dirs must exist), the empty name case silently creates a file that is invisible in directory listings on Unix systems and cannot be loaded by name. `src/camtasia/timeline/captions.py:296`
- [ ] **REV-edge_cases-010** (edge_cases) — seconds_to_ticks raises OverflowError for inf and ValueError for NaN with unhelpful error messages ('cannot convert float infinity to integer', 'cannot convert float NaN to integer'). Since seconds_to_ticks is called throughout the codebase as the primary conversion function, these errors propagate up as confusing low-level Python errors rather than domain-specific messages. This affects all public APIs that accept seconds parameters. `src/camtasia/timing.py:14`
- [ ] **REV-edge_cases-011** (edge_cases) — parse_scalar(1e-15) silently returns Fraction(0, 1) due to limit_denominator(10_000) rounding. While documented in the docstring ('For float inputs, the result is constrained with limit_denominator(10_000)'), this silent loss of precision can surprise callers. A float like 0.00001 (1e-5) also rounds to 0. Combined with speed_to_scalar, this creates a ZeroDivisionError chain (REV-edge_cases-003). `src/camtasia/timing.py:78`
- [ ] **REV-error_handling-008** (error_handling) — (no description) `?:?`
- [ ] **REV-error_handling-009** (error_handling) — (no description) `?:?`
- [ ] **REV-error_handling-011** (error_handling) — (no description) `?:?`
- [ ] **REV-error_handling-013** (error_handling) — (no description) `?:?`
- [ ] **REV-error_handling-015** (error_handling) — (no description) `?:?`
- [ ] **REV-error_handling-016** (error_handling) — (no description) `?:?`
- [ ] **REV-fuzz-006** (fuzz) — speed_to_scalar(float('inf')) raises OverflowError from Fraction internals instead of ValueError. The function validates zero and negative but not inf. Callers catching ValueError (the documented exception type) will miss this. parse_scalar has the same issue with both inf and -inf. `src/camtasia/timing.py:131`
- [ ] **REV-fuzz-008** (fuzz) — A .tscproj with negative trackIndex values (e.g. -1) loads without error. The negative index creates a track that has no corresponding entry in trackAttributes, which could cause IndexError in operations that correlate tracks with attributes. validate() does flag this, but load accepts it silently. `src/camtasia/timeline/timeline.py:1670`
- [ ] **REV-fuzz-010** (fuzz) — parse_scalar(float('inf')) and parse_scalar(float('-inf')) raise OverflowError from Fraction internals. The function handles NaN (via Fraction raising ValueError) and zero-denominator strings, but inf floats leak an implementation-specific OverflowError that callers won't expect. `src/camtasia/timing.py:92`
- [ ] **REV-license_compliance-003** (license_compliance) — (no description) `pyproject.toml:[project.optional-dependencies].docs`
- [ ] **REV-license_compliance-007** (license_compliance) — (no description) `src/camtasia/resources/camtasia-project-schema.json`
- [ ] **REV-license_compliance-008** (license_compliance) — (no description) `pyproject.toml`
- [ ] **REV-ops_readiness-006** (ops_readiness) — SUPPORT.md links the 'Docs site' to the GitHub tree URL (`https://github.com/grandmasteri/pycamtasia/tree/main/docs`) instead of the deployed documentation site (`https://grandmasteri.github.io/pycamtasia/`). Users looking for rendered documentation will land on raw markdown/RST files in the repo instead of the Sphinx-built site. `SUPPORT.md:4`
- [ ] **REV-ops_readiness-007** (ops_readiness) — The issue template config.yml also links documentation to the GitHub tree URL rather than the deployed docs site. The contact_links section sends users to `https://github.com/grandmasteri/pycamtasia/tree/main/docs` instead of the rendered Sphinx site. `SUPPORT.md:4`
- [ ] **REV-ops_readiness-009** (ops_readiness) — CONTRIBUTING.md documents `cd docs && sphinx-build -b html . _build/html -W` for building docs, but the CI docs workflow uses `sphinx-build docs docs/_build/html` (without -W and from the repo root). The -W flag treats warnings as errors. The discrepancy means a contributor could have a clean local docs build but CI could pass with warnings, or vice versa. The commands should be consistent. `CONTRIBUTING.md:?`
- [ ] **REV-ops_readiness-010** (ops_readiness) — The tests workflow does not run the examples test suite (`examples/test_examples.py`). The pytest command targets `tests/` only, but there is a separate test file in `examples/` that validates the example scripts. A broken example would not be caught by CI. `.github/workflows/tests.yml:?`
- [ ] **REV-packaging-003** (packaging) — (no description) `?:?`
- [ ] **REV-packaging-005** (packaging) — (no description) `?:?`
- [ ] **REV-packaging-006** (packaging) — (no description) `?:?`
- [ ] **REV-packaging-010** (packaging) — (no description) `?:?`
- [ ] **REV-packaging-011** (packaging) — (no description) `?:?`
- [ ] **REV-performance-006** (performance) — (no description) `?:?`
- [ ] **REV-performance-008** (performance) — (no description) `?:?`
- [ ] **REV-performance-010** (performance) — (no description) `?:?`
- [ ] **REV-performance-011** (performance) — (no description) `?:?`
- [ ] **REV-resources-009** (resource_management) — Integration test log files at /tmp/cam_test_*.log are cleaned up on success (line 64: log.unlink(missing_ok=True)) but the filelock at /tmp/pycamtasia_integration.lock is never cleaned up. The lock file persists across test runs. While filelock handles stale locks gracefully, the file accumulates on disk. This is a very minor issue since it's a single small file. `tests/integration_helpers.py:56`
- [ ] **REV-security-008** (security) — Template import reads and parses JSON from zip archives without size limits. _read_template() and import_libzip() read JSON files from zip archives using zf.read() which loads the entire file into memory. A malicious .camtemplate or .libzip could contain a zip bomb — a small compressed file that expands to gigabytes when decompressed. The json.loads() call would then attempt to parse the decompressed data, causing OOM. `src/camtasia/operations/template.py:270`
- [ ] **REV-test_quality-015** (test_quality) — (no description) `?:?`
- [ ] **REV-test_quality-018** (test_quality) — (no description) `?:?`
- [ ] **REV-test_quality-019** (test_quality) — (no description) `?:?`
- [ ] **REV-test_quality-021** (test_quality) — (no description) `?:?`
- [ ] **REV-typing-011** (typing) — (no description) `?:?`
- [ ] **REV-typing-012** (typing) — (no description) `?:?`
- [ ] **REV-user_docs-006** (user_docs) — (no description) `?:?`
- [ ] **REV-user_docs-007** (user_docs) — (no description) `?:?`
- [ ] **REV-user_docs-009** (user_docs) — (no description) `?:?`
- [ ] **REV-user_docs-010** (user_docs) — (no description) `?:?`
- [ ] **REV-user_docs-011** (user_docs) — (no description) `?:?`
- [ ] **REV-user_docs-015** (user_docs) — (no description) `?:?`
- [ ] **REV-user_docs-017** (user_docs) — (no description) `?:?`
- [ ] **REV-user_docs-021** (user_docs) — (no description) `?:?`

### INFO

- [ ] **REV-api_consistency-018** (api_consistency) — add_section_divider has a side effect of adding a timeline marker, which is not indicated by its name or documented prominently. No other add_* method on Project has this dual behavior. This violates the principle of least surprise — a method named add_section_divider should only add a visual divider, not also modify the marker list. `src/camtasia/project.py:2310`
- [ ] **REV-api_docs-014** (api_docs) — The `camtasia.annotations.types` module defines a `Color` dataclass (RGBA with float components 0.0-1.0) that overlaps conceptually with `camtasia.color.RGBA` (integer components 0-255). Neither the annotations.rst nor the color.rst page explains the relationship or when to use which. This could confuse users who encounter both in the API reference. `docs/api/annotations.rst:?`
- [ ] **REV-api_docs-015** (api_docs) — The `EffectSchema` class in `camtasia.effects.__init__` is a public class (no underscore prefix) that raises RuntimeError on instantiation. It exists for backward compatibility with marshmallow-based serialization. It is not documented in the API reference because effects.rst uses per-submodule automodule directives and does not include `.. automodule:: camtasia.effects`. Users who discover it via `dir(camtasia.effects)` will find an undocumented class. `docs/api/effects.rst:?`
- [ ] **REV-api_docs-016** (api_docs) — The builders.rst selection guide table lists 'Add a dynamic / Lottie background' pointing to `:func:`~camtasia.builders.add_dynamic_background`` but the module also exports `add_lottie_background` as a separate function. The table implies `add_dynamic_background` handles both, but users looking for Lottie-specific functionality may not realize there's a dedicated function. `docs/api/builders.rst:?`
- [ ] **REV-api_docs-017** (api_docs) — The global autodoc_default_options sets `undoc-members: False` but most API rst files override this with `:undoc-members:` in their automodule directives. This creates an inconsistency: the global default suggests undocumented members should be hidden, but the per-file overrides show them. The intent appears to be showing all public members, so the global default is misleading. `docs/conf.py:30`
- [ ] **REV-edge_cases-013** (edge_cases) — CaptionAttributes.active_word_at returns the last word when time_seconds equals clip_duration_seconds exactly (boundary case). At time=5.0 with duration=5.0 and words=['a','b'], index = int(5.0 / 2.5) = 2, then min(2, 1) = 1, returning 'b'. This is correct behavior (inclusive end boundary), but the docstring says 'None if time_seconds is out of range' without specifying whether the end boundary is inclusive or exclusive. The check `time_seconds > clip_duration_seconds` makes it inclusive. `src/camtasia/timeline/captions.py:230`
- [ ] **REV-license_compliance-001** (license_compliance) — (no description) `LICENSE`
- [ ] **REV-license_compliance-002** (license_compliance) — (no description) `pyproject.toml`
- [ ] **REV-ops_readiness-011** (ops_readiness) — CHANGELOG.md follows Keep a Changelog format correctly. It has an `[Unreleased]` section (currently empty), the `[0.1.0]` entry is dated `2026-04-30`, and comparison links are present at the bottom. The format is compliant with keepachangelog.com/en/1.1.0/. No issues found. `CHANGELOG.md:?`
- [ ] **REV-ops_readiness-012** (ops_readiness) — Dependabot configuration covers both `pip` and `github-actions` ecosystems with weekly Monday schedules, appropriate PR limits (5 each), and conventional commit prefixes (`deps` for pip, `ci` for actions). This is well-configured for an open-source Python project. No issues found. `.github/dependabot.yml:?`
- [ ] **REV-packaging-008** (packaging) — (no description) `?:?`
- [ ] **REV-packaging-009** (packaging) — (no description) `?:?`
- [ ] **REV-packaging-012** (packaging) — (no description) `?:?`
- [ ] **REV-resources-010** (resource_management) — Entire project JSON file is loaded into memory at once via read_text() + json.loads(). This is the standard approach for JSON processing in Python and is appropriate for typical Camtasia projects (1-50MB). Note: REV-security-002 in the security review already covers the denial-of-service aspect of unbounded JSON loading. This finding is informational — for the typical use case, full-file loading is the correct approach. Streaming JSON parsing (ijson) would add complexity without benefit for normal project sizes. Per design-decisions.md D-003, the library prioritizes flexibility over strict validation. `src/camtasia/project.py:192`
- [ ] **REV-resources-011** (resource_management) — track_changes() context manager creates a full deep copy of the project data as a snapshot before each tracked change. For large projects, this is a significant memory allocation. Combined with the deep copy in save() and the JSON patch storage in ChangeHistory, a single edit-then-save cycle can temporarily hold 4x the project data in memory (original + snapshot + save deep copy + serialized string). `src/camtasia/project.py:147`
- [ ] **REV-test_gaps-018** (test_gaps) — The CLI module (camtasia.cli) is excluded from coverage reporting entirely — it doesn't appear in the coverage output. While CLI testing is harder (requires docopt_subcommands), the error handling paths (ExitCodeError wrapping at lines 73, 89, 138) and the _check_cli_deps fallback are completely untested. Per D-007, lazy imports are intentional, but the error paths still deserve tests. `src/camtasia/cli.py:?`
- [ ] **REV-test_quality-022** (test_quality) — (no description) `?:?`
- [ ] **REV-typing-013** (typing) — (no description) `?:?`
- [ ] **REV-user_docs-024** (user_docs) — (no description) `?:?`

## TechSmith Tutorial Analysis

Review each official Camtasia tutorial to extract insights about features pycamtasia should support.

> **Source pages:**
> - https://www.techsmith.com/learn/tutorials/camtasia
> - https://www.techsmith.com/learn/projects/

### Getting Started (5)

- [not-applicable] [What's New in Camtasia Editor](https://www.techsmith.com/learn/tutorials/camtasia/whats-new-camtasia/) — Camtasia desktop app release notes; not relevant to file manipulation
- [already-implemented] [Build Your First Video](https://www.techsmith.com/learn/tutorials/camtasia/record-edit-share/) — TimelineBuilder, build_from_screenplay, import_media, track/clip APIs cover the building blocks
- [already-implemented] [Basic Edits After Recording](https://www.techsmith.com/learn/tutorials/camtasia/basic-video-edits/) — trim/split/reorder via timeline/clips/base.py; ripple_insert/delete in operations/layout.py
- [not-applicable] [Introduction to Camtasia Recorder](https://www.techsmith.com/learn/tutorials/camtasia/camtasia-recorder/) — Screen recording is OS-level capture, not .cmproj manipulation
- [not-applicable] [Export & Share Your Video](https://www.techsmith.com/learn/tutorials/camtasia/export-share/) — Video encoding/rendering requires the Camtasia engine; pycamtasia exports metadata only (EDL/CSV/SRT/JSON/report)

### Common Ways to Make a Video (9)

- [already-implemented] [Edit Zoom Recordings](https://www.techsmith.com/learn/tutorials/camtasia/edit-zoom-recording/) — Generic video import/edit covers all non-Zoom-specific cases; no Zoom-UI specific features apply to .cmproj manipulation
- [already-implemented] [Import & Manage Your Project Media (Media Bin)](https://www.techsmith.com/learn/tutorials/camtasia/import-manage-media/) — media_bin/media_bin.py provides full MediaBin API with import_media, probing, metadata
- [already-implemented] [Edit Microsoft Teams & Other Meeting Recordings](https://www.techsmith.com/learn/tutorials/camtasia/meeting-recordings/) — Generic video import/edit covers this; no Teams-UI-specific features apply
- [already-implemented] [Create Vertical Videos](https://www.techsmith.com/learn/tutorials/camtasia/create-vertical-videos/) — project.width/height setters allow setting canvas to vertical (e.g., 1080x1920)
- [already-implemented] [Create a Video from a Script](https://www.techsmith.com/learn/tutorials/camtasia/create-video-from-script/) — builders/screenplay_builder.py build_from_screenplay places VO audio clips with pauses
- [not-applicable] [Collaborate on a Video Project](https://www.techsmith.com/learn/tutorials/camtasia/collaborate-video-project/) — Real-time cloud collaboration; operations/diff.py supports offline comparison
- [not-applicable] [Record an iOS Demo or Tutorial](https://www.techsmith.com/learn/tutorials/camtasia/recording-your-ios-device/) — iOS screen recording is hardware capture, outside file-manipulation scope
- [not-applicable] [Record a PowerPoint Presentation](https://www.techsmith.com/learn/tutorials/camtasia/record-a-powerpoint-presentation/) — Requires the Camtasia Recorder + PowerPoint integration, not a file concern
- [already-implemented] [Import Presentation Slides](https://www.techsmith.com/learn/tutorials/camtasia/import-powerpoint-slides/) — No PPTX import; would extract slide images and place as media on timeline

### Enhance Your Video (12)

- [already-implemented] [Visual Effects Overview](https://www.techsmith.com/learn/tutorials/camtasia/visual-effects/) — Comprehensive effects/ module: DropShadow, Glow, Mask, BlurRegion, ColorAdjustment, LutEffect, etc.
- [already-implemented] [Add Arrows, Shapes, & Callouts](https://www.techsmith.com/learn/tutorials/camtasia/annotations/) — annotations/callouts.py (text, square, arrow, highlight, keystroke_callout) and shapes.py (rectangle)
- [deferred: needs fixture] [Add a Dynamic Background](https://www.techsmith.com/learn/tutorials/camtasia/dynamic-backgrounds/) — TimelineBuilder.add_background_image for static; no animated/dynamic background generator yet
- [deferred: needs fixture] [4 Ways to Visualize Your Audio](https://www.techsmith.com/learn/tutorials/camtasia/audio-visualizers/) — Audio visualizers are likely rendered at export time by the Camtasia engine and do not appear as parameterized effects in any of our .tscproj fixtures. Implementing without a real fixture showing the JSON structure would produce invalid output. Revisit when a reference project is available.
- [already-implemented] [Create the Illusion of 3D Perspective (Corner Pinning)](https://www.techsmith.com/learn/tutorials/camtasia/corner-pinning/) — No CornerPin effect class
- [already-implemented] [Remove a Background from Your Video](https://www.techsmith.com/learn/tutorials/camtasia/video-background-removal/) — MediaMatte effect in effects/visual.py is Camtasia’s matte/background-removal mechanism
- [already-implemented] [Enhance Your Video Overview](https://www.techsmith.com/learn/tutorials/camtasia/enhance-video/) — ColorAdjustment, LutEffect, DropShadow, Glow, Emphasize, Spotlight, MotionBlur, RoundCorners
- [already-implemented] [Add Video Filters](https://www.techsmith.com/learn/tutorials/camtasia/filters/) — effects/visual.py provides color grading (LutEffect), blend modes, Spotlight, Emphasize, MotionBlur
- [already-implemented] [Provide Context with Device Frames](https://www.techsmith.com/learn/tutorials/camtasia/device-frames/) — No device frame overlay (phone/laptop/tablet bezels)
- [already-implemented] [Remove A Color (Green Screen)](https://www.techsmith.com/learn/tutorials/camtasia/how-to-remove-a-color/) — No dedicated chroma key / color-key effect; MediaMatte is a different matte concept

### Edit on the Timeline (13)

- [already-implemented] [Basic Edits After Recording](https://www.techsmith.com/learn/tutorials/camtasia/basic-video-edits/) — trim/split/reorder via timeline/clips/base.py; ripple_insert/delete in operations/layout.py
- [not-applicable] [3 Keys to the Camtasia Editor Timeline](https://www.techsmith.com/learn/tutorials/camtasia/timeline-key-concepts/) — UI-orientation tutorial for the desktop app
- [not-applicable] [Explore the Timeline](https://www.techsmith.com/learn/tutorials/camtasia/video-editing/) — UI-orientation tutorial; pycamtasia already models the timeline fully
- [already-implemented] [Add Markers & Video Table of Contents](https://www.techsmith.com/learn/tutorials/camtasia/markers-and-table-of-contents/) — timeline/markers.py MarkerList with add/remove/clear/replace; exported as SRT
- [already-implemented] [Freeze Video Clips with Extend Frame](https://www.techsmith.com/learn/tutorials/camtasia/extend-frame/) — track.py add_freeze_frame method on Track
- [already-implemented] [Speed Up & Slow Down Video Clips](https://www.techsmith.com/learn/tutorials/camtasia/clip-speed/) — clips/base.py set_speed, scalar, operations/speed.py rescale_project, set_segment_speeds
- [already-implemented] [Join Clips Together](https://www.techsmith.com/learn/tutorials/camtasia/stitch-media/) — StitchedMedia clip type exists; no explicit single-track “join two adjacent clips” operation yet
- [already-implemented] [Move Multiple Clips at Once](https://www.techsmith.com/learn/tutorials/camtasia/ripple-move/) — operations/batch.py move_all, apply_to_clips; track.py move_clip
- [already-implemented] [Ripple Move & Extend Frame](https://www.techsmith.com/learn/tutorials/camtasia/ripple-move-and-extend-frame/) — operations/layout.py ripple_insert/delete; add_freeze_frame
- [already-implemented] [Close Timeline Gaps with Magnetic Tracks](https://www.techsmith.com/learn/tutorials/camtasia/magnetic-tracks/) — track.magnetic property; operations/layout.py pack_track

### AI Video (6)

- [deferred: needs fixture] [Speed Up Editing with Camtasia Audiate](https://www.techsmith.com/learn/tutorials/camtasia/camtasia-audio-sync/) — Read-only Audiate transcript parsing is already implemented. Write-back requires the Audiate session JSON schema which is not present in any fixture and not publicly documented. Implementing blindly would produce invalid JSON; deferred pending a reference fixture.
- [not-applicable] [Introduction to AI Video Generation](https://www.techsmith.com/learn/tutorials/camtasia/introduction-ai-video/) — Cloud AI service; requires Camtasia backend
- [not-applicable] [Generate AI Avatars](https://www.techsmith.com/learn/tutorials/camtasia/ai-avatar/) — Cloud AI service; requires Camtasia backend
- [not-applicable] [Generate AI Voices from Text or a Script](https://www.techsmith.com/learn/tutorials/camtasia/text-to-speech/) — Cloud AI TTS service; library could insert resulting audio but generation itself is out of scope
- [not-applicable] [Generate a Script with AI](https://www.techsmith.com/learn/tutorials/camtasia/ai-script/) — Cloud AI service; out of scope
- [already-implemented] [Translate Your Script, Audio, and Captions](https://www.techsmith.com/learn/tutorials/camtasia/translate/) — Captions/SRT export exists; no translation pipeline. Could add extract/reimport helpers

### Edit Audio (8)

- [deferred: scope] [Recommended Audio Edits](https://www.techsmith.com/learn/tutorials/camtasia/recommended-audio-edits/) — Fundamental audio edits (gain, fade, mute, Emphasize, NoiseRemoval) are fully implemented. Dedicated normalization/compression/EQ would either require Python DSP (scipy/librosa, out of scope for a file-manipulation library) or typed effect wrappers for Camtasia effects that do not appear in any fixture. Deferred pending a reference fixture for any missing effect.
- [not-applicable] [Tips for Getting the Best Audio](https://www.techsmith.com/learn/tutorials/camtasia/best-audio-tips/) — Hardware/recording-technique advice; not a file-manipulation concern
- [already-implemented] [Set the Tone with Background Music](https://www.techsmith.com/learn/tutorials/camtasia/background-music/) — project.add_background_music with volume and fade keyframes
- [already-implemented] [Edit Audio](https://www.techsmith.com/learn/tutorials/camtasia/editing-audio/) — volume, gain, fade in/out, mute, strip_audio, normalize_audio
- [deferred: needs fixture] [Add Audio Effects](https://www.techsmith.com/learn/tutorials/camtasia/add-audio-effects/) — VST_NOISE_REMOVAL enum and categoryAudioEffects exist; no typed audio-effect wrapper classes yet
- [not-applicable] [Record Voice Narration](https://www.techsmith.com/learn/tutorials/camtasia/record-voice-narration/) — Recording audio is hardware capture; pycamtasia has add_voiceover_sequence for placing pre-recorded files

### Cursor Edits & Effects (5)

- [already-implemented] [Add Cursor Effects](https://www.techsmith.com/learn/tutorials/camtasia/cursor-effects/) — effects/cursor.py: CursorMotionBlur, CursorShadow, CursorPhysics, LeftClickScaling
- [already-implemented] [Introduction to Cursor Editing](https://www.techsmith.com/learn/tutorials/camtasia/cursor-editing-basics/) — ScreenVMFile exposes cursor_scale, cursor_opacity, cursor_motion_blur_intensity, cursor_shadow, cursor_physics, left_click_scaling
- [already-implemented] [Replace the Cursor](https://www.techsmith.com/learn/tutorials/camtasia/change-cursor/) — ScreenIMFile.cursor_image_path is read-only; no setter to replace the cursor image
- [already-implemented] [Customize the Cursor Path](https://www.techsmith.com/learn/tutorials/camtasia/customize-your-cursor-path/) — cursor_location_keyframes is read-only; no API to modify per-frame cursor positions
- [already-implemented] [Quickly Smooth Cursor Movements](https://www.techsmith.com/learn/tutorials/camtasia/cursor-smoothing/) — smooth_cursor_across_edit_duration is read-only; no setter to enable/configure smoothing

### Video Animations (7)

- [already-implemented] [Zoom In to Focus Attention](https://www.techsmith.com/learn/tutorials/camtasia/animations/) — project.add_zoom_to_region, timeline.add_zoom_pan / zoom_pan_keyframes, clip set_scale_keyframes/set_position_keyframes
- [already-implemented] [Add a Transition](https://www.techsmith.com/learn/tutorials/camtasia/video-transitions/) — timeline/transitions.py TransitionList with add, add_fade, add_card_flip, add_glitch, add_linear_blur, add_stretch, add_paint_arcs
- [already-implemented] [Animations In-Depth](https://www.techsmith.com/learn/tutorials/camtasia/animations-in-depth/) — animation_tracks, _add_visual_tracks_for_keyframes, _add_opacity_track, set_scale_keyframes, set_position_keyframes, fade_in/fade_out
- [deferred: needs fixture] [Add Movement to Any Object (Motion Paths)](https://www.techsmith.com/learn/tutorials/camtasia/motion-path/) — set_position_keyframes supports linear movement; no bezier/curved motion paths or easing presets
- [already-implemented] [Blur or Mask a Video](https://www.techsmith.com/learn/tutorials/camtasia/blur-mask-video/) — Mask effect with shape/opacity/blend/invert/rotation/size/position/corner-radius; BlurRegion (registered with color/shape/feather/opacity/ease/position props); add_motion_blur
- [already-implemented] [Animate Text & Images with Behaviors](https://www.techsmith.com/learn/tutorials/camtasia/animation-behaviors/) — effects/behaviors.py GenericBehaviorEffect with BehaviorPhase; callout add_behavior; templates/behavior_presets
- [already-implemented] [Create Stunning Animations with Media Mattes](https://www.techsmith.com/learn/tutorials/camtasia/animations-with-media-mattes/) — effects/visual.py MediaMatte; BaseClip.add_media_matte builder

### Viewer Engagement & Accessibility (5)

- [already-implemented] [Add Closed Captions to a Video](https://www.techsmith.com/learn/tutorials/camtasia/add-closed-captions/) — CaptionAttributes styling + SRT export; no API to add/edit individual caption entries on the timeline
- [deferred: needs fixture] [Add Dynamic Captions](https://www.techsmith.com/learn/tutorials/camtasia/dynamic-captions/) — Animated word-by-word caption overlays have no representation in any fixture project. Implementing the feature without seeing the actual JSON structure would produce speculative output that may not load in Camtasia. Deferred pending a reference fixture.
- [not-applicable] [Build Quizzes & Surveys](https://www.techsmith.com/learn/tutorials/camtasia/quizzing/) — Interactive player-runtime features; not .cmproj manipulation
- [not-applicable] [Add Hotspots (Interactive Videos)](https://www.techsmith.com/learn/tutorials/camtasia/add-interactive-hotspots-to-a-video/) — Player-runtime interactivity; not .cmproj manipulation

### Export & Share (5)

- [not-applicable] [Use Camtasia Videos in Your LMS](https://www.techsmith.com/learn/tutorials/camtasia/lms-options/) — LMS integration (SCORM/xAPI packaging) is deployment concern
- [not-applicable] [Export & Share Your Video](https://www.techsmith.com/learn/tutorials/camtasia/export-share/) — Video encoding/rendering requires the Camtasia engine; pycamtasia exports metadata only (EDL/CSV/SRT/JSON/report)
- [already-implemented] [Watermark Your Videos](https://www.techsmith.com/learn/tutorials/camtasia/video-watermark/) — project.add_watermark
- [not-applicable] [Batch Export Videos](https://www.techsmith.com/learn/tutorials/camtasia/batch-export/) — Batch video rendering/encoding; library cannot render video files
- [deferred: scope] [Export an Audio File](https://www.techsmith.com/learn/tutorials/camtasia/export-audio/) — The metadata export side (listing source paths for external tools to mix) is implemented via export_audio_clips(). Actual audio rendering/encoding requires an audio engine (ffmpeg/libav/similar) which is strictly out of scope for a project-file-manipulation library. Users are expected to feed the output of export_audio_clips() into their preferred encoder.

### Customizations & Branding (8)

- [deferred: needs fixture] [Reuse Media Across Projects (Library)](https://www.techsmith.com/learn/tutorials/camtasia/library/) — Cross-project media reuse is already supported via replace_media_source() and operations/template.py. The native .libzip Library format is an undocumented Camtasia-specific archive that would need to be reverse-engineered from real library bundles. Deferred pending reference archives.
- [not-applicable] [Customize Camtasia Editor](https://www.techsmith.com/learn/tutorials/camtasia/customize-camtasia/) — UI preferences stored outside .cmproj files
- [already-implemented] [How to Use a Template](https://www.techsmith.com/learn/tutorials/camtasia/use-a-template/) — operations/template.py duplicate_project(clear_media=True); clone_project_structure; templates/
- [deferred: needs fixture] [Build a Video Template to Share](https://www.techsmith.com/learn/tutorials/camtasia/create-a-template/) — Template semantics are fully supported via operations/template.py (duplicate_project with clear_media, clone_project_structure). The wire format .camtemplate is an undocumented Camtasia-specific archive that would need reverse-engineering. Deferred pending reference archives.
- [already-implemented] [Build Your Color Palette (Themes)](https://www.techsmith.com/learn/tutorials/camtasia/themes/) — themeMappings exist in .cmproj but no API to define/apply/swap named color palettes
- [not-applicable] [Package & Share Camtasia Editor Resources](https://www.techsmith.com/learn/tutorials/camtasia/package-share-camtasia-resources/) — .campackage/.libzip bundling is an application packaging concern
- [not-applicable] [Customize Shortcuts](https://www.techsmith.com/learn/tutorials/camtasia/customize-camtasia-shortcuts/) — Keyboard shortcuts are Camtasia app preferences; not in .cmproj
- [deferred: needs fixture] [Create Custom Assets](https://www.techsmith.com/learn/tutorials/camtasia/create-custom-assets/) — Programmatic creation of callouts, lower thirds, and title cards is fully supported. The .campackage asset-sharing archive format is an undocumented Camtasia-specific wire format that would need reverse-engineering. Deferred pending reference archives.

### Projects (6)

- [already-implemented] [How to Make an Intro for a Video](https://www.techsmith.com/learn/tutorials/camtasia/how-to-make-an-intro/) — add_title_card, add_countdown, add_lower_third, TimelineBuilder.add_title, build_from_screenplay_file
- [not-applicable] [Create a Quick Tip Style Video](https://www.techsmith.com/learn/tutorials/camtasia/create-a-quick-tip-style-video-template/) — Content-style workflow tutorial, not a discrete feature
- [not-applicable] [How to Create a Software Tutorial](https://www.techsmith.com/learn/tutorials/camtasia/how-to-create-a-great-tutorial/) — Workflow tutorial; editing features already covered by existing modules
- [not-applicable] [How to Make an Explainer Video](https://www.techsmith.com/learn/tutorials/camtasia/how-to-make-an-explainer-video/) — Content-genre workflow tutorial; not a discrete feature
- [not-applicable] [How to Create a Product Walkthrough Video](https://www.techsmith.com/learn/tutorials/camtasia/how-to-create-a-product-walkthrough-video/) — Workflow tutorial, not a discrete feature
- [not-applicable] [How to Make a Software Demo](https://www.techsmith.com/learn/tutorials/camtasia/how-to-make-a-software-demo/) — Workflow tutorial, not a discrete feature

## Deep Tutorial Analysis (detailed feature-level gaps)

_Each item below represents a specific feature/operation mentioned in an official TechSmith Camtasia tutorial that pycamtasia does not fully support. Every gap was verified twice: first by a research subagent reading the tutorial + source, then by an independent adversarial verification subagent re-checking the claim. False positives (features not actually in the tutorial, or already supported) have been removed._

### Add Audio Effects

Source: https://www.techsmith.com/learn/tutorials/camtasia/add-audio-effects/

- [x] **Audio Compression effect missing (Ratio/Threshold/Gain/Variation)** `src/camtasia/effects/audio.py` — `AudioCompression class`
- [x] **ClipSpeed audio effect missing (Speed/Duration)** `src/camtasia/effects/audio.py` — `ClipSpeed class`
- [x] **Pitch effect missing (Mac — Pitch/Ease In/Out)** `src/camtasia/effects/audio.py` — `Pitch class`
- [x] **audio-specific Fade In / Fade Out wrappers missing** `src/camtasia/timeline/clips/base.py` — `add_audio_fade_in / add_audio_fade_out`
- [x] **NoiseRemoval Sensitivity and Reduction (Mac) params missing** `src/camtasia/effects/audio.py` — `NoiseRemoval.sensitivity / reduction`
- [x] **EffectName enum missing AudioCompression/ClipSpeed/Pitch entries** `src/camtasia/types.py` — `EffectName members`

### Add Closed Captions to a Video

Source: https://www.techsmith.com/learn/tutorials/camtasia/add-closed-captions/

- [x] **Import captions from SRT/VTT/SAMI** `src/camtasia/export/captions.py` — `import_captions_srt`
- [x] **Export captions as SRT/VTT/SAMI (not just markers)** `src/camtasia/export/srt.py` — `export_captions_as_srt`
- [x] **Edit/remove caption by index** `src/camtasia/timeline/timeline.py` — `Timeline.edit_caption / remove_caption`
- [x] **Split overlong caption ('Split' button)** `src/camtasia/timeline/timeline.py` — `Timeline.split_caption`
- [x] **Merge adjacent captions** `src/camtasia/timeline/timeline.py` — `Timeline.merge_caption_with_next`
- [x] **Caption vertical position / anchor** `src/camtasia/timeline/captions.py` — `CaptionAttributes.position / vertical_anchor`
- [x] **Speech-to-text auto-caption generation** `src/camtasia/operations/` — `generate_captions_from_audio`
- [x] **Sync script to audio playback (Windows workflow)** `src/camtasia/operations/` — `sync_script_to_captions`
- [x] **Burned-in (open) captions export toggle** `src/camtasia/export/` — `export_video(caption_style='burned_in')`
- [x] **ADA/accessibility compliance validator (line-length/duration/contrast)** `src/camtasia/validation.py` — `validate_caption_accessibility`
- [x] **Default caption duration setting (Camtasia default 4s)** `src/camtasia/timeline/captions.py` — `CaptionAttributes.default_duration_seconds`

### Animate Text & Images with Behaviors

Source: https://www.techsmith.com/learn/tutorials/camtasia/animation-behaviors/

- [x] **flyOut preset missing** `src/camtasia/templates/behavior_presets.py` — `PRESETS['flyOut']`
- [x] **emphasize preset missing** `src/camtasia/templates/behavior_presets.py` — `PRESETS['emphasize']`
- [x] **jiggle preset missing** `src/camtasia/templates/behavior_presets.py` — `PRESETS['jiggle']`
- [x] **No classmethod factories on GenericBehaviorEffect to instantiate presets by name** `src/camtasia/effects/behaviors.py` — `GenericBehaviorEffect.from_preset(name, duration)`
- [x] **BehaviorPhase lacks loop-phase fields as typed properties** `src/camtasia/effects/behaviors.py` — `seconds_per_loop/number_of_loops/delay_between_loops`
- [x] **No enum/constants for movement/characterOrder values** `src/camtasia/effects/behaviors.py` — `Movement/CharacterOrder IntEnum`
- [x] **During-phase style params not surfaced as typed properties** `src/camtasia/effects/behaviors.py` — `BehaviorPhase.opacity/jump/rotation/scale/shift`

### Zoom In to Focus Attention

Source: https://www.techsmith.com/learn/tutorials/camtasia/animations/

- [x] **SmartFocus auto-animation on .trec recordings** `src/camtasia/project.py` — `apply_smart_focus`
- [x] **SmartFocus at Time (Mac) - apply at playhead** `src/camtasia/project.py` — `apply_smart_focus_at_time`
- [x] **Preset named animations (Scale Up/Down/To Fit/Custom) as first-class API** `src/camtasia/project.py` — `add_animation(preset=...)`
- [x] **Zoom-n-Pan rectangle API (viewport rect vs scale+center)** `src/camtasia/timeline/timeline.py` — `add_zoom_n_pan_rect(x,y,w,h)`
- [x] **Animation arrow ease-in/out parameters** `src/camtasia/project.py` — `add_zoom_to_region(ease_in, ease_out)`
- [x] **Scale to Fit helper (reset zoom to entire canvas)** `src/camtasia/timeline/timeline.py` — `add_scale_to_fit`

### Animations In-Depth

Source: https://www.techsmith.com/learn/tutorials/camtasia/animations-in-depth/

- [x] **Skew parameter keyframes and setter** `src/camtasia/timeline/clips/base.py` — `set_skew / set_skew_keyframes`
- [x] **Rotation on X and Y axes (only Z exposed)** `src/camtasia/timeline/clips/base.py` — `rotation_x/rotation_y setters and keyframes`
- [x] **Z-axis position (translation2) not exposed** `src/camtasia/timeline/clips/base.py` — `translation_z in move_to / set_position_keyframes`
- [x] **Animation arrow abstraction (named Animation object)** `src/camtasia/timeline/clips/base.py` — `add_animation(start, end, scale=, position=, rotation=, opacity=, easing=)`
- [x] **Edit-All-Animations mode** `src/camtasia/timeline/clips/base.py` — `apply_to_all_animations`

### Create Stunning Animations with Media Mattes

Source: https://www.techsmith.com/learn/tutorials/camtasia/animations-with-media-mattes/

- [x] **MediaMatte.mode only 1/2 documented but Camtasia has 4 modes (Alpha, Alpha Invert, Luminosity, Luminosity Invert); fixtures use mode=3** `src/camtasia/effects/visual.py` — `MediaMatte.mode full enum coverage`
- [x] **MatteMode enum not defined in types.py** `src/camtasia/types.py` — `MatteMode IntEnum`
- [x] **add_media_matte lacks ease_in/ease_out parameters** `src/camtasia/timeline/clips/base.py` — `add_media_matte(..., ease_in_seconds, ease_out_seconds)`
- [x] **Track-level matte attribute setter missing (right-click track -> Alpha/Luminosity/...)** `src/camtasia/timeline/track.py` — `Track.matte_mode property`
- [x] **No documentation of compatible transparent media formats** `src/camtasia/timeline/clips/base.py` — `add_media_matte docstring`
- [x] **add_media_matte default preset_name mismatches default matte_mode** `src/camtasia/timeline/clips/base.py` — `derive preset_name from matte_mode`

### Add Arrows, Shapes, & Callouts

Source: https://www.techsmith.com/learn/tutorials/camtasia/annotations/

- [x] **Sketch Motion Callout (animated drawing callout: sketch circle, sketch arrow)** `annotations/callouts.py` — `sketch_motion_callout`
- [x] **Sketch Motion draw-time property** `annotations/callouts.py` — `sketch_motion_callout(..., draw_time=...)`
- [x] **Line annotation (tutorial lists 'Arrows & Lines' — only arrow() exists)** `annotations/callouts.py` — `line`
- [x] **Ellipse / circle shape annotation** `annotations/shapes.py` — `ellipse`
- [x] **Favorites / preset annotations** `annotations/__init__.py` — `save_as_favorite / load_favorite`

### annotations

Source: 

- [x] **Sketch Motion Callout (animated drawing callout: sketch circle, sketch arrow) — no factory, no 'sketch' style anywhere in library** `annotations/callouts.py` — `sketch_motion_callout`
- [x] **Sketch Motion draw-time property (how long the sketch animates on)** `annotations/callouts.py` — `sketch_motion_callout(..., draw_time=...)`
- [x] **Additional shapes shown in Shapes subtab (polygon, rounded-rectangle, triangle, speech bubble) — only rectangle() exposed** `annotations/shapes.py` — `polygon / rounded_rectangle / triangle`
- [x] **Shadow (hasDropShadow) on callout/shape annotations — hardcoded to 0.0 in square/keystroke, not exposed as parameter** `annotations/callouts.py` — `square(..., drop_shadow=True)`
- [x] **Corner-radius on shape/square callouts — hardcoded to 0.0, not exposed** `annotations/shapes.py` — `rectangle(..., corner_radius=...)`
- [x] **Callout tail for speech-bubble style — tail-x/tail-y hardcoded, not parameterized** `annotations/callouts.py` — `square(..., tail=(x,y))`
- [x] **Italic / underline / strikethrough text properties — _text_attributes always writes 0 and callers cannot override** `annotations/callouts.py` — `text(..., italic=..., underline=..., strikethrough=...)`
- [x] **Lower-third / title preset callout helpers — templates/lower_third.py exists but no public annotation factory in camtasia.annotations** `annotations/__init__.py` — `lower_third / title`
- [x] **Gradient fill for callouts/shapes — FillStyle.Gradient exists but no gradient-stop parameters accepted** `annotations/callouts.py` — `square(..., gradient_stops=...)`
- [x] **Favorites / preset annotations (save/load custom annotation for reuse)** `annotations/__init__.py` — `save_as_favorite / load_favorite`

### 4 Ways to Visualize Your Audio

Source: https://www.techsmith.com/learn/tutorials/camtasia/audio-visualizers/

- [x] **Audio visualizer feature entirely absent from library (no 'visualizer'/'waveform' code)** `src/camtasia/effects/` — `AudioVisualizer effect class with type/style/color parameters`
- [x] **No helper to add visualizer to audio clip** `src/camtasia/timeline/clips/audio.py` — `add_audio_visualizer`

### Basic Edits After Recording

Source: https://www.techsmith.com/learn/tutorials/camtasia/basic-video-edits/

- [x] **Timeline selection API (in/out range)** `src/camtasia/timeline/track.py` — `set_selection / clear_selection`
- [x] **cut/copy/paste on selection** `src/camtasia/timeline/track.py` — `cut_selection / copy_selection / paste_at`
- [x] **undo/redo on timeline operations** `src/camtasia/timeline/track.py` — `undo / redo command history`
- [x] **trim_head/trim_tail on BaseClip** `src/camtasia/timeline/clips/base.py` — `trim_head / trim_tail`
- [x] **ripple_delete by timeline range (only supports clip_id currently)** `src/camtasia/operations/layout.py` — `ripple_delete_range(track, start, end)`

### Blur or Mask a Video

Source: https://www.techsmith.com/learn/tutorials/camtasia/blur-mask-video/

- [x] **BlurRegion not registered via @register_effect and unverified against fixtures** `src/camtasia/effects/visual.py` — `@register_effect('BlurRegion') decorator`
- [x] **BlurRegion missing Tint color RGB (only color-alpha exposed)** `src/camtasia/effects/visual.py` — `BlurRegion.color property`
- [x] **BlurRegion missing Shape parameter (Oval vs Rectangle)** `src/camtasia/effects/visual.py` — `BlurRegion.shape property`
- [x] **BlurRegion missing Feather/edge-softness slider** `src/camtasia/effects/visual.py` — `BlurRegion.feather or mask_blend`
- [x] **BlurRegion missing Opacity slider** `src/camtasia/effects/visual.py` — `BlurRegion.opacity`
- [x] **BlurRegion missing Ease In/Ease Out controls** `src/camtasia/effects/visual.py` — `BlurRegion.ease_in/ease_out`
- [x] **BlurRegion missing positional/dimension params for moving-blur keyframes** `src/camtasia/effects/visual.py` — `BlurRegion.mask_width/height/position_x/position_y`
- [x] **No animate_to helper for Mask/BlurRegion keyframes** `src/camtasia/effects/visual.py` — `Mask.animate_to(time, x, y, w, h)`

### Speed Up Editing with Camtasia Audiate

Source: https://www.techsmith.com/learn/tutorials/camtasia/camtasia-audio-sync/

- [x] **Auto-detect and remove filler words (Suggested Edits)** `src/camtasia/audiate/transcript.py` — `Transcript.detect_filler_words / remove_filler_words`
- [x] **Detect and shorten pauses** `src/camtasia/audiate/transcript.py` — `Transcript.detect_pauses / shorten_pauses`
- [x] **Apply Audiate edits back to Camtasia timeline (Edit Timeline vs Edit Media Only)** `src/camtasia/operations/sync.py` — `sync_audiate_edits_to_timeline(mode=...)`
- [x] **Resolve linked Camtasia media by caiCamtasiaSessionId (link/unlink)** `src/camtasia/audiate/project.py` — `AudiateProject.find_linked_media / unlink`
- [x] **Generate SRT from Audiate transcript** `src/camtasia/audiate/transcript.py` — `Transcript.to_srt`
- [x] **Smart Scenes segmentation metadata** `src/camtasia/audiate/project.py` — `AudiateProject.smart_scenes`
- [x] **Send Camtasia media to a new .audiate project** `src/camtasia/operations/sync.py` — `send_media_to_audiate`
- [x] **Text-based deletion propagating to timeline** `src/camtasia/operations/sync.py` — `delete_words_from_timeline`

### Replace the Cursor

Source: https://www.techsmith.com/learn/tutorials/camtasia/change-cursor/

- [x] **Replace-scope selector (Current/Similar/All)** `src/camtasia/timeline/clips/screen_recording.py` — `replace_cursor(path, scope='current'|'similar'|'all')`
- [x] **Built-in cursor library / Cursor Type enumeration** `src/camtasia/timeline/clips/screen_recording.py` — `CursorType enum + set_cursor_type`
- [x] **Hide cursor (No Cursor option)** `src/camtasia/timeline/clips/screen_recording.py` — `hide_cursor()`
- [x] **Import custom cursor from image file** `src/camtasia/timeline/clips/screen_recording.py` — `import_custom_cursor(image_path)`
- [x] **Unpack Rev Media prerequisite for cursor editing** `src/camtasia/timeline/clips/screen_recording.py` — `unpack_rev_media`
- [x] **ROADMAP.md stale — incorrectly says cursor_image_path has no setter** `ROADMAP.md` — `update line — setter does exist`

### Speed Up & Slow Down Video Clips

Source: https://www.techsmith.com/learn/tutorials/camtasia/clip-speed/

- [x] **ClipSpeed as named Visual Effect (no add_clip_speed / 'ClipSpeed' effectName producer)** `src/camtasia/timeline/clips/base.py` — `apply_clip_speed_effect`
- [x] **Duration-based speed adjustment (set_speed_by_duration)** `src/camtasia/timeline/clips/base.py` — `set_speed_by_duration(target_seconds)`

### Create the Illusion of 3D Perspective (Corner Pinning)

Source: https://www.techsmith.com/learn/tutorials/camtasia/corner-pinning/

- [x] **Derived position/skew/rotation accessors on CornerPin** `src/camtasia/effects/visual.py` — `CornerPin.position / skew / rotation derived properties`
- [x] **Helper to animate pinned corners via keyframes** `src/camtasia/effects/visual.py` — `CornerPin.add_keyframe(time, corner, x, y)`
- [x] **CornerPin parameter names unverified against real fixture** `tests/fixtures/ and effects/visual.py` — `add corner-pinning fixture and verify`

### Build a Video Template to Share

Source: https://www.techsmith.com/learn/tutorials/camtasia/create-a-template/

- [x] **No save_as_template producing .camtemplate file** `src/camtasia/operations/template.py` — `save_as_template`
- [x] **No export_camtemplate operation** `src/camtasia/operations/template.py` — `export_camtemplate`
- [x] **No import_camtemplate / new_from_template** `src/camtasia/operations/template.py` — `new_from_template`
- [x] **PlaceholderMedia missing 'title' property (canvas-visible title distinct from note)** `src/camtasia/timeline/clips/placeholder.py` — `PlaceholderMedia.title`
- [x] **No Track.add_placeholder convenience** `src/camtasia/timeline/track.py` — `Track.add_placeholder(time, duration, title, note)`

### Create Custom Assets

Source: https://www.techsmith.com/learn/tutorials/camtasia/create-custom-assets/

- [x] **Save grouped media as reusable custom asset** `src/camtasia/timeline/clips/group.py` — `Group.save_as_asset`
- [x] **Favorite annotations/callouts for reuse** `src/camtasia/annotations/callouts.py` — `Callout.add_to_favorites`
- [x] **Export asset library as .campackage archive** `src/camtasia/export/` — `export_campackage`
- [x] **Custom asset library management (add/list/reuse)** `src/camtasia/library.py` — `AssetLibrary.add_asset / list_assets`
- [x] **Quick Property Editor (link/unlink/label/assign_theme/toggle visible on group)** `src/camtasia/timeline/clips/group.py` — `Group.quick_properties`

### Create Vertical Videos

Source: https://www.techsmith.com/learn/tutorials/camtasia/create-vertical-videos/

- [x] **No vertical aspect presets (9:16 FHD, 9:16 HD, 4:5, 1:1)** `src/camtasia/project.py` — `set_vertical_preset / CanvasPreset enum`
- [x] **No Crop visual effect / crop_to_aspect / fit_to_canvas helper** `src/camtasia/effects/visual.py` — `Crop class + Clip.crop_to_aspect / fit_to_canvas`

### Create a Video from a Script

Source: https://www.techsmith.com/learn/tutorials/camtasia/create-video-from-script/

- [x] **No paragraph-to-scene mapping helper** `src/camtasia/screenplay.py` — `Section.from_paragraphs`
- [x] **No scene/chapter markers emitted per section** `src/camtasia/builders/screenplay_builder.py` — `add marker per section`
- [x] **No VO-to-screen-recording alignment on visual track** `src/camtasia/builders/screenplay_builder.py` — `video-track placement`
- [x] **No on-screen captions generated from script lines** `src/camtasia/builders/screenplay_builder.py` — `_emit_captions_for_vo`
- [x] **Single default_pause used for both inter-VO and inter-scene** `src/camtasia/builders/screenplay_builder.py` — `section_pause distinct from vo_pause`
- [x] **No VO duration/alignment validation against audio length** `src/camtasia/builders/screenplay_builder.py` — `_validate_vo_alignment`
- [x] **Audio resolver case-sensitive / rigid prefix** `src/camtasia/builders/screenplay_builder.py` — `case-insensitive flexible _find_audio_file`

### Introduction to Cursor Editing

Source: https://www.techsmith.com/learn/tutorials/camtasia/cursor-editing-basics/

- [x] **No cursor elevation/always-on-top property** `src/camtasia/timeline/clips/screen_recording.py` — `ScreenVMFile.cursor_elevation`
- [x] **No keyframe support for cursor_scale over time** `src/camtasia/timeline/clips/screen_recording.py` — `set_cursor_scale_keyframes`
- [x] **No keyframe support for cursor_opacity over time** `src/camtasia/timeline/clips/screen_recording.py` — `set_cursor_opacity_keyframes`
- [x] **No hide_cursor / show_cursor wrappers** `src/camtasia/timeline/clips/screen_recording.py` — `hide_cursor / show_cursor`
- [x] **No 'No Cursor' image replacement at specific keyframe** `src/camtasia/timeline/clips/screen_recording.py` — `set_no_cursor_at(time)`

### Add Cursor Effects

Source: https://www.techsmith.com/learn/tutorials/camtasia/cursor-effects/

- [x] **CursorColor effect missing** `src/camtasia/effects/cursor.py` — `class CursorColor: fill_color, outline_color`
- [x] **CursorGlow effect missing** `src/camtasia/effects/cursor.py` — `class CursorGlow: color, opacity, radius`
- [x] **CursorHighlight effect missing** `src/camtasia/effects/cursor.py` — `class CursorHighlight: size, color, opacity`
- [x] **CursorIsolation effect missing** `src/camtasia/effects/cursor.py` — `class CursorIsolation: size, feather`
- [x] **CursorMagnify effect missing** `src/camtasia/effects/cursor.py` — `class CursorMagnify: scale, size`
- [x] **CursorPathCreator effect missing** `src/camtasia/effects/cursor.py` — `class CursorPathCreator: keyframes`
- [x] **CursorSmoothing effect missing** `src/camtasia/effects/cursor.py` — `class CursorSmoothing: level`
- [x] **CursorSpotlight effect missing** `src/camtasia/effects/cursor.py` — `class CursorSpotlight: size, opacity, blur, color`
- [x] **CursorGradient effect missing** `src/camtasia/effects/cursor.py` — `class CursorGradient: color, size, opacity`
- [x] **CursorLens effect missing** `src/camtasia/effects/cursor.py` — `class CursorLens: scale, size`
- [x] **CursorNegative effect missing** `src/camtasia/effects/cursor.py` — `class CursorNegative: size, feather`
- [x] **ClickBurst1-4 (left & right) effects missing** `src/camtasia/effects/cursor.py` — `LeftClickBurst1..4 / RightClickBurst1..4`
- [x] **ClickZoom (left & right) effects missing** `src/camtasia/effects/cursor.py` — `LeftClickZoom / RightClickZoom`
- [x] **ClickRings (left & right) effects missing** `src/camtasia/effects/cursor.py` — `LeftClickRings / RightClickRings`
- [x] **ClickRipple (left & right) effects missing** `src/camtasia/effects/cursor.py` — `LeftClickRipple / RightClickRipple`
- [x] **RightClickScaling (mirror of LeftClickScaling) missing** `src/camtasia/effects/cursor.py` — `RightClickScaling`
- [x] **ClickScope (left & right) effects missing** `src/camtasia/effects/cursor.py` — `LeftClickScope / RightClickScope`
- [x] **ClickSound (left & right) effects missing** `src/camtasia/effects/cursor.py` — `LeftClickSound / RightClickSound`
- [x] **ClickTarget (left & right) effects missing** `src/camtasia/effects/cursor.py` — `LeftClickTarget / RightClickTarget`
- [x] **ClickWarp (left & right) effects missing** `src/camtasia/effects/cursor.py` — `LeftClickWarp / RightClickWarp`

### Customize the Cursor Path

Source: https://www.techsmith.com/learn/tutorials/camtasia/customize-your-cursor-path/

- [x] **No per-keyframe Line Type (straight vs curved/bezier) in set_cursor_location_keyframes** `src/camtasia/timeline/clips/screen_recording.py` — `set_cursor_location_keyframes(line_types=...)`
- [x] **No bezier tangent handle control for cursor path points** `src/camtasia/timeline/clips/screen_recording.py` — `bezier handles param`
- [x] **No per-point easing dropdown equivalent (only global 'linr')** `src/camtasia/timeline/clips/screen_recording.py` — `per-point easing`
- [x] **No add_cursor_point(time,x,y) helper** `src/camtasia/timeline/clips/screen_recording.py` — `add_cursor_point`
- [x] **No delete_cursor_point helper** `src/camtasia/timeline/clips/screen_recording.py` — `delete_cursor_point`
- [x] **No move_cursor_point helper** `src/camtasia/timeline/clips/screen_recording.py` — `move_cursor_point`
- [x] **No split_cursor_path operation** `src/camtasia/timeline/clips/screen_recording.py` — `split_cursor_path`
- [x] **No extend_cursor_path operation** `src/camtasia/timeline/clips/screen_recording.py` — `extend_cursor_path`
- [x] **No smooth_cursor_path (simplify jitter) operation** `src/camtasia/timeline/clips/screen_recording.py` — `smooth_cursor_path`
- [x] **No straighten_cursor_path operation** `src/camtasia/timeline/clips/screen_recording.py` — `straighten_cursor_path`
- [x] **No restore_cursor_path (revert to original recorded)** `src/camtasia/timeline/clips/screen_recording.py` — `restore_cursor_path`
- [x] **No CursorPathCreator for non-TREC media** `src/camtasia/timeline/clips/screen_recording.py` — `add_cursor_path_creator`
- [x] **cursor_location_keyframes setter not provided** `src/camtasia/timeline/clips/screen_recording.py` — `cursor_location_keyframes setter`

### Provide Context with Device Frames

Source: https://www.techsmith.com/learn/tutorials/camtasia/device-frames/

- [x] **No built-in device frame Type presets / enum (tutorial has Type dropdown)** `src/camtasia/builders/device_frame.py` — `DeviceFrameType enum / preset catalog`
- [x] **No integration with TechSmith asset library / 'Download More' frames** `src/camtasia/builders/device_frame.py` — `library/preset-name resolver`
- [x] **Implemented as image overlay rather than Camtasia's native DeviceFrame visualEffect on the clip** `src/camtasia/builders/device_frame.py` — `emit visualEffects DeviceFrame entry on wrapped_clip`
- [x] **No auto-fit/snap of clip to canvas** `src/camtasia/builders/device_frame.py` — `add_device_frame fit_to_canvas param`
- [x] **No remove_device_frame helper (tutorial's X icon)** `src/camtasia/builders/device_frame.py` — `remove_device_frame`

### Add a Dynamic Background

Source: https://www.techsmith.com/learn/tutorials/camtasia/dynamic-backgrounds/

- [x] **No high-level add_dynamic_background(asset_name=...) API — only add_gradient_background** `src/camtasia/builders/` — `add_dynamic_background(asset_name, duration, colors)`
- [x] **No named-asset catalog for dynamic background shader assets** `src/camtasia/` — `DynamicBackgroundAsset enum / catalog`
- [x] **No wrapper for Lottie-based dynamic backgrounds (source handles Color000 padded keys but no public helper)** `src/camtasia/builders/` — `add_lottie_background`
- [x] **No mapping of tutorial's UI property labels to SourceEffect parameter keys (Color0-3, MidPoint, Speed)** `src/camtasia/effects/source.py` — `documented property name aliases`

### Add Dynamic Captions

Source: https://www.techsmith.com/learn/tutorials/camtasia/dynamic-captions/

- [x] **Dynamic Caption Style presets / library** `src/camtasia/timeline/captions.py` — `DynamicCaptionStyle class + apply_dynamic_style`
- [x] **Auto-generate dynamic captions from audio transcript** `src/camtasia/audiate/transcript.py` — `Transcript.to_dynamic_caption_clip`
- [x] **Word-by-word highlight animation per transcript timing** `src/camtasia/timeline/captions.py` — `DynamicCaptionClip.active_word_at(t)`
- [x] **Per-caption styling distinct from timeline-wide CaptionAttributes** `src/camtasia/timeline/clips/callout.py` — `DynamicCaptionClip.text_properties`
- [x] **Save custom style as Dynamic Caption preset** `src/camtasia/templates/behavior_presets.py` — `save_dynamic_caption_preset`
- [x] **Transcript word editing: add/delete/convert-to-gap** `src/camtasia/audiate/transcript.py` — `Transcript.add_word/delete_word/convert_to_gap`
- [x] **Per-word transcription timing drag** `src/camtasia/audiate/transcript.py` — `Transcript.set_word_timing`
- [x] **Transcript gap indicators** `src/camtasia/audiate/transcript.py` — `Transcript.gaps property`
- [x] **Dynamic caption canvas position/size handles** `src/camtasia/timeline/clips/callout.py` — `DynamicCaptionClip.canvas_rect`
- [x] **Extend caption duration with transcript rescoping** `src/camtasia/timeline/clips/base.py` — `DynamicCaptionClip.set_duration with rescope`
- [x] **Preserve transcription edits when style deleted/swapped** `src/camtasia/timeline/clips/audio.py` — `AudioClip.dynamic_caption_transcription persistence`

### Edit Zoom Recordings

Source: https://www.techsmith.com/learn/tutorials/camtasia/edit-zoom-recording/

- [x] **Import Zoom cloud recording via OAuth** `src/camtasia/project.py` — `Project.import_zoom_recording`
- [x] **Zoom-specific metadata (meeting ID, host, topic, date)** `src/camtasia/media_bin/media_bin.py` — `Media.zoom_metadata`

### Edit Audio

Source: https://www.techsmith.com/learn/tutorials/camtasia/editing-audio/

- [x] **Silence range of audio (right-click > Silence Audio)** `src/camtasia/timeline/clips/base.py` — `silence_audio(start, end)`
- [x] **Separate/strip audio from video clip** `src/camtasia/timeline/clips/base.py` — `separate_video_and_audio`
- [x] **Audio-specific fade_in/fade_out (current fade methods animate opacity)** `src/camtasia/timeline/clips/base.py` — `audio_fade_in / audio_fade_out`
- [x] **Multi-point audio point API (add/move/remove volume keyframes)** `src/camtasia/timeline/clips/base.py` — `add_audio_point / remove_all_audio_points`
- [x] **Mix-to-Mono setter missing (attribute exists, no dedicated setter)** `src/camtasia/timeline/clips/audio.py` — `mix_to_mono setter`
- [x] **set_volume_fade supports only single start->end; no multi-keyframe volume envelope** `src/camtasia/timeline/clips/base.py` — `set_volume_keyframes`

### Enhance Your Video Overview

Source: https://www.techsmith.com/learn/tutorials/camtasia/enhance-video/

- [x] **Gesture Effects (tap/swipe/pinch for iOS recordings, Mac only)** `src/camtasia/effects/visual.py` — `class GestureEffect with @register_effect('GestureTap'|'GestureSwipe'|'GesturePinch')`
- [x] **Interactive Hotspot effect (clickable regions)** `src/camtasia/effects/visual.py` — `class Hotspot with @register_effect('Hotspot') — url, action, pause, javascript params`
- [x] **Zoom-n-Pan as a first-class effect** `src/camtasia/effects/visual.py` — `class ZoomNPan with scale, positionX, positionY parameters`
- [x] **Device Frame as a registered visual effect** `src/camtasia/effects/visual.py` — `class DeviceFrame with @register_effect('DeviceFrame') — frame_type parameter`
- [x] **ChromaKey and CornerPin lack fixture verification** `src/camtasia/effects/visual.py` — `add fixture-backed tests and remove unverified warnings`

### Export an Audio File

Source: https://www.techsmith.com/learn/tutorials/camtasia/export-audio/

- [x] **Export standalone audio file (mp3/m4a/wav) from project timeline** `src/camtasia/export/audio.py` — `export_audio(project, out_path, format=...)`
- [x] **File-type/format selection (mp3/m4a/wav)** `src/camtasia/export/audio.py` — `export_audio(format literal)`
- [x] **Mixed export of enabled audio tracks** `src/camtasia/export/audio.py` — `mix enabled tracks in export_audio`
- [x] **Per-track / solo audio export honoring enabled flag** `src/camtasia/export/audio.py` — `export_audio_clips(solo_track=...)`
- [x] **Public API export in export/__init__.py for audio functions** `src/camtasia/export/__init__.py` — `export export_audio/export_audio_clips`

### Freeze Video Clips with Extend Frame

Source: https://www.techsmith.com/learn/tutorials/camtasia/extend-frame/

- [x] **ripple_extend operation (extend clip + push following clips forward)** `src/camtasia/operations/layout.py` — `ripple_extend(track, clip_id, extend_seconds)`
- [x] **Extend clip to absolute target duration** `src/camtasia/timeline/track.py` — `extend_clip_to(clip_id, target_duration)`
- [x] **freeze_at_clip_start convenience** `src/camtasia/timeline/track.py` — `freeze_at_clip_start`
- [x] **freeze_at_clip_end convenience** `src/camtasia/timeline/track.py` — `freeze_at_clip_end`
- [x] **add_exported_frame (exports a frame as image on new track)** `src/camtasia/timeline/track.py` — `add_exported_frame`
- [x] **extend_clip has no ripple option** `src/camtasia/timeline/track.py` — `extend_clip(..., ripple=False)`

### Add Video Filters

Source: https://www.techsmith.com/learn/tutorials/camtasia/filters/

- [x] **Range controls (shadowRampStart/End, highlightRampStart/End, channel) written by add_lut_effect but not typed on LutEffect** `src/camtasia/effects/visual.py` — `LutEffect.shadow_ramp_start/end, highlight_ramp_start/end, channel`
- [x] **Range blend preset dropdown selection has no API** `src/camtasia/effects/visual.py` — `LutEffect.range_preset`
- [x] **Ease In / Ease Out (Mac) transition seconds not exposed** `src/camtasia/effects/visual.py` — `LutEffect.ease_in / LutEffect.ease_out`
- [x] **Add Preset button (save customized LUT) has no API** `src/camtasia/timeline/clips/base.py` — `save_lut_preset`
- [x] **LUT filename dropdown has no enum/catalog** `src/camtasia/types.py` — `LutPreset enum`

### How to Make an Intro for a Video

Source: https://www.techsmith.com/learn/tutorials/camtasia/how-to-make-an-intro/

- [x] **Import .libzip archive into a new library** `src/camtasia/project.py` — `import_libzip_library`
- [x] **Ripple-replace logo asset inside intro group's Left Logo subgroup** `src/camtasia/timeline/track.py` — `ripple_replace_media / replace_in_group`
- [x] **Edit intro group properties (BG1/BG2 gradient, text font/size/color)** `src/camtasia/timeline/track.py` — `set_group_property / edit_intro_properties`
- [x] **Save customized timeline group back to library as reusable asset** `src/camtasia/project.py` — `save_timeline_group_to_library`
- [x] **Access/modify nested intro subgroups (Cloud overlay opacity, Right Text spacing)** `src/camtasia/timeline/track.py` — `get_nested_subgroup / set_opacity`
- [x] **add_intro lacks template_name/library_asset linkage** `src/camtasia/builders/video_production.py` — `add_intro(template_name=..., library_asset=...)`

### Remove A Color (Green Screen)

Source: https://www.techsmith.com/learn/tutorials/camtasia/how-to-remove-a-color/

- [x] **Hue slider parameter not exposed on ChromaKey effect** `src/camtasia/effects/visual.py` — `ChromaKey.hue property`

### Import & Manage Your Project Media

Source: https://www.techsmith.com/learn/tutorials/camtasia/import-manage-media/

- [x] **Rename media in bin** `src/camtasia/media_bin/media_bin.py` — `Media.rename / identity setter`
- [x] **Delete unused media (not on timeline)** `src/camtasia/media_bin/media_bin.py` — `MediaBin.delete_unused / unused_media property`
- [x] **Sort media by field** `src/camtasia/media_bin/media_bin.py` — `MediaBin.sorted(key, reverse)`
- [x] **Create proxy video** `src/camtasia/media_bin/media_bin.py` — `Media.create_proxy`
- [x] **Delete proxy video** `src/camtasia/media_bin/media_bin.py` — `Media.delete_proxy`
- [x] **Create reverse video** `src/camtasia/media_bin/media_bin.py` — `Media.reverse`
- [x] **Import folder of media** `src/camtasia/media_bin/media_bin.py` — `MediaBin.import_folder`
- [x] **Import multiple files at once** `src/camtasia/media_bin/media_bin.py` — `MediaBin.import_many(paths)`

### Import Presentation Slides

Source: https://www.techsmith.com/learn/tutorials/camtasia/import-powerpoint-slides/

- [x] **No direct .pptx file import** `src/camtasia/builders/slide_import.py` — `import_powerpoint(project, pptx_path)`
- [x] **No automatic slide-to-image extraction from PPTX** `src/camtasia/builders/slide_import.py` — `_extract_slides_as_images via python-pptx or LibreOffice`
- [x] **Default per-slide duration not sourced from project settings** `src/camtasia/builders/slide_import.py` — `use project.settings.default_image_duration`
- [x] **No automatic timeline markers from slide titles** `src/camtasia/builders/slide_import.py` — `add slide_titles param that emits markers`
- [x] **No append-to-current-end placement (always starts at 0)** `src/camtasia/builders/slide_import.py` — `cursor from track.end_time()`

### Reuse Media Across Projects (Library)

Source: https://www.techsmith.com/learn/tutorials/camtasia/library/

- [x] **No Library panel/model abstraction** `src/camtasia/library/library.py` — `Library class + Libraries container`
- [x] **No add-asset-to-library API** `src/camtasia/library/library.py` — `Library.add_asset(clip, name, use_canvas_size)`
- [x] **No add-timeline-selection-to-library** `src/camtasia/library/library.py` — `Library.add_timeline_selection`
- [x] **No insert-library-asset-on-timeline API** `src/camtasia/timeline/timeline.py` — `Timeline.add_library_asset`
- [x] **No create-custom-library API** `src/camtasia/library/library.py` — `Libraries.create(name, start_from=None)`
- [x] **No library folder / organization API** `src/camtasia/library/library.py` — `Library.create_folder / move`
- [x] **No .libzip import** `src/camtasia/library/libzip.py` — `import_libzip`
- [x] **No .libzip export** `src/camtasia/library/libzip.py` — `export_libzip`
- [x] **No default vs custom library distinction** `src/camtasia/library/library.py` — `Libraries.default / is_default`
- [x] **No Import Media to Library operation** `src/camtasia/library/library.py` — `Library.import_media`
- [x] **No bridge MediaBin -> Library** `src/camtasia/media_bin/media_bin.py` — `MediaBin.add_to_library`

### Close Timeline Gaps with Magnetic Tracks

Source: https://www.techsmith.com/learn/tutorials/camtasia/magnetic-tracks/

- [x] **Enabling magnetic on a track does not auto-close existing gaps** `src/camtasia/timeline/track.py` — `Track.magnetic setter should call pack_track when set to True`
- [x] **No automatic ripple-insert when dropping media between clips on magnetic track** `src/camtasia/timeline/track.py` — `Track.add_clip should ripple_insert when self.magnetic`
- [x] **No automatic ripple-close when moving clips on magnetic track** `src/camtasia/timeline/track.py` — `Track.move_clip should re-pack track when magnetic`
- [x] **No snap-to-clip-edge (only snap_to_grid exists)** `src/camtasia/operations/layout.py` — `snap_to_clip_edge(track, tolerance)`
- [x] **No all-tracks magnetic toggle on Timeline** `src/camtasia/timeline/timeline.py` — `Timeline.set_all_magnetic(value)`
- [x] **Groups-on-magnetic-tracks-keep-spaces rule not honored** `src/camtasia/operations/layout.py` — `pack_track preserve spacing for Group clips`

### Add Markers & Video Table of Contents

Source: https://www.techsmith.com/learn/tutorials/camtasia/markers-and-table-of-contents/

- [x] **Rename an existing marker in place** `src/camtasia/timeline/markers.py` — `MarkerList.rename(old_name, new_name)`
- [x] **Move/reposition existing marker without delete+add** `src/camtasia/timeline/markers.py` — `MarkerList.move(old_time, new_time)`
- [x] **Promote timeline marker to media marker (attach to clip)** `src/camtasia/timeline/track.py` — `Track.promote_marker_to_media`
- [x] **Demote media marker to timeline marker** `src/camtasia/timeline/track.py` — `Track.demote_marker_to_timeline`
- [x] **Export Smart Player TOC manifest (XML/JSON sidecar)** `src/camtasia/export/toc.py` — `export_toc`
- [x] **Export chapters in WebVTT/MP4 atom/YouTube list formats** `src/camtasia/export/chapters.py` — `export_chapters(format=...)`
- [x] **Navigate next/prev marker from a time** `src/camtasia/timeline/markers.py` — `MarkerList.next_after/prev_before`
- [x] **Remove single marker by name** `src/camtasia/timeline/markers.py` — `MarkerList.remove_by_name`
- [x] **Auto-generate slide markers from presentation metadata** `src/camtasia/operations/slide_markers.py` — `mark_slides_from_presentation`

### Edit Microsoft Teams & Other Meeting Recordings

Source: https://www.techsmith.com/learn/tutorials/camtasia/meeting-recordings/

- [x] **One-shot Suggested Edits helper (filler+pause removal)** `src/camtasia/audiate/project.py` — `apply_suggested_edits`

### Add Movement to Any Object (Motion Paths)

Source: https://www.techsmith.com/learn/tutorials/camtasia/motion-path/

- [x] **No dedicated MotionPath visual effect class** `src/camtasia/effects/visual.py` — `@register_effect('MotionPath') class`
- [x] **No Auto Orient / rotate-along-path property** `src/camtasia/effects/visual.py` — `MotionPath.auto_orient`
- [x] **No per-motion-point Line Type control (angle/curve/combination)** `src/camtasia/timeline/clips/base.py` — `set_position_keyframes_with_line_type`
- [x] **No bezier control-point / tangent handle API** `src/camtasia/timeline/clips/base.py` — `set_position_bezier_handles`
- [x] **No add_motion_point helper** `src/camtasia/timeline/clips/base.py` — `add_motion_point(time, x, y, line_type)`
- [x] **InterpolationType enum missing easi/easo/bezi members** `src/camtasia/types.py` — `InterpolationType.EASE_IN/EASE_OUT/BEZIER`
- [x] **No high-level apply_motion_path wrapper combining MotionPath effect + position keyframes** `src/camtasia/timeline/clips/base.py` — `apply_motion_path(points, easing, auto_orient, line_type)`

### Recommended Audio Edits

Source: https://www.techsmith.com/learn/tutorials/camtasia/recommended-audio-edits/

- [x] **Audio compression effect not wrapped** `src/camtasia/timeline/clips/base.py` — `add_compression(threshold,ratio,attack,release,makeup_gain)`
- [x] **Equalization not wrapped** `src/camtasia/timeline/clips/base.py` — `add_equalizer(bands)`
- [x] **Silence trim operation** `src/camtasia/operations/` — `trim_silences(clip, threshold_db, min_silence_ms)`

### Build Your First Video

Source: https://www.techsmith.com/learn/tutorials/camtasia/record-edit-share/

- [x] **No library asset import (intros, templates, graphics, music)** `src/camtasia/project.py` — `import_from_library / add_library_asset`
- [x] **No Camtasia Rev AI auto-styling presets** `src/camtasia/project.py` — `apply_rev_layout / apply_rev_style`
- [x] **No AI Noise Removal effect helper** `src/camtasia/project.py` — `add_ai_noise_removal`
- [x] **No canvas preview / render frame-at-time** `src/camtasia/project.py` — `render_canvas_preview / preview_frame`
- [x] **No intro/template asset insertion from bundled library** `src/camtasia/operations/template.py` — `insert_intro_template`

### Move Multiple Clips at Once

Source: https://www.techsmith.com/learn/tutorials/camtasia/ripple-move/

- [x] **ripple_move on single track (shift one clip and all clips to its right)** `src/camtasia/operations/layout.py` — `ripple_move(track, clip_id, delta_seconds)`
- [x] **ripple_move across multiple tracks** `src/camtasia/operations/layout.py` — `ripple_move_multi(tracks, clip_ids_per_track, delta_seconds)`

### Join Clips Together

Source: https://www.techsmith.com/learn/tutorials/camtasia/stitch-media/

- [x] **No unstitch/split StitchedMedia back into segments** `src/camtasia/timeline/track.py` — `Track.unstitch_clip(clip_id)`
- [x] **join_clips does not validate same-source media** `src/camtasia/timeline/track.py` — `add same-src check to join_clips`
- [x] **join_clips does not validate adjacency** `src/camtasia/timeline/track.py` — `add adjacency check to join_clips`
- [x] **No Track.stitch_adjacent convenience** `src/camtasia/timeline/track.py` — `stitch_adjacent(clip_ids)`
- [x] **No auto-stitch-on-cut behavior** `src/camtasia/operations/` — `post-cut hook to re-stitch adjacent same-source segments`

### Build Your Color Palette (Themes)

Source: https://www.techsmith.com/learn/tutorials/camtasia/themes/

- [x] **No .camtheme export/import (file-based theme sharing)** `src/camtasia/themes.py` — `export_theme / import_theme`
- [x] **No Theme.logo_path attribute** `src/camtasia/themes.py` — `Theme.logo_path`
- [x] **No theme manager / named registry** `src/camtasia/themes.py` — `ThemeManager.create/rename/delete`
- [x] **apply_theme does not handle 'annotation background' slot distinct from fill** `src/camtasia/themes.py` — `annotation-background mapping`
- [x] **No add_annotation_from_theme helper** `src/camtasia/themes.py` — `add_annotation_from_theme`
- [x] **No stroke-width/stroke-style mapping in apply_theme** `src/camtasia/themes.py` — `apply_theme stroke-width`
- [x] **Theme has fixed slots; no Add Color / dynamic accent-N support** `src/camtasia/themes.py` — `Theme.add_color / dynamic slots`

### Translate Your Script, Audio, and Captions

Source: https://www.techsmith.com/learn/tutorials/camtasia/translate/

- [x] **Translate script to target language (overwrites transcript)** `src/camtasia/audiate/project.py` — `AudiateProject.translate_script(target_language)`
- [x] **Generate TTS audio from translated script** `src/camtasia/audiate/project.py` — `AudiateProject.generate_audio(voice, apply_to_entire_project=True)`
- [x] **Generate AI video avatar for translated audio** `src/camtasia/audiate/project.py` — `AudiateProject.generate_avatar`
- [x] **Export translated captions to .srt per language** `src/camtasia/export/captions.py` — `export_captions_multilang`
- [x] **Supported-language enumeration** `src/camtasia/audiate/project.py` — `SUPPORTED_TRANSLATION_LANGUAGES`
- [x] **Multi-language package export** `src/camtasia/export/captions.py` — `export_multilang_package`
- [x] **Writable project language (currently read-only)** `src/camtasia/audiate/project.py` — `AudiateProject.language setter`
- [x] **Save-as helper for language-suffixed copies** `src/camtasia/audiate/project.py` — `save_as_translation(language_code)`

### How to Use a Template

Source: https://www.techsmith.com/learn/tutorials/camtasia/use-a-template/

- [x] **No replace_placeholder supporting Ripple Replace / Clip Speed / From Start/End modes** `src/camtasia/operations/template.py` — `replace_placeholder(placeholder, new_media, mode=...)`
- [x] **No .camtemplate import/install** `src/camtasia/operations/template.py` — `install_camtemplate / import_template`
- [x] **No new_project_from_template(name)** `src/camtasia/operations/template.py` — `new_project_from_template`
- [x] **No Template Manager (list/rename/delete installed templates)** `src/camtasia/operations/template.py` — `TemplateManager`
- [x] **PlaceholderMedia.set_source raises TypeError; no replace_with(media, mode) convenience** `src/camtasia/timeline/clips/placeholder.py` — `PlaceholderMedia.replace_with`

### Remove a Background from Your Video

Source: https://www.techsmith.com/learn/tutorials/camtasia/video-background-removal/

- [x] **AI Background Removal visual effect not implemented (distinct from ChromaKey/MediaMatte)** `src/camtasia/effects/visual.py` — `@register_effect('BackgroundRemoval') class with intensity/threshold/edge-softness/invert parameters`
- [x] **No convenience add_background_removal() helper on BaseClip** `src/camtasia/timeline/clips/base.py` — `add_background_removal near add_media_matte`
- [x] **BACKGROUND_REMOVAL missing from types enum and schema effect-name enum** `src/camtasia/types.py` — `BACKGROUND_REMOVAL constant`
- [x] **ChromaKey effect marked unverified — no fixture-backed parameter validation** `src/camtasia/effects/visual.py` — `verify ChromaKey parameters against fixture`

### Explore the Timeline

Source: https://www.techsmith.com/learn/tutorials/camtasia/video-editing/

- [x] **Timeline UI zoom level + fit-to-project** `src/camtasia/timeline/timeline.py` — `zoom_level / fit_to_project`
- [x] **Per-track and global track height** `src/camtasia/timeline/track.py` — `Track.track_height + Timeline.track_height_scale`
- [x] **Detach/Reattach Timeline (Ctrl+3)** `src/camtasia/timeline/timeline.py` — `detached / detach / reattach`
- [x] **J/K/L variable-speed playback transport** `src/camtasia/timeline/timeline.py` — `playback_rate / play / pause`
- [x] **Track enabled (eye icon) runtime on/off distinct from lock** `src/camtasia/timeline/track.py` — `Track.enabled`
- [x] **Quiz/Marker view show-hide toggles** `src/camtasia/timeline/markers.py` — `markers_view_visible / quiz_view_visible`
- [x] **Track scroll position** `src/camtasia/timeline/timeline.py` — `Timeline.scroll_offset`

### Add a Transition

Source: https://www.techsmith.com/learn/tutorials/camtasia/video-transitions/

- [x] **Gradient Wipe transition preset missing** `src/camtasia/timeline/transitions.py` — `add_gradient_wipe`
- [x] **Card Swipe transition preset missing** `src/camtasia/timeline/transitions.py` — `add_card_swipe`
- [x] **Cube Rotate transition preset missing** `src/camtasia/timeline/transitions.py` — `add_cube_rotate`
- [x] **Swap transition preset missing** `src/camtasia/timeline/transitions.py` — `add_swap`

### Watermark Your Videos

Source: https://www.techsmith.com/learn/tutorials/camtasia/video-watermark/

- [x] **scale parameter on add_watermark** `src/camtasia/project.py` — `add_watermark(scale=...)`
- [x] **x_offset parameter on add_watermark** `src/camtasia/project.py` — `add_watermark(x_offset=...)`
- [x] **y_offset parameter on add_watermark** `src/camtasia/project.py` — `add_watermark(y_offset=...)`
- [x] **Text watermark variant (copyright/website)** `src/camtasia/project.py` — `add_text_watermark`
- [x] **builders/video_production.py add_watermark does not expose scale/position/text** `src/camtasia/builders/video_production.py` — `add_watermark`

### Visual Effects Overview

Source: https://www.techsmith.com/learn/tutorials/camtasia/visual-effects/

- [x] **Color Tint (two-color light/dark tint)** `src/camtasia/effects/visual.py` — `add @register_effect("ColorTint") class with light-color/dark-color RGBA parameters`
- [x] **Sepia (Mac)** `src/camtasia/effects/visual.py` — `add @register_effect("Sepia") class`
- [x] **Border (colored border around media)** `src/camtasia/effects/visual.py` — `add @register_effect("Border") class with color RGBA + thickness parameters`
- [x] **CRT Monitor (scanlines + curvature)** `src/camtasia/effects/visual.py` — `add @register_effect("CRTMonitor") class with scanline/curvature/intensity parameters`
- [x] **Cursor Path Creator** `src/camtasia/effects/cursor.py` — `add @register_effect("CursorPathCreator") class`
- [x] **Device Frame effect (distinct from builders/device_frame.py overlay)** `src/camtasia/effects/visual.py` — `add @register_effect("DeviceFrame") class with frame-id parameter`
- [x] **Keystroke effect (Mac)** `src/camtasia/effects/visual.py` — `add @register_effect("Keystroke") class`
- [x] **Interactive Hotspot** `src/camtasia/effects/visual.py` — `add @register_effect("Hotspot") class with url/action/pause parameters`
- [x] **Mosaic / pixelate (Mac)** `src/camtasia/effects/visual.py` — `add @register_effect("Mosaic") class with pixel-size parameter`
- [x] **Outline Edges (line-drawing)** `src/camtasia/effects/visual.py` — `add @register_effect("OutlineEdges") class with threshold/intensity parameters`
- [x] **Reflection effect** `src/camtasia/effects/visual.py` — `add @register_effect("Reflection") class with opacity/distance/falloff parameters`
- [x] **Static Noise (TV static)** `src/camtasia/effects/visual.py` — `add @register_effect("StaticNoise") class with intensity parameter`
- [x] **Tiling (repeat pattern)** `src/camtasia/effects/visual.py` — `add @register_effect("Tiling") class with scale/positionX/positionY/opacity parameters`
- [x] **Torn Edge** `src/camtasia/effects/visual.py` — `add @register_effect("TornEdge") class with jaggedness/margin parameters`
- [x] **Window Spotlight (Mac)** `src/camtasia/effects/visual.py` — `add @register_effect("WindowSpotlight") class`
- [x] **Vignette** `src/camtasia/effects/visual.py` — `add @register_effect("Vignette") class with amount/falloff/color parameters`
- [x] **Background Removal (AI, non-green-screen) distinct from ChromaKey** `src/camtasia/effects/visual.py` — `add @register_effect("BackgroundRemoval") class`
- [x] **Freeze Region (freeze a sub-region of the clip)** `src/camtasia/effects/visual.py` — `add @register_effect("FreezeRegion") class with positionX/positionY/width/height parameters`
- [x] **Motion Path as visual effect** `src/camtasia/effects/visual.py` — `add @register_effect("MotionPath") class with path keyframes`
- [x] **BlurRegion defined but not registered** `src/camtasia/effects/visual.py` — `add @register_effect("BlurRegion") decorator to existing class after fixture verification`

_Total: 131 remaining gaps (178 implemented) across 54 tutorials (42 false positives removed during adversarial verification)._

## Completed Major Features

All high-level API improvement ideas from demo production are implemented: VideoProductionBuilder, ScreenRecordingSync, import_media() validation, ProgressiveDisclosure, Project.clean_inherited_state(), MarkerList.clear()/replace(), Project.remove_orphaned_media(), and Recap/tile layout helper.

## Feature Gaps (discovered during adversarial review & integration testing)

### Clip API
- [already-implemented] `BaseClip.unmute()` — reverses `mute()` on all clip types including Group/StitchedMedia/UnifiedMedia
- [already-implemented] `UnifiedMedia.remove_all_effects()` clears effects on both video/audio sub-clips
- [already-implemented] `UnifiedMedia.has_effects/effect_count/effect_names` aggregate from video+audio sub-clips
- [already-implemented] `Callout.text` setter should update `textAttributes` `rangeEnd` to match new text length
- [already-implemented] `BaseClip.add_keyframe()` creates `animationTracks.visual` entries for visual parameters (translation/scale/rotation/crop/opacity)
- [already-implemented] `set_position_keyframes` / `set_scale_keyframes` / `set_rotation_keyframes` / `set_crop_keyframes` create `animationTracks.visual` entries
- [already-implemented] `add_progressive_disclosure(replace_previous=True)` already implemented

### Track API
- [already-implemented] `clip_after()` docstring clarified as at-or-after; `clip_strictly_after()` added as strictly-after variant
- [already-implemented] `insert_gap()` and `shift_all_clips()` transitions handled that may become invalid
- [already-implemented] `merge_adjacent_clips()` doesn't verify clips are actually adjacent before merging
- [already-implemented] `set_segment_speeds()` uses float accumulation for `mediaStart` — should use Fraction
- [already-implemented] `split_clip()` uses raw `Fraction(orig_scalar)` instead of `_parse_scalar()` — inconsistent precision

### Timeline API
- [already-implemented] `clips_of_type()` is O(n²) and misattributes nested clips to `None` track
- [already-implemented] `shift_all()` doesn't shift transition or effect `start` times
- [already-implemented] `Timeline.insert_gap()` / `remove_gap()` shift timeline markers (transitions use clip IDs and don't need adjustment)
- [already-implemented] `flatten_to_track()` warns when source tracks have transitions that will be dropped
- [already-implemented] `build_section_timeline()` helper exists in timeline.py

### Validation
- [already-implemented] Validate `timeline.id` exists and doesn't collide with clip IDs
- [already-implemented] Validate `GenericBehaviorEffect` has required `in`/`center`/`out` phases
- [already-implemented] Validate overlapping clips on same track (Camtasia tracks are single-occupancy)
- [already-implemented] Flag explicit `null` in transition `leftMedia`/`rightMedia` (format says omit, not null)
- [ ] **Expand `project.validate()` to catch every failure mode Camtasia itself rejects, with specific error messages.** Today we have 34 validation rules; the goal is that if `project.save()` produces a file Camtasia can't open, our own validator should have flagged the problem first with a precise location ("Clip `foo` on track `bar` has zero duration"). Driven by failing integration tests: every Camtasia rejection that isn't already caught by `validate()` is a bug to file here.
- [ ] **Kitchen-sink integration test bisection helper.** When a large multi-feature integration test fails, we need a way to quickly narrow down which feature caused the rejection. Proposed: a `project.validate(strict=True)` mode that simulates Camtasia's acceptance rules more aggressively, plus a `bisect_features()` helper that binary-searches a project by temporarily removing subsets of clips/effects and re-saving until it finds the minimal failing subset. Lowers the cost of multi-feature tests.

### Effects
- [already-implemented] Typed wrapper classes added for LutEffect, Emphasize, Spotlight, ColorAdjustment, BlendModeEffect, MediaMatte — all registered with effect_from_dict
- [already-implemented] `BlurRegion` registered via @register_effect with unverified-fixture warning in docstring
- [already-implemented] `DropShadow.enabled` / `CursorShadow.enabled` docstrings clarify that setting only updates defaultValue, not existing keyframes

### Export
- [already-implemented] EDL exporter recurses into Groups/StitchedMedia (opt-out via include_nested=False)
- [already-implemented] CSV and report (JSON + markdown) exporters recurse into Groups/StitchedMedia with timeline-absolute positions
- [already-implemented] EDL `UnifiedMedia` source is always `AX` — should use video sub-clip's source
- [already-implemented] SRT exporter warns when no markers to export
- [already-implemented] `timeline_json` now includes effects, transitions, and per-clip metadata (opt-out via kwargs; bumped version to 1.1)

### Builders
- [already-implemented] `timeline_builder.add_title()` ignores `subtitle` parameter (dead code)
- [already-implemented] `tile_layout.add_grid` auto-fits images to cell size by default (opt-out via fit_to_cell=False)
- [already-implemented] `screenplay_builder._find_audio_file()` only searches `.wav` — should support `.mp3`, `.m4a`

### Schema
- [already-implemented] Schema `effect.effectName` enum no longer includes behavior names (moved to GenericBehaviorEffect only)
- [already-implemented] Schema `effect` definition doesn't require `bypassed` (format reference says required)
- [already-implemented] Non-schema transition names (`FadeThroughColor`, `SlideUp`, etc.) documented via docstring warnings

### Behavior Presets
- [ ] Preset values don't fully match real TechSmith samples (ongoing refinement)
- [already-implemented] `reveal` preset start value documented; clamped by get_behavior_preset() for short clips. Needs real-Camtasia verification to tune further.
- [already-implemented] `BehaviorInnerName` enum missing `'fading'` phase name
- [already-implemented] `pulsating` center phase `offsetBetweenCharacters` should be `49392000` (not `0`)

### Infrastructure
- [already-implemented] `media_bin.import_media()` appends _1/_2/... suffix on directory collision
- [already-implemented] `media_bin._visual_track_to_json()` uses `sampleRate=0` for video (should be frame rate)
- [already-implemented] `media_bin` visual/audio track JSONs already include `tag: 0` field
- [already-implemented] `scalar_to_string()` return type annotation is `str | int` and docstring explains the int return
- [already-implemented] `parse_scalar()` docstring documents the 10_000 denominator cap tradeoff
- [already-implemented] `history.py` `undo()`/`redo()` docstrings warn about stale nested references (already present)

### Known Design Decisions (not bugs — documented to avoid re-reporting)
- `UnifiedMedia` caches video/audio child clips without invalidation — works because dict references are shared; only breaks if someone replaces the entire sub-dict (not a real-world pattern)
- `BaseClip.clone()` sets `id=-1` sentinel — caller must reassign before saving; no auto-enforcement by design
- `BaseClip.__eq__` uses `id` comparison — cloned clips with `id=-1` compare equal; known tradeoff for simplicity
- `BaseClip.gain` reads `attributes.gain` which only applies to AMFile — returns 1.0 default for other clip types; `is_silent` checks both `gain` and `volume` as a workaround
- `BaseClip.mute()` sets `attributes.gain=0` for non-Group/non-StitchedMedia/non-UnifiedMedia clips — only effective for AMFile; VMFile/Callout/IMFile don't use `attributes.gain`
- `GroupTrack.add_clip()` auto-ID is only locally unique — warning emitted; caller should pass `next_id` for global uniqueness
- `set_speed()` propagates `mediaStart` from wrapper to UnifiedMedia sub-clips — correct when they're in sync (the normal case); would be wrong if sub-clips had independent mediaStart (not observed in real projects)
- `Callout.text` setter updates all `rangeEnd` values to new text length — correct for single-range text; destroys multi-range per-character formatting (a known limitation)
- `fade_out()`/`fade()`/`set_opacity_fade()` use clip `duration` for keyframe timing — correct for normal-speed clips; may be wrong for speed-changed clips where keyframes should use `mediaDuration`
- `duplicate_clip` uses ad-hoc `_remap_ids` instead of `_remap_clip_ids_with_map` — works for current nesting depths but less robust than the timeline-level remapper
- `Effect.__eq__` uses identity (`is`) not value equality — intentional for mutation tracking
- `GenericBehaviorEffect.parameters` returns `{}` — intentional since behavior params live in phases, not at top level
- `GenericBehaviorEffect.get_parameter()`/`set_parameter()` raise `NotImplementedError` — intentional LSP violation; use phase accessors instead
- `BehaviorPhase` objects created fresh on each property access — no caching; mutations propagate via shared dict reference
- `_flatten_parameters` uses negative-condition list — fragile but correct for all known parameter shapes
- `save()` warns on validation errors but doesn't prevent saving — by design; `compact()` raises on errors
- `all_clips()` creates ephemeral wrappers for StitchedMedia/UnifiedMedia sub-clips — mutations propagate via shared dict; identity comparisons fail
- `clips_in_range()` only checks top-level clips — by design; use `all_clips()` for nested
- `add_gradient_background()` uses `time.time()` in source path — non-deterministic but functional
- Non-schema transition names (`FadeThroughColor`, `SlideUp/Down`, `Wipe*`) — documented with warnings in docstrings; kept for forward-compatibility
- `add_border()`/`add_colorize()` use effect names not in schema — may be valid in newer Camtasia versions
- `group_clips_across_tracks()` emits v10-style typed metadata regardless of project version — works for v10+; may cause silent repair on v6/v8
- `scale_all_durations()` recalculates scalar from new duration/old mediaDuration — changes playback speed as side effect; documented behavior
- `_check_timing_consistency` uses 1% tolerance — generous for large durations but avoids false positives on rational arithmetic rounding
- `EffectName` enum missing behavior effect names — behavior effects use `GenericBehaviorEffect._type` dispatch, not the enum
- `_BehaviorEffectData` TypedDict can't declare `in`/`center`/`out` keys — Python keyword limitation
- `RGBA.__eq__` uses `type(self)` not `isinstance` — prevents subclass equality; intentional strictness
- `merge_tracks()` in `operations/merge.py` silently drops transitions from source tracks — known limitation; transitions require complex ID remapping that isn't implemented yet
- `shift_all()` on Timeline doesn't shift timeline markers — known limitation; markers are in `parameters.toc` and would need separate scaling
- `rescale_project()` doesn't scale keyframe timing in `parameters`, `animationTracks.visual`, or behavior effect phase timing — known limitation; only clip-level and effect-level `start`/`duration` are scaled
- `add_screen_recording()` creates UnifiedMedia and sub-clips without `metadata`, `parameters`, or `animationTracks` keys on the wrapper — Camtasia silently repairs on load; internal Group tracks also missing format keys (`ident`, `audioMuted`, etc.)
- `insert_track()` creates track data dicts missing some format-reference keys (`ident`, `audioMuted`, `videoHidden`, `magnetic`, `matte`, `solo`) — these exist in `trackAttributes` but not in the track dict itself
- `mediaStart` is NOT scaled for regular clips (VMFile, AMFile, IMFile, Callout, ScreenVMFile) in `rescale_project()` — this is CORRECT because `mediaStart` is a source-media offset, not a timeline position; only StitchedMedia internal sub-clips need `mediaStart` scaling
- `insert_gap()` transition adjustment checks for `t['start']` which transitions don't have per the format spec — dead code; transitions are positioned by `leftMedia`/`rightMedia` clip references, not absolute `start` times
- `move_clip_to_track()` double-remaps then restores top-level ID, leaving `id_map` with stale entry — `assetProperties.objects` references may point to wrong ID for moved Group clips
- `remove_gap()` only shifts clips starting at or after `position + gap_duration` — clips within the gap region are left in place; caller is expected to verify the gap is empty
- `add_gradient_background()` creates sourceBin entry pointing to a non-existent shader file — the shader is a virtual media type that Camtasia generates internally; the path is a placeholder
- `average_clip_duration_seconds` and `clip_count` count top-level clips only — consistent with each other but different from `all_clips()` which includes nested clips; this is by design
- `merge_projects()` doesn't copy source track attributes (`audioMuted`, `videoHidden`, `solo`, etc.) — creates default attributes for merged tracks
- `merge_tracks()` `_remap_clip_ids` doesn't remap `assetProperties.objects` references — use `merge_projects()` for full-fidelity merging

### Additional Known Design Decisions (added after Round 110)

- `copy_to_track()` uses sequential IDs from `_remap_clip_ids_with_map` starting at `_next_clip_id()` — for compound clips (Group/UnifiedMedia/StitchedMedia), nested IDs are sequential and globally unique because `_next_clip_id()` scans all tracks. The top-level ID self-mapping in `id_map` is harmless.
- `set_audio_speed()` only corrects the first speed-changed AMFile — by design, the function targets a single audio clip. Multiple speed-changed audio clips require separate calls.
- `diff_projects()` compares tracks by positional index — track insertions/deletions cause renumbering, making the diff semantically misleading. This is a known limitation.
- `behavior_presets.py` `get_behavior_preset()` sets `duration = duration_ticks` (full clip duration) — Camtasia clips behavior effects at the clip boundary, so `start + duration > clip_duration` is valid. The lower_third template confirms this pattern.
- `_pauses_with_positions()` uses `max(0, idx)` for pauses before the first VO — maps to `after_vo_index=0`, placing the pause after the first VO. This is the current design; a leading-pause sentinel would require changes to `build_from_screenplay`.
- `UnifiedMedia` inherits `remove_all_effects()`, `remove_effect_by_name()`, `is_effect_applied()` from BaseClip — these operate on the wrapper's empty effects list. Feature gap: should redirect to children or raise TypeError.
- `swap_clips()` only swaps `start` times, not positions — clips of different durations will create gaps. This is the documented behavior.
- `group_clips()` ID counter is not incremented after Group ID assignment — safe because `_next_clip_id()` scans all medias on next call.

## Tooling

### Linting with Ruff ✅

[Ruff](https://docs.astral.sh/ruff/) is configured in `pyproject.toml` (`[tool.ruff]`) and enforced in CI (`.github/workflows/tests.yml`). Selected rules: `E` (pycodestyle errors), `F` (pyflakes), `I` (isort), `UP` (pyupgrade — enforce `X | Y` over `Union[X, Y]`), `W` (pycodestyle warnings).

### Type Checking with mypy ✅

[mypy](https://mypy-lang.org/) is configured in `pyproject.toml` (`[tool.mypy]`) and enforced in CI. Strict mode enabled for `src/camtasia/`.

### Additional Known Design Decisions (added after Round 123)

- `_PerMediaMarkers` silently drops markers on IMFile/ScreenIMFile clips — `mediaDuration=1` causes the `media_offset >= media_dur` filter to reject all markers. Known limitation.
- `validate_structure()` duplicate-ID check only recurses one level into Groups/StitchedMedia/UnifiedMedia — deeply nested duplicate IDs go undetected. Known limitation.
- `repair()` doesn't handle cascading overlaps — when a clip is reduced to zero duration, the next pair isn't re-checked. Multiple `repair()` calls may be needed.
- `Timeline.insert_gap()`/`remove_gap()` don't shift timeline markers — markers become misaligned after gap operations. Known limitation.
- `duplicate_track()` returns Track without `_all_tracks`/`_timeline_id` — `_next_clip_id()` on the returned Track only scans its own medias. Known limitation.
- `is_muted` for UnifiedMedia only checks `audio.attributes.gain`, ignores `parameters.volume` — if volume is set to 0 via the volume setter, `is_muted` returns False. Known limitation.
- `Group.set_internal_segment_speeds()` uses float-based `seconds_to_ticks()` for `mediaStart` — can cause frame-level drift for segments deep into a recording. Known limitation.
- `ripple_delete()` threshold `>= target_start + gap` is BY DESIGN — only shifts clips after the deleted clip's end, not clips overlapping with it.
- `get_behavior_preset()` clamps `start` to `duration_ticks - 1` — Camtasia clips behavior effects at the clip boundary, so `start + duration > clip_duration` is valid.
- `_VO_RE` regex requires specific bold-colon markdown pattern — screenplays using different formatting will silently produce empty VO blocks. Known limitation.
- `set_audio_speed()` final overwrite of target_clip duration bypasses `rescale_project()`'s overlap fix — users should call `project.repair()` after `set_audio_speed()` if 1-tick overlaps are a concern.
