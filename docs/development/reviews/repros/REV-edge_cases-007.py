"""REV-edge_cases-007: MarkerList with negative time, duplicate times, unicode names."""
from camtasia.timeline.markers import MarkerList, EDIT_RATE

data = {}
ml = MarkerList(data)

# Add marker with negative time
m = ml.add("negative", -EDIT_RATE)
print(f"Added marker at negative time: {m}")
print(f"time_seconds: {m.time_seconds}")

# Add marker with zero time
m = ml.add("zero", 0)
print(f"Added marker at zero: {m}")

# Add duplicate markers at same time
ml.add("dup1", 1000)
ml.add("dup2", 1000)
print(f"Markers after adding two at same time: {len(ml)}")

# remove_at with duplicate times - removes ALL at that time
ml.remove_at(1000)
print(f"Markers after remove_at(1000): {len(ml)}")

# Unicode marker names
ml.add("🎬 Start", EDIT_RATE)
ml.add("日本語マーカー", EDIT_RATE * 2)
ml.add("", EDIT_RATE * 3)  # empty name
ml.add("\x00null\x00byte", EDIT_RATE * 4)  # null bytes
print(f"Unicode markers count: {len(ml)}")
for m in ml:
    print(f"  {m.name!r} at {m.time_seconds:.2f}s")

# rename with empty string
ml.rename("🎬 Start", "")
print("Renamed to empty string OK")

# move to negative time
ml.move(EDIT_RATE * 2, -EDIT_RATE * 100)
print("Moved to negative time OK")

# next_after / prev_before with extreme values
result = ml.next_after(-999999999999)
print(f"next_after(-huge) = {result}")
result = ml.prev_before(999999999999)
print(f"prev_before(huge) = {result}")
