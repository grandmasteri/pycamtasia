"""Kitchen-sink stress tests for pycamtasia.

Each test exercises 10+ features simultaneously to stress-test feature
INTERACTIONS. If a test fails, it's a high-signal discovery that some
combination of features is broken.
"""
from __future__ import annotations

import struct
import zlib
from pathlib import Path

import pytest

from camtasia import (
    BehaviorPreset,
    CalloutShape,
    EffectName,
    InterpolationType,
    TransitionType,
    export_csv,
    export_edl,
    export_markers_as_srt,
    seconds_to_ticks,
)
from camtasia.operations import (
    compact_project,
    merge_tracks,
    pack_track,
    remove_empty_tracks,
    ripple_delete,
    ripple_insert,
    ripple_move,
    save_as_template,
    new_from_template,
)
from tests.integration_helpers import INTEGRATION_MARKERS, open_in_camtasia

pytestmark = INTEGRATION_MARKERS

FIXTURES = Path(__file__).parent / 'fixtures'
EMPTY_WAV = FIXTURES / 'empty.wav'


def _create_test_image(tmp_path: Path, name: str = 'img.png') -> Path:
    """Create a minimal 1x1 white PNG."""
    def _chunk(chunk_type, data):
        c = chunk_type + data
        return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c) & 0xffffffff)
    sig = b'\x89PNG\r\n\x1a\n'
    ihdr = _chunk(b'IHDR', struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0))
    idat = _chunk(b'IDAT', zlib.compress(b'\x00\xff\xff\xff'))
    iend = _chunk(b'IEND', b'')
    path = tmp_path / name
    path.write_bytes(sig + ihdr + idat + iend)
    return path


class TestFullVideoProduction:
    """Simulates a realistic YouTube video project with many features."""

    def test_full_video_production_opens(self, project, tmp_path):
        project.width = 1920
        project.height = 1080

        # Import media
        audio = project.import_media(EMPTY_WAV)
        img = _create_test_image(tmp_path, 'frame.png')
        image_media = project.import_media(img)

        # Create 4 tracks
        title_track = project.timeline.add_track('Titles')
        main_track = project.timeline.add_track('Main')
        broll_track = project.timeline.add_track('B-Roll')
        music_track = project.timeline.add_track('Music')

        # Title card at start
        title_callout = title_track.add_callout(
            'My Video Title', start_seconds=0.0, duration_seconds=3.0,
            font_size=128.0,
        )
        title_callout.add_behavior(BehaviorPreset.REVEAL)

        # End card
        end_callout = title_track.add_callout(
            'Thanks for watching!', start_seconds=57.0, duration_seconds=3.0,
        )
        end_callout.add_behavior(BehaviorPreset.FADE)

        # Main video clips (5 clips, 10s each)
        main_clips = []
        for i in range(5):
            clip = main_track.add_clip(
                'IMFile', image_media.id,
                seconds_to_ticks(i * 10), seconds_to_ticks(10),
            )
            main_clips.append(clip)

        # Transitions between main clips
        for i in range(4):
            main_track.add_transition(
                TransitionType.FADE_THROUGH_BLACK,
                main_clips[i], main_clips[i + 1],
                duration_seconds=0.5,
            )

        # B-roll clips (5 clips)
        broll_clips = []
        for i in range(5):
            clip = broll_track.add_clip(
                'IMFile', image_media.id,
                seconds_to_ticks(5 + i * 10), seconds_to_ticks(5),
            )
            broll_clips.append(clip)

        # Effects on main clips
        main_clips[0].add_color_adjustment(brightness=0.05, contrast=0.1)
        main_clips[1].add_drop_shadow()
        main_clips[2].add_border(width=3.0, color=(0.2, 0.4, 0.8, 1.0))
        main_clips[3].add_round_corners(radius=10.0)

        # Callouts (annotations) on B-roll track
        shapes = [
            CalloutShape.TEXT, CalloutShape.TEXT_RECTANGLE,
            CalloutShape.ARROW, CalloutShape.SHAPE_RECTANGLE,
            CalloutShape.SHAPE_ELLIPSE,
        ]
        for i, shape in enumerate(shapes):
            co = title_track.add_callout(
                f'Note {i}', start_seconds=10.0 + i * 8, duration_seconds=4.0,
            )
            if i < 3:
                co.add_behavior(BehaviorPreset.POP_UP)

        # Background music
        for i in range(6):
            music_track.add_audio(audio.id, start_seconds=i * 10, duration_seconds=10.0)

        # Timeline markers
        for i in range(6):
            project.timeline.add_marker(f'Chapter {i+1}', time_seconds=i * 10.0)

        open_in_camtasia(project, timeout=30)



