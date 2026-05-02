"""REV-edge_cases-014: extend_dynamic_caption with zero and negative new_duration."""
from camtasia.timeline.captions import extend_dynamic_caption
from camtasia.timing import seconds_to_ticks

# Callout with word timings
callout_data = {
    'duration': seconds_to_ticks(5.0),
    'metadata': {
        'dynamicCaptionTranscription': {
            'words': [
                {'start': 0.0, 'end': 1.0, 'text': 'hello'},
                {'start': 1.0, 'end': 2.5, 'text': 'world'},
                {'start': 2.5, 'end': 5.0, 'text': 'test'},
            ]
        }
    }
}

# Zero new duration - ratio becomes 0, all word timings collapse to 0
import copy
data_zero = copy.deepcopy(callout_data)
extend_dynamic_caption(data_zero, 0.0)
words = data_zero['metadata']['dynamicCaptionTranscription']['words']
print(f"Zero duration: words = {words}")
print(f"  duration ticks = {data_zero['duration']}")

# Negative new duration - ratio becomes negative, word timings flip
data_neg = copy.deepcopy(callout_data)
extend_dynamic_caption(data_neg, -5.0)
words = data_neg['metadata']['dynamicCaptionTranscription']['words']
print(f"Negative duration: words = {words}")
print(f"  duration ticks = {data_neg['duration']}")

# NaN duration
import math
data_nan = copy.deepcopy(callout_data)
extend_dynamic_caption(data_nan, math.nan)
words = data_nan['metadata']['dynamicCaptionTranscription']['words']
print(f"NaN duration: words = {words}")
