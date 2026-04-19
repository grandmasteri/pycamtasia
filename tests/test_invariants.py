"""Property-based tests verifying structural invariants after random operation sequences."""
from __future__ import annotations

import copy
import shutil
import tempfile
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

from camtasia import load_project
from camtasia.history import ChangeHistory
from camtasia.operations.layout import pack_track, ripple_delete
from camtasia.timeline.clips.base import BaseClip
from camtasia.timeline.clips.group import Group
from camtasia.timeline.track import Track
from camtasia.timing import ticks_to_seconds

RESOURCES = Path(__file__).parent.parent / 'src' / 'camtasia' / 'resources'

TICK = 705_600_000  # ~23.5 s at 30 fps editRate


def _fresh_project():
    """Load template into an isolated temp copy (safe for Hypothesis)."""
    td = tempfile.mkdtemp()
    dst = Path(td) / 'test.cmproj'
    shutil.copytree(RESOURCES / 'new.cmproj', dst)
    return load_project(dst)


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
    proj = _fresh_project()
    proj._data.setdefault('sourceBin', []).append({
        'id': 1, 'src': './media/test.wav', 'rect': [0, 0, 0, 0],
        'lastMod': '20260101T000000',
        'sourceTracks': [{'range': [0, 48000], 'type': 2, 'editRate': 48000, 'sampleRate': 48000, 'bitDepth': 16, 'numChannels': 1}],
    })
    track = proj.timeline.add_track('Test')
    clip_ids: list[int] = []

    for op in operations:
        if op == 'add':
            clip = track.add_clip('AMFile', 1, len(clip_ids) * TICK, TICK)
            clip_ids.append(clip.id)
        elif op == 'remove' and clip_ids:
            track.remove_clip(clip_ids.pop(0))
        elif op == 'clear':
            track.clear()
            clip_ids.clear()

    errors = [i for i in proj.validate() if i.level == 'error' and 'missing source ID' not in i.message]
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


# ------------------------------------------------------------------
# 7. pack_track preserves clip count
# ------------------------------------------------------------------

@given(st.integers(min_value=1, max_value=8))
@settings(max_examples=20, deadline=None)
def test_pack_preserves_clip_count(num_clips):
    """Packing a track should not add or remove clips."""
    track, data = _make_track()
    for i in range(num_clips):
        track.add_clip('AMFile', 1, i * TICK * 3, TICK)  # gaps between clips
    original_count = len(data['medias'])
    pack_track(track)
    assert len(data['medias']) == original_count


# ------------------------------------------------------------------
# 8. ripple_delete reduces clip count by 1
# ------------------------------------------------------------------

@given(st.integers(min_value=2, max_value=8))
@settings(max_examples=20, deadline=None)
def test_ripple_delete_reduces_count(num_clips):
    """Ripple delete should remove exactly one clip."""
    track, data = _make_track()
    ids = []
    for i in range(num_clips):
        clip = track.add_clip('AMFile', 1, i * TICK, TICK)
        ids.append(clip.id)
    ripple_delete(track, ids[0])
    assert len(data['medias']) == num_clips - 1


# ------------------------------------------------------------------
# 9. All operations leave valid project state
# ------------------------------------------------------------------

