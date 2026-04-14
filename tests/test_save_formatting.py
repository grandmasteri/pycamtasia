from __future__ import annotations
"""Tests for Project._flatten_parameters() parameter flattening."""

from camtasia.project import Project


def test_plain_param_dict_flattened_to_scalar():
    """A param dict without keyframes, interp, uiHints, or name is replaced by its defaultValue."""
    obj = {"opacity": {"type": "double", "defaultValue": 0.5}}
    Project._flatten_parameters(obj)
    assert obj["opacity"] == 0.5


def test_param_dict_with_interp_preserved():
    """A param dict with interp is left as-is (preserves interpolation type)."""
    original = {"type": "double", "defaultValue": 0.5, "interp": "eioe"}
    obj = {"opacity": dict(original)}
    Project._flatten_parameters(obj)
    assert obj["opacity"] == original


def test_param_dict_with_keyframes_preserved():
    """A param dict that has keyframes is left as-is."""
    original = {"type": "double", "defaultValue": 0.5, "keyframes": [{"time": 0, "value": 1.0}]}
    obj = {"opacity": dict(original)}
    Project._flatten_parameters(obj)
    assert obj["opacity"] == original


def test_effect_def_entry_preserved():
    """A dict with a 'name' field (effectDef entry) is left untouched."""
    original = {"type": "double", "defaultValue": 0.5, "name": "blur"}
    obj = {"effect": dict(original)}
    Project._flatten_parameters(obj)
    assert obj["effect"] == original


def test_nested_structures_walked():
    """Flattening recurses into nested dicts and lists."""
    obj = {
        "outer": {
            "inner": {"type": "int", "defaultValue": 3}
        },
        "items": [
            {"param": {"type": "double", "defaultValue": 1.0}}
        ],
    }
    Project._flatten_parameters(obj)
    assert obj["outer"]["inner"] == 3
    assert obj["items"][0]["param"] == 1.0