class TestPodcastAudioHeavy:
    """Audio-focused project with many clips, effects, and captions."""

    def test_podcast_audio_heavy_opens(self, project, tmp_path):
        project.width = 1920
        project.height = 1080

        audio = project.import_media(EMPTY_WAV)

        # Two audio tracks with 12 clips each
        host_track = project.timeline.add_track('Host')
        guest_track = project.timeline.add_track('Guest')

        host_clips = []
        guest_clips = []
        for i in range(12):
            hc = host_track.add_audio(audio.id, start_seconds=i * 5, duration_seconds=5.0)
            hc.add_audio_fade_in(0.3)
            hc.add_audio_fade_out(0.3)
            hc.add_equalizer([(100.0, 2.0), (1000.0, -1.0), (8000.0, 1.5)])
            host_clips.append(hc)

            gc = guest_track.add_audio(audio.id, start_seconds=i * 5, duration_seconds=5.0)
            gc.add_audio_fade_in(0.2)
            gc.add_audio_fade_out(0.2)
            gc.add_equalizer([(200.0, 1.0), (3000.0, -0.5)])
            guest_clips.append(gc)

        # Noise removal on some clips
        for clip in host_clips[::3]:
            clip.add_noise_removal(amount=0.6)
        for clip in guest_clips[::4]:
            clip.add_noise_removal(amount=0.7)

        # Chapter markers
        for i in range(5):
            project.timeline.add_marker(f'Chapter {i+1}', time_seconds=i * 12.0)

        # Captions
        for i in range(8):
            project.timeline.add_caption(
                f'Caption line {i+1}', start_seconds=i * 7.0, duration_seconds=6.0,
            )

        # Export SRT
        srt_path = tmp_path / 'chapters.srt'
        export_markers_as_srt(project, srt_path)
        assert srt_path.exists()

        open_in_camtasia(project, timeout=30)



class TestRippleOperationsChaos:
    """Chained ripple/layout operations in sequence."""

    def test_ripple_operations_chaos_opens(self, project):
        audio = project.import_media(EMPTY_WAV)

        # Start with 10 clips on 3 tracks
        tracks = [project.timeline.add_track(f'Track-{i}') for i in range(3)]
        clips_by_track = {}
        for t_idx, track in enumerate(tracks):
            clips = []
            for i in range(4 if t_idx < 2 else 2):
                c = track.add_audio(audio.id, start_seconds=i * 3, duration_seconds=3.0)
                clips.append(c)
            clips_by_track[t_idx] = clips

        # ripple_insert on track 0
        ripple_insert(tracks[0], position_seconds=1.5, duration_seconds=2.0)

        # ripple_move on track 1
        ripple_move(tracks[1], clip_id=clips_by_track[1][0].id, delta_seconds=6.0)

        # split_clip on track 0 (after ripple_insert of 2.0s at 1.5s, clip[1]
        # now starts at 5.0s and ends at 8.0s. Split at midpoint 6.5s.)
        tracks[0].split_clip(clips_by_track[0][1].id, split_at_seconds=6.5)

        # ripple_delete on track 1
        ripple_delete(tracks[1], clip_id=clips_by_track[1][1].id)

        # merge_tracks
        merge_tracks(project, source_index=2, dest_index=0)

        # pack_track on track 0
        pack_track(tracks[0])

        # remove_empty_tracks
        remove_empty_tracks(project)

        # compact_project
        compact_project(project)

        open_in_camtasia(project, timeout=30)



