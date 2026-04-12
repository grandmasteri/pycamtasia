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


# ------------------------------------------------------------------
# 4. Split clip preserves total duration
# ------------------------------------------------------------------

@given(st.floats(min_value=0.1, max_value=0.9))
@settings(max_examples=30, deadline=None)
def test_split_preserves_total_duration(split_fraction):
    """Splitting a clip should preserve the total duration."""
    track, _ = _make_track()
    dur_ticks = TICK * 10  # 10 seconds
    clip = track.add_clip('AMFile', 1, 0, dur_ticks)
    original_dur = clip.duration

    split_point = split_fraction * 10.0  # 0.1s to 9.0s
    left, right = track.split_clip(clip.id, split_point)

    assert left.duration + right.duration == original_dur


# ------------------------------------------------------------------
# 5. Track.clear() leaves no clips or transitions
# ------------------------------------------------------------------

@given(st.integers(min_value=1, max_value=10))
@settings(max_examples=20, deadline=None)
def test_clear_leaves_empty_track(num_clips):
    """clear() should remove all clips and transitions."""
    track, data = _make_track()
    ids = []
    for i in range(num_clips):
        clip = track.add_clip('AMFile', 1, i * TICK, TICK)
        ids.append(clip.id)
    # Add some transitions
    if len(ids) >= 2:
        data.setdefault('transitions', []).append(
            {'leftMedia': ids[0], 'rightMedia': ids[1], 'name': 'FadeThroughBlack', 'duration': 100}
        )
    track.clear()
    assert data.get('medias', []) == []
    assert data.get('transitions', []) == []


# ------------------------------------------------------------------
# 6. Duplicate clip creates unique IDs
# ------------------------------------------------------------------

@given(st.integers(min_value=1, max_value=5))
@settings(max_examples=20, deadline=None)
def test_duplicate_creates_unique_ids(num_duplicates):
    """Duplicating clips should never create ID collisions."""
    track, _ = _make_track()
    original = track.add_clip('AMFile', 1, 0, TICK)

    all_ids = [original.id]
    for _ in range(num_duplicates):
        dup = track.duplicate_clip(all_ids[-1])
        all_ids.append(dup.id)

    assert len(all_ids) == len(set(all_ids)), f'Duplicate IDs: {all_ids}'