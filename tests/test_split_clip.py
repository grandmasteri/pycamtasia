"""Tests for Track.split_clip()."""
from __future__ import annotations

from camtasia.timeline.track import Track
from camtasia.timing import seconds_to_ticks


def _make_track(*medias):
    """Build a Track with the given media dicts."""
    attrs = {'ident': 'test', 'audioMuted': False, 'videoHidden': False}
    data = {'trackIndex': 0, 'medias': list(medias)}
    return Track(attrs, data), data


def _simple_clip(clip_id=1, start_s=10.0, dur_s=10.0):
    """Return a simple VMFile clip dict."""
    return {
        'id': clip_id,
        '_type': 'VMFile',
        'src': 1,
        'trackNumber': 0,
        'start': seconds_to_ticks(start_s),
        'duration': seconds_to_ticks(dur_s),
        'mediaStart': 0,
        'mediaDuration': seconds_to_ticks(dur_s),
        'scalar': 1,
        'metadata': {},
        'parameters': {},
        'effects': [],
        'animationTracks': {},
    }


def _group_clip(clip_id=1, start_s=10.0, dur_s=10.0):
    """Return a Group clip dict with internal tracks."""
    return {
        'id': clip_id,
        '_type': 'Group',
        'trackNumber': 0,
        'start': seconds_to_ticks(start_s),
        'duration': seconds_to_ticks(dur_s),
        'mediaStart': 0,
        'mediaDuration': seconds_to_ticks(dur_s),
        'scalar': '6723/5755',
        'metadata': {},
        'parameters': {},
        'effects': [],
        'animationTracks': {},
        'attributes': {'ident': 'Rev Media'},
        'tracks': [
            {
                'trackIndex': 0,
                'medias': [{
                    'id': 2,
                    '_type': 'VMFile',
                    'src': 1,
                    'trackNumber': 0,
                    'start': 0,
                    'duration': seconds_to_ticks(dur_s),
                    'mediaStart': 0,
                    'mediaDuration': seconds_to_ticks(dur_s),
                    'scalar': 1,
                    'metadata': {},
                    'parameters': {},
                    'effects': [],
                    'animationTracks': {},
                }],
            },
            {
                'trackIndex': 1,
                'medias': [{
                    'id': 3,
                    '_type': 'UnifiedMedia',
                    'video': {
                        'id': 4,
                        '_type': 'ScreenVMFile',
                        'src': 2,
                        'trackNumber': 0,
                        'start': 0,
                        'duration': seconds_to_ticks(dur_s),
                        'mediaStart': 0,
                        'mediaDuration': seconds_to_ticks(dur_s),
                        'scalar': 1,
                    },
                    'audio': {
                        'id': 5,
                        '_type': 'AMFile',
                        'src': 2,
                        'trackNumber': 1,
                    },
                    'effects': [],
                    'start': 0,
                    'duration': seconds_to_ticks(dur_s),
                    'mediaStart': 0,
                    'mediaDuration': seconds_to_ticks(dur_s),
                    'scalar': 1,
                }],
            },
        ],
    }


class TestSplitClip:
    def test_split_creates_two_clips(self):
        track, data = _make_track(_simple_clip())
        track.split_clip(1, 15.0)
        assert [m['_type'] for m in data['medias']] == ['VMFile', 'VMFile']

    def test_split_clip_removes_transitions(self):
        track, data = _make_track(_simple_clip(1, 0.0, 10.0), _simple_clip(2, 10.0, 10.0))
        data['transitions'] = [
            {'leftMedia': 1, 'rightMedia': 2, 'duration': 100},
        ]
        track.split_clip(1, 5.0)
        assert data['transitions'] == []

    def test_split_durations_add_up(self):
        orig_dur = seconds_to_ticks(10.0)
        track, _data = _make_track(_simple_clip())
        left, right = track.split_clip(1, 15.0)
        assert left.duration + right.duration == orig_dur

    def test_split_right_media_start(self):
        track, _ = _make_track(_simple_clip())
        _left, right = track.split_clip(1, 15.0)
        expected_offset = seconds_to_ticks(15.0) - seconds_to_ticks(10.0)
        assert right.media_start == expected_offset

    def test_split_right_media_start_preserves_original_offset(self):
        """When a clip has a non-zero mediaStart, the right half must add it."""
        clip = _simple_clip(clip_id=1, start_s=10.0, dur_s=10.0)
        clip['mediaStart'] = seconds_to_ticks(5.0)  # non-zero original offset
        track, _ = _make_track(clip)
        _left, right = track.split_clip(1, 15.0)
        split_offset = seconds_to_ticks(15.0) - seconds_to_ticks(10.0)
        assert right.media_start == seconds_to_ticks(5.0) + split_offset

    def test_split_preserves_scalar(self):
        track, _ = _make_track(_group_clip())
        left, right = track.split_clip(1, 15.0)
        assert left.scalar == right.scalar

    def test_split_assigns_new_ids(self):
        track, data = _make_track(_group_clip())
        left, right = track.split_clip(1, 15.0)
        # Right half gets a new group ID different from left
        assert right.id != left.id
        # All IDs in right half's internal tracks should be new
        left_ids = _collect_ids(data['medias'][0])
        right_ids = _collect_ids(data['medias'][1])
        assert left_ids.isdisjoint(right_ids)


