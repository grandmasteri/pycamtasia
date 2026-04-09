"""Integration tests exercising pycamtasia against a real Camtasia 2026 project."""
from __future__ import annotations

import copy
from fractions import Fraction

import pytest

from camtasia.media_bin import Media, MediaBin, MediaType
from camtasia.operations.speed import rescale_project, set_audio_speed
from camtasia.timeline.clips import (
    AMFile,
    Callout,
    Group,
    IMFile,
    ScreenVMFile,
    StitchedMedia,
    VMFile,
    clip_from_dict,
)
from camtasia.timeline.markers import MarkerList
from camtasia.timeline.timeline import Timeline
from camtasia.timeline.transitions import Transition
from camtasia.timing import EDIT_RATE

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _scene(data):
    return data['timeline']['sceneTrack']['scenes'][0]['csml']


def _track_clips(data, track_index):
    return [clip_from_dict(m) for m in _scene(data)['tracks'][track_index].get('medias', [])]


def _timeline(data):
    return Timeline(data['timeline'])


# ===========================================================================
# Project-level
# ===========================================================================

class TestProjectLevel:
    def test_edit_rate(self, test_project_a_data):
        assert test_project_a_data['editRate'] == 705_600_000

    def test_dimensions(self, test_project_a_data):
        assert test_project_a_data['width'] == 1920.0
        assert test_project_a_data['height'] == 1080.0

    def test_video_frame_rate(self, test_project_a_data):
        assert test_project_a_data['videoFormatFrameRate'] == 60


# ===========================================================================
# Media Bin
# ===========================================================================

class TestMediaBin:
    @pytest.fixture
    def media_bin(self, test_project_a_data):
        from pathlib import Path
        return MediaBin(test_project_a_data['sourceBin'], Path('.'))

    def test_media_items(self, media_bin):
        actual_ids = [m.id for m in media_bin]
        expected_ids = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
        assert actual_ids == expected_ids

    def test_screen_recording_is_trec(self, media_bin):
        actual_source = media_bin[2].source
        assert actual_source.suffix == '.trec'

    def test_wav_audio(self, media_bin):
        actual_source = media_bin[3].source
        assert actual_source.suffix == '.wav'

    def test_planning_process_png(self, media_bin):
        actual_source = media_bin[6].source
        assert actual_source.name == 'diagram-process.png'

    def test_media_type_video_shader(self, media_bin):
        assert media_bin[1].type == MediaType.Video

    def test_media_type_audio(self, media_bin):
        assert media_bin[3].type == MediaType.Audio

    def test_media_type_image(self, media_bin):
        assert media_bin[6].type == MediaType.Image

    def test_dimensions_screen_recording(self, media_bin):
        assert media_bin[2].dimensions == (2560, 1440)

    def test_dimensions_use_cases_diagram(self, media_bin):
        assert media_bin[8].dimensions == (1920, 1080)


# ===========================================================================
# Timeline Structure
# ===========================================================================

class TestTimelineStructure:
    def test_track_count(self, test_project_a_data):
        actual_track_count = len(list(_timeline(test_project_a_data).tracks))
        assert actual_track_count == 4

    def test_track_0_clip_types(self, test_project_a_data):
        actual_types = [c.clip_type for c in _track_clips(test_project_a_data, 0)]
        expected_types = ['AMFile', 'StitchedMedia', 'StitchedMedia']
        assert actual_types == expected_types

    def test_track_0_clip_classes(self, test_project_a_data):
        actual_classes = [type(c) for c in _track_clips(test_project_a_data, 0)]
        expected_classes = [AMFile, StitchedMedia, StitchedMedia]
        assert actual_classes == expected_classes

    def test_track_1_clip_types(self, test_project_a_data):
        actual_types = [c.clip_type for c in _track_clips(test_project_a_data, 1)]
        expected_types = ['VMFile']
        assert actual_types == expected_types

    def test_track_2_clip_types(self, test_project_a_data):
        actual_types = [c.clip_type for c in _track_clips(test_project_a_data, 2)]
        expected_types = [
            'Callout', 'IMFile', 'IMFile', 'Group', 'Group',
            'IMFile', 'IMFile', 'Callout',
        ]
        assert actual_types == expected_types

    def test_track_3_empty(self, test_project_a_data):
        actual_clips = _track_clips(test_project_a_data, 3)
        assert actual_clips == []


# ===========================================================================
# Clip Properties
# ===========================================================================

