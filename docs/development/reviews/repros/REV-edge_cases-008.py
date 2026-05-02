"""REV-edge_cases-008: TransitionList.add with zero and negative duration_ticks."""
from camtasia.timeline.transitions import TransitionList

data = {}
tl = TransitionList(data)

# Zero duration transition
t = tl.add("Fade", 1, 2, 0)
print(f"Zero duration transition: {t}")
print(f"  duration_seconds: {t.duration_seconds}")

# Negative duration transition
t = tl.add("Fade", 1, 2, -705600000)
print(f"Negative duration transition: {t}")
print(f"  duration_seconds: {t.duration_seconds}")

# add_dissolve with zero duration
t = tl.add_dissolve(1, 2, duration_seconds=0.0)
print(f"Zero-second dissolve: {t}")

# add_dissolve with negative duration
t = tl.add_dissolve(1, 2, duration_seconds=-1.0)
print(f"Negative-second dissolve: {t}")
print(f"  duration_seconds: {t.duration_seconds}")

# Same clip on both sides
t = tl.add("Fade", 5, 5, 705600000)
print(f"Self-transition (same clip both sides): {t}")

print(f"\nTotal transitions: {len(tl)}")
