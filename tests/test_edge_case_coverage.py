"""Edge-case coverage tests for uncovered lines in pycamtasia."""
from __future__ import annotations

from fractions import Fraction
from pathlib import Path

from camtasia.operations.cleanup import remove_orphaned_media
from camtasia.operations.speed import rescale_project
from camtasia.timing import seconds_to_ticks


STITCHED_MEDIA = {
    '_type': 'StitchedMedia', 'id': 10, 'start': 0, 'duration': 100,
    'mediaStart': 0, 'mediaDuration': 100, 'scalar': 1,
    'parameters': {}, 'effects': [], 'metadata': {}, 'animationTracks': {},
    'minMediaStart': 0,
    'medias': [
        {'_type': 'AMFile', 'id': 11, 'start': 0, 'duration': 50, 'src': 1,
         'mediaStart': 0, 'mediaDuration': 50, 'scalar': 1,
         'parameters': {}, 'effects': [], 'metadata': {}, 'animationTracks': {}},
        {'_type': 'AMFile', 'id': 12, 'start': 50, 'duration': 50, 'src': 1,
         'mediaStart': 0, 'mediaDuration': 50, 'scalar': 1,
         'parameters': {}, 'effects': [], 'metadata': {}, 'animationTracks': {}},
    ],
}

UNIFIED_MEDIA = {
    '_type': 'UnifiedMedia', 'id': 20, 'start': 100, 'duration': 100,
    'mediaStart': 0, 'mediaDuration': 100, 'scalar': 1,
    'parameters': {}, 'effects': [], 'metadata': {}, 'animationTracks': {},
    'video': {'_type': 'VMFile', 'id': 21, 'start': 0, 'duration': 100, 'src': 2,
              'mediaStart': 0, 'mediaDuration': 100, 'scalar': 1,
              'parameters': {}, 'effects': [], 'metadata': {}, 'animationTracks': {}},
    'audio': {'_type': 'AMFile', 'id': 22, 'start': 0, 'duration': 100, 'src': 3,
              'mediaStart': 0, 'mediaDuration': 100, 'scalar': 1,
              'parameters': {}, 'effects': [], 'metadata': {}, 'animationTracks': {}},
}


def _inject_clips(project, clip_dicts):
    """Insert raw clip dicts into the first track of a project."""
    tracks = project._data['timeline']['sceneTrack']['scenes'][0]['csml']['tracks']
    for clip in clip_dicts:
        tracks[0]['medias'].append(clip)


def _add_source(project, media_id, src_path='./media/clip.mp4', track_type=0):
    """Add a sourceBin entry."""
    project._data.setdefault('sourceBin', []).append({
        'id': media_id,
        'src': src_path,
        'rect': [0, 0, 1920, 1080],
        'sourceTracks': [{'range': [0, 300], 'type': track_type}],
    })


# ── 1. all_clips() recursion into StitchedMedia / UnifiedMedia ──────────

class TestAllClipsRecursion:
    def test_timeline_all_clips_returns_nested(self, project):
        import copy
        _inject_clips(project, [copy.deepcopy(STITCHED_MEDIA), copy.deepcopy(UNIFIED_MEDIA)])
        ids = {c.id for c in project.timeline.all_clips()}
        assert {10, 11, 12, 20, 21, 22}.issubset(ids)

    def test_project_all_clips_returns_nested(self, project):
        import copy
        _inject_clips(project, [copy.deepcopy(STITCHED_MEDIA), copy.deepcopy(UNIFIED_MEDIA)])
        ids = {c.id for _, c in project.all_clips}
        assert {10, 11, 12, 20, 21, 22}.issubset(ids)


# ── 2. speed.py — UnifiedMedia recursion in rescale_project ─────────────

class TestRescaleUnifiedMedia:
    def test_unified_media_children_scaled(self, project):
        import copy
        _inject_clips(project, [copy.deepcopy(UNIFIED_MEDIA)])
        factor = Fraction(2)
        rescale_project(project._data, factor)
        tracks = project._data['timeline']['sceneTrack']['scenes'][0]['csml']['tracks']
        um = next(m for m in tracks[0]['medias'] if m['_type'] == 'UnifiedMedia')
        assert um['video']['start'] == 0
        assert um['video']['duration'] == 200
        assert um['audio']['start'] == 0
        assert um['audio']['duration'] == 200


# ── 3. callout.py — stroke_color animated value handling ────────────────