@given(st.lists(st.sampled_from([
    'add', 'remove', 'split', 'duplicate', 'clear', 'pack', 'move'
]), min_size=1, max_size=12))
@settings(max_examples=50, deadline=None)
def test_all_operations_leave_valid_state(operations):
    """Any sequence of operations should leave no stale transitions."""
    track, data = _make_track()
    clip_ids = []

    for op in operations:
        try:
            if op == 'add':
                clip = track.add_clip('AMFile', 1, len(clip_ids) * TICK, TICK)
                clip_ids.append(clip.id)
            elif op == 'remove' and clip_ids:
                cid = clip_ids.pop(0)
                track.remove_clip(cid)
            elif op == 'split' and clip_ids:
                # Split the last clip at its midpoint
                cid = clip_ids[-1]
                for m in data['medias']:
                    if m['id'] == cid:
                        mid = m['start'] + m['duration'] // 2
                        if mid > m['start'] and mid < m['start'] + m['duration']:
                            left, right = track.split_clip(cid, ticks_to_seconds(mid))
                            clip_ids[-1] = left.id
                            clip_ids.append(right.id)
                        break
            elif op == 'duplicate' and clip_ids:
                dup = track.duplicate_clip(clip_ids[-1])
                clip_ids.append(dup.id)
            elif op == 'clear':
                track.clear()
                clip_ids.clear()
            elif op == 'pack' and clip_ids:
                pack_track(track)
            elif op == 'move' and clip_ids:
                track.move_clip(clip_ids[-1], len(clip_ids) * 10.0)
        except (KeyError, ValueError):
            pass  # Some operations may fail on edge cases

    # INVARIANT: no stale transitions
    existing_ids = {m['id'] for m in data.get('medias', [])}
    for trans in data.get('transitions', []):
        left = trans.get('leftMedia')
        right = trans.get('rightMedia')
        if left is not None:
            assert left in existing_ids, f'Stale leftMedia={left}'
        if right is not None:
            assert right in existing_ids, f'Stale rightMedia={right}'

    # INVARIANT: no duplicate IDs
    all_ids = [m['id'] for m in data.get('medias', [])]
    assert len(all_ids) == len(set(all_ids)), f'Duplicate IDs: {all_ids}'


# ------------------------------------------------------------------
# 10. trim_clip preserves non-negative duration
# ------------------------------------------------------------------

@given(st.floats(min_value=0.01, max_value=0.49))
@settings(max_examples=20, deadline=None)
def test_trim_preserves_positive_duration(trim_fraction):
    """Trimming should never produce zero or negative duration."""
    track, data = _make_track()
    clip = track.add_clip('AMFile', 1, 0, TICK * 10)
    trim_amount = trim_fraction * 10.0
    track.trim_clip(clip.id, trim_start_seconds=trim_amount)
    actual_dur = data['medias'][0]['duration']
    assert actual_dur > 0


# ------------------------------------------------------------------
# 11. extend_clip preserves positive duration
# ------------------------------------------------------------------

@given(st.floats(min_value=-4.9, max_value=10.0))
@settings(max_examples=20, deadline=None)
def test_extend_preserves_positive_duration(extend_amount):
    """Extending should keep duration positive."""
    track, data = _make_track()
    clip = track.add_clip('AMFile', 1, 0, TICK * 5)
    try:
        track.extend_clip(clip.id, extend_seconds=extend_amount)
        assert data['medias'][0]['duration'] > 0
    except ValueError:
        pass  # Expected for large negative extensions


# ------------------------------------------------------------------
# 12. swap_clips is its own inverse
# ------------------------------------------------------------------

@given(st.integers(min_value=2, max_value=5))
@settings(max_examples=20, deadline=None)
def test_swap_is_own_inverse(num_clips):
    """Swapping twice returns to original state."""
    track, data = _make_track()
    ids = []
    for i in range(num_clips):
        clip = track.add_clip('AMFile', 1, i * TICK, TICK)
        ids.append(clip.id)
    original_starts = {m['id']: m['start'] for m in data['medias']}
    track.swap_clips(ids[0], ids[-1])
    track.swap_clips(ids[0], ids[-1])
    restored_starts = {m['id']: m['start'] for m in data['medias']}
    assert original_starts == restored_starts


# ------------------------------------------------------------------
# 13. replace_clip preserves clip count
# ------------------------------------------------------------------

@given(st.integers(min_value=2, max_value=5))
@settings(max_examples=20, deadline=None)
def test_replace_preserves_clip_count(num_clips):
    track, data = _make_track()
    ids = []
    for i in range(num_clips):
        clip = track.add_clip('AMFile', 1, i * TICK, TICK)
        ids.append(clip.id)
    original_count = len(data['medias'])
    new_data = {'_type': 'VMFile', 'src': 2, 'start': 0, 'duration': TICK}
    track.replace_clip(ids[0], new_data)
    assert len(data['medias']) == original_count


# ------------------------------------------------------------------
# 14. replace_clip cascades transitions
# ------------------------------------------------------------------

