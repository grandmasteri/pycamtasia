"""Property-based invariant tests using hypothesis.

Generates random sequences of mutations and asserts that project invariants
hold after each step. Catches entire classes of bugs at once rather than
relying on adversarial review finding each specific case.
"""
from __future__ import annotations

from fractions import Fraction

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from hypothesis.stateful import RuleBasedStateMachine, invariant, rule
import pytest

from camtasia.timing import seconds_to_ticks
from camtasia.validation import _check_compound_invariants


def _make_project_with_clips(num_clips: int) -> object:
    """Build a fresh project with N simple video clips on one track."""
    from pathlib import Path
    import tempfile

    from camtasia import Project
    tmp = Path(tempfile.mkdtemp()) / 'test.cmproj'
    proj = Project.new(str(tmp), width=1920, height=1080)
    # Project.new() provides default tracks; use the first
    track = proj.timeline.tracks[0]
    for i in range(num_clips):
        src_id = proj.media_bin.next_id()
        proj._data.setdefault('sourceBin', []).append({
            '_type': 'IMFile',
            'id': src_id,
            'src': f'./media/fake{i}.png',
            'sourceTracks': [{
                'range': [0, 1],
                'type': 'Video',
                'editRate': 30,
                'trackRect': [0, 0, 1920, 1080],
                'sampleRate': 30,
                'bitDepth': 24,
                'numChannels': 0,
                'integratedLUFS': 100.0,
                'peakLevel': -1.0,
                'metaData': f'fake{i}.png',
            }],
            'lastMod': 'Mon Jan 01 00:00:00 2024',
            'loudnessNormalization': False,
            'rect': [0, 0, 1920, 1080],
        })
        track.add_clip('IMFile', src_id, seconds_to_ticks(i * 2.0), seconds_to_ticks(1.0))
    return proj


