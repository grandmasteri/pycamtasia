"""REV-edge_cases-002: FrameStamp with zero frame_rate causes ZeroDivisionError."""
from camtasia.frame_stamp import FrameStamp

# Zero frame_rate - should this be allowed?
fs = FrameStamp(frame_number=100, frame_rate=0)

# Accessing frame_time triggers divmod by zero
try:
    result = fs.frame_time
    print(f"UNEXPECTED: frame_time with rate=0 returned {result}")
except ZeroDivisionError as e:
    print(f"CONFIRMED: FrameStamp(frame_number=100, frame_rate=0).frame_time -> ZeroDivisionError")

# Accessing time triggers division by zero
try:
    result = fs.time
    print(f"UNEXPECTED: time with rate=0 returned {result}")
except ZeroDivisionError as e:
    print(f"CONFIRMED: FrameStamp(frame_number=100, frame_rate=0).time -> ZeroDivisionError")

# __str__ also triggers divmod
try:
    result = str(fs)
    print(f"UNEXPECTED: str() with rate=0 returned {result}")
except ZeroDivisionError as e:
    print(f"CONFIRMED: str(FrameStamp(frame_number=100, frame_rate=0)) -> ZeroDivisionError")

# Negative frame_rate
fs_neg = FrameStamp(frame_number=100, frame_rate=-30)
try:
    result = fs_neg.frame_time
    print(f"Negative rate frame_time: {result}")
except Exception as e:
    print(f"Negative rate frame_time error: {type(e).__name__}: {e}")