def _collect_ids(media_dict):
    """Collect all IDs from a media dict including internal tracks."""
    ids = {media_dict['id']}
    for t in media_dict.get('tracks', []):
        for m in t.get('medias', []):
            ids.add(m['id'])
            if 'video' in m:
                ids.add(m['video']['id'])
            if 'audio' in m:
                ids.add(m['audio']['id'])
    return ids


class TestSplitClipRemapsAssetProperties:
    """Cover split_clip: _remap_clip_ids_with_map handles attributes.assetProperties."""

    def test_split_remaps_asset_property_ids(self):
        clip = _simple_clip(clip_id=1, start_s=10.0, dur_s=10.0)
        clip['attributes'] = {
            'assetProperties': [{'objects': [1]}],
        }
        track, _data = _make_track(clip)
        _left, right = track.split_clip(1, 15.0)
        # The right half's attributes.assetProperties should have remapped IDs
        right_asset_ids = [
            oid
            for ap in right._data.get('attributes', {}).get('assetProperties', [])
            for oid in ap.get('objects', [])
        ]
        assert all(rid != 1 for rid in right_asset_ids)


# ── Bug fix: split_clip effect timing ────────────────────────────────


def _effect_clip(clip_id=1, start_s=0.0, dur_s=10.0, effects=None):
    return {
        'id': clip_id,
        '_type': 'VMFile',
        'src': 1,
        'trackNumber': 0,
        'start': seconds_to_ticks(start_s),
        'duration': seconds_to_ticks(dur_s),
        'mediaStart': 0,
        'mediaDuration': seconds_to_ticks(dur_s),
        'scalar': 1,
        'metadata': {},
        'parameters': {},
        'effects': effects or [],
        'animationTracks': {},
    }


def _make_effect_track(*medias):
    attrs = {'ident': 'test', 'audioMuted': False, 'videoHidden': False}
    data = {'trackIndex': 0, 'medias': list(medias)}
    return Track(attrs, data)


