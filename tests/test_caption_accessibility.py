"""Tests for validate_caption_accessibility in camtasia.validation."""
from __future__ import annotations

from pathlib import Path
import tempfile

import pytest

from camtasia import Project
from camtasia.validation import (
    _contrast_ratio,
    _relative_luminance,
    validate_caption_accessibility,
)


@pytest.fixture
def project_with_captions():
    """Project with three well-formed captions on a Subtitles track."""
    tmp = Path(tempfile.mkdtemp()) / 'test.cmproj'
    proj = Project.new(str(tmp))
    proj.add_subtitle_track([
        (0.0, 3.0, 'Hello world'),
        (4.0, 2.5, 'Short line'),
        (7.0, 4.0, 'Third caption here'),
    ])
    return proj


@pytest.fixture
def empty_project():
    """Project with no subtitle track."""
    tmp = Path(tempfile.mkdtemp()) / 'test.cmproj'
    return Project.new(str(tmp))


class TestValidateCaptionAccessibilityClean:
    def test_no_issues_for_well_formed_captions(self, project_with_captions):
        issues = validate_caption_accessibility(project_with_captions)
        # Default white-on-black has high contrast, durations are fine, lines are short
        assert issues == []

    def test_empty_project_returns_no_issues(self, empty_project):
        issues = validate_caption_accessibility(empty_project)
        assert issues == []


class TestLineTooLong:
    def test_detects_line_exceeding_max_words(self):
        tmp = Path(tempfile.mkdtemp()) / 'test.cmproj'
        proj = Project.new(str(tmp))
        proj.add_subtitle_track([
            (0.0, 3.0, 'one two three four five six seven eight'),
        ])
        issues = validate_caption_accessibility(proj)
        long_issues = [i for i in issues if i['type'] == 'line_too_long']
        assert len(long_issues) == 1
        assert long_issues[0]['value'] == 8
        assert long_issues[0]['clip_index'] == 0

    def test_respects_custom_max_words(self):
        tmp = Path(tempfile.mkdtemp()) / 'test.cmproj'
        proj = Project.new(str(tmp))
        proj.add_subtitle_track([
            (0.0, 3.0, 'one two three four five'),
        ])
        issues = validate_caption_accessibility(proj, max_words_per_line=4)
        long_issues = [i for i in issues if i['type'] == 'line_too_long']
        assert len(long_issues) == 1
        assert long_issues[0]['value'] == 5

    def test_checks_each_line_separately(self):
        tmp = Path(tempfile.mkdtemp()) / 'test.cmproj'
        proj = Project.new(str(tmp))
        proj.add_subtitle_track([
            (0.0, 3.0, 'short\none two three four five six seven eight'),
        ])
        issues = validate_caption_accessibility(proj)
        long_issues = [i for i in issues if i['type'] == 'line_too_long']
        assert len(long_issues) == 1

    def test_exactly_max_words_is_ok(self):
        tmp = Path(tempfile.mkdtemp()) / 'test.cmproj'
        proj = Project.new(str(tmp))
        proj.add_subtitle_track([
            (0.0, 3.0, 'one two three four five six seven'),
        ])
        issues = validate_caption_accessibility(proj)
        long_issues = [i for i in issues if i['type'] == 'line_too_long']
        assert long_issues == []


class TestDurationTooLong:
    def test_detects_long_duration(self):
        tmp = Path(tempfile.mkdtemp()) / 'test.cmproj'
        proj = Project.new(str(tmp))
        proj.add_subtitle_track([
            (0.0, 10.0, 'Long caption'),
        ])
        issues = validate_caption_accessibility(proj)
        long_issues = [i for i in issues if i['type'] == 'duration_too_long']
        assert len(long_issues) == 1
        assert long_issues[0]['clip_index'] == 0

    def test_respects_custom_max_duration(self):
        tmp = Path(tempfile.mkdtemp()) / 'test.cmproj'
        proj = Project.new(str(tmp))
        proj.add_subtitle_track([
            (0.0, 4.0, 'Caption'),
        ])
        issues = validate_caption_accessibility(proj, max_duration_seconds=3.0)
        long_issues = [i for i in issues if i['type'] == 'duration_too_long']
        assert len(long_issues) == 1


