"""Behavior effect preset templates from real Camtasia projects."""
from __future__ import annotations

import copy
from typing import Any

# Direction keyframe template (shared by all presets with direction params)
_DIRECTION_KF = {'endTime': 0, 'time': 0, 'value': 0, 'duration': 0}
_DIRECTION_PARAM = {
    'type': 'int',
    'valueBounds': {'minValue': 0, 'maxValue': 3, 'defaultValue': 0},
    'uiHints': {'userInterfaceType': 2, 'unitType': 0},
    'keyframes': [_DIRECTION_KF],
}
_DIRECTION_KF_OUT = {'endTime': 0, 'time': 0, 'value': 0, 'duration': 0}
_DIRECTION_PARAM_OUT = {
    'type': 'int',
    'valueBounds': {'minValue': 0, 'maxValue': 3, 'defaultValue': 2},
    'uiHints': {'userInterfaceType': 2, 'unitType': 0},
    'keyframes': [_DIRECTION_KF_OUT],
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
        # NOTE: start=1411200000 (~2s) matches one real TechSmith sample but
        # has not been broadly verified across Camtasia versions. The value
        # is clamped by get_behavior_preset() to max(0, duration_ticks-1),
        # so short clips automatically get a smaller start offset.
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
                'name': 'hinge', 'type': 1, 'characterOrder': 3,
                'offsetBetweenCharacters': 35280000,
                'suggestedDurationPerCharacter': 1728720000,
                'overlapProportion': '1/3', 'movement': 30,
                'springDamping': 9.2959911040146, 'springStiffness': 50.0, 'bounceBounciness': 0.45,
            },
            'parameters': {'direction': {
                'type': 'int',
                'valueBounds': {'minValue': 0, 'maxValue': 3, 'defaultValue': 3},
                'uiHints': {'userInterfaceType': 2, 'unitType': 0},
                'keyframes': [{'endTime': 0, 'time': 0, 'value': 0, 'duration': 0}],
            }},
        },
        'center': {**_NONE_CENTER, 'attributes': {**_NONE_CENTER['attributes'], 'offsetBetweenCharacters': 0}},
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
            'default-behavior-center-style': 'tremble',
            'default-behavior-out-direction': {'type': 'int', 'value': 2},
            'presetName': 'Sliding',
        },
    },
    'pulsating': {
        'effectName': 'pulsating',
        'start': 0,
        'in': {
            'attributes': {
                'name': 'shifting', 'type': 1, 'characterOrder': 4,
                'offsetBetweenCharacters': 14112000,
                'suggestedDurationPerCharacter': 1070160000,
                'overlapProportion': 0, 'movement': 30,
                'springDamping': 7.0, 'springStiffness': 50.0, 'bounceBounciness': 0.45,
            },
        },
        'center': {
            'attributes': {
                'name': 'pulsate', 'type': 1, 'characterOrder': 6,
                'offsetBetweenCharacters': 49392000, 'secondsPerLoop': 1,
                'numberOfLoops': -1, 'delayBetweenLoops': 0,
            },
            'parameters': {
                'movement': {'type': 'int', 'defaultValue': 27,
                    'valueBounds': {'minValue': 0, 'maxValue': 31, 'defaultValue': 27},
                    'uiHints': {'userInterfaceType': 4, 'unitType': 0},
                    'keyframes': [{'endTime': 0, 'time': 0, 'value': 27, 'duration': 0}]},
                'scale': {'type': 'double', 'defaultValue': 1.08,
                    'valueBounds': {'minValue': 0.01, 'maxValue': 2.0, 'defaultValue': 1.08},
                    'uiHints': {'userInterfaceType': 1, 'unitType': 1},
                    'keyframes': [{'endTime': 0, 'time': 0, 'value': 1.08, 'duration': 0}]},
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
                'offsetBetweenCharacters': 49392000,
                'suggestedDurationPerCharacter': 705600000,
                'overlapProportion': 0, 'movement': 0,
                'springDamping': 5.0, 'springStiffness': 50.0, 'bounceBounciness': 0.45,
            },
        },
        'center': _NONE_CENTER,
        'out': _NONE_OUT,
        'metadata': {'presetName': 'Shifting'},
    },
    'flyOut': {
        'effectName': 'flyOut',
        'start': 0,
        'in': {
            'attributes': {
                'name': 'none', 'type': 1, 'characterOrder': 6,
                'offsetBetweenCharacters': 0,
                'suggestedDurationPerCharacter': 0,
                'overlapProportion': 0, 'movement': -1,
                'springDamping': 5.0, 'springStiffness': 50.0, 'bounceBounciness': 0.45,
            },
        },
        'center': _NONE_CENTER,
        'out': {
            'attributes': {
                'name': 'flyOut', 'type': 0, 'characterOrder': 6,
                'offsetBetweenCharacters': 35280000,
                'suggestedDurationPerCharacter': 705600000,
                'overlapProportion': 0, 'movement': 16,
                'springDamping': 5.0, 'springStiffness': 50.0, 'bounceBounciness': 0.45,
            },
            'parameters': {'direction': _DIRECTION_PARAM_OUT},
        },
        'metadata': {'presetName': 'FlyOut'},
    },
    'emphasize': {
        'effectName': 'emphasize',
        'start': 0,
        'in': _NONE_OUT,
        'center': {
            'attributes': {
                'name': 'emphasize', 'type': 1, 'characterOrder': 6,
                'offsetBetweenCharacters': 0, 'secondsPerLoop': 1,
                'numberOfLoops': -1, 'delayBetweenLoops': 0,
            },
            'parameters': {
                'scale': {'type': 'double', 'defaultValue': 1.15,
                    'valueBounds': {'minValue': 0.01, 'maxValue': 2.0, 'defaultValue': 1.15},
                    'uiHints': {'userInterfaceType': 1, 'unitType': 1}},
                'opacity': {'type': 'double', 'defaultValue': 0.8,
                    'valueBounds': {'minValue': 0.0, 'maxValue': 1.0, 'defaultValue': 0.8},
                    'uiHints': {'userInterfaceType': 1, 'unitType': 0}},
            },
        },
        'out': _NONE_OUT,
        'metadata': {'presetName': 'Emphasize'},
    },
    'jiggle': {
        'effectName': 'jiggle',
        'start': 0,
        'in': _NONE_OUT,
        'center': {
            'attributes': {
                'name': 'jiggle', 'type': 0, 'characterOrder': 6,
                'offsetBetweenCharacters': 0, 'secondsPerLoop': '1/2',
                'numberOfLoops': -1, 'delayBetweenLoops': 0,
            },
            'parameters': {
                'rotation': {'type': 'double', 'defaultValue': 0.035,
                    'valueBounds': {'minValue': 0.0, 'maxValue': 1.0, 'defaultValue': 0.035},
                    'uiHints': {'userInterfaceType': 1, 'unitType': 3}},
                'horizontal': {'type': 'double', 'defaultValue': 3.0,
                    'valueBounds': {'minValue': 0.0, 'maxValue': 32.0, 'defaultValue': 3.0},
                    'uiHints': {'userInterfaceType': 1, 'unitType': 0}},
                'vertical': {'type': 'double', 'defaultValue': 3.0,
                    'valueBounds': {'minValue': 0.0, 'maxValue': 32.0, 'defaultValue': 3.0},
                    'uiHints': {'userInterfaceType': 1, 'unitType': 0}},
            },
        },
        'out': _NONE_OUT,
        'metadata': {'presetName': 'Jiggle'},
    },
}

PRESETS = {k: copy.deepcopy(v) for k, v in PRESETS.items()}  # Break shared references between presets


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
    template: dict[str, Any] = copy.deepcopy(PRESETS[preset_name])
    effect = {
        '_type': 'GenericBehaviorEffect',
        'effectName': template['effectName'],
        'bypassed': False,
        'start': min(template['start'], max(0, duration_ticks - 1)),
        'duration': duration_ticks,
        'in': template['in'],
        'center': template['center'],
        'out': template['out'],
    }
    if 'metadata' in template:
        effect['metadata'] = template['metadata']
    return effect
