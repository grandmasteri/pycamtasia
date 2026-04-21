"""Tests for the Theme / apply_theme API."""
from __future__ import annotations

from pathlib import Path
import tempfile

import pytest

from camtasia import Project, Theme, apply_theme


@pytest.fixture
def project_with_themed_callout():
    tmp = Path(tempfile.mkdtemp()) / 'test.cmproj'
    proj = Project.new(str(tmp))
    track = proj.timeline.get_or_create_track('Captions')
    callout = track.add_callout('Hello', 0.0, 2.0, font_size=32.0)
    # Inject themeMappings referencing this callout
    callout._data.setdefault('attributes', {})['assetProperties'] = [
        {
            'type': 1,
            'name': 'Callout',
            'objects': [callout.id],
            'themeMappings': {
                'outline': 'accent-1',
                'fill': 'accent-2',
                'font-color': 'foreground-1',
                'font-family': 'font-1',
            },
        },
    ]
    return proj, callout


def test_theme_resolve_known_slots():
    t = Theme()
    assert t.resolve('accent-1') == (0.18, 0.47, 0.78, 1.0)
    assert t.resolve('font-1') == 'Helvetica'


def test_theme_resolve_unknown_raises():
    t = Theme()
    with pytest.raises(KeyError, match='Unknown theme slot'):
        t.resolve('not-a-slot')


def test_theme_resolve_custom_slot():
    t = Theme(custom={'logo-1': '/path/to/logo.png'})
    assert t.resolve('logo-1') == '/path/to/logo.png'


def test_apply_theme_writes_colors(project_with_themed_callout):
    proj, callout = project_with_themed_callout
    theme = Theme(
        accent_1=(1.0, 0.0, 0.0, 1.0),       # red outline
        accent_2=(0.0, 1.0, 0.0, 1.0),       # green fill
        foreground_1=(0.0, 0.0, 1.0, 1.0),   # blue font
        font_1='Georgia',
    )
    count = apply_theme(proj, theme)
    assert count == 4
    cdef = callout._data['def']
    assert cdef['stroke-color-red'] == 1.0
    assert cdef['fill-color-green'] == 1.0
    assert cdef['font']['color-blue'] == 1.0
    assert cdef['font']['name'] == 'Georgia'


def test_apply_theme_skips_empty_slots():
    """A mapping value of '' should be skipped."""
    tmp = Path(tempfile.mkdtemp()) / 'test.cmproj'
    proj = Project.new(str(tmp))
    track = proj.timeline.get_or_create_track('T')
    callout = track.add_callout('X', 0.0, 1.0)
    callout._data.setdefault('attributes', {})['assetProperties'] = [
        {
            'type': 1, 'name': 'C', 'objects': [callout.id],
            'themeMappings': {'outline': ''},   # empty mapping
        },
    ]
    count = apply_theme(proj, Theme())
    assert count == 0


def test_apply_theme_handles_missing_clip():
    """themeMappings referencing non-existent clip IDs are ignored."""
    tmp = Path(tempfile.mkdtemp()) / 'test.cmproj'
    proj = Project.new(str(tmp))
    track = proj.timeline.get_or_create_track('T')
    callout = track.add_callout('X', 0.0, 1.0)
    callout._data.setdefault('attributes', {})['assetProperties'] = [
        {
            'type': 1, 'name': 'C', 'objects': [99999],
            'themeMappings': {'outline': 'accent-1'},
        },
    ]
    count = apply_theme(proj, Theme())
    assert count == 0


def test_apply_theme_skips_unknown_slots_silently():
    """An unknown slot value is skipped (no exception)."""
    tmp = Path(tempfile.mkdtemp()) / 'test.cmproj'
    proj = Project.new(str(tmp))
    track = proj.timeline.get_or_create_track('T')
    callout = track.add_callout('X', 0.0, 1.0)
    callout._data.setdefault('attributes', {})['assetProperties'] = [
        {
            'type': 1, 'name': 'C', 'objects': [callout.id],
            'themeMappings': {'outline': 'totally-made-up-slot'},
        },
    ]
    count = apply_theme(proj, Theme())
    assert count == 0


def test_apply_theme_recurses_into_group():
    """apply_theme walks nested clips inside Groups to find themed callouts."""
    tmp = Path(tempfile.mkdtemp()) / 'test.cmproj'
    proj = Project.new(str(tmp))
    track = proj.timeline.get_or_create_track('T')
    c1 = track.add_callout('A', 0.0, 1.0)
    c2 = track.add_callout('B', 1.0, 1.0)
    group = track.group_clips([c1.id, c2.id])
    # Fetch the actual post-grouping inner clip dict (IDs get reassigned)
    inner_dict = group._data['tracks'][0]['medias'][0]
    inner_id = inner_dict['id']
    # Attach themeMappings to the inner clip (found via recursion into Group)
    inner_dict.setdefault('attributes', {})['assetProperties'] = [
        {'type': 1, 'name': 'C', 'objects': [inner_id],
         'themeMappings': {'outline': 'accent-1'}},
    ]
    count = apply_theme(proj, Theme(accent_1=(0.5, 0.0, 0.0, 1.0)))
    assert count == 1
    assert inner_dict['def']['stroke-color-red'] == 0.5
    # Reference to group keeps the Group alive
    assert group.id
    assert c1.id and c2.id  # wrapper objects still valid


