"""REV-performance-002: O(n²) duplicate-ID location lookup in validation.

_check_duplicate_clip_ids collects all (id, location) pairs into a list,
then for each duplicate ID, does a linear scan of the entire list to find
locations: `locs = [loc for i, loc in all_ids if i == mid]`.

With D duplicate IDs and N total clips, this is O(D * N). If many IDs
are duplicated (pathological but possible), this becomes O(N²).
"""
import time
from collections import Counter, defaultdict

N = 10_000

# Simulate: list of (id, location) pairs with some duplicates
all_ids = [(i % (N // 2), f"track[{i % 10}]") for i in range(N)]

# Current approach: O(D * N)
t0 = time.perf_counter()
counts = Counter(mid for mid, _ in all_ids)
for mid, count in counts.items():
    if count > 1:
        locs = [loc for i, loc in all_ids if i == mid]
t1 = time.perf_counter()
print(f"Current O(D*N): {t1 - t0:.4f}s")

# Fixed approach: O(N) with defaultdict
t2 = time.perf_counter()
id_to_locs: dict[int, list[str]] = defaultdict(list)
for mid, loc in all_ids:
    id_to_locs[mid].append(loc)
for mid, locs in id_to_locs.items():
    if len(locs) > 1:
        pass  # locs already collected
t3 = time.perf_counter()
print(f"Fixed O(N): {t3 - t2:.4f}s")
print(f"Speedup: {(t1-t0)/(t3-t2):.1f}x")