@given(st.integers(min_value=2, max_value=5))
@settings(max_examples=20, deadline=None)
def test_replace_cascades_transitions(num_clips):
    track, data = _make_track()
    ids = []
    for i in range(num_clips):
        clip = track.add_clip('AMFile', 1, i * TICK, TICK)
        ids.append(clip.id)
    if len(ids) >= 2:
        data.setdefault('transitions', []).append(
            {'leftMedia': ids[0], 'rightMedia': ids[1], 'name': 'X', 'duration': 100}
        )
    new_data = {'_type': 'VMFile', 'src': 2, 'start': 0, 'duration': TICK}
    track.replace_clip(ids[0], new_data)
    existing_ids = {m['id'] for m in data['medias']}
    for t in data.get('transitions', []):
        if t.get('leftMedia') is not None:
            assert t['leftMedia'] in existing_ids
        if t.get('rightMedia') is not None:
            assert t['rightMedia'] in existing_ids


# ------------------------------------------------------------------
# 15. reorder_clips preserves all clip IDs
# ------------------------------------------------------------------

@given(st.permutations(range(3)))
@settings(max_examples=20, deadline=None)
def test_reorder_preserves_all_ids(perm):
    track, data = _make_track()
    ids = []
    for i in range(3):
        clip = track.add_clip('AMFile', 1, i * TICK, TICK)
        ids.append(clip.id)
    reordered = [ids[i] for i in perm]
    track.reorder_clips(reordered)
    actual_ids = {m['id'] for m in data['medias']}
    assert actual_ids == set(ids)


# ------------------------------------------------------------------
# 16. insert_clip_at preserves existing clips
# ------------------------------------------------------------------

@given(st.integers(min_value=1, max_value=5))
@settings(max_examples=20, deadline=None)
def test_insert_preserves_existing(num_existing):
    track, data = _make_track()
    for i in range(num_existing):
        track.add_clip('AMFile', 1, i * TICK * 2, TICK)
    original_count = len(data['medias'])
    track.insert_clip_at('AMFile', 1, 0.5, 0.5)
    assert len(data['medias']) == original_count + 1


# ------------------------------------------------------------------
# 17. opacity stays in valid range after set
# ------------------------------------------------------------------

@given(st.floats(min_value=0.0, max_value=1.0))
@settings(max_examples=20, deadline=None)
def test_opacity_stays_valid(value):
    data = {'_type': 'VMFile', 'id': 1, 'start': 0, 'duration': TICK, 'parameters': {}}
    clip = BaseClip(data)
    clip.opacity = value
    assert 0.0 <= clip.opacity <= 1.0


# ------------------------------------------------------------------
# 18. volume stays non-negative after set
# ------------------------------------------------------------------

@given(st.floats(min_value=0.0, max_value=10.0))
@settings(max_examples=20, deadline=None)
def test_volume_stays_non_negative(value):
    data = {'_type': 'AMFile', 'id': 1, 'start': 0, 'duration': TICK, 'parameters': {}}
    clip = BaseClip(data)
    clip.volume = value
    assert clip.volume == value


# ------------------------------------------------------------------
# 19. merge_adjacent preserves total duration
# ------------------------------------------------------------------

@given(st.integers(min_value=2, max_value=5))
@settings(max_examples=20, deadline=None)
def test_merge_adjacent_preserves_total_duration(num_clips):
    track, data = _make_track()
    ids = []
    total_dur = 0
    for i in range(num_clips):
        clip = track.add_clip('AMFile', 1, i * TICK, TICK, media_start=i * TICK)
        ids.append(clip.id)
        total_dur += TICK
    # Merge first two
    track.merge_adjacent_clips(ids[0], ids[1])
    actual_total = sum(m['duration'] for m in data['medias'])
    assert actual_total == total_dur


# ------------------------------------------------------------------
# 20. set_speed preserves clip start position
# ------------------------------------------------------------------

@given(st.floats(min_value=0.1, max_value=10.0))
@settings(max_examples=20, deadline=None)
def test_set_speed_preserves_start(speed):
    data = {'_type': 'VMFile', 'id': 1, 'start': TICK * 5, 'duration': TICK * 3, 'parameters': {}}
    clip = BaseClip(data)
    original_start = clip.start
    clip.set_speed(speed)
    assert clip.start == original_start

