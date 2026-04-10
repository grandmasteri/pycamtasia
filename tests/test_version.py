"""Tests for camtasia.version module."""

from camtasia.version import __version__, __version_info__


class TestVersion:
    """Tests for version constants."""

    def test_version_is_string(self):
        assert isinstance(__version__, str)
        assert "." in __version__

    def test_version_info_is_tuple_of_parts(self):
        assert __version_info__ == tuple(__version__.split("."))
        assert len(__version_info__) == 3
