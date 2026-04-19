"""Tests for camtasia.color module — hex_rgb function and RGBA class."""
from __future__ import annotations

import pytest

from camtasia.color import RGBA, hex_rgb


class TestHexRgbParsing:
    """Tests for hex_rgb parsing of various hex color formats."""

    @pytest.mark.parametrize(("hex_input", "expected"), [
        ("#abc", (0xaa, 0xbb, 0xcc)),
        ("abc", (0xaa, 0xbb, 0xcc)),
        ("#abcd", (0xaa, 0xbb, 0xcc, 0xdd)),
        ("#ff8800", (0xff, 0x88, 0x00)),
        ("ff8800", (0xff, 0x88, 0x00)),
        ("#ff880044", (0xff, 0x88, 0x00, 0x44)),
        ("ff880044", (0xff, 0x88, 0x00, 0x44)),
    ])
    def test_valid_hex_formats(self, hex_input, expected):
        actual_result = hex_rgb(hex_input)
        assert actual_result == expected

    @pytest.mark.parametrize("bad_input", [
        "ab",
        "abcde",
        "abcdefabc",
        "",
    ])
    def test_invalid_hex_raises_value_error(self, bad_input):
        with pytest.raises(ValueError, match="Could not interpret"):
            hex_rgb(bad_input)


class TestRGBAConstruction:
    """Tests for RGBA class construction and properties."""

    def test_direct_construction(self):
        color = RGBA(10, 20, 30, 40)
        assert color.red == 10
        assert color.green == 20
        assert color.blue == 30
        assert color.alpha == 40

    def test_from_hex_rgb(self):
        color = RGBA.from_hex("#ff8800")
        assert color.as_tuple() == (0xff, 0x88, 0x00, 255)

    def test_from_hex_rgba(self):
        color = RGBA.from_hex("#ff880044")
        assert color.as_tuple() == (0xff, 0x88, 0x00, 0x44)

    def test_from_floats(self):
        color = RGBA.from_floats(1.0, 0.5, 0.0, 1.0)
        assert color.red == 255
        assert color.green == 128  # round(0.5 * 255) = 128
        assert color.blue == 0
        assert color.alpha == 255

    @pytest.mark.parametrize(("channel", "args"), [
        ("red", (-1, 0, 0, 0)),
        ("red", (256, 0, 0, 0)),
        ("green", (0, -1, 0, 0)),
        ("green", (0, 256, 0, 0)),
        ("blue", (0, 0, -1, 0)),
        ("blue", (0, 0, 256, 0)),
        ("alpha", (0, 0, 0, -1)),
        ("alpha", (0, 0, 0, 256)),
    ])
    def test_out_of_range_channel_raises(self, channel, args):
        with pytest.raises(ValueError, match=f"{channel} channel"):
            RGBA(*args)

    def test_boundary_values_valid(self):
        color = RGBA(0, 0, 0, 0)
        assert color.as_tuple() == (0, 0, 0, 0)
        color = RGBA(255, 255, 255, 255)
        assert color.as_tuple() == (255, 255, 255, 255)


class TestRGBABehavior:
    """Tests for RGBA equality, hashing, and repr."""

    def test_equality(self):
        assert RGBA(1, 2, 3, 4) == RGBA(1, 2, 3, 4)

    def test_inequality(self):
        assert RGBA(1, 2, 3, 4) != RGBA(5, 6, 7, 8)

    def test_not_equal_to_non_rgba(self):
        assert RGBA(1, 2, 3, 4) != "not a color"

    def test_hash_equal_objects(self):
        assert hash(RGBA(1, 2, 3, 4)) == hash(RGBA(1, 2, 3, 4))

    def test_repr(self):
        actual_result = repr(RGBA(10, 20, 30, 40))
        assert actual_result == "RGBA(red=10, green=20, blue=30, alpha=40)"


class TestRGBAToHex:
    def test_to_hex(self):
        c = RGBA(255, 128, 0, 255)
        assert c.to_hex() == '#ff8000ff'

class TestRGBAToFloats:
    def test_to_floats(self):
        c = RGBA(255, 0, 128, 255)
        r, g, b, a = c.to_floats()
        assert r == 1.0
        assert g == 0.0
        assert abs(b - 128/255) < 0.001
        assert a == 1.0


# ── color.py non-integer channels (from test_coverage_extras.py) ──


class TestColorFromFloatsError:
    def test_non_integer_channels_raise(self):
        with pytest.raises(TypeError, match='integers'):
            RGBA(1.5, 0, 0, 255)  # type: ignore[arg-type]


# ── Merged from test_coverage_misc.py ────────────────────────────────


class TestHexRgb4Digit:
    def test_4_digit_hex(self):
        result = hex_rgb('#F0A8')
        assert len(result) == 4
        assert result == (255, 0, 170, 136)

    def test_invalid_length_raises(self):
        with pytest.raises(ValueError, match='Could not interpret'):
            hex_rgb('#12345')