# ---------------------------------------------------------------------------
# 21. undo fully reverts any operation sequence
# ---------------------------------------------------------------------------

@given(st.lists(st.sampled_from(['add', 'remove', 'clear']), min_size=1, max_size=5))
@settings(max_examples=30, deadline=None)
def test_undo_fully_reverts_operations(operations):
    """Undoing a tracked change block restores the exact original state."""
    original_data = {'tracks': [{'medias': [], 'transitions': []}]}
    project_data = copy.deepcopy(original_data)
    history = ChangeHistory()

    snapshot_before = copy.deepcopy(project_data)
    medias = project_data['tracks'][0]['medias']
    next_id = 1
    for operation in operations:
        if operation == 'add':
            medias.append({'id': next_id, '_type': 'AMFile', 'start': next_id * TICK, 'duration': TICK})
            next_id += 1
        elif operation == 'remove' and medias:
            medias.pop(0)
        elif operation == 'clear':
            medias.clear()
    history.record('batch', snapshot_before, project_data)

    if history.can_undo:
        history.undo(project_data)
        assert project_data == original_data


# ---------------------------------------------------------------------------
# 22. overlaps_with is symmetric
# ---------------------------------------------------------------------------

@given(
    st.integers(min_value=0, max_value=10),
    st.integers(min_value=1, max_value=5),
    st.integers(min_value=0, max_value=10),
    st.integers(min_value=1, max_value=5),
)
@settings(max_examples=30, deadline=None)
def test_overlaps_with_is_symmetric(start_a, duration_a, start_b, duration_b):
    """If A overlaps B, then B overlaps A."""
    clip_a = BaseClip({'_type': 'VMFile', 'id': 1, 'start': start_a * TICK, 'duration': duration_a * TICK})
    clip_b = BaseClip({'_type': 'VMFile', 'id': 2, 'start': start_b * TICK, 'duration': duration_b * TICK})
    assert clip_a.overlaps_with(clip_b) == clip_b.overlaps_with(clip_a)


# ---------------------------------------------------------------------------
# 23. distance_to sign matches gap direction
# ---------------------------------------------------------------------------

@given(
    st.integers(min_value=0, max_value=5),
    st.integers(min_value=1, max_value=3),
    st.integers(min_value=6, max_value=12),
    st.integers(min_value=1, max_value=3),
)
@settings(max_examples=30, deadline=None)
def test_distance_to_positive_when_gap_exists(start_a, duration_a, start_b, duration_b):
    """distance_to is positive when there's a gap (B starts after A ends)."""
    clip_a = BaseClip({'_type': 'VMFile', 'id': 1, 'start': start_a * TICK, 'duration': duration_a * TICK})
    clip_b = BaseClip({'_type': 'VMFile', 'id': 2, 'start': start_b * TICK, 'duration': duration_b * TICK})
    # B starts at 6+ ticks, A ends at most 5+3=8 ticks, so gap depends on values
    end_a = (start_a + duration_a) * TICK
    if start_b * TICK > end_a:
        assert clip_a.distance_to(clip_b) > 0


# ---------------------------------------------------------------------------
# 24. distribute_evenly produces no gaps when gap=0
# ---------------------------------------------------------------------------

@given(st.integers(min_value=2, max_value=6))
@settings(max_examples=20, deadline=None)
def test_distribute_evenly_no_gaps(num_clips):
    """distribute_evenly with gap=0 should produce contiguous clips."""
    track, data = _make_track()
    for clip_index in range(num_clips):
        track.add_clip('AMFile', 1, clip_index * TICK * 3, TICK)  # with gaps
    track.distribute_evenly(gap_seconds=0.0)
    sorted_medias = sorted(data['medias'], key=lambda m: m['start'])
    for i in range(len(sorted_medias) - 1):
        current_end = sorted_medias[i]['start'] + sorted_medias[i]['duration']
        next_start = sorted_medias[i + 1]['start']
        assert current_end == next_start, f'Gap between clips {i} and {i+1}'


