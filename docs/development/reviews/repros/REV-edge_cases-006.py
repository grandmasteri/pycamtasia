"""REV-edge_cases-006: CaptionAttributes.font_size with zero and negative values."""
from camtasia.timeline.captions import CaptionAttributes

data = {}
ca = CaptionAttributes(data)

# font_size = 0 should be rejected (< 1)
try:
    ca.font_size = 0
    print(f"OK: font_size=0 rejected")
except ValueError as e:
    print(f"OK: font_size=0 -> ValueError: {e}")

# font_size = -1 should be rejected
try:
    ca.font_size = -1
    print(f"OK: font_size=-1 rejected")
except ValueError as e:
    print(f"OK: font_size=-1 -> ValueError: {e}")

# opacity with NaN
import math
try:
    ca.opacity = math.nan
    print(f"UNEXPECTED: opacity=NaN accepted, value={ca.opacity}")
except ValueError as e:
    print(f"OK: opacity=NaN -> ValueError: {e}")

# opacity with negative zero
ca.opacity = -0.0
print(f"opacity=-0.0 accepted: {ca.opacity}")

# default_duration_seconds = 0.0 should be rejected (> 0)
try:
    ca.default_duration_seconds = 0.0
    print(f"OK: default_duration_seconds=0.0 rejected")
except ValueError as e:
    print(f"OK: default_duration_seconds=0.0 -> ValueError: {e}")

# default_duration_seconds = -1.0
try:
    ca.default_duration_seconds = -1.0
    print(f"OK: default_duration_seconds=-1.0 rejected")
except ValueError as e:
    print(f"OK: default_duration_seconds=-1.0 -> ValueError: {e}")

# active_word_at with empty words list
result = ca.active_word_at(1.0, [], 5.0)
print(f"active_word_at(1.0, [], 5.0) = {result}")

# active_word_at with zero duration
result = ca.active_word_at(0.0, ["hello"], 0.0)
print(f"active_word_at(0.0, ['hello'], 0.0) = {result}")

# active_word_at at exact boundary
result = ca.active_word_at(5.0, ["a", "b"], 5.0)
print(f"active_word_at(5.0, ['a','b'], 5.0) = {result}")