@given(
    factor_num=st.integers(min_value=1, max_value=10),
    factor_denom=st.integers(min_value=1, max_value=10),
)
@settings(max_examples=30, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_rescale_project_preserves_invariants(factor_num: int, factor_denom: int) -> None:
    """rescale_project by any rational factor must preserve compound invariants."""
    from camtasia.operations.speed import rescale_project
    proj = _make_project_with_clips(3)
    factor = Fraction(factor_num, factor_denom)
    rescale_project(proj._data, factor)
    issues = _check_compound_invariants(proj._data)
    assert issues == [], f'Invariants violated after rescale by {factor}: {[i.message for i in issues]}'


@given(speed=st.floats(min_value=0.1, max_value=10.0, allow_nan=False, allow_infinity=False))
@settings(max_examples=30, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_set_speed_preserves_invariants(speed: float) -> None:
    """Calling set_speed on a clip preserves compound invariants."""
    proj = _make_project_with_clips(1)
    track = proj.timeline.tracks[0]
    clips = list(track.clips)
    if clips:
        clips[0].set_speed(speed)
    issues = _check_compound_invariants(proj._data)
    assert issues == [], f'Invariants violated after set_speed({speed}): {[i.message for i in issues]}'


@given(shift_seconds=st.floats(min_value=-5.0, max_value=5.0, allow_nan=False, allow_infinity=False))
@settings(max_examples=30, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_shift_all_preserves_invariants(shift_seconds: float) -> None:
    """Shifting all clips preserves compound invariants."""
    proj = _make_project_with_clips(3)
    proj.timeline.shift_all(shift_seconds)
    issues = _check_compound_invariants(proj._data)
    assert issues == [], f'Invariants violated after shift_all({shift_seconds}): {[i.message for i in issues]}'


@given(factor=st.floats(min_value=0.1, max_value=10.0, allow_nan=False, allow_infinity=False))
@settings(max_examples=30, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_scale_all_durations_preserves_invariants(factor: float) -> None:
    """scale_all_durations on a track preserves compound invariants."""
    proj = _make_project_with_clips(3)
    track = proj.timeline.tracks[0]
    track.scale_all_durations(factor)
    issues = _check_compound_invariants(proj._data)
    assert issues == [], f'Invariants violated after scale_all_durations({factor}): {[i.message for i in issues]}'


@pytest.mark.parametrize('mutation_name', ['set_speed', 'scale_all_durations', 'shift_all', 'rescale_project'])
def test_smoke_mutations_preserve_invariants(mutation_name: str) -> None:
    """Smoke test: each core mutation preserves invariants on a simple project."""
    proj = _make_project_with_clips(3)
    track = proj.timeline.tracks[0]
    if mutation_name == 'set_speed':
        next(iter(track.clips)).set_speed(2.0)
    elif mutation_name == 'scale_all_durations':
        track.scale_all_durations(1.5)
    elif mutation_name == 'shift_all':
        proj.timeline.shift_all(1.0)
    elif mutation_name == 'rescale_project':
        from camtasia.operations.speed import rescale_project
        rescale_project(proj._data, Fraction(2, 3))
    issues = _check_compound_invariants(proj._data)
    assert issues == [], f'{mutation_name} violated invariants: {[i.message for i in issues]}'


def _make_project_with_unified_clip() -> object:
    """Build a project with a UnifiedMedia clip (video+audio)."""
    from pathlib import Path
    import tempfile

    from camtasia import Project
    tmp = Path(tempfile.mkdtemp()) / 'test.cmproj'
    proj = Project.new(str(tmp), width=1920, height=1080)
    # Manually inject a UnifiedMedia clip with synced video and audio sub-clips
    src_id = proj.media_bin.next_id()
    proj._data.setdefault('sourceBin', []).append({
        '_type': 'UnifiedMedia',
        'id': src_id,
        'src': './media/fake.mp4',
        'sourceTracks': [{
            'range': [0, 300],
            'type': 'Video',
            'editRate': 30,
            'trackRect': [0, 0, 1920, 1080],
            'sampleRate': 30,
            'bitDepth': 24,
            'numChannels': 0,
            'integratedLUFS': 100.0,
            'peakLevel': -1.0,
            'metaData': 'fake.mp4',
        }],
        'lastMod': 'Mon Jan 01 00:00:00 2024',
        'loudnessNormalization': False,
        'rect': [0, 0, 1920, 1080],
    })
    track_data = proj.timeline.tracks[0]._data
    track_data.setdefault('medias', []).append({
        '_type': 'UnifiedMedia',
        'id': 100,
        'start': 0,
        'duration': seconds_to_ticks(10.0),
        'mediaStart': 0,
        'mediaDuration': seconds_to_ticks(10.0),
        'scalar': 1,
        'parameters': {},
        'effects': [],
        'metadata': {},
        'animationTracks': {},
        'attributes': {},
        'video': {
            '_type': 'VMFile',
            'id': 101,
            'src': src_id,
            'start': 0,
            'duration': seconds_to_ticks(10.0),
            'mediaStart': 0,
            'mediaDuration': seconds_to_ticks(10.0),
            'scalar': 1,
            'trackNumber': 0,
            'parameters': {},
            'effects': [],
            'metadata': {},
            'animationTracks': {},
            'attributes': {'ident': ''},
        },
        'audio': {
            '_type': 'AMFile',
            'id': 102,
            'src': src_id,
            'start': 0,
            'duration': seconds_to_ticks(10.0),
            'mediaStart': 0,
            'mediaDuration': seconds_to_ticks(10.0),
            'scalar': 1,
            'channelNumber': '0',
            'trackNumber': 0,
            'parameters': {},
            'effects': [],
            'metadata': {},
            'animationTracks': {},
            'attributes': {'ident': ''},
        },
    })
    # Sanity check: invariants hold on the fresh project
    assert _check_compound_invariants(proj._data) == []
    return proj


@given(speed=st.floats(min_value=0.25, max_value=4.0, allow_nan=False, allow_infinity=False))
@settings(max_examples=20, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_set_speed_unified_media_preserves_invariants(speed: float) -> None:
    """set_speed on a UnifiedMedia clip must keep wrapper and sub-clip in sync."""
    proj = _make_project_with_unified_clip()
    track = proj.timeline.tracks[0]
    next(iter(track.clips)).set_speed(speed)
    issues = _check_compound_invariants(proj._data)
    assert issues == [], f'Invariants violated after UnifiedMedia.set_speed({speed}): {[i.message for i in issues]}'


@given(factor_num=st.integers(min_value=1, max_value=5), factor_denom=st.integers(min_value=1, max_value=5))
@settings(max_examples=20, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_rescale_unified_media_preserves_invariants(factor_num: int, factor_denom: int) -> None:
    """rescale_project on UnifiedMedia must keep wrapper and sub-clip in sync."""
    from camtasia.operations.speed import rescale_project
    proj = _make_project_with_unified_clip()
    rescale_project(proj._data, Fraction(factor_num, factor_denom))
    issues = _check_compound_invariants(proj._data)
    assert issues == [], f'Invariants violated after UnifiedMedia rescale({factor_num}/{factor_denom}): {[i.message for i in issues]}'


@given(new_duration_seconds=st.floats(min_value=1.0, max_value=30.0, allow_nan=False, allow_infinity=False))
@settings(max_examples=20, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_duration_setter_unified_media_preserves_invariants(new_duration_seconds: float) -> None:
    """Setting .duration on a UnifiedMedia clip must keep wrapper and sub-clip in sync."""
    proj = _make_project_with_unified_clip()
    track = proj.timeline.tracks[0]
    next(iter(track.clips)).duration = seconds_to_ticks(new_duration_seconds)
    issues = _check_compound_invariants(proj._data)
    assert issues == [], f'Invariants violated after UnifiedMedia.duration={new_duration_seconds}: {[i.message for i in issues]}'


@given(new_start_seconds=st.floats(min_value=0.0, max_value=30.0, allow_nan=False, allow_infinity=False))
@settings(max_examples=20, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_start_setter_unified_media_preserves_invariants(new_start_seconds: float) -> None:
    """Setting .start on a UnifiedMedia clip must keep wrapper and sub-clip in sync."""
    proj = _make_project_with_unified_clip()
    track = proj.timeline.tracks[0]
    next(iter(track.clips)).start = seconds_to_ticks(new_start_seconds)
    issues = _check_compound_invariants(proj._data)
    assert issues == [], f'Invariants violated after UnifiedMedia.start={new_start_seconds}: {[i.message for i in issues]}'





class UnifiedMediaStateMachine(RuleBasedStateMachine):
    """Stateful property test: compose random mutations on a UnifiedMedia clip
    and assert invariants hold after every step."""

    def __init__(self) -> None:
        super().__init__()
        self.proj = _make_project_with_unified_clip()
        # Add a second simple clip so group_clips/ungroup can do real work
        src_id = self.proj.media_bin.next_id()
        self.proj._data.setdefault('sourceBin', []).append({
            '_type': 'IMFile', 'id': src_id, 'src': './media/fake_2.png',
            'sourceTracks': [{
                'range': [0, 1], 'type': 'Video', 'editRate': 30,
                'trackRect': [0, 0, 1920, 1080], 'sampleRate': 30, 'bitDepth': 24,
                'numChannels': 0, 'integratedLUFS': 100.0, 'peakLevel': -1.0,
                'metaData': 'fake_2.png',
            }],
            'lastMod': 'Mon Jan 01 00:00:00 2024', 'loudnessNormalization': False,
            'rect': [0, 0, 1920, 1080],
        })
        self.proj.timeline.tracks[0].add_clip(
            'IMFile', src_id, seconds_to_ticks(15.0), seconds_to_ticks(2.0),
        )

    def _clip(self) -> object | None:
        clips = list(self.proj.timeline.tracks[0].clips)
        return clips[0] if clips else None

    @rule(speed=st.floats(min_value=0.25, max_value=4.0, allow_nan=False, allow_infinity=False))
    def do_set_speed(self, speed: float) -> None:
        clip = self._clip()
        if clip is not None:
            clip.set_speed(speed)

    @rule(factor_num=st.integers(min_value=1, max_value=4), factor_denom=st.integers(min_value=1, max_value=4))
    def do_rescale(self, factor_num: int, factor_denom: int) -> None:
        from camtasia.operations.speed import rescale_project
        rescale_project(self.proj._data, Fraction(factor_num, factor_denom))

    @rule(shift_seconds=st.floats(min_value=-3.0, max_value=3.0, allow_nan=False, allow_infinity=False))
    def do_shift(self, shift_seconds: float) -> None:
        self.proj.timeline.shift_all(shift_seconds)

    @rule(new_dur=st.floats(min_value=0.5, max_value=20.0, allow_nan=False, allow_infinity=False))
    def do_set_duration(self, new_dur: float) -> None:
        clip = self._clip()
        if clip is not None:
            clip.duration = seconds_to_ticks(new_dur)

    @rule(factor=st.floats(min_value=0.1, max_value=5.0, allow_nan=False, allow_infinity=False))
    def do_scale_all_durations(self, factor: float) -> None:
        self.proj.timeline.tracks[0].scale_all_durations(factor)

    @rule(split_seconds=st.floats(min_value=0.1, max_value=5.0, allow_nan=False, allow_infinity=False))
    def do_split(self, split_seconds: float) -> None:
        clip = self._clip()
        if clip is None:
            return
        track = self.proj.timeline.tracks[0]
        clip_start_s = clip.start / 705600000
        clip_dur_s = clip.duration / 705600000
        split_at = clip_start_s + min(split_seconds, max(0.0, clip_dur_s - 0.01))
        if split_at <= clip_start_s or split_at >= clip_start_s + clip_dur_s:
            return
        track.split_clip(clip.id, split_at)

    @rule(trim_start=st.floats(min_value=0.0, max_value=2.0, allow_nan=False, allow_infinity=False),
          trim_end=st.floats(min_value=0.0, max_value=2.0, allow_nan=False, allow_infinity=False))
    def do_trim(self, trim_start: float, trim_end: float) -> None:
        clip = self._clip()
        if clip is None:
            return
        dur_s = clip.duration / 705600000
        if trim_start + trim_end >= dur_s - 0.01:
            return
        self.proj.timeline.tracks[0].trim_clip(
            clip.id, trim_start_seconds=trim_start, trim_end_seconds=trim_end,
        )

    @rule(extend_seconds=st.floats(min_value=-3.0, max_value=5.0, allow_nan=False, allow_infinity=False))
    def do_extend(self, extend_seconds: float) -> None:
        clip = self._clip()
        if clip is None:
            return
        dur_s = clip.duration / 705600000
        if dur_s + extend_seconds < 0.1:
            return
        self.proj.timeline.tracks[0].extend_clip(clip.id, extend_seconds=extend_seconds)

    @rule()
    def do_group_ungroup(self) -> None:
        """Group the current clips, then immediately ungroup to stress-test the round-trip."""
        track = self.proj.timeline.tracks[0]
        clip_ids = [c.id for c in track.clips]
        if len(clip_ids) == 0:
            return
        group = track.group_clips(clip_ids)
        track.ungroup_clip(group.id)

    @rule()
    def do_save_reload_roundtrip(self) -> None:
        """Save the project and reload it, then continue mutating. Catches serialization bugs."""
        import json
        # Serialize and parse back in-place (simulates save+reload)
        serialized = json.dumps(self.proj._data)
        reloaded = json.loads(serialized)
        # Swap the underlying dict
        self.proj._data.clear()
        self.proj._data.update(reloaded)

    @rule(at_seconds=st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False),
          gap_seconds=st.floats(min_value=0.1, max_value=3.0, allow_nan=False, allow_infinity=False))
    def do_insert_gap(self, at_seconds: float, gap_seconds: float) -> None:
        self.proj.timeline.tracks[0].insert_gap(at_seconds, gap_seconds)

    @rule(at_seconds=st.floats(min_value=0.0, max_value=20.0, allow_nan=False, allow_infinity=False))
    def do_remove_gap(self, at_seconds: float) -> None:
        import contextlib
        # KeyError/ValueError when no gap exists at that position is valid precondition
        # failure, not a bug
        with contextlib.suppress(KeyError, ValueError):
            self.proj.timeline.tracks[0].remove_gap_at(at_seconds)

    @rule()
    def do_duplicate_clip(self) -> None:
        clip = self._clip()
        if clip is None:
            return
        self.proj.timeline.tracks[0].duplicate_clip(clip.id)

    @invariant()
    def compound_invariants_hold(self) -> None:
        issues = _check_compound_invariants(self.proj._data)
        assert issues == [], f'Invariants violated: {[i.message for i in issues]}'


TestUnifiedMediaStateful = UnifiedMediaStateMachine.TestCase
TestUnifiedMediaStateful.settings = settings(
    max_examples=50,
    stateful_step_count=20,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)



class TestInvariantCheckerDetectsViolations:
    """Direct tests of _check_compound_invariants that construct broken data."""

    def test_unified_media_mismatched_start_detected(self):
        data = {'timeline': {'sceneTrack': {'scenes': [{'csml': {'tracks': [
            {'trackIndex': 0, 'medias': [{
                '_type': 'UnifiedMedia', 'id': 1, 'start': 100,
                'duration': 1000, 'mediaDuration': 1000, 'mediaStart': 0, 'scalar': 1,
                'video': {'_type': 'VMFile', 'id': 2, 'start': 999, 'duration': 1000},
                'audio': {'_type': 'AMFile', 'id': 3, 'start': 100, 'duration': 1000},
            }], 'transitions': []},
        ]}}]}}}
        issues = _check_compound_invariants(data)
        assert len(issues) == 1
        assert 'video.start=999' in issues[0].message

    def test_stitched_media_string_fraction_detected(self):
        data = {'timeline': {'sceneTrack': {'scenes': [{'csml': {'tracks': [
            {'trackIndex': 0, 'medias': [{
                '_type': 'StitchedMedia', 'id': 1, 'start': 0, 'duration': 1000,
                'medias': [{'_type': 'VMFile', 'id': 2, 'start': 0, 'duration': '500/3'}],
            }], 'transitions': []},
        ]}}]}}}
        issues = _check_compound_invariants(data)
        assert len(issues) == 1
        assert 'string fraction' in issues[0].message
        assert issues[0].level == 'error'

    def test_unified_media_with_none_video_skipped(self):
        data = {'timeline': {'sceneTrack': {'scenes': [{'csml': {'tracks': [
            {'trackIndex': 0, 'medias': [{
                '_type': 'UnifiedMedia', 'id': 1, 'start': 0, 'duration': 1000,
                'mediaDuration': 1000, 'mediaStart': 0, 'scalar': 1,
                'video': None,
                'audio': {'_type': 'AMFile', 'id': 3, 'start': 0, 'duration': 1000,
                          'mediaDuration': 1000, 'mediaStart': 0, 'scalar': 1},
            }], 'transitions': []},
        ]}}]}}}
        issues = _check_compound_invariants(data)
        assert issues == []



def _make_project_with_group() -> object:
    """Build a project with a Group containing a UnifiedMedia clip and a simple IMFile."""
    from pathlib import Path
    import tempfile

    from camtasia import Project
    tmp = Path(tempfile.mkdtemp()) / 'test.cmproj'
    proj = Project.new(str(tmp), width=1920, height=1080)
    src_id = proj.media_bin.next_id()
    proj._data.setdefault('sourceBin', []).append({
        '_type': 'IMFile', 'id': src_id, 'src': './media/fake.png',
        'sourceTracks': [{'range': [0, 1], 'type': 'Video', 'editRate': 30,
            'trackRect': [0, 0, 1920, 1080], 'sampleRate': 30, 'bitDepth': 24,
            'numChannels': 0, 'integratedLUFS': 100.0, 'peakLevel': -1.0,
            'metaData': 'fake.png'}],
        'lastMod': 'X', 'loudnessNormalization': False, 'rect': [0, 0, 1920, 1080],
    })
    track = proj.timeline.tracks[0]
    # Inject a Group with one inner UnifiedMedia + one inner IMFile
    track._data.setdefault('medias', []).append({
        '_type': 'Group', 'id': 200, 'start': 0,
        'duration': seconds_to_ticks(10.0), 'mediaStart': 0,
        'mediaDuration': seconds_to_ticks(10.0), 'scalar': 1,
        'parameters': {}, 'effects': [], 'metadata': {},
        'animationTracks': {}, 'attributes': {'ident': '', 'widthAttr': 1920.0, 'heightAttr': 1080.0},
        'tracks': [{
            'trackIndex': 0,
            'medias': [
                {
                    '_type': 'UnifiedMedia', 'id': 201, 'start': 0,
                    'duration': seconds_to_ticks(5.0), 'mediaStart': 0,
                    'mediaDuration': seconds_to_ticks(5.0), 'scalar': 1,
                    'parameters': {}, 'effects': [], 'metadata': {},
                    'animationTracks': {}, 'attributes': {},
                    'video': {'_type': 'VMFile', 'id': 202, 'src': src_id, 'start': 0,
                        'duration': seconds_to_ticks(5.0), 'mediaStart': 0,
                        'mediaDuration': seconds_to_ticks(5.0), 'scalar': 1,
                        'trackNumber': 0, 'parameters': {}, 'effects': [], 'metadata': {},
                        'animationTracks': {}, 'attributes': {'ident': ''}},
                    'audio': {'_type': 'AMFile', 'id': 203, 'src': src_id, 'start': 0,
                        'duration': seconds_to_ticks(5.0), 'mediaStart': 0,
                        'mediaDuration': seconds_to_ticks(5.0), 'scalar': 1,
                        'channelNumber': '0', 'trackNumber': 0, 'parameters': {},
                        'effects': [], 'metadata': {}, 'animationTracks': {},
                        'attributes': {'ident': ''}},
                },
                {
                    '_type': 'IMFile', 'id': 204, 'src': src_id,
                    'start': seconds_to_ticks(5.0), 'duration': seconds_to_ticks(5.0),
                    'mediaStart': 0, 'mediaDuration': 1, 'scalar': 1,
                    'trackNumber': 0, 'parameters': {}, 'effects': [], 'metadata': {},
                    'animationTracks': {}, 'attributes': {'ident': ''},
                    'trimStartSum': 0,
                },
            ],
            'transitions': [],
        }],
    })
    assert _check_compound_invariants(proj._data) == []
    return proj


class GroupStateMachine(RuleBasedStateMachine):
    """Stateful test: random mutations on a Group-containing project."""

    def __init__(self) -> None:
        super().__init__()
        self.proj = _make_project_with_group()

    def _group(self) -> object | None:
        for c in self.proj.timeline.tracks[0].clips:
            if c.clip_type == 'Group':
                return c
        return None

    @rule(speed=st.floats(min_value=0.25, max_value=4.0, allow_nan=False, allow_infinity=False))
    def do_set_speed_group(self, speed: float) -> None:
        g = self._group()
        if g is not None:
            g.set_speed(speed)

    @rule(factor_num=st.integers(min_value=1, max_value=4), factor_denom=st.integers(min_value=1, max_value=4))
    def do_rescale(self, factor_num: int, factor_denom: int) -> None:
        from camtasia.operations.speed import rescale_project
        rescale_project(self.proj._data, Fraction(factor_num, factor_denom))

    @rule(shift_seconds=st.floats(min_value=-3.0, max_value=3.0, allow_nan=False, allow_infinity=False))
    def do_shift(self, shift_seconds: float) -> None:
        self.proj.timeline.shift_all(shift_seconds)

    @rule(factor=st.floats(min_value=0.25, max_value=4.0, allow_nan=False, allow_infinity=False))
    def do_scale_all_durations(self, factor: float) -> None:
        self.proj.timeline.tracks[0].scale_all_durations(factor)

    @rule()
    def do_ungroup(self) -> None:
        """Ungroup, placing inner clips back on the track."""
        g = self._group()
        if g is not None:
            self.proj.timeline.tracks[0].ungroup_clip(g.id)

    @invariant()
    def compound_invariants_hold(self) -> None:
        issues = _check_compound_invariants(self.proj._data)
        assert issues == [], f'Invariants violated: {[i.message for i in issues]}'


TestGroupStateful = GroupStateMachine.TestCase
TestGroupStateful.settings = settings(
    max_examples=50,
    stateful_step_count=20,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)



def _make_project_with_stitched() -> object:
    """Build a project with a StitchedMedia containing a UnifiedMedia segment + a VMFile segment."""
    from pathlib import Path
    import tempfile

    from camtasia import Project
    tmp = Path(tempfile.mkdtemp()) / 'test.cmproj'
    proj = Project.new(str(tmp), width=1920, height=1080)
    src_id = proj.media_bin.next_id()
    proj._data.setdefault('sourceBin', []).append({
        '_type': 'VMFile', 'id': src_id, 'src': './media/fake.mp4',
        'sourceTracks': [{'range': [0, 300], 'type': 'Video', 'editRate': 30,
            'trackRect': [0, 0, 1920, 1080], 'sampleRate': 30, 'bitDepth': 24,
            'numChannels': 0, 'integratedLUFS': 100.0, 'peakLevel': -1.0,
            'metaData': 'fake.mp4'}],
        'lastMod': 'X', 'loudnessNormalization': False, 'rect': [0, 0, 1920, 1080],
    })
    track = proj.timeline.tracks[0]
    seg_dur = seconds_to_ticks(3.0)
    track._data.setdefault('medias', []).append({
        '_type': 'StitchedMedia', 'id': 300, 'start': 0,
        'duration': seg_dur * 2, 'mediaStart': 0,
        'mediaDuration': seg_dur * 2, 'scalar': 1, 'minMediaStart': 0,
        'parameters': {}, 'effects': [], 'metadata': {},
        'animationTracks': {}, 'attributes': {},
        'medias': [
            {
                '_type': 'UnifiedMedia', 'id': 301, 'start': 0,
                'duration': seg_dur, 'mediaStart': 0,
                'mediaDuration': seg_dur, 'scalar': 1,
                'parameters': {}, 'effects': [], 'metadata': {},
                'animationTracks': {}, 'attributes': {},
                'video': {'_type': 'VMFile', 'id': 302, 'src': src_id, 'start': 0,
                    'duration': seg_dur, 'mediaStart': 0,
                    'mediaDuration': seg_dur, 'scalar': 1,
                    'trackNumber': 0, 'parameters': {}, 'effects': [], 'metadata': {},
                    'animationTracks': {}, 'attributes': {'ident': ''}},
                'audio': {'_type': 'AMFile', 'id': 303, 'src': src_id, 'start': 0,
                    'duration': seg_dur, 'mediaStart': 0,
                    'mediaDuration': seg_dur, 'scalar': 1,
                    'channelNumber': '0', 'trackNumber': 0, 'parameters': {},
                    'effects': [], 'metadata': {}, 'animationTracks': {},
                    'attributes': {'ident': ''}},
            },
            {
                '_type': 'VMFile', 'id': 304, 'src': src_id,
                'start': seg_dur, 'duration': seg_dur,
                'mediaStart': 0, 'mediaDuration': seg_dur, 'scalar': 1,
                'trackNumber': 0, 'parameters': {}, 'effects': [], 'metadata': {},
                'animationTracks': {}, 'attributes': {'ident': ''},
            },
        ],
    })
    assert _check_compound_invariants(proj._data) == []
    return proj


class StitchedMediaStateMachine(RuleBasedStateMachine):
    """Stateful test: random mutations on a StitchedMedia-containing project."""

    def __init__(self) -> None:
        super().__init__()
        self.proj = _make_project_with_stitched()

    def _stitched(self) -> object | None:
        for c in self.proj.timeline.tracks[0].clips:
            if c.clip_type == 'StitchedMedia':
                return c
        return None

    @rule(speed=st.floats(min_value=0.25, max_value=4.0, allow_nan=False, allow_infinity=False))
    def do_set_speed(self, speed: float) -> None:
        s = self._stitched()
        if s is not None:
            s.set_speed(speed)

    @rule(factor_num=st.integers(min_value=1, max_value=4), factor_denom=st.integers(min_value=1, max_value=4))
    def do_rescale(self, factor_num: int, factor_denom: int) -> None:
        from camtasia.operations.speed import rescale_project
        rescale_project(self.proj._data, Fraction(factor_num, factor_denom))

    @rule(shift_seconds=st.floats(min_value=-3.0, max_value=3.0, allow_nan=False, allow_infinity=False))
    def do_shift(self, shift_seconds: float) -> None:
        self.proj.timeline.shift_all(shift_seconds)

    @rule(factor=st.floats(min_value=0.25, max_value=4.0, allow_nan=False, allow_infinity=False))
    def do_scale_all_durations(self, factor: float) -> None:
        self.proj.timeline.tracks[0].scale_all_durations(factor)

    @rule(new_dur=st.floats(min_value=1.0, max_value=15.0, allow_nan=False, allow_infinity=False))
    def do_set_duration(self, new_dur: float) -> None:
        s = self._stitched()
        if s is not None:
            s.duration = seconds_to_ticks(new_dur)

    @rule(
        first_end=st.floats(min_value=0.5, max_value=2.5, allow_nan=False, allow_infinity=False),
        first_scalar=st.floats(min_value=0.5, max_value=2.0, allow_nan=False, allow_infinity=False),
        second_scalar=st.floats(min_value=0.5, max_value=2.0, allow_nan=False, allow_infinity=False),
    )
    def do_set_segment_speeds(self, first_end: float, first_scalar: float, second_scalar: float) -> None:
        """Use track.set_segment_speeds on a non-compound clip to stress-test segment logic."""
        # Need a simple clip (not StitchedMedia itself) — this is only meaningful
        # when the track has a non-compound clip. Skip if not present.
        for c in self.proj.timeline.tracks[0].clips:
            if c.clip_type in ('VMFile', 'AMFile'):
                import contextlib
                with contextlib.suppress(ValueError, KeyError):
                    self.proj.timeline.tracks[0].set_segment_speeds(
                        c.id,
                        [(first_end, first_scalar), (first_end + 1.0, second_scalar)],
                    )
                return

    @invariant()
    def compound_invariants_hold(self) -> None:
        issues = _check_compound_invariants(self.proj._data)
        assert issues == [], f'Invariants violated: {[i.message for i in issues]}'


TestStitchedMediaStateful = StitchedMediaStateMachine.TestCase
TestStitchedMediaStateful.settings = settings(
    max_examples=50,
    stateful_step_count=20,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
