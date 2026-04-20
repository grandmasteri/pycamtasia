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

    @invariant()
    def compound_invariants_hold(self) -> None:
        issues = _check_compound_invariants(self.proj._data)
        assert issues == [], f'Invariants violated: {[i.message for i in issues]}'


TestUnifiedMediaStateful = UnifiedMediaStateMachine.TestCase
TestUnifiedMediaStateful.settings = settings(
    max_examples=100,
    stateful_step_count=25,
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
