"""REV-performance-006: save() calls validate() which re-traverses all clips.

save() unconditionally calls self.validate() before writing. This means
every save does: deepcopy + validate (17 tree walks) + flatten + json.dumps
+ 4 regex passes over the output string. For large projects this adds up.
"""
import time
import json
import sys
sys.path.insert(0, 'src')

# Measure just the json.dumps + regex post-processing portion
import re

clip = {
    "id": 0, "_type": "AMFile", "src": 1, "start": 0,
    "duration": 705600000, "mediaDuration": 705600000,
    "mediaStart": 0, "scalar": 1,
    "parameters": {"volume": 1.0},
    "effects": [],
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
    "sourceBin": [{"id": i} for i in range(100)],
    "timeline": {"sceneTrack": {"scenes": [{"csml": {"tracks": tracks}}]}},
}

# json.dumps
t0 = time.perf_counter()
text = json.dumps(data, indent=2, ensure_ascii=False, allow_nan=True)
t1 = time.perf_counter()
print(f"json.dumps: {t1-t0:.3f}s ({len(text):,} bytes)")

# Regex pass 1: infinity replacement
t2 = time.perf_counter()
text2 = re.sub(r'("(?:[^"\\]|\\.)*")|-?Infinity\b|NaN\b', lambda m: m.group(0), text)
t3 = time.perf_counter()
print(f"Regex infinity: {t3-t2:.3f}s")

# Regex pass 2: colon spacing (line-by-line)
t4 = time.perf_counter()
lines = text2.split('\n')
for i, line in enumerate(lines):
    if '\\"' not in line:
        lines[i] = re.sub(r'(^\s*"[^"]+")\s*:', r'\1 :', line)
text3 = '\n'.join(lines)
t5 = time.perf_counter()
print(f"Regex colon spacing ({len(lines)} lines): {t5-t4:.3f}s")

# Regex pass 3: collapse arrays
t6 = time.perf_counter()
text4 = re.sub(
    r'\[\s*(?:-?[\d.]+(?:e[+-]?\d+)?|"[^"]*"|true|false|null)'
    r'(?:,\s*(?:-?[\d.]+(?:e[+-]?\d+)?|"[^"]*"|true|false|null))*'
    r'\s*\]',
    lambda m: '[' + ', '.join(re.findall(r'-?[\d.]+(?:e[+-]?\d+)?|"[^"]*"|true|false|null', m.group(0))) + ']',
    text3, flags=re.DOTALL,
)
t7 = time.perf_counter()
print(f"Regex collapse arrays: {t7-t6:.3f}s")

# Regex pass 4: expand empty objects
t8 = time.perf_counter()
text5 = re.sub(r'^([ \t]*)("[^"]*"[ \t]*:[ \t]*)\{\}([ \t]*,?)[ \t]*$', r'\1\2{\n\1}\3', text4, flags=re.MULTILINE)
t9 = time.perf_counter()
print(f"Regex empty objects: {t9-t8:.3f}s")

# Regex pass 5: trailing comma space
t10 = time.perf_counter()
text6 = re.sub(r',\n', ', \n', text5)
t11 = time.perf_counter()
print(f"Regex trailing comma: {t11-t10:.3f}s")

print(f"\nTotal post-processing: {(t3-t2)+(t5-t4)+(t7-t6)+(t9-t8)+(t11-t10):.3f}s")
print(f"Total json.dumps + post: {(t1-t0)+(t3-t2)+(t5-t4)+(t7-t6)+(t9-t8)+(t11-t10):.3f}s")