class TestDurationTooShort:
    def test_detects_short_duration(self):
        tmp = Path(tempfile.mkdtemp()) / 'test.cmproj'
        proj = Project.new(str(tmp))
        proj.add_subtitle_track([
            (0.0, 0.5, 'Flash'),
        ])
        issues = validate_caption_accessibility(proj)
        short_issues = [i for i in issues if i['type'] == 'duration_too_short']
        assert len(short_issues) == 1
        assert short_issues[0]['clip_index'] == 0
        assert short_issues[0]['value'] == 0.5


class TestContrastRatio:
    def test_low_contrast_detected(self):
        tmp = Path(tempfile.mkdtemp()) / 'test.cmproj'
        proj = Project.new(str(tmp))
        proj.add_subtitle_track([(0.0, 3.0, 'Hello')])
        # Set fg and bg to similar colors (low contrast)
        attrs = proj.timeline.caption_attributes
        attrs.foreground_color = [128, 128, 128, 255]
        attrs.background_color = [120, 120, 120, 255]
        issues = validate_caption_accessibility(proj)
        contrast_issues = [i for i in issues if i['type'] == 'low_contrast']
        assert len(contrast_issues) == 1
        assert contrast_issues[0]['value'] < 4.5

    def test_high_contrast_passes(self, project_with_captions):
        # Default white-on-black should pass
        issues = validate_caption_accessibility(project_with_captions)
        contrast_issues = [i for i in issues if i['type'] == 'low_contrast']
        assert contrast_issues == []

    def test_custom_min_contrast(self):
        tmp = Path(tempfile.mkdtemp()) / 'test.cmproj'
        proj = Project.new(str(tmp))
        proj.add_subtitle_track([(0.0, 3.0, 'Hello')])
        # White on black has ~21:1 contrast
        issues = validate_caption_accessibility(proj, min_contrast_ratio=25.0)
        contrast_issues = [i for i in issues if i['type'] == 'low_contrast']
        assert len(contrast_issues) == 1


class TestLuminanceAndContrast:
    def test_relative_luminance_black(self):
        assert _relative_luminance([0, 0, 0, 255]) == pytest.approx(0.0)

    def test_relative_luminance_white(self):
        assert _relative_luminance([255, 255, 255, 255]) == pytest.approx(1.0, abs=0.01)

    def test_contrast_ratio_black_white(self):
        ratio = _contrast_ratio([255, 255, 255, 255], [0, 0, 0, 255])
        assert ratio == pytest.approx(21.0, abs=0.1)

    def test_contrast_ratio_same_color(self):
        ratio = _contrast_ratio([100, 100, 100, 255], [100, 100, 100, 255])
        assert ratio == pytest.approx(1.0)


class TestNonCalloutOnSubtitlesTrack:
    """Cover validation.py line 642: skip non-Callout clips on Subtitles track."""

    def test_skips_non_callout_clips(self, project_with_captions):
        from camtasia.timing import seconds_to_ticks
        track = project_with_captions.timeline.find_track_by_name('Subtitles')
        # Add a non-Callout clip to the Subtitles track
        track._data.setdefault('medias', []).append({
            'id': 777, '_type': 'VMFile', 'src': 1,
            'start': seconds_to_ticks(20.0),
            'duration': seconds_to_ticks(2.0),
            'mediaStart': 0, 'mediaDuration': seconds_to_ticks(2.0),
            'scalar': 1, 'parameters': {}, 'effects': [],
        })
        issues = validate_caption_accessibility(project_with_captions)
        # Should not crash — the VMFile is simply skipped
        assert all(i['type'] != 'unknown_clip_type' for i in issues)
