"""REV-performance-001: Regex recompilation on every save().

The save() method compiles 4+ regex patterns on every call via re.sub().
For a project with ~10,000 clips, the JSON output can be 5-10 MB of text.
Running complex regexes over multi-MB strings is already expensive;
recompiling them each time adds overhead.
"""
import re
import time
import json

# Simulate a large project JSON output (~5 MB)
sample_line = '  "someKey": 12345.6789,\n'
text = "{\n" + sample_line * 100_000 + "}\n"
print(f"Text size: {len(text):,} bytes")

# Measure: re.sub with inline pattern (current approach)
t0 = time.perf_counter()
for _ in range(10):
    re.sub(r'("(?:[^"\\]|\\.)*")|-?Infinity\b|NaN\b', lambda m: m.group(0), text)
t1 = time.perf_counter()
print(f"Inline re.sub x10: {t1 - t0:.3f}s")

# Measure: pre-compiled pattern
PAT = re.compile(r'("(?:[^"\\]|\\.)*")|-?Infinity\b|NaN\b')
t2 = time.perf_counter()
for _ in range(10):
    PAT.sub(lambda m: m.group(0), text)
t3 = time.perf_counter()
print(f"Compiled re.sub x10: {t3 - t2:.3f}s")

print(f"Ratio: {(t1-t0)/(t3-t2):.2f}x")
