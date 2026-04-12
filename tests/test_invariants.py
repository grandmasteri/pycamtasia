"""Property-based tests verifying structural invariants after random operation sequences."""
from __future__ import annotations

from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

from camtasia.timeline.track import Track

RESOURCES = Path(__file__).parent.parent / 'src' / 'camtasia' / 'resources'

TICK = 705_600_000  # ~23.5 s at 30 fps editRate


def _make_track():
    data = {'trackIndex': 0, 'medias': [], 'transitions': []}
    return Track({'ident': 'test'}, data), data


# ------------------------------------------------------------------
# 1. No duplicate clip IDs after any add/remove/duplicate sequence
# ------------------------------------------------------------------

@given(st.lists(st.sampled_from(['add', 'remove', 'duplicate']), min_size=1, max_size=10))
@settings(max_examples=50, deadline=None)
def test_no_duplicate_ids_after_operations(operations):
    """Clip IDs must be unique after any sequence of operations."""
    track, data = _make_track()
    clip_ids: list[int] = []

    for op in operations:
        if op == 'add':
            clip = track.add_clip('AMFile', 1, len(clip_ids) * TICK, TICK)
            clip_ids.append(clip.id)
        elif op == 'remove' and clip_ids:
            track.remove_clip(clip_ids.pop(0))
        elif op == 'duplicate' and clip_ids:
            try:
                new_clip = track.duplicate_clip(clip_ids[-1])
                clip_ids.append(new_clip.id)
            except Exception:
                pass

    all_ids = [m['id'] for m in data.get('medias', [])]
    assert len(all_ids) == len(set(all_ids)), f'Duplicate IDs found: {all_ids}'


# ------------------------------------------------------------------
# 2. No stale transition references after any clip mutation
# ------------------------------------------------------------------

@given(st.lists(st.sampled_from(['add', 'remove', 'add_transition']), min_size=1, max_size=15))
@settings(max_examples=50, deadline=None)
def test_no_stale_transitions_after_operations(operations):
    """Transitions must only reference existing clip IDs."""
    track, data = _make_track()
    clip_ids: list[int] = []

    for op in operations:
        if op == 'add':
            clip = track.add_clip('AMFile', 1, len(clip_ids) * TICK, TICK)
            clip_ids.append(clip.id)
        elif op == 'remove' and clip_ids:
            track.remove_clip(clip_ids.pop(0))
        elif op == 'add_transition' and len(clip_ids) >= 2:
            try:
                track.transitions.add_fade_through_black(
                    clip_ids[-2], clip_ids[-1], TICK // 2,
                )
            except Exception:
                pass

    existing_ids = {m['id'] for m in data.get('medias', [])}
    for trans in data.get('transitions', []):
        left = trans.get('leftMedia')
        right = trans.get('rightMedia')
        if left is not None:
            assert left in existing_ids, f'Stale leftMedia={left}, existing={existing_ids}'
        if right is not None:
            assert right in existing_ids, f'Stale rightMedia={right}, existing={existing_ids}'


# ------------------------------------------------------------------
# 3. validate() returns no errors after any operation sequence
# ------------------------------------------------------------------

@given(st.lists(st.sampled_from(['add', 'remove', 'clear']), min_size=1, max_size=10))
@settings(max_examples=30, deadline=None)
def test_validate_clean_after_operations(operations):
    """Project.validate() should find no errors after any operation sequence."""
    from camtasia import load_project

    proj = load_project(RESOURCES / 'new.cmproj')
    track = proj.timeline.add_track('Test')
    clip_ids: list[int] = []

    for op in operations:
        if op == 'add':
            clip = track.add_clip('AMFile', None, len(clip_ids) * TICK, TICK)
            clip_ids.append(clip.id)
        elif op == 'remove' and clip_ids:
            track.remove_clip(clip_ids.pop(0))
        elif op == 'clear':
            track.clear()
            clip_ids.clear()

    errors = [i for i in proj.validate() if i.level == 'error']
    assert errors == [], f'Validation errors: {[e.message for e in errors]}'