def test_apply_theme_resolves_across_stitched_and_unified():
    """apply_theme finds clips inside StitchedMedia / UnifiedMedia for themeMappings resolution."""
    tmp = Path(tempfile.mkdtemp()) / 'test.cmproj'
    proj = Project.new(str(tmp))
    track = proj.timeline.get_or_create_track('T')
    c1 = track.add_callout('C', 0.0, 2.0)
    # Build a UnifiedMedia wrapper with a nested video sub-clip of id 777
    track._data.setdefault('medias', []).append({
        '_type': 'UnifiedMedia', 'id': 500, 'start': 0, 'duration': 1000,
        'mediaStart': 0, 'mediaDuration': 1000, 'scalar': 1,
        'parameters': {}, 'effects': [], 'metadata': {},
        'animationTracks': {}, 'attributes': {},
        'video': {'_type': 'VMFile', 'id': 777, 'start': 0, 'duration': 1000,
                  'mediaStart': 0, 'mediaDuration': 1000, 'scalar': 1,
                  'parameters': {}, 'effects': [], 'attributes': {}},
        'audio': {'_type': 'AMFile', 'id': 778, 'start': 0, 'duration': 1000,
                  'mediaStart': 0, 'mediaDuration': 1000, 'scalar': 1,
                  'parameters': {}, 'effects': [], 'attributes': {}},
    })
    # Also a StitchedMedia with a callout segment of id 888
    track._data['medias'].append({
        '_type': 'StitchedMedia', 'id': 600, 'start': 0, 'duration': 1000,
        'mediaStart': 0, 'mediaDuration': 1000, 'scalar': 1,
        'parameters': {}, 'effects': [], 'metadata': {},
        'animationTracks': {}, 'attributes': {},
        'medias': [{'_type': 'Callout', 'id': 888, 'start': 0, 'duration': 1000,
                    'def': {}, 'parameters': {}, 'effects': [], 'attributes': {}}],
    })
    # Attach themeMappings on c1 but referencing IDs 777 and 888 (nested)
    c1._data.setdefault('attributes', {})['assetProperties'] = [
        {'type': 1, 'name': 'C', 'objects': [777, 888],
         'themeMappings': {'outline': 'accent-1'}},
    ]
    count = apply_theme(proj, Theme(accent_1=(0.9, 0.0, 0.0, 1.0)))
    # 2 clips (video + callout) each got outline applied
    assert count == 2


def test_apply_theme_finds_clip_inside_group():
    """_find_clip_by_id must descend into Group inner tracks."""
    tmp = Path(tempfile.mkdtemp()) / 'test.cmproj'
    proj = Project.new(str(tmp))
    track = proj.timeline.get_or_create_track('T')
    c1 = track.add_callout('A', 0.0, 1.0)
    c2 = track.add_callout('B', 1.0, 1.0)
    grp = track.group_clips([c1.id, c2.id])  # c1 and c2 get new IDs inside the group
    # Fetch the actual inner clip id from the group's data
    inner_clips = grp._data['tracks'][0]['medias']
    inner_id = inner_clips[0]['id']
    # Put themeMappings on a separate clip but reference the re-IDed inner
    c3 = track.add_callout('C', 2.0, 1.0)
    c3._data.setdefault('attributes', {})['assetProperties'] = [
        {'type': 1, 'name': 'C', 'objects': [inner_id],
         'themeMappings': {'outline': 'accent-1'}},
    ]
    count = apply_theme(proj, Theme(accent_1=(0.7, 0.0, 0.0, 1.0)))
    assert count == 1


def test_apply_theme_empty_mappings_ignored():
    """assetProperties with empty themeMappings or empty objects are skipped."""
    tmp = Path(tempfile.mkdtemp()) / 'test.cmproj'
    proj = Project.new(str(tmp))
    track = proj.timeline.get_or_create_track('T')
    callout = track.add_callout('X', 0.0, 1.0)
    callout._data.setdefault('attributes', {})['assetProperties'] = [
        {'type': 1, 'name': 'C', 'objects': [], 'themeMappings': {}},
        {'type': 1, 'name': 'C', 'objects': [callout.id], 'themeMappings': {}},
    ]
    count = apply_theme(proj, Theme())
    assert count == 0
