from __future__ import annotations

import pytest

from camtasia.timeline.track import Track, _VALID_CLIP_TYPES


def _make_track(medias=None, index=0):
    data = {"trackIndex": index, "medias": medias or []}
    attrs = {"ident": f"Track-{index}"}
    return Track(attrs, data)


def _make_track_with_clips(n=2, index=0):
    medias = [
        {"id": i + 1, "_type": "IMFile", "src": 10 + i, "trackNumber": 0,
         "start": i * 1000, "duration": 1000, "mediaStart": 0,
         "mediaDuration": 1, "scalar": 1, "metadata": {},
         "animationTracks": {}, "parameters": {}, "effects": []}
        for i in range(n)
    ]
    return _make_track(medias=medias, index=index)


class TestTrackEqHash:
    def test_same_data_object_is_equal(self):
        data = {"trackIndex": 0, "medias": []}
        t1 = Track({"ident": "A"}, data)
        t2 = Track({"ident": "B"}, data)
        assert t1 == t2

    def test_same_index_different_data_is_equal(self):
        t1 = _make_track(index=3)
        t2 = _make_track(index=3)
        assert t1 == t2

    def test_different_index_not_equal(self):
        t1 = _make_track(index=0)
        t2 = _make_track(index=1)
        assert t1 != t2

    def test_not_equal_to_non_track(self):
        t = _make_track()
        assert t != "not a track"

    def test_hash_same_index(self):
        t1 = _make_track(index=5)
        t2 = _make_track(index=5)
        assert hash(t1) == hash(t2)

    def test_usable_in_set(self):
        t1 = _make_track(index=0)
        t2 = _make_track(index=0)
        assert {t1, t2} == {t1}


class TestTrackLen:
    def test_empty_track(self):
        t = _make_track()
        assert len(t) == 0

    def test_track_with_clips(self):
        t = _make_track_with_clips(3)
        assert len(t) == 3
        assert [c.id for c in t.clips] == [1, 2, 3]

    def test_no_medias_key(self):
        data = {"trackIndex": 0}
        t = Track({"ident": "X"}, data)
        assert len(t) == 0


class TestClipCount:
    def test_matches_len(self):
        t = _make_track_with_clips(4)
        assert t.clip_count == len(t) == 4

    def test_empty(self):
        t = _make_track()
        assert t.clip_count == 0


class TestFindClip:
    def test_found(self):
        t = _make_track_with_clips(3)
        clip = t.find_clip(2)
        assert clip is not None
        assert clip.id == 2

    def test_not_found(self):
        t = _make_track_with_clips(3)
        assert t.find_clip(999) is None


class TestAddClipValidation:
    def test_invalid_type_raises(self):
        t = _make_track()
        with pytest.raises(ValueError, match="Unknown clip type 'Bogus'"):
            t.add_clip("Bogus", 1, 0, 1000)

    @pytest.mark.parametrize("clip_type", sorted(_VALID_CLIP_TYPES))
    def test_valid_types_accepted(self, clip_type):
        t = _make_track()
        source_id = None if clip_type in ("Callout", "Group") else 1
        clip = t.add_clip(clip_type, source_id, 0, 1000)
        assert clip is not None
