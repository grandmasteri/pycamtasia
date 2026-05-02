"""REV-performance-004: Fraction construction overhead in _check_clip_overlap_on_track.

The overlap check creates Fraction objects from string representations
of integer tick values. Since ticks are always integers (per D-005),
int() is sufficient and much faster than Fraction(str(...)).
"""
import time
from fractions import Fraction

N = 10_000
values = [str(i * 705600000) for i in range(N)]

# Current: Fraction(str(x))
t0 = time.perf_counter()
for v in values:
    int(Fraction(v))
t1 = time.perf_counter()
print(f"Fraction(str(x)) x{N}: {t1 - t0:.3f}s")

# Fixed: int(x) directly
t2 = time.perf_counter()
for v in values:
    int(v)
t3 = time.perf_counter()
print(f"int(x) x{N}: {t3 - t2:.4f}s")
print(f"Speedup: {(t1-t0)/(t3-t2):.0f}x")
