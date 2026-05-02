"""REV-performance-003: Full deepcopy of project data on every save().

save() calls copy.deepcopy(self._data) to avoid mutating the live data
during _flatten_parameters. For a project with 10,000 clips, the data
dict can be 5-10 MB of nested dicts/lists. deepcopy is expensive.
"""
import copy
import json
import time

# Build a representative nested dict (~5 MB)
clip = {
    "id": 0, "_type": "AMFile", "src": 1, "start": 0,
    "duration": 705600000, "mediaDuration": 705600000,
    "mediaStart": 0, "scalar": 1,
    "parameters": {
        "volume": {"type": "double", "defaultValue": 1.0},
        "geometryCrop0": {"type": "double", "defaultValue": 0.0},
    },
    "effects": [{"_type": "SomeEffect", "name": "blur", "parameters": {"radius": 5}}],
    "animationTracks": {"visual": [{"range": [0, 705600000]}]},
}

tracks = []
for t in range(20):
    medias = []
    for c in range(500):
        d = dict(clip)
        d["id"] = t * 500 + c
        medias.append(d)
    tracks.append({"trackIndex": t, "medias": medias})

data = {
    "sourceBin": [{"id": i, "src": f"media_{i}.mp4"} for i in range(100)],
    "timeline": {"sceneTrack": {"scenes": [{"csml": {"tracks": tracks}}]}},
}

size = len(json.dumps(data))
print(f"Data size: {size:,} bytes ({size/1024/1024:.1f} MB)")

t0 = time.perf_counter()
for _ in range(5):
    copy.deepcopy(data)
t1 = time.perf_counter()
print(f"deepcopy x5: {t1 - t0:.3f}s ({(t1-t0)/5:.3f}s each)")