class TestGroupTransitionBehaviorInteractions:
    """Known tricky combinations of groups, transitions, behaviors."""

    def test_group_transition_behavior_interactions_opens(self, project, tmp_path):
        track = project.timeline.add_track('Content')

        # Create 3 callouts (callouts support behaviors; image clips don't)
        c1 = track.add_callout('First', start_seconds=0.0, duration_seconds=5.0)
        c2 = track.add_callout('Second', start_seconds=5.0, duration_seconds=5.0)
        c3 = track.add_callout('Third', start_seconds=10.0, duration_seconds=5.0)

        # Add transition between clips 1 and 2
        track.add_transition(
            TransitionType.FADE_THROUGH_BLACK, c1, c2, duration_seconds=0.5,
        )

        # Add behavior to c1 BEFORE grouping (behaviors attach to clips, not groups)
        c1.add_behavior(BehaviorPreset.REVEAL)

        # Group clips 1 and 2
        group = track.group_clips([c1.id, c2.id])

        # Split clip 3 (NOT in the group)
        left, right = track.split_clip(c3.id, split_at_seconds=12.5)

        # Apply effects to the group and split clips
        group.add_drop_shadow()
        group.add_round_corners(radius=8.0)
        left.add_color_adjustment(brightness=0.1)
        right.add_border(width=2.0, color=(1.0, 0.0, 0.0, 1.0))

        # Add a callout on a separate track that overlaps the group
        callout_track = project.timeline.add_track('Annotations')
        co = callout_track.add_callout('Overlay', start_seconds=2.0, duration_seconds=6.0)
        co.add_behavior(BehaviorPreset.POP_UP)
        co.add_drop_shadow()

        open_in_camtasia(project, timeout=30)



class TestLargeProjectScale:
    """Scale stress: 100 clips, 8 tracks, many effects and transitions."""

    def test_large_project_scale_opens(self, project, tmp_path):
        project.width = 1920
        project.height = 1080

        audio = project.import_media(EMPTY_WAV)
        img = _create_test_image(tmp_path, 'tile.png')
        image_media = project.import_media(img)

        # 8 tracks
        tracks = [project.timeline.add_track(f'Track-{i}') for i in range(8)]

        # Distribute ~100 clips across tracks
        all_clips = []
        clip_idx = 0
        for t_idx, track in enumerate(tracks):
            n_clips = 13 if t_idx < 4 else 12
            for i in range(n_clips):
                if t_idx % 2 == 0:
                    c = track.add_clip(
                        'IMFile', image_media.id,
                        seconds_to_ticks(i * 3), seconds_to_ticks(3),
                    )
                else:
                    c = track.add_audio(
                        audio.id, start_seconds=i * 3, duration_seconds=3.0,
                    )
                all_clips.append((track, c))
                clip_idx += 1

        # 20 effects on various clips
        for i in range(20):
            _, clip = all_clips[i * 5 % len(all_clips)]
            if i % 4 == 0:
                clip.add_drop_shadow()
            elif i % 4 == 1:
                clip.add_round_corners(radius=6.0)
            elif i % 4 == 2:
                clip.add_color_adjustment(brightness=0.05)
            else:
                clip.add_glow(radius=20.0)

        # 10 transitions on even tracks (image tracks)
        for t_idx in (0, 2, 4, 6):
            track = tracks[t_idx]
            medias = track._data.get('medias', [])
            from camtasia.timeline import clip_from_dict
            for i in range(min(2, len(medias) - 1)):
                left = clip_from_dict(medias[i])
                right = clip_from_dict(medias[i + 1])
                track.add_transition(
                    TransitionType.FADE, left, right, duration_seconds=0.3,
                )

        # 15 callouts
        callout_track = project.timeline.add_track('Callouts')
        for i in range(15):
            callout_track.add_callout(
                f'Label {i}', start_seconds=i * 2.5, duration_seconds=2.0,
            )

        # Markers
        for i in range(10):
            project.timeline.add_marker(f'M{i}', time_seconds=i * 4.0)

        open_in_camtasia(project, timeout=30)



class TestExportRoundtrip:
    """Multi-export workflow: CSV, EDL, SRT all at once."""

    def test_export_roundtrip_opens(self, project, tmp_path):
        audio = project.import_media(EMPTY_WAV)
        img = _create_test_image(tmp_path, 'export_img.png')
        image_media = project.import_media(img)

        track = project.timeline.add_track('Content')
        for i in range(6):
            track.add_clip(
                'IMFile', image_media.id,
                seconds_to_ticks(i * 5), seconds_to_ticks(5),
            )

        audio_track = project.timeline.add_track('Audio')
        for i in range(6):
            audio_track.add_audio(audio.id, start_seconds=i * 5, duration_seconds=5.0)

        # Markers
        for i in range(5):
            project.timeline.add_marker(f'Section {i+1}', time_seconds=i * 6.0)

        # Captions
        for i in range(4):
            project.timeline.add_caption(
                f'Subtitle {i+1}', start_seconds=i * 7.0, duration_seconds=5.0,
            )

        # Export all formats
        csv_path = tmp_path / 'timeline.csv'
        edl_path = tmp_path / 'timeline.edl'
        srt_path = tmp_path / 'markers.srt'

        export_csv(project, csv_path)
        export_edl(project, edl_path)
        export_markers_as_srt(project, srt_path)

        assert csv_path.exists()
        assert edl_path.exists()
        assert srt_path.exists()

        # Project should still open after exports
        open_in_camtasia(project, timeout=30)



