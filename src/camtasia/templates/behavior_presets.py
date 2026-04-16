"""Behavior effect preset templates from real Camtasia projects."""
from __future__ import annotations
import copy

# Direction keyframe template (shared by all presets with direction params)
_DIRECTION_KF = {'endTime': 0, 'time': 0, 'value': 0, 'duration': 0}
_DIRECTION_PARAM = {
    'type': 'int',
    'valueBounds': {'minValue': 0, 'maxValue': 3, 'defaultValue': 0},
    'uiHints': {'userInterfaceType': 2, 'unitType': 0},
    'keyframes': [_DIRECTION_KF],
}
_DIRECTION_PARAM_OUT = {
    'type': 'int',
    'valueBounds': {'minValue': 0, 'maxValue': 3, 'defaultValue': 2},
    'uiHints': {'userInterfaceType': 2, 'unitType': 0},
    'keyframes': [_DIRECTION_KF],
}

# "None" phase templates
_NONE_CENTER = {
    'attributes': {
        'name': 'none', 'type': 1, 'characterOrder': 6,
        'offsetBetweenCharacters': 0, 'secondsPerLoop': 1,
        'numberOfLoops': -1, 'delayBetweenLoops': 0,
    }
}
_NONE_OUT = {
    'attributes': {
        'name': 'none', 'type': 1, 'characterOrder': 6,
        'offsetBetweenCharacters': 0, 'suggestedDurationPerCharacter': 0,
        'overlapProportion': 0, 'movement': -1,
        'springDamping': 5.0, 'springStiffness': 50.0, 'bounceBounciness': 0.45,
    }
}

