"""Tests for typing fixes (REV-typing-001 through REV-typing-005)."""
from __future__ import annotations

import inspect


class TestShapeAnnotations:
    """REV-typing-001: shapes.py factory functions must have type annotations."""

    def test_rectangle_has_annotations(self) -> None:
        from camtasia.annotations.shapes import rectangle
        ann = inspect.get_annotations(rectangle)
        assert 'return' in ann
        assert 'fill_color' in ann

    def test_ellipse_has_annotations(self) -> None:
        from camtasia.annotations.shapes import ellipse
        ann = inspect.get_annotations(ellipse)
        assert 'return' in ann
        assert 'fill_color' in ann

    def test_triangle_has_annotations(self) -> None:
        from camtasia.annotations.shapes import triangle
        ann = inspect.get_annotations(triangle)
        assert 'return' in ann
        assert 'fill_color' in ann

    def test_rectangle_still_works(self) -> None:
        from camtasia.annotations.shapes import rectangle
        from camtasia.annotations.types import Color
        result = rectangle(fill_color=Color(1.0, 0.0, 0.0))
        assert result['shape'] == 'shape-rectangle'

    def test_ellipse_still_works(self) -> None:
        from camtasia.annotations.shapes import ellipse
        result = ellipse()
        assert result['shape'] == 'shape-ellipse'

    def test_triangle_still_works(self) -> None:
        from camtasia.annotations.shapes import triangle
        result = triangle()
        assert result['shape'] == 'shape-triangle'


class TestCalloutAnnotations:
    """REV-typing-002: callouts.py text() and square() must have type annotations."""

    def test_text_has_annotations(self) -> None:
        from camtasia.annotations.callouts import text
        ann = inspect.get_annotations(text)
        assert 'return' in ann
        assert 'text' in ann

    def test_square_has_annotations(self) -> None:
        from camtasia.annotations.callouts import square
        ann = inspect.get_annotations(square)
        assert 'return' in ann
        assert 'text' in ann

    def test_text_still_works(self) -> None:
        from camtasia.annotations.callouts import text
        result = text('hello', 'Arial', 'Bold')
        assert result['text'] == 'hello'

    def test_square_still_works(self) -> None:
        from camtasia.annotations.callouts import square
        result = square('hello', 'Arial', 'Bold')
        assert result['text'] == 'hello'


class TestSubpackageAll:
    """REV-typing-003: library and media_bin __init__.py must define __all__."""

    def test_library_has_all(self) -> None:
        import camtasia.library
        assert hasattr(camtasia.library, '__all__')
        assert 'Library' in camtasia.library.__all__
        assert 'LibraryAsset' in camtasia.library.__all__
        assert 'Libraries' in camtasia.library.__all__
        assert 'import_libzip' in camtasia.library.__all__
        assert 'export_libzip' in camtasia.library.__all__

    def test_media_bin_has_all(self) -> None:
        import camtasia.media_bin
        assert hasattr(camtasia.media_bin, '__all__')
        assert 'Media' in camtasia.media_bin.__all__
        assert 'MediaBin' in camtasia.media_bin.__all__
        assert 'MediaType' in camtasia.media_bin.__all__


class TestWithUndoDecorator:
    """REV-typing-005: with_undo() must not return bare Callable."""

    def test_with_undo_return_not_bare_callable(self) -> None:
        from camtasia.history import with_undo
        ann = inspect.get_annotations(with_undo)
        assert 'return' in ann
        ret_str = ann['return']
        # Should not be bare 'Callable' — should have type args
        assert ret_str != 'Callable'


class TestDocstringFix:
    """REV-docstrings-001: remove_media docstring must match implementation."""

    def test_remove_media_docstring_matches_default(self) -> None:
        from camtasia.operations.media_ops import remove_media
        doc = remove_media.__doc__
        assert doc is not None
        # Should NOT say "By default, this will also remove references"
        assert 'By default, this will also remove' not in doc
        # Should mention that it raises ValueError by default
        assert 'ValueError' in doc