class TestHistoryStress:
    """Undo/redo chaos with many tracked changes."""

    def test_history_stress_opens(self, project, tmp_path):
        audio = project.import_media(EMPTY_WAV)
        img = _create_test_image(tmp_path, 'hist.png')
        image_media = project.import_media(img)

        track = project.timeline.add_track('Main')

        # Build complex project with 20 tracked operations
        for i in range(10):
            with project.track_changes(f'add audio clip {i}'):
                track.add_audio(audio.id, start_seconds=i * 2, duration_seconds=2.0)

        for i in range(5):
            with project.track_changes(f'add image clip {i}'):
                track.add_clip(
                    'IMFile', image_media.id,
                    seconds_to_ticks(20 + i * 3), seconds_to_ticks(3),
                )

        for i in range(3):
            with project.track_changes(f'add marker {i}'):
                project.timeline.add_marker(f'Mark {i}', time_seconds=i * 10.0)

        with project.track_changes('add callout'):
            callout_track = project.timeline.add_track('Notes')
            callout_track.add_callout('Note', start_seconds=5.0, duration_seconds=3.0)

        with project.track_changes('set dimensions'):
            project.width = 3840
            project.height = 2160

        # Undo 15 times
        for _ in range(15):
            project.undo()

        # Redo 10 times
        for _ in range(10):
            project.redo()

        # Undo 5 times
        for _ in range(5):
            project.undo()

        # Redo all remaining
        for _ in range(20):
            try:
                project.redo()
            except (IndexError, Exception):
                break

        open_in_camtasia(project, timeout=30)



class TestTemplateRoundtrip:
    """Template with lots of features: save, load, modify, open both."""

    def test_template_roundtrip_with_features_opens(self, project, tmp_path):
        audio = project.import_media(EMPTY_WAV)
        img = _create_test_image(tmp_path, 'tpl.png')
        image_media = project.import_media(img)

        project.width = 1920
        project.height = 1080

        # Build a feature-rich project
        track = project.timeline.add_track('Video')
        audio_track = project.timeline.add_track('Audio')
        callout_track = project.timeline.add_track('Callouts')

        for i in range(4):
            c = track.add_clip(
                'IMFile', image_media.id,
                seconds_to_ticks(i * 5), seconds_to_ticks(5),
            )
            c.add_drop_shadow()

        for i in range(4):
            audio_track.add_audio(audio.id, start_seconds=i * 5, duration_seconds=5.0)

        for i in range(3):
            co = callout_track.add_callout(
                f'Callout {i}', start_seconds=i * 6, duration_seconds=4.0,
            )
            co.add_behavior(BehaviorPreset.SLIDING)

        project.timeline.add_marker('Intro', time_seconds=0.0)
        project.timeline.add_marker('Main', time_seconds=5.0)
        project.timeline.add_marker('Outro', time_seconds=15.0)

        # Save as template
        template_path = tmp_path / 'feature_rich.camtemplate'
        save_as_template(project, 'Feature Rich', template_path)
        assert template_path.exists()

        # Create new project from template
        new_proj_path = tmp_path / 'from_template.cmproj'
        new_proj = new_from_template(template_path, new_proj_path)

        # Modify the new project further
        new_track = new_proj.timeline.add_track('Extra')
        new_audio = new_proj.import_media(EMPTY_WAV)
        new_track.add_audio(new_audio.id, start_seconds=0.0, duration_seconds=10.0)
        new_proj.timeline.add_marker('New marker', time_seconds=8.0)

        # Both should open
        open_in_camtasia(project, timeout=30)
        open_in_camtasia(new_proj, timeout=30)