class TestClipProperties:
    def test_amfile_14_scalar(self, test_project_a_data):
        actual_clip = _track_clips(test_project_a_data, 0)[0]
        assert actual_clip.id == 14
        assert actual_clip.scalar == Fraction(4509, 4825)

    def test_amfile_14_start_seconds(self, test_project_a_data):
        actual_clip = _track_clips(test_project_a_data, 0)[0]
        assert actual_clip.start_seconds == pytest.approx(0.0)

    def test_amfile_14_source_id(self, test_project_a_data):
        actual_clip = _track_clips(test_project_a_data, 0)[0]
        assert actual_clip.source_id == 3

    def test_vmfile_31_source_id(self, test_project_a_data):
        actual_clip = _track_clips(test_project_a_data, 1)[0]
        assert actual_clip.id == 31
        assert actual_clip.source_id == 5

    def test_vmfile_31_start(self, test_project_a_data):
        actual_clip = _track_clips(test_project_a_data, 1)[0]
        assert actual_clip.start == 0

    def test_vmfile_31_media_start_trimmed(self, test_project_a_data):
        actual_clip = _track_clips(test_project_a_data, 1)[0]
        assert actual_clip.media_start == 592704000000

    def test_callout_32_text(self, test_project_a_data):
        actual_clip = _track_clips(test_project_a_data, 2)[0]
        assert actual_clip.id == 32
        assert isinstance(actual_clip, Callout)
        assert actual_clip.text.startswith('SampleApp Quality Analysis')

    def test_imfile_33_source_id(self, test_project_a_data):
        actual_clip = _track_clips(test_project_a_data, 2)[1]
        assert actual_clip.id == 33
        assert isinstance(actual_clip, IMFile)
        assert actual_clip.source_id == 6


# ===========================================================================
# Transitions
# ===========================================================================

class TestTransitions:
    def test_track_1_transition_count(self, test_project_a_data):
        actual_transitions = list(_timeline(test_project_a_data).tracks[1].transitions)
        assert [t.name for t in actual_transitions] == ['FadeThroughBlack']

    def test_track_1_transition_duration(self, test_project_a_data):
        actual_transition = list(_timeline(test_project_a_data).tracks[1].transitions)[0]
        assert actual_transition.duration_seconds == pytest.approx(1.0)

    def test_track_2_transition_names(self, test_project_a_data):
        actual_names = [t.name for t in _timeline(test_project_a_data).tracks[2].transitions]
        expected_names = ['FadeThroughBlack'] * 7
        assert actual_names == expected_names

    def test_track_2_transition_durations(self, test_project_a_data):
        actual_durations = [t.duration_seconds for t in _timeline(test_project_a_data).tracks[2].transitions]
        expected_durations = [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 1.0]
        assert actual_durations == pytest.approx(expected_durations)

    def test_track_2_first_transition_media_ids(self, test_project_a_data):
        actual_transition = list(_timeline(test_project_a_data).tracks[2].transitions)[0]
        assert actual_transition.left_media_id == 32
        assert actual_transition.right_media_id == 33

    def test_track_2_last_transition_is_fade_out(self, test_project_a_data):
        actual_transition = list(_timeline(test_project_a_data).tracks[2].transitions)[-1]
        assert actual_transition.left_media_id == 82
        assert actual_transition.right_media_id is None


# ===========================================================================
# Markers
# ===========================================================================

class TestMarkers:
    def test_marker_count(self, test_project_a_data):
        actual_markers = list(_timeline(test_project_a_data).markers)
        assert [m.name for m in actual_markers] == [
            kf['value'] for kf in test_project_a_data['timeline']['parameters']['toc']['keyframes']
        ]

    def test_first_marker_time(self, test_project_a_data):
        actual_first = list(_timeline(test_project_a_data).markers)[0]
        actual_seconds = actual_first.time / EDIT_RATE
        # ~2:44.83 = 164.83s
        assert actual_seconds == pytest.approx(164.83, abs=0.01)

    def test_last_marker_label(self, test_project_a_data):
        actual_last = list(_timeline(test_project_a_data).markers)[-1]
        assert actual_last.name.startswith('l')


# ===========================================================================
# Nested Structures
# ===========================================================================

