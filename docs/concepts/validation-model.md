# Validation Model

Camtasia's `.tscproj` format is reverse-engineered — there is no official spec.
Invalid JSON can cause Camtasia to silently drop data or crash on load.
pycamtasia includes a structural validation system that catches common issues
before they reach the application.

## What `validate_all` checks

The `validate_all` function runs a suite of checks against the raw project
data dict:

```python
from camtasia import validate_all, load_project

project = load_project("my_video.cmproj")
issues = validate_all(project._data)

for issue in issues:
    print(f"[{issue.level}] {issue.message}")
```

### Checks performed

| Check | Level | What it catches |
|-------|-------|-----------------|
| Duplicate clip IDs | error | Two clips sharing the same integer ID |
| Track index mismatch | warning | `trackIndex` value doesn't match array position |
| Transition references | error | Transition pointing to a clip ID that doesn't exist on the track |
| Transition completeness | error | Transition missing both `leftMedia` and `rightMedia` |
| Track attributes count | warning | `trackAttributes` array length doesn't match tracks count |
| Source bin references | error | Clip `src` pointing to a source bin ID that doesn't exist |
| Group required fields | warning | Group clip missing required parameters or metadata keys |
| Clip timing | warning | Clips with negative start or non-positive duration |
| Edit rate | — | Verifies the edit rate is the expected 705,600,000 |
| Source bin IDs | — | Checks for duplicate IDs in the source bin |
| Timing consistency | warning | `mediaDuration` doesn't match `duration / scalar` |
| Compound invariants | — | Structural invariants for compound clip types |
| Timeline ID uniqueness | — | Duplicate IDs across the entire timeline |
| Behavior effect structure | — | Validates behavior effect JSON structure |
| Clip overlap | — | Detects overlapping clips on the same track |
| Transition null endpoints | — | Transitions with null endpoint references |

All checks recurse into Group clips and StitchedMedia to validate nested
structures.

## Severity levels

Each `ValidationIssue` has a `level` field:

- **`error`** — structural problem that will likely cause Camtasia to
  malfunction. Examples: duplicate clip IDs, broken source references,
  invalid transition references.
- **`warning`** — potential issue that may cause subtle problems. Examples:
  mismatched track indices, missing optional metadata, timing inconsistencies.

```python
from camtasia.validation import ValidationIssue

issue = ValidationIssue(
    level="error",
    message="Duplicate clip ID 42 in: ['track[0]', 'track[1]']",
    source_id=42,
)
```

## Automatic validation on save

`project.save()` runs validation automatically and emits Python warnings for
any errors found. The save proceeds regardless — validation is advisory, not
blocking.

## Schema validation

For stricter checking, `validate_against_schema` validates against a bundled
JSON Schema (requires the `jsonschema` package):

```python
from camtasia.validation import validate_against_schema

issues = validate_against_schema(project._data)
```

## The Camtasia integration test pattern

Because the format is reverse-engineered, structural validation alone isn't
sufficient. The project follows a mandatory integration test pattern:

1. Save the project JSON before your change (backup)
2. Apply your change and save
3. Open the result in Camtasia — check for exceptions, visual correctness,
   playback
4. Compare JSON diff to verify only intended changes were made

The `scripts/camtasia_validate.sh` script automates opening projects in
Camtasia on macOS.

## Extending validation

To add a new check, write a function that takes the raw project data dict and
returns a list of `ValidationIssue` objects:

```python
def _check_my_invariant(data: dict) -> list[ValidationIssue]:
    issues = []
    # ... inspect data ...
    if problem_found:
        issues.append(ValidationIssue("warning", "Description of the issue"))
    return issues
```

Then add it to the `validate_all` function's check list.

## See also

- {doc}`/concepts/project-model` — the Project that validation checks
- {doc}`/concepts/camtasia-file-format` — the JSON structure being validated
- {doc}`/api/validation` — full validation API reference
- {doc}`/guides/best-practices` — development best practices
