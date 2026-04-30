"""Tests for Group quick_properties editor methods."""
from __future__ import annotations

import pytest

from camtasia.timeline.clips import Group
from camtasia.timing import seconds_to_ticks


def _make_group(**overrides) -> Group:
    """Build a minimal Group for quick_properties testing."""
    data = {
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
        'attributes': {'ident': 'TestGroup'},
        'tracks': [],
        **overrides,
    }
    return Group(data)


class TestQuickPropertiesDefault:
    def test_returns_dict_with_all_keys(self) -> None:
        group = _make_group()
        qp = group.quick_properties
        assert set(qp.keys()) == {'linked', 'labels', 'theme_slots', 'visible'}

    def test_all_sub_dicts_start_empty(self) -> None:
        group = _make_group()
        qp = group.quick_properties
        assert qp == {'linked': {}, 'labels': {}, 'theme_slots': {}, 'visible': {}}

    def test_repeated_access_returns_same_object(self) -> None:
        group = _make_group()
        qp1 = group.quick_properties
        qp2 = group.quick_properties
        assert qp1 is qp2


class TestQuickPropertiesSetter:
    def test_replaces_entire_dict(self) -> None:
        group = _make_group()
        replacement = {
            'linked': {'x': '/a/b'},
            'labels': {'x': 'X Label'},
            'theme_slots': {},
            'visible': {'x': True},
        }
        group.quick_properties = replacement
        assert group.quick_properties is replacement

    def test_setter_persists_in_metadata(self) -> None:
        group = _make_group()
        group.quick_properties = {'linked': {}, 'labels': {}, 'theme_slots': {}, 'visible': {}}
        assert 'quickProperties' in group._data['metadata']


class TestLinkProperty:
    def test_adds_linked_entry(self) -> None:
        group = _make_group()
        group.link_property('opacity', '/effects/opacity')
        assert group.quick_properties['linked'] == {'opacity': '/effects/opacity'}

    def test_returns_self_for_chaining(self) -> None:
        group = _make_group()
        result = group.link_property('x', '/path')
        assert result is group

    def test_multiple_links(self) -> None:
        group = _make_group()
        group.link_property('a', '/path/a').link_property('b', '/path/b')
        assert group.quick_properties['linked'] == {'a': '/path/a', 'b': '/path/b'}


class TestUnlinkProperty:
    def test_removes_linked_entry(self) -> None:
        group = _make_group()
        group.link_property('opacity', '/effects/opacity')
        group.unlink_property('opacity')
        assert group.quick_properties['linked'] == {}

    def test_raises_key_error_for_missing(self) -> None:
        group = _make_group()
        with pytest.raises(KeyError):
            group.unlink_property('nonexistent')

    def test_returns_self_for_chaining(self) -> None:
        group = _make_group()
        group.link_property('x', '/path')
        result = group.unlink_property('x')
        assert result is group


class TestSetLabel:
    def test_sets_label(self) -> None:
        group = _make_group()
        group.set_label('opacity', 'Opacity Level')
        assert group.quick_properties['labels'] == {'opacity': 'Opacity Level'}

    def test_returns_self(self) -> None:
        group = _make_group()
        assert group.set_label('x', 'X') is group


class TestAssignThemeSlot:
    def test_assigns_slot(self) -> None:
        group = _make_group()
        group.assign_theme_slot('fill', 'accent-1')
        assert group.quick_properties['theme_slots'] == {'fill': 'accent-1'}

    def test_returns_self(self) -> None:
        group = _make_group()
        assert group.assign_theme_slot('fill', 'accent-1') is group


class TestSetPropertyVisible:
    def test_sets_visible_true(self) -> None:
        group = _make_group()
        group.set_property_visible('opacity', True)
        assert group.quick_properties['visible'] == {'opacity': True}

    def test_sets_visible_false(self) -> None:
        group = _make_group()
        group.set_property_visible('opacity', False)
        assert group.quick_properties['visible'] == {'opacity': False}

    def test_returns_self(self) -> None:
        group = _make_group()
        assert group.set_property_visible('x', True) is group


class TestQuickPropertiesIntegration:
    def test_full_workflow(self) -> None:
        group = _make_group()
        group.link_property('fill', '/effects/fill')
        group.set_label('fill', 'Fill Color')
        group.assign_theme_slot('fill', 'accent-1')
        group.set_property_visible('fill', True)

        qp = group.quick_properties
        assert qp['linked']['fill'] == '/effects/fill'
        assert qp['labels']['fill'] == 'Fill Color'
        assert qp['theme_slots']['fill'] == 'accent-1'
        assert qp['visible']['fill'] is True

    def test_preserves_existing_metadata(self) -> None:
        group = _make_group(metadata={'existingKey': 42})
        group.link_property('x', '/path')
        assert group._data['metadata']['existingKey'] == 42
        assert group.quick_properties['linked'] == {'x': '/path'}

    def test_initializes_missing_sub_keys(self) -> None:
        """If metadata has partial quickProperties, missing sub-keys are filled."""
        group = _make_group(metadata={'quickProperties': {'linked': {'a': '/b'}}})
        qp = group.quick_properties
        assert qp['linked'] == {'a': '/b'}
        assert qp['labels'] == {}
        assert qp['theme_slots'] == {}
        assert qp['visible'] == {}