class TestNestedStructures:
    def test_stitched_media_15_nested_clips(self, test_project_a_data):
        actual_clip = _track_clips(test_project_a_data, 0)[1]
        assert actual_clip.id == 15
        assert isinstance(actual_clip, StitchedMedia)
        actual_nested = actual_clip.nested_clips
        actual_types = [c.clip_type for c in actual_nested]
        expected_types = ['AMFile'] * 7
        assert actual_types == expected_types

    def test_stitched_media_15_nested_ids(self, test_project_a_data):
        actual_clip = _track_clips(test_project_a_data, 0)[1]
        actual_ids = [c.id for c in actual_clip.nested_clips]
        expected_ids = [16, 17, 18, 19, 20, 21, 22]
        assert actual_ids == expected_ids

    def test_group_38_has_screen_vm_files(self, test_project_a_data):
        actual_clip = _track_clips(test_project_a_data, 2)[4]
        assert actual_clip.id == 38
        assert isinstance(actual_clip, Group)
        actual_track_1_types = [c.clip_type for c in actual_clip.tracks[1].clips]
        assert 'ScreenVMFile' in actual_track_1_types

    def test_group_38_screen_vm_file_effects(self, test_project_a_data):
        actual_group = _track_clips(test_project_a_data, 2)[4]
        assert actual_group.id == 38
        # First clip on track 1 is a ScreenVMFile with effects
        actual_screen_clip = actual_group.tracks[1].clips[0]
        actual_effect_names = [e['effectName'] for e in actual_screen_clip.effects]
        assert 'RoundCorners' in actual_effect_names
        assert 'DropShadow' in actual_effect_names


# ===========================================================================
# Speed Changes
# ===========================================================================

class TestSpeedChanges:
    def test_amfile_14_speed_scalar(self, test_project_a_data):
        actual_clip = _track_clips(test_project_a_data, 0)[0]
        assert actual_clip.id == 14
        assert actual_clip.scalar == Fraction(4509, 4825)

    def test_group_38_screen_vm_file_speed_changed(self, test_project_a_data):
        actual_group = _track_clips(test_project_a_data, 2)[4]
        assert actual_group.id == 38
        actual_screen_clips = [
            c for c in actual_group.tracks[1].clips
            if isinstance(c, ScreenVMFile)
        ]
        actual_speed_changed = [c for c in actual_screen_clips if c.scalar != 1]
        # id=48 scalar=51/101, id=49 scalar=49/64, id=50 scalar=69/142, etc.
        assert actual_speed_changed[0].id == 48
        assert actual_speed_changed[0].scalar == Fraction(51, 101)


# ===========================================================================
# Operations
# ===========================================================================

class TestRescaleProject:
    def test_rescale_scales_clip_timing(self, test_project_a_data):
        actual_data = copy.deepcopy(test_project_a_data)
        factor = Fraction(2, 1)  # double all durations

        expected_original_start = _scene(test_project_a_data)['tracks'][1]['medias'][0]['start']
        expected_original_duration = _scene(test_project_a_data)['tracks'][1]['medias'][0]['duration']

        rescale_project(actual_data, factor)

        actual_clip = _scene(actual_data)['tracks'][1]['medias'][0]
        assert actual_clip['start'] == expected_original_start * 2
        assert actual_clip['duration'] == expected_original_duration * 2

    def test_rescale_scales_transitions(self, test_project_a_data):
        actual_data = copy.deepcopy(test_project_a_data)
        expected_original_dur = _scene(test_project_a_data)['tracks'][2]['transitions'][0]['duration']

        rescale_project(actual_data, Fraction(2, 1))

        actual_dur = _scene(actual_data)['tracks'][2]['transitions'][0]['duration']
        assert actual_dur == expected_original_dur * 2

    def test_rescale_scales_markers(self, test_project_a_data):
        actual_data = copy.deepcopy(test_project_a_data)
        expected_original_time = test_project_a_data['timeline']['parameters']['toc']['keyframes'][0]['time']

        rescale_project(actual_data, Fraction(2, 1))

        actual_time = actual_data['timeline']['parameters']['toc']['keyframes'][0]['time']
        assert actual_time == expected_original_time * 2


class TestSetAudioSpeed:
    def test_set_audio_speed_resets_scalar(self, test_project_a_data):
        actual_data = copy.deepcopy(test_project_a_data)
        set_audio_speed(actual_data, target_speed=1.0)

        actual_amfile = _scene(actual_data)['tracks'][0]['medias'][0]
        assert actual_amfile['id'] == 14
        assert actual_amfile['scalar'] == 1