class TestCalloutStrokeColorAnimated:
    def test_stroke_color_setter_preserves_keyframes(self, project):
        from camtasia.timeline.clips.callout import Callout
        keyframes = [{'time': 0, 'value': 0.5}, {'time': 100, 'value': 1.0}]
        data = {
            '_type': 'Callout', 'id': 99, 'start': 0, 'duration': 100,
            'mediaStart': 0, 'mediaDuration': 100, 'scalar': 1,
            'parameters': {}, 'effects': [], 'metadata': {}, 'animationTracks': {},
            'def': {
                'stroke-color-red': {'defaultValue': 0.1, 'keyframes': list(keyframes)},
                'stroke-color-green': {'defaultValue': 0.2, 'keyframes': list(keyframes)},
                'stroke-color-blue': {'defaultValue': 0.3, 'keyframes': list(keyframes)},
                'stroke-color-opacity': {'defaultValue': 0.4, 'keyframes': list(keyframes)},
            },
        }
        callout = Callout(data)
        callout.stroke_color = (0.9, 0.8, 0.7, 0.6)
        d = callout.definition
        assert d['stroke-color-red']['defaultValue'] == 0.9
        assert d['stroke-color-green']['defaultValue'] == 0.8
        assert d['stroke-color-blue']['defaultValue'] == 0.7
        assert d['stroke-color-opacity']['defaultValue'] == 0.6
        # keyframes preserved
        assert d['stroke-color-red']['keyframes'] == keyframes


# ── 4. tile_layout.py — negative duration guard ─────────────────────────

class TestTileLayoutNegativeDuration:
    def test_stagger_causes_fewer_tiles(self, project):
        from camtasia.builders.tile_layout import TileLayout
        FIXTURES = Path(__file__).parent / 'fixtures'
        dummy = FIXTURES / 'empty.wav'
        layout = TileLayout(project)
        images = [dummy] * 6
        # end=5s, stagger=2s → tile 3 starts at 6s > 5s → tile_duration <= 0
        placed = layout.add_grid(images, start_seconds=0, end_seconds=5, stagger_seconds=2)
        assert len(placed) < 6


# ── 5. media_bin.py — Media.type with empty sourceTracks ────────────────

class TestMediaTypeEmptySourceTracks:
    def test_type_returns_none_for_empty_source_tracks(self, project):
        from camtasia.media_bin.media_bin import Media
        media = Media({'id': 1, 'src': './test.mp4', 'rect': [0, 0, 100, 100], 'sourceTracks': []})
        assert media.type is None


# ── 6. cleanup.py — StitchedMedia recursion in _collect_source_ids ──────

class TestCleanupStitchedMediaSources:
    def test_stitched_media_sub_clip_sources_not_orphaned(self, project):
        import copy
        _add_source(project, 1, './media/audio1.mp3', track_type=1)
        _add_source(project, 2, './media/video.mp4')
        _add_source(project, 999, './media/orphan.mp4')
        _inject_clips(project, [copy.deepcopy(STITCHED_MEDIA)])
        removed = remove_orphaned_media(project)
        assert 1 not in removed  # sub-clip src
        assert 999 in removed    # orphan


# ── 7. project.py — extract_audio_track source lookup ───────────────────

class TestExtractAudioTrack:
    def test_extract_audio_track_includes_source_path(self, project, tmp_path):
        _add_source(project, 42, './media/narration.mp3', track_type=1)
        audio_clip = {
            '_type': 'AMFile', 'id': 50, 'start': 0,
            'duration': seconds_to_ticks(5.0),
            'mediaStart': 0, 'mediaDuration': seconds_to_ticks(5.0),
            'scalar': 1, 'src': 42,
            'parameters': {}, 'effects': [], 'metadata': {}, 'animationTracks': {},
        }
        _inject_clips(project, [audio_clip])
        out = tmp_path / 'audio_list.txt'
        project.extract_audio_track(out)
        content = out.read_text()
        assert 'narration.mp3' in content


class TestAllEffectsRecursion:
    """Cover timeline.py all_effects recursion into StitchedMedia/UnifiedMedia."""

    def test_effects_on_stitched_media_sub_clips(self, project):
        track = project.timeline.add_track('Test')
        stitched = {
            '_type': 'StitchedMedia', 'id': 30, 'start': 0, 'duration': 100,
            'mediaStart': 0, 'mediaDuration': 100, 'scalar': 1,
            'parameters': {}, 'effects': [], 'metadata': {}, 'animationTracks': {},
            'minMediaStart': 0,
            'medias': [
                {'_type': 'AMFile', 'id': 31, 'start': 0, 'duration': 50, 'src': 1,
                 'effects': [{'effectName': 'Emphasize', 'parameters': {}}]},
            ],
        }
        track._data.setdefault('medias', []).append(stitched)
        all_effs = project.timeline.all_effects
        effect_names = [e[2].get('effectName') for e in all_effs]
        assert 'Emphasize' in effect_names

    def test_effects_on_unified_media_sub_clips(self, project):
        track = project.timeline.add_track('Test')
        unified = {
            '_type': 'UnifiedMedia', 'id': 40, 'start': 0, 'duration': 100,
            'mediaStart': 0, 'mediaDuration': 100, 'scalar': 1,
            'parameters': {}, 'effects': [], 'metadata': {}, 'animationTracks': {},
            'video': {'_type': 'VMFile', 'id': 41, 'start': 0, 'duration': 100, 'src': 2,
                      'effects': [{'effectName': 'DropShadow', 'parameters': {}}]},
            'audio': {'_type': 'AMFile', 'id': 42, 'start': 0, 'duration': 100, 'src': 3,
                      'effects': [{'effectName': 'Emphasize', 'parameters': {}}]},
        }
        track._data.setdefault('medias', []).append(unified)
        all_effs = project.timeline.all_effects
        effect_names = [e[2].get('effectName') for e in all_effs]
        assert 'DropShadow' in effect_names
        assert 'Emphasize' in effect_names


