"""REV-edge_cases-015: Track.add_clip with zero duration and scalar edge cases."""
import json, tempfile, os
from camtasia.project import Project

tmpdir = tempfile.mkdtemp()
proj = Project.new(os.path.join(tmpdir, "test.tscproj"))
track = proj.timeline.add_track("test")

# Zero duration clip
try:
    clip = track.add_clip("AMFile", 1, start=0, duration=0)
    print(f"Zero duration clip accepted: id={clip.id}, duration={clip.duration}")
except (ValueError, Exception) as e:
    print(f"Zero duration rejected: {type(e).__name__}: {e}")

# Negative duration clip
try:
    clip = track.add_clip("AMFile", 1, start=0, duration=-705600000)
    print(f"Negative duration clip accepted: id={clip.id}, duration={clip.duration}")
except (ValueError, Exception) as e:
    print(f"Negative duration rejected: {type(e).__name__}: {e}")

# Negative start
try:
    clip = track.add_clip("AMFile", 1, start=-705600000, duration=705600000)
    print(f"Negative start clip accepted: id={clip.id}, start={clip.start}")
except (ValueError, Exception) as e:
    print(f"Negative start rejected: {type(e).__name__}: {e}")

# Zero scalar (should be rejected)
try:
    clip = track.add_clip("AMFile", 1, start=0, duration=705600000, scalar=0)
    print(f"UNEXPECTED: Zero scalar accepted")
except ValueError as e:
    print(f"OK: Zero scalar rejected: {e}")

# Negative scalar
try:
    clip = track.add_clip("AMFile", 1, start=0, duration=705600000, scalar=-1)
    print(f"UNEXPECTED: Negative scalar accepted")
except ValueError as e:
    print(f"OK: Negative scalar rejected: {e}")

print(f"\nTotal clips on track: {len(track)}")