# ---------------------------------------------------------------------------
# 25. align_clips_to_start always starts at 0
# ---------------------------------------------------------------------------

@given(st.lists(st.integers(min_value=1, max_value=100), min_size=1, max_size=5))
@settings(max_examples=20, deadline=None)
def test_align_always_starts_at_zero(start_offsets):
    """align_clips_to_start should always result in first clip at 0."""
    track, data = _make_track()
    for i, offset in enumerate(start_offsets):
        track.add_clip('AMFile', 1, offset * TICK, TICK)
    track.align_clips_to_start()
    if data['medias']:
        first_start = min(m['start'] for m in data['medias'])
        assert first_start == 0


# ---------------------------------------------------------------------------
# 26. remove_short_clips never removes clips above threshold
# ---------------------------------------------------------------------------

@given(st.floats(min_value=0.5, max_value=5.0))
@settings(max_examples=20, deadline=None)
def test_remove_short_clips_preserves_long_clips(threshold_seconds):
    """remove_short_clips should never remove clips at or above the threshold."""
    track, data = _make_track()
    # Add clips of varying durations
    track.add_clip('AMFile', 1, 0, TICK)                    # 1s
    track.add_clip('AMFile', 1, TICK * 2, TICK * 3)         # 3s
    track.add_clip('AMFile', 1, TICK * 6, TICK * 10)        # 10s
    
    original_long_clip_count = sum(
        1 for m in data['medias']
        if m.get('duration', 0) >= threshold_seconds * TICK
    )
    
    track.remove_short_clips(threshold_seconds)
    
    remaining_count = len(data['medias'])
    assert remaining_count == original_long_clip_count


# ---------------------------------------------------------------------------
# 27. reverse_clip_order preserves all clip IDs
# ---------------------------------------------------------------------------

@given(st.integers(min_value=2, max_value=6))
@settings(max_examples=20, deadline=None)
def test_reverse_preserves_all_ids(num_clips):
    """Reversing clip order should not lose or duplicate any clip IDs."""
    track, data = _make_track()
    original_ids: set[int] = set()
    for clip_index in range(num_clips):
        clip = track.add_clip('AMFile', 1, clip_index * TICK, TICK)
        original_ids.add(clip.id)
    track.reverse_clip_order()
    reversed_ids: set[int] = {int(media_dict['id']) for media_dict in data['medias']}
    assert reversed_ids == original_ids


# ---------------------------------------------------------------------------
# 28. set_start_seconds and set_duration_seconds round-trip
# ---------------------------------------------------------------------------

@given(st.floats(min_value=0.0, max_value=100.0), st.floats(min_value=0.1, max_value=50.0))
@settings(max_examples=20, deadline=None)
def test_set_start_duration_roundtrip(start_seconds, duration_seconds):
    """Setting start/duration in seconds should round-trip correctly."""
    data = {'_type': 'VMFile', 'id': 1, 'start': 0, 'duration': TICK}
    clip = BaseClip(data)
    clip.set_start_seconds(start_seconds)
    clip.set_duration_seconds(duration_seconds)
    assert abs(clip.start_seconds - start_seconds) < 0.001
    assert abs(clip.duration_seconds - duration_seconds) < 0.001


# ---------------------------------------------------------------------------
# 29. group_clips preserves total clip content
# ---------------------------------------------------------------------------

@given(st.integers(min_value=2, max_value=5))
@settings(max_examples=20, deadline=None)
def test_group_clips_preserves_content(num_clips):
    """Grouping clips should preserve all clip data inside the Group."""
    track, data = _make_track()
    clip_ids: list[int] = []
    for clip_index in range(num_clips):
        clip = track.add_clip('AMFile', 1, clip_index * TICK, TICK)
        clip_ids.append(clip.id)
    
    # Group all clips
    group = track.group_clips(clip_ids)
    
    # The Group should contain all the clips
    assert group.clip_count == num_clips
    # The track should now have exactly 1 clip (the Group)
    assert [m['_type'] for m in data['medias']] == ['Group']


