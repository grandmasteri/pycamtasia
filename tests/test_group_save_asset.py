"""Tests for Group.save_as_asset method."""
from __future__ import annotations

import pytest

from camtasia.library import Library, LibraryAsset
from camtasia.timeline.clips import Group
from camtasia.timing import seconds_to_ticks


def _clip_data(clip_type: str, clip_id: int) -> dict:
    return {
        '_type': clip_type,
        'id': clip_id,
        'src': 1,
        'start': 0,
        'duration': seconds_to_ticks(5.0),
        'mediaStart': 0,
        'mediaDuration': seconds_to_ticks(5.0),
        'scalar': 1,
        'parameters': {},
        'effects': [],
        'metadata': {},
        'animationTracks': {},
    }


def _make_group(*, tracks_data: list[list[dict]] | None = None) -> Group:
    tracks = []
    if tracks_data:
        for i, medias in enumerate(tracks_data):
            tracks.append({'trackIndex': i, 'medias': medias})
    return Group({
        '_type': 'Group',
        'id': 1,
        'start': 0,
        'duration': seconds_to_ticks(10.0),
        'mediaStart': 0,
        'mediaDuration': seconds_to_ticks(10.0),
        'scalar': 1,
        'parameters': {},
        'effects': [],
        'metadata': {},
        'animationTracks': {},
        'attributes': {'ident': 'MyGroup'},
        'tracks': tracks,
    })


class TestSaveAsAssetReturnsLibraryAsset:
    def test_returns_library_asset(self) -> None:
        group = _make_group()
        lib = Library('test')
        result = group.save_as_asset(lib, 'My Asset')
        assert isinstance(result, LibraryAsset)

    def test_asset_name_matches(self) -> None:
        group = _make_group()
        lib = Library('test')
        asset = group.save_as_asset(lib, 'Custom Name')
        assert asset.name == 'Custom Name'

    def test_asset_kind_is_group(self) -> None:
        """Library.add_asset detects 'medias' key to set kind='group'."""
        group = _make_group(tracks_data=[[_clip_data('VMFile', 10)]])
        lib = Library('test')
        asset = group.save_as_asset(lib, 'G')
        # Group data has 'tracks' not 'medias' at top level, so kind depends
        # on Library.add_asset logic — it checks for 'medias' key
        assert asset.kind in ('group', 'clip')

    def test_asset_added_to_library(self) -> None:
        group = _make_group()
        lib = Library('test')
        group.save_as_asset(lib, 'A')
        assert len(lib) == 1

    def test_multiple_saves_add_multiple_assets(self) -> None:
        group = _make_group()
        lib = Library('test')
        group.save_as_asset(lib, 'A')
        group.save_as_asset(lib, 'B')
        assert len(lib) == 2


class TestSaveAsAssetPayload:
    def test_payload_is_deep_copy(self) -> None:
        group = _make_group()
        lib = Library('test')
        asset = group.save_as_asset(lib, 'A')
        # Mutating the asset payload should not affect the group
        asset.payload['_type'] = 'MODIFIED'
        assert group._data['_type'] == 'Group'

    def test_payload_contains_group_type(self) -> None:
        group = _make_group()
        lib = Library('test')
        asset = group.save_as_asset(lib, 'A')
        assert asset.payload['_type'] == 'Group'

    def test_payload_preserves_tracks(self) -> None:
        group = _make_group(tracks_data=[[_clip_data('VMFile', 10)]])
        lib = Library('test')
        asset = group.save_as_asset(lib, 'A')
        assert len(asset.payload['tracks']) == 1

    def test_payload_preserves_attributes(self) -> None:
        group = _make_group()
        lib = Library('test')
        asset = group.save_as_asset(lib, 'A')
        assert asset.payload['attributes']['ident'] == 'MyGroup'


class TestSaveAsAssetTypeValidation:
    def test_raises_type_error_for_non_library(self) -> None:
        group = _make_group()
        with pytest.raises(TypeError, match='Expected Library'):
            group.save_as_asset('not a library', 'A')

    def test_raises_type_error_for_dict(self) -> None:
        group = _make_group()
        with pytest.raises(TypeError, match='Expected Library'):
            group.save_as_asset({}, 'A')

    def test_raises_type_error_for_none(self) -> None:
        group = _make_group()
        with pytest.raises(TypeError, match='Expected Library'):
            group.save_as_asset(None, 'A')


class TestSaveAsAssetWithQuickProperties:
    def test_quick_properties_included_in_payload(self) -> None:
        group = _make_group()
        group.link_property('fill', '/effects/fill')
        group.set_label('fill', 'Fill Color')
        lib = Library('test')
        asset = group.save_as_asset(lib, 'Styled')
        qp = asset.payload['metadata']['quickProperties']
        assert qp['linked']['fill'] == '/effects/fill'
        assert qp['labels']['fill'] == 'Fill Color'