class TestMultiFormatMedia:
    """Mixed media: audio, image, callouts, background music on separate tracks."""

    def test_multi_format_media_opens(self, project, tmp_path):
        project.width = 1920
        project.height = 1080

        audio = project.import_media(EMPTY_WAV)
        img = _create_test_image(tmp_path, 'mixed.png')
        image_media = project.import_media(img)

        # Separate tracks for each media type
        video_track = project.timeline.add_track('Video')
        image_track = project.timeline.add_track('Images')
        audio_track = project.timeline.add_track('Narration')
        music_track = project.timeline.add_track('Music')
        callout_track = project.timeline.add_track('Callouts')

        # Video-like clips (images used as video placeholders)
        video_clips = []
        for i in range(4):
            c = video_track.add_clip(
                'IMFile', image_media.id,
                seconds_to_ticks(i * 8), seconds_to_ticks(8),
            )
            video_clips.append(c)

        # Transitions between video clips
        for i in range(3):
            video_track.add_transition(
                TransitionType.SLIDE_LEFT, video_clips[i], video_clips[i + 1],
                duration_seconds=0.5,
            )

        # Image clips on separate track
        for i in range(6):
            c = image_track.add_clip(
                'IMFile', image_media.id,
                seconds_to_ticks(i * 5), seconds_to_ticks(5),
            )
            c.add_round_corners(radius=12.0)

        # Narration audio
        for i in range(8):
            c = audio_track.add_audio(audio.id, start_seconds=i * 4, duration_seconds=4.0)
            c.add_audio_fade_in(0.2)
            c.add_audio_fade_out(0.2)

        # Background music (continuous)
        for i in range(4):
            music_track.add_audio(audio.id, start_seconds=i * 8, duration_seconds=8.0)

        # Callouts overlapping everything
        for i in range(5):
            co = callout_track.add_callout(
                f'Point {i+1}', start_seconds=i * 6, duration_seconds=4.0,
            )
            co.add_behavior(BehaviorPreset.FLY_IN)
            co.add_drop_shadow()

        # Markers
        for i in range(4):
            project.timeline.add_marker(f'Segment {i+1}', time_seconds=i * 8.0)

        open_in_camtasia(project, timeout=30)



class TestExtremeKeyframes:
    """Keyframe stress: many effects with 20+ keyframes each."""

    def test_extreme_keyframes_opens(self, project, tmp_path):
        project.width = 1920
        project.height = 1080

        img = _create_test_image(tmp_path, 'kf.png')
        image_media = project.import_media(img)

        track = project.timeline.add_track('Animated')

        # Create 5 clips, each with many keyframes
        for clip_idx in range(5):
            clip = track.add_clip(
                'IMFile', image_media.id,
                seconds_to_ticks(clip_idx * 10), seconds_to_ticks(10),
            )

            # 25 keyframes on scale0 parameter
            for kf_idx in range(25):
                t = kf_idx * 0.4
                val = 1.0 + (kf_idx % 5) * 0.1
                clip.add_keyframe('scale0', t, val)

            # 20 keyframes on scale1 parameter
            for kf_idx in range(20):
                t = kf_idx * 0.5
                val = 1.0 + (kf_idx % 3) * 0.15
                clip.add_keyframe('scale1', t, val)

            # 20 keyframes on opacity
            for kf_idx in range(20):
                t = kf_idx * 0.5
                val = 0.5 + (kf_idx % 4) * 0.125
                clip.add_keyframe('opacity', t, val)

            # Add visual effects too
            clip.add_drop_shadow()
            clip.add_color_adjustment(brightness=0.05, saturation=0.1)

        # Add some callouts with behaviors (different animation type)
        callout_track = project.timeline.add_track('Labels')
        for i in range(4):
            co = callout_track.add_callout(
                f'KF Test {i}', start_seconds=i * 12, duration_seconds=8.0,
            )
            co.add_behavior(BehaviorPreset.PULSATING)

        # Markers
        for i in range(5):
            project.timeline.add_marker(f'Keyframe Set {i+1}', time_seconds=i * 10.0)

        open_in_camtasia(project, timeout=30)