# ---------------------------------------------------------------------------
# 30. remove_internal_clip reduces clip_count by 1
# ---------------------------------------------------------------------------

@given(st.integers(min_value=2, max_value=5))
@settings(max_examples=20, deadline=None)
def test_remove_internal_clip_reduces_count(num_clips):
    """Removing an internal clip should reduce clip_count by exactly 1."""
    group_data = {
        '_type': 'Group', 'id': 1, 'start': 0, 'duration': TICK * num_clips,
        'mediaDuration': TICK * num_clips, 'mediaStart': 0, 'scalar': 1,
        'parameters': {}, 'effects': [], 'metadata': {}, 'animationTracks': {},
        'attributes': {'ident': '', 'gain': 1.0, 'mixToMono': False,
                       'widthAttr': 0.0, 'heightAttr': 0.0, 'maxDurationAttr': 0, 'assetProperties': []},
        'tracks': [{'trackIndex': 0, 'medias': [
            {'id': i + 10, '_type': 'AMFile', 'start': i * TICK, 'duration': TICK}
            for i in range(num_clips)
        ], 'transitions': [], 'parameters': {}, 'ident': '',
           'audioMuted': False, 'videoHidden': False, 'magnetic': False, 'matte': 0, 'solo': False}],
    }
    group = Group(group_data)
    original_count: int = group.clip_count
    group.remove_internal_clip(10)  # remove first clip
    assert group.clip_count == original_count - 1


# ---------------------------------------------------------------------------
# 32. clone_track preserves clip count
# ---------------------------------------------------------------------------

@given(st.integers(min_value=1, max_value=5))
@settings(max_examples=20, deadline=None)
def test_clone_track_preserves_clip_count(num_clips):
    """Cloning a track should preserve the number of clips."""
    proj = _fresh_project()
    track = proj.timeline.add_track('Source')
    for i in range(num_clips):
        track.add_clip('AMFile', 1, i * TICK, TICK)
    
    cloned = proj.clone_track('Source', 'Cloned')
    assert len(cloned) == num_clips


# ---------------------------------------------------------------------------
# 32. remove_all_effects then effect_count is 0
# ---------------------------------------------------------------------------

@given(st.integers(min_value=1, max_value=4))
@settings(max_examples=20, deadline=None)
def test_remove_all_effects_zeroes_count(num_clips):
    """After remove_all_effects, no clip should have effects."""
    proj = _fresh_project()
    track = proj.timeline.add_track('Test')
    for i in range(num_clips):
        clip = track.add_clip('VMFile', 1, i * TICK, TICK)
        clip.add_drop_shadow()
    
    proj.remove_all_effects()
    
    for _, clip in proj.all_clips:
        assert clip._data.get('effects', []) == []


# ---------------------------------------------------------------------------
# 33. normalize_audio sets all audio gains equal
# ---------------------------------------------------------------------------

@given(st.floats(min_value=0.1, max_value=2.0))
@settings(max_examples=20, deadline=None)
def test_normalize_audio_equalizes_gain(target_gain):
    """After normalize_audio, all audio clips should have the target gain."""
    proj = _fresh_project()
    track = proj.timeline.add_track('Audio')
    for i in range(3):
        clip = track.add_audio(1, start_seconds=float(i), duration_seconds=1.0)
        clip.gain = float(i + 1) * 0.5  # different gains
    
    proj.normalize_audio(target_gain)
    
    for _, clip in proj.all_clips:
        if clip.is_audio:
            assert abs(clip.gain - target_gain) < 0.001


# ---------------------------------------------------------------------------
# 34. replace_all_media changes all matching sources
# ---------------------------------------------------------------------------

@given(st.integers(min_value=1, max_value=5))
@settings(max_examples=20, deadline=None)
def test_replace_all_media_changes_all(num_clips):
    """replace_all_media should change all clips with the old source ID."""
    proj = _fresh_project()
    track = proj.timeline.add_track('Test')
    for i in range(num_clips):
        track.add_clip('VMFile', 42, i * TICK, TICK)
    
    count = proj.replace_all_media(42, 99)
    
    assert count == num_clips
    for _, clip in proj.all_clips:
        assert clip._data.get('src') != 42
