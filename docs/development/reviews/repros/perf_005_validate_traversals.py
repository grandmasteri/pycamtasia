"""REV-performance-005: validate_all traverses the clip tree 17+ times.

Each of the 17 check functions in validate_all() independently walks
the entire clip tree. For 10,000 clips, this means 170,000+ dict
lookups that could be done in a single pass.
"""
import time
import json

# Build representative project data
clip = {
    "id": 0, "_type": "AMFile", "src": 1, "start": 0,
    "duration": 705600000, "mediaDuration": 705600000,
    "mediaStart": 0, "scalar": 1,
    "parameters": {"volume": 1.0},
    "effects": [],
    "metadata": {},
}

tracks = []
for t in range(20):
    medias = []
    for c in range(500):
        d = dict(clip)
        d["id"] = t * 500 + c
        d["src"] = c % 100
        medias.append(d)
    tracks.append({"trackIndex": t, "medias": medias, "transitions": []})

data = {
    "version": "10.0",
    "sourceBin": [{"id": i, "src": f"media_{i}.mp4"} for i in range(100)],
    "timeline": {
        "id": 99999,
        "sceneTrack": {"scenes": [{"csml": {"tracks": tracks}}]},
        "trackAttributes": [{"ident": f"t{i}"} for i in range(20)],
    },
}

print(f"Clips: {sum(len(t['medias']) for t in tracks)}")

# Measure: count dict.get() calls via wrapper
call_count = 0
original_get = dict.get

# Time the full validation
import sys
sys.path.insert(0, 'src')
from camtasia.validation import validate_all

t0 = time.perf_counter()
issues = validate_all(data)
t1 = time.perf_counter()
print(f"validate_all: {t1 - t0:.3f}s, {len(issues)} issues")

# Run 5 times
t2 = time.perf_counter()
for _ in range(5):
    validate_all(data)
t3 = time.perf_counter()
print(f"validate_all x5: {t3 - t2:.3f}s ({(t3-t2)/5:.3f}s each)")