class TestEffectsCaptionsMarkersCombined:
    """Every effect type + captions + markers on a single timeline."""

    def test_effects_captions_markers_combined_opens(self, project, tmp_path):
        project.width = 1920
        project.height = 1080

        audio = project.import_media(EMPTY_WAV)
        img = _create_test_image(tmp_path, 'combo.png')
        image_media = project.import_media(img)

        video_track = project.timeline.add_track('Video')
        audio_track = project.timeline.add_track('Audio')

        # 8 image clips with different effects on each
        clips = []
        for i in range(8):
            c = video_track.add_clip(
                'IMFile', image_media.id,
                seconds_to_ticks(i * 5), seconds_to_ticks(5),
            )
            clips.append(c)

        # Apply different effects to each clip
        clips[0].add_drop_shadow()
        clips[1].add_round_corners(radius=20.0)
        clips[2].add_glow(radius=30.0, intensity=0.5)
        clips[3].add_color_adjustment(brightness=0.1, contrast=0.2, saturation=-0.1)
        clips[4].add_border(width=5.0, color=(0.0, 1.0, 0.0, 1.0))
        clips[5].add_drop_shadow()
        clips[5].add_round_corners(radius=10.0)  # stacked effects
        clips[6].add_color_adjustment(brightness=-0.1)
        clips[6].add_glow(radius=15.0)  # stacked effects
        clips[7].add_border(width=2.0, color=(0.5, 0.5, 1.0, 1.0))
        clips[7].add_drop_shadow()

        # Audio with effects
        for i in range(8):
            ac = audio_track.add_audio(audio.id, start_seconds=i * 5, duration_seconds=5.0)
            ac.add_audio_fade_in(0.5)
            ac.add_audio_fade_out(0.5)
            if i % 2 == 0:
                ac.add_equalizer([(500.0, 1.5), (4000.0, -1.0)])

        # Transitions
        for i in range(0, 6, 2):
            video_track.add_transition(
                TransitionType.FADE, clips[i], clips[i + 1], duration_seconds=0.4,
            )

        # Captions
        for i in range(6):
            project.timeline.add_caption(
                f'Scene {i+1} description', start_seconds=i * 6, duration_seconds=5.0,
            )

        # Markers
        for i in range(8):
            project.timeline.add_marker(f'Scene {i+1}', time_seconds=i * 5.0)

        # Callouts with behaviors
        co_track = project.timeline.add_track('Annotations')
        presets = [BehaviorPreset.REVEAL, BehaviorPreset.SLIDING,
                   BehaviorPreset.FLY_IN, BehaviorPreset.JIGGLE]
        for i, preset in enumerate(presets):
            co = co_track.add_callout(
                f'Annotation {i}', start_seconds=i * 10, duration_seconds=5.0,
            )
            co.add_behavior(preset)

        open_in_camtasia(project, timeout=30)



class TestMultiGroupNestedOperations:
    """Multiple groups with effects, splits, and cross-track interactions."""

    def test_multi_group_nested_operations_opens(self, project, tmp_path):
        project.width = 1920
        project.height = 1080

        audio = project.import_media(EMPTY_WAV)
        img = _create_test_image(tmp_path, 'grp.png')
        image_media = project.import_media(img)

        track_a = project.timeline.add_track('Track A')
        track_b = project.timeline.add_track('Track B')
        track_c = project.timeline.add_track('Track C')

        # Create callouts on track A and group them (callouts support behaviors)
        a_clips = []
        for i in range(4):
            c = track_a.add_callout(
                f'Slide {i}', start_seconds=i * 4.0, duration_seconds=4.0,
            )
            a_clips.append(c)

        # Apply behavior to a clip BEFORE grouping (behaviors attach to clips, not groups)
        a_clips[0].add_behavior(BehaviorPreset.FADE)

        group_a = track_a.group_clips([a_clips[0].id, a_clips[1].id])
        group_a.add_drop_shadow()

        # Create clips on track B and group them
        b_clips = []
        for i in range(4):
            c = track_b.add_audio(audio.id, start_seconds=i * 4, duration_seconds=4.0)
            b_clips.append(c)

        # Add effects to individual audio clips before grouping
        b_clips[0].add_audio_fade_in(0.5)
        b_clips[1].add_equalizer([(1000.0, 2.0)])
        b_clips[2].add_noise_removal(amount=0.5)
        b_clips[3].add_audio_fade_out(0.5)

        group_b = track_b.group_clips([b_clips[0].id, b_clips[1].id])

        # Track C: callouts with transitions and splits
        c_clips = []
        for i in range(3):
            co = track_c.add_callout(
                f'Group Test {i}', start_seconds=i * 6, duration_seconds=6.0,
            )
            co.add_behavior(BehaviorPreset.EMPHASIZE)
            c_clips.append(co)

        # Split one of the ungrouped clips on track A
        track_a.split_clip(a_clips[2].id, split_at_seconds=10.0)

        # Add transitions on track A between remaining clips
        medias = track_a._data.get('medias', [])
        from camtasia.timeline import clip_from_dict
        if len(medias) >= 2:
            left = clip_from_dict(medias[-2])
            right = clip_from_dict(medias[-1])
            track_a.add_transition(
                TransitionType.FADE_THROUGH_BLACK, left, right, duration_seconds=0.3,
            )

        # Markers and captions
        for i in range(4):
            project.timeline.add_marker(f'Group {i+1}', time_seconds=i * 4.0)
        project.timeline.add_caption('Group test caption', start_seconds=2.0, duration_seconds=4.0)

        open_in_camtasia(project, timeout=30)