class TestSplitClipEffectTiming:
    def test_left_half_removes_effect_past_new_end(self):
        """Effect starting past the split point should be removed from left half."""
        eff = {'effectName': 'Glow', 'start': seconds_to_ticks(7.0), 'duration': seconds_to_ticks(2.0), 'parameters': {}}
        track = _make_effect_track(_effect_clip(clip_id=1, start_s=0.0, dur_s=10.0, effects=[eff]))
        left, _right = track.split_clip(1, 5.0)
        assert len(left._data['effects']) == 0

    def test_left_half_trims_effect_spanning_split(self):
        """Effect spanning the split point should be trimmed on the left half."""
        eff = {'effectName': 'Glow', 'start': seconds_to_ticks(3.0), 'duration': seconds_to_ticks(5.0), 'parameters': {}}
        track = _make_effect_track(_effect_clip(clip_id=1, start_s=0.0, dur_s=10.0, effects=[eff]))
        left, _right = track.split_clip(1, 5.0)
        left_eff = left._data['effects'][0]
        assert left_eff['start'] == seconds_to_ticks(3.0)
        assert left_eff['duration'] == seconds_to_ticks(2.0)

    def test_right_half_shifts_effect_start(self):
        """Effect in the right portion should have start shifted by split offset."""
        eff = {'effectName': 'Glow', 'start': seconds_to_ticks(7.0), 'duration': seconds_to_ticks(2.0), 'parameters': {}}
        track = _make_effect_track(_effect_clip(clip_id=1, start_s=0.0, dur_s=10.0, effects=[eff]))
        _left, right = track.split_clip(1, 5.0)
        right_eff = right._data['effects'][0]
        assert right_eff['start'] == seconds_to_ticks(2.0)
        assert right_eff['duration'] == seconds_to_ticks(2.0)

    def test_right_half_removes_effect_entirely_in_left(self):
        """Effect entirely before the split point should be removed from right half."""
        eff = {'effectName': 'Glow', 'start': seconds_to_ticks(1.0), 'duration': seconds_to_ticks(2.0), 'parameters': {}}
        track = _make_effect_track(_effect_clip(clip_id=1, start_s=0.0, dur_s=10.0, effects=[eff]))
        _left, right = track.split_clip(1, 5.0)
        assert len(right._data['effects']) == 0

    def test_right_half_trims_effect_spanning_split(self):
        """Effect spanning the split boundary should be trimmed on the right half."""
        eff = {'effectName': 'Glow', 'start': seconds_to_ticks(3.0), 'duration': seconds_to_ticks(5.0), 'parameters': {}}
        track = _make_effect_track(_effect_clip(clip_id=1, start_s=0.0, dur_s=10.0, effects=[eff]))
        _left, right = track.split_clip(1, 5.0)
        right_eff = right._data['effects'][0]
        assert right_eff['start'] == 0
        assert right_eff['duration'] == seconds_to_ticks(3.0)

    def test_effect_without_start_duration_preserved_on_both(self):
        """Effects without start/duration fields should be kept on both halves."""
        eff = {'effectName': 'ColorAdjust', 'parameters': {'brightness': 0.5}}
        track = _make_effect_track(_effect_clip(clip_id=1, start_s=0.0, dur_s=10.0, effects=[eff]))
        left, right = track.split_clip(1, 5.0)
        assert len(left._data['effects']) == 1
        assert len(right._data['effects']) == 1

    def test_left_half_keeps_effect_fully_within(self):
        """Effect fully within the left half should be kept unchanged."""
        eff = {'effectName': 'Glow', 'start': seconds_to_ticks(1.0), 'duration': seconds_to_ticks(2.0), 'parameters': {}}
        track = _make_effect_track(_effect_clip(clip_id=1, start_s=0.0, dur_s=10.0, effects=[eff]))
        left, _right = track.split_clip(1, 5.0)
        left_eff = left._data['effects'][0]
        assert left_eff['start'] == seconds_to_ticks(1.0)
        assert left_eff['duration'] == seconds_to_ticks(2.0)


    # -- Bug: effects with only 'start' or only 'duration' must be handled --

    def test_effect_with_only_start_kept_on_left(self):
        """Effect with start but no duration (instantaneous) should be kept on left if before split."""
        eff = {'effectName': 'Flash', 'start': seconds_to_ticks(2.0)}
        track = _make_effect_track(_effect_clip(clip_id=1, start_s=0.0, dur_s=10.0, effects=[eff]))
        left, _right = track.split_clip(1, 5.0)
        assert len(left._data['effects']) == 1
        assert left._data['effects'][0]['start'] == seconds_to_ticks(2.0)

    def test_effect_with_only_start_shifted_on_right(self):
        """Effect with start but no duration past split should appear on right, shifted."""
        eff = {'effectName': 'Flash', 'start': seconds_to_ticks(7.0)}
        track = _make_effect_track(_effect_clip(clip_id=1, start_s=0.0, dur_s=10.0, effects=[eff]))
        _left, right = track.split_clip(1, 5.0)
        assert len(right._data['effects']) == 1
        assert right._data['effects'][0]['start'] == seconds_to_ticks(2.0)

    def test_effect_with_only_duration_kept_on_both(self):
        """Effect with duration but no start (starts at 0) should be trimmed on left, shifted on right."""
        eff = {'effectName': 'Glow', 'duration': seconds_to_ticks(8.0)}
        track = _make_effect_track(_effect_clip(clip_id=1, start_s=0.0, dur_s=10.0, effects=[eff]))
        left, right = track.split_clip(1, 5.0)
        # Left: start=0, dur=8 -> trimmed to dur=5 (split point)
        assert len(left._data['effects']) == 1
        assert left._data['effects'][0]['duration'] == seconds_to_ticks(5.0)
        # Right: start=0, dur=8, split at 5 -> new_dur = 8-5 = 3
        assert len(right._data['effects']) == 1
        assert right._data['effects'][0]['duration'] == seconds_to_ticks(3.0)
