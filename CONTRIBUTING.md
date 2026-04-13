# Contributing to pycamtasia

## Setup

```bash
git clone <repo-url> && cd pycamtasia
pip install -e '.[test]'
```

## Running Tests

```bash
pytest                  # All unit tests (~13s)
pytest --cov            # With coverage (~27s, must be 100%)
pytest -m integration   # Integration tests (requires Camtasia on macOS)
```

## Key Rules

1. **Clip mutations must cascade-delete transitions.** Never delete clips by mutating `_data['medias']` directly — use `track.remove_clip()`, which removes transitions referencing the clip.

2. **Parameter keys use hyphens.** Camtasia's JSON uses `mask-shape`, not `mask_shape`. Python properties handle the mapping, but raw dicts must use hyphens.

3. **Effects use plain scalar format.** Parameters are flat: `{"defaultValue": 16.0, "type": "double", "interp": "linr"}`. No extra nesting.

4. **Camtasia integration test is mandatory** for any change affecting `.tscproj` output. The JSON format is reverse-engineered — always validate in the real app.

5. **100% line coverage required.** The build fails below 100%.

6. **Use [Conventional Commits](https://www.conventionalcommits.org/).** Examples: `feat: add mask effect`, `fix: cascade-delete on group clips`, `test: cover edge case in split`.

## How To: Add a New Effect

Follow the pattern in `src/camtasia/effects/base.py` → `add_drop_shadow`:

1. Define the effect class (or reuse an existing one).
2. Add a factory/convenience method on the clip or effect list.
3. Use hyphenated parameter keys and plain scalar format.
4. Add unit tests. Verify in Camtasia if it affects output.

## How To: Add a New Transition

Follow the pattern in `src/camtasia/timeline/transitions.py` → `add_dissolve`:

1. Add the transition type constant if needed.
2. Implement the builder method on `TransitionList`.
3. Ensure cascade-delete is covered for clips adjacent to the transition.
4. Add unit tests. Verify in Camtasia.

## How To: Add a Behavior Preset

Add the preset dict to `src/camtasia/templates/behavior_presets.py`. Follow the existing entries for structure and naming. Add a test that round-trips the preset.

## Don't Guess at JSON

Always reverse-engineer from real Camtasia output:

1. Perform the action in the Camtasia GUI.
2. Diff the `.tscproj` JSON before and after.
3. Implement based on the diff.
