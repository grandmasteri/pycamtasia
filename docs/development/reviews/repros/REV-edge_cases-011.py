"""REV-edge_cases-011: hex_rgb silently accepts fullwidth Unicode digits as valid hex."""
from camtasia.color import hex_rgb

# Fullwidth digits ０１２３４５ (U+FF10-FF15) have len() == 6 but are NOT hex
# Python's int(..., 16) actually accepts them!
fullwidth = "\uff10\uff11\uff12\uff13\uff14\uff15"
print(f"Input: {fullwidth!r} (len={len(fullwidth)})")

try:
    result = hex_rgb(fullwidth)
    print(f"hex_rgb accepted fullwidth digits: {result}")
    # Check: int('\uff10\uff11', 16) actually works in Python
    print(f"int('\\uff10\\uff11', 16) = {int(chr(0xff10) + chr(0xff11), 16)}")
except ValueError as e:
    print(f"Rejected: {e}")

# This is actually Python's int() being permissive with Unicode digits
# The real question: does this produce correct color values?
# '\uff10\uff11' should be "01" -> 1, but let's check
r, g, b = hex_rgb(fullwidth)
print(f"RGB: ({r}, {g}, {b})")
# Compare with ASCII equivalent
r2, g2, b2 = hex_rgb("012345")
print(f"ASCII '012345' RGB: ({r2}, {g2}, {b2})")
print(f"Match: {(r,g,b) == (r2,g2,b2)}")
