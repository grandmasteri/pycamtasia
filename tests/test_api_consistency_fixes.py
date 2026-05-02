"""Regression tests for api_consistency review findings."""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import PropertyMock, patch
import warnings

if TYPE_CHECKING:
    from camtasia.project import Project


# ── REV-api_consistency-001: duration_formatted deprecation ──────


class TestDurationFormattedDeprecation:
    """duration_formatted should emit DeprecationWarning."""

    def test_emits_deprecation_warning(self):
        from camtasia.project import Project

        with patch.object(Project, 'duration_seconds', new_callable=PropertyMock, return_value=125.0):
            proj = object.__new__(Project)
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter('always')
                _ = proj.duration_formatted
                assert any(issubclass(x.category, DeprecationWarning) for x in w)

    def test_deprecation_message_mentions_total_duration_formatted(self):
        from camtasia.project import Project

        with patch.object(Project, 'duration_seconds', new_callable=PropertyMock, return_value=125.0):
            proj = object.__new__(Project)
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter('always')
                _ = proj.duration_formatted
                msgs = [str(x.message) for x in w if issubclass(x.category, DeprecationWarning)]
                assert any('total_duration_formatted' in m for m in msgs)


# ── REV-api_consistency-003: add_gradient_background track_name ──


class TestGradientBackgroundTrackName:
    """add_gradient_background should accept track_name like other add_* methods."""

    def test_accepts_track_name_kwarg(self, project: Project):
        project.add_gradient_background(duration_seconds=5.0, track_name='BG')
        assert 'BG' in [t.name for t in project.timeline.tracks]

    def test_default_track_name_is_background(self, project: Project):
        project.add_gradient_background(duration_seconds=5.0)
        assert 'Background' in [t.name for t in project.timeline.tracks]


# ── REV-api_consistency-005: color parameter consistency ─────────


class TestColorParameterConsistency:
    """All color params should accept RGBA float 4-tuples."""

    def test_add_title_card_accepts_rgba_4tuple(self, project: Project):
        clip = project.add_title_card('Test', font_color=(1.0, 0.0, 0.0, 0.5))
        assert clip is not None

    def test_add_subtitle_track_accepts_rgba_4tuple(self, project: Project):
        clips = project.add_subtitle_track(
            [(0.0, 2.0, 'Sub')], font_color=(0.0, 1.0, 0.0, 0.8),
        )
        assert len(clips) == 1

    def test_add_caption_accepts_rgba_4tuple(self, project: Project):
        clip = project.add_caption('Cap', 0.0, 2.0, font_color=(0.0, 0.0, 1.0, 1.0))
        assert clip is not None

    def test_track_add_lower_third_accepts_float_rgba(self, project: Project):
        track = project.timeline.get_or_create_track('LT')
        group = track.add_lower_third(
            'Name', 'Title', 0.0, 5.0,
            title_color=(1.0, 0.0, 0.0, 1.0),
        )
        assert group is not None

    def test_track_add_lower_third_int_rgba_warns(self, project: Project):
        track = project.timeline.get_or_create_track('LT')
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            track.add_lower_third(
                'Name', 'Title', 0.0, 5.0,
                title_color=(255, 0, 0, 255),
            )
            assert any(issubclass(x.category, DeprecationWarning) for x in w)


# ── REV-api_consistency-006: Project.add_lower_third rename ──────


class TestProjectAddSimpleLowerThird:
    """Project.add_lower_third should be renamed to add_simple_lower_third."""

    def test_add_simple_lower_third_exists(self, project: Project):
        assert hasattr(project, 'add_simple_lower_third')

    def test_old_name_emits_deprecation(self, project: Project):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            project.add_lower_third('Title')
            assert any(issubclass(x.category, DeprecationWarning) for x in w)

    def test_add_simple_lower_third_works(self, project: Project):
        clip = project.add_simple_lower_third('Title', subtitle_text='Sub')
        assert clip is not None


# ── REV-api_consistency-008: voiceover_sequence deprecation ──────


class TestVoiceoverSequenceDeprecation:
    """add_voiceover_sequence should emit DeprecationWarning."""

    def test_emits_deprecation_warning(self, project: Project):
        fixtures = Path(__file__).parent / 'fixtures'
        wav = fixtures / 'empty.wav'
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            project.add_voiceover_sequence([wav])
            assert any(
                issubclass(x.category, DeprecationWarning)
                and 'add_voiceover_sequence_v2' in str(x.message)
                for x in w
            )