class TestCalloutStrokeColorAnimatedGetter:
    """Cover callout.py:188 - stroke_color getter with animated values."""

    def test_stroke_color_getter_with_animated_dict(self):
        from camtasia.timeline.clips.callout import Callout
        data = {
            '_type': 'Callout', 'id': 1, 'start': 0, 'duration': 100,
            'def': {
                'stroke-color-red': {'type': 'double', 'defaultValue': 0.5, 'keyframes': [{'time': 0, 'value': 0.5}]},
                'stroke-color-green': 0.3,
                'stroke-color-blue': 0.1,
                'stroke-color-opacity': 1.0,
            },
        }
        callout = Callout(data)
        r, g, b, a = callout.stroke_color
        assert r == 0.5  # reads defaultValue from animated dict


class TestExtractAudioTrackSourceLookup:
    """Cover project.py:2459 - source lookup in extract_audio_track."""

    def test_extract_finds_source_path(self, project, tmp_path):
        from pathlib import Path
        # Import a real audio file
        wav = Path(__file__).parent / 'fixtures' / 'empty.wav'
        media = project.import_media(wav)
        # Add audio clip referencing it
        track = project.timeline.add_track('VO')
        track.add_audio(media.id, start_seconds=0, duration_seconds=1)
        # Extract
        out = tmp_path / 'audio.txt'
        project.extract_audio_track(str(out))
        content = out.read_text()
        assert len(content.strip()) > 0


class TestAllEffectsGroupRecursion:
    """Cover timeline.py:396-399 - all_effects Group recursion."""

    def test_effects_on_group_internal_clips(self, project):
        track = project.timeline.add_track('Test')
        group = {
            '_type': 'Group', 'id': 50, 'start': 0, 'duration': 100,
            'mediaStart': 0, 'mediaDuration': 100, 'scalar': 1,
            'parameters': {}, 'effects': [], 'metadata': {}, 'animationTracks': {},
            'attributes': {'ident': '', 'gain': 1.0, 'mixToMono': False,
                           'widthAttr': 0.0, 'heightAttr': 0.0, 'maxDurationAttr': 0, 'assetProperties': []},
            'tracks': [{
                'trackIndex': 0, 'medias': [
                    {'_type': 'VMFile', 'id': 51, 'start': 0, 'duration': 100, 'src': 1,
                     'effects': [{'effectName': 'Glow', 'parameters': {}}]},
                ], 'transitions': [], 'parameters': {}, 'ident': '',
                'audioMuted': False, 'videoHidden': False, 'magnetic': False, 'matte': 0, 'solo': False,
            }],
        }
        track._data.setdefault('medias', []).append(group)
        all_effs = project.timeline.all_effects
        effect_names = [e[2].get('effectName') for e in all_effs]
        assert 'Glow' in effect_names


class TestCalloutFillColorAnimatedSetter:
    """Cover callout.py:188 - fill_color setter with animated dict values."""

    def test_fill_color_setter_preserves_keyframes(self):
        from camtasia.timeline.clips.callout import Callout
        data = {
            '_type': 'Callout', 'id': 1, 'start': 0, 'duration': 100,
            'def': {
                'fill-color-red': {'type': 'double', 'defaultValue': 0.5, 'keyframes': [{'time': 0, 'value': 0.5}]},
                'fill-color-green': {'type': 'double', 'defaultValue': 0.3, 'keyframes': []},
                'fill-color-blue': 0.1,
                'fill-color-opacity': 1.0,
            },
        }
        callout = Callout(data)
        callout.fill_color = (0.9, 0.8, 0.7, 0.6)
        # Animated dicts should have defaultValue updated
        assert data['def']['fill-color-red']['defaultValue'] == 0.9
        assert data['def']['fill-color-red']['keyframes'] == [{'time': 0, 'value': 0.5}]  # preserved
        # Plain scalar should be replaced
        assert data['def']['fill-color-blue'] == 0.7