PRESETS = {
    'reveal': {
        'effectName': 'reveal',
        'start': 1411200000,
        'in': {
            'attributes': {
                'name': 'reveal', 'type': 0, 'characterOrder': 7,
                'offsetBetweenCharacters': 35280000,
                'suggestedDurationPerCharacter': 517440000,
                'overlapProportion': 0, 'movement': 16,
                'springDamping': 5.0, 'springStiffness': 50.0, 'bounceBounciness': 0.45,
            },
            'parameters': {'direction': _DIRECTION_PARAM},
        },
        'center': _NONE_CENTER,
        'out': {
            'attributes': {
                'name': 'reveal', 'type': 0, 'characterOrder': 7,
                'offsetBetweenCharacters': 35280000,
                'suggestedDurationPerCharacter': 399840000,
                'overlapProportion': '1/2', 'movement': 6,
                'springDamping': 5.0, 'springStiffness': 50.0, 'bounceBounciness': 0.45,
            },
            'parameters': {'direction': _DIRECTION_PARAM_OUT},
        },
        'metadata': {
            'default-behavior-center-style': 'reveal',
            'default-behavior-in-type': {'type': 'double', 'value': 1.0},
            'default-behavior-out-direction': {'type': 'int', 'value': 2},
            'default-behavior-out-type': {'type': 'double', 'value': 1.0},
            'presetName': 'Reveal',
        },
    },
    'fade': {
        'effectName': 'fade',
        'start': 470400000,
        'in': {
            'attributes': {
                'name': 'fadeIn', 'type': 1, 'characterOrder': 6,
                'offsetBetweenCharacters': 35280000,
                'suggestedDurationPerCharacter': 705600000,
                'overlapProportion': 0, 'movement': 0,
                'springDamping': 5.0, 'springStiffness': 50.0, 'bounceBounciness': 0.45,
            },
        },
        'center': _NONE_CENTER,
        'out': _NONE_OUT,
        'metadata': {'presetName': 'Fade'},
    },
    'flyIn': {
        'effectName': 'flyIn',
        'start': 0,
        'in': {
            'attributes': {
                'name': 'flyIn', 'type': 0, 'characterOrder': 6,
                'offsetBetweenCharacters': 35280000,
                'suggestedDurationPerCharacter': 705600000,
                'overlapProportion': 0, 'movement': 16,
                'springDamping': 5.0, 'springStiffness': 50.0, 'bounceBounciness': 0.45,
            },
            'parameters': {'direction': _DIRECTION_PARAM},
        },
        'center': _NONE_CENTER,
        'out': _NONE_OUT,
        'metadata': {'presetName': 'FlyIn'},
    },
    'popUp': {
        'effectName': 'popUp',
        'start': 0,
        'in': {
            'attributes': {
                'name': 'grow', 'type': 1, 'characterOrder': 6,
                'offsetBetweenCharacters': 35280000,
                'suggestedDurationPerCharacter': 705600000,
                'overlapProportion': 0, 'movement': 0,
                'springDamping': 5.0, 'springStiffness': 50.0, 'bounceBounciness': 0.45,
            },
        },
        'center': _NONE_CENTER,
        'out': _NONE_OUT,
        'metadata': {'presetName': 'PopUp'},
    },
    'sliding': {
        'effectName': 'sliding',
        'start': 0,
        'in': {
            'attributes': {
                'name': 'sliding', 'type': 0, 'characterOrder': 7,
                'offsetBetweenCharacters': 35280000,
                'suggestedDurationPerCharacter': 705600000,
                'overlapProportion': '11/20', 'movement': 16,
                'springDamping': 5.0, 'springStiffness': 50.0, 'bounceBounciness': 0.45,
            },
            'parameters': {'direction': _DIRECTION_PARAM},
        },
        'center': {
            'attributes': {
                'name': 'tremble', 'type': 0, 'characterOrder': 0,
                'offsetBetweenCharacters': 0, 'secondsPerLoop': '4/5',
                'numberOfLoops': -1, 'delayBetweenLoops': 0,
            },
            'parameters': {
                'horizontal': {'type': 'double', 'defaultValue': 6.0,
                    'valueBounds': {'minValue': 0.0, 'maxValue': 32.0, 'defaultValue': 6.0},
                    'uiHints': {'userInterfaceType': 1, 'unitType': 0}},
                'rotation': {'type': 'double', 'defaultValue': 0.0174,
                    'valueBounds': {'minValue': 0.0, 'maxValue': 1.0, 'defaultValue': 0.0174},
                    'uiHints': {'userInterfaceType': 1, 'unitType': 3}},
                'vertical': {'type': 'double', 'defaultValue': 2.0,
                    'valueBounds': {'minValue': 0.0, 'maxValue': 32.0, 'defaultValue': 2.0},
                    'uiHints': {'userInterfaceType': 1, 'unitType': 0}},
            },
        },
        'out': {
            'attributes': {
                'name': 'sliding', 'type': 0, 'characterOrder': 7,
                'offsetBetweenCharacters': 35280000,
                'suggestedDurationPerCharacter': 705600000,
                'overlapProportion': '11/20', 'movement': 8,
                'springDamping': 5.0, 'springStiffness': 50.0, 'bounceBounciness': 0.45,
            },
            'parameters': {'direction': _DIRECTION_PARAM_OUT},
        },
        'metadata': {
            'default-behavior-center-style': 'fading',
            'default-behavior-out-direction': {'type': 'int', 'value': 2},
            'presetName': 'Sliding',
        },
    },
    'pulsating': {
        'effectName': 'pulsating',
        'start': 0,
        'in': {
            'attributes': {
                'name': 'shifting', 'type': 0, 'characterOrder': 6,
                'offsetBetweenCharacters': 0,
                'suggestedDurationPerCharacter': 705600000,
                'overlapProportion': 0, 'movement': 0,
                'springDamping': 5.0, 'springStiffness': 50.0, 'bounceBounciness': 0.45,
            },
        },
        'center': {
            'attributes': {
                'name': 'pulsate', 'type': 1, 'characterOrder': 6,
                'offsetBetweenCharacters': 0, 'secondsPerLoop': 1,
                'numberOfLoops': -1, 'delayBetweenLoops': 0,
            },
        },
        'out': _NONE_OUT,
        'metadata': {'presetName': 'Pulsating'},
    },
    'shifting': {
        'effectName': 'shifting',
        'start': 0,
        'in': {
            'attributes': {
                'name': 'shifting', 'type': 0, 'characterOrder': 6,
                'offsetBetweenCharacters': 0,
                'suggestedDurationPerCharacter': 705600000,
                'overlapProportion': 0, 'movement': 0,
                'springDamping': 5.0, 'springStiffness': 50.0, 'bounceBounciness': 0.45,
            },
        },
        'center': _NONE_CENTER,
        'out': _NONE_OUT,
        'metadata': {'presetName': 'Shifting'},
    },
}




def get_behavior_preset(preset_name: str, duration_ticks: int) -> dict:
    """Get a complete behavior effect dict for a preset.
    
    Args:
        preset_name: Preset name (e.g. 'reveal', 'sliding').
        duration_ticks: Clip duration in ticks.
    
    Returns:
        Complete GenericBehaviorEffect dict ready to append to effects.
    
    Raises:
        ValueError: Unknown preset name.
    """
    if preset_name not in PRESETS:
        raise ValueError(
            f"Unknown behavior preset '{preset_name}'. "
            f"Available: {sorted(PRESETS)}"
        )
    template = copy.deepcopy(PRESETS[preset_name])
    effect = {
        '_type': 'GenericBehaviorEffect',
        'effectName': template['effectName'],
        'bypassed': False,
        'start': template['start'],
        'duration': max(0, duration_ticks - template['start']),
        'in': template['in'],
        'center': template['center'],
        'out': template['out'],
    }
    if 'metadata' in template:
        effect['metadata'] = template['metadata']
    return effect
