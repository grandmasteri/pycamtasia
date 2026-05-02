"""REV-edge_cases-003: _lcm(0, n) causes ZeroDivisionError, propagates through FrameStamp arithmetic."""
from camtasia.frame_stamp import FrameStamp, _lcm

# Direct _lcm with zero
try:
    result = _lcm(0, 30)
    print(f"UNEXPECTED: _lcm(0, 30) = {result}")
except ZeroDivisionError:
    print("CONFIRMED: _lcm(0, 30) -> ZeroDivisionError")

try:
    result = _lcm(30, 0)
    print(f"UNEXPECTED: _lcm(30, 0) = {result}")
except ZeroDivisionError:
    print("CONFIRMED: _lcm(30, 0) -> ZeroDivisionError")

# Adding FrameStamps with zero frame_rate
fs_zero = FrameStamp(frame_number=10, frame_rate=0)
fs_normal = FrameStamp(frame_number=10, frame_rate=30)
try:
    result = fs_zero + fs_normal
    print(f"UNEXPECTED: zero-rate + normal = {result}")
except ZeroDivisionError:
    print("CONFIRMED: FrameStamp(rate=0) + FrameStamp(rate=30) -> ZeroDivisionError")

# Negative frame_rate in _lcm
try:
    result = _lcm(-30, 60)
    print(f"_lcm(-30, 60) = {result}")
except Exception as e:
    print(f"_lcm(-30, 60) -> {type(e).__name__}: {e}")
