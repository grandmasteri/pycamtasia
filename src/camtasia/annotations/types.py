"""Annotation type definitions."""

from dataclasses import dataclass
from enum import Enum


@dataclass(frozen=True)
class Color:
    """RGBA color with components in the range [0.0, 1.0]."""
    red: float
    green: float
    blue: float
    opacity: float = 1.0

    def __post_init__(self) -> None:
        for comp in ('red', 'green', 'blue', 'opacity'):
            if not 0.0 <= getattr(self, comp) <= 1.0:
                raise ValueError(
                    f'Color {comp} component must be in the range [0.0, 1.0].')


class HorizontalAlignment(Enum):
    """Horizontal text alignment options."""
    Left = 'left'
    Center = 'center'
    Right = 'right'


class VerticalAlignment(Enum):
    """Vertical text alignment options."""
    Top = 'top'
    Center = 'center'
    Bottom = 'bottom'


class FillStyle(Enum):
    """Shape fill style options."""
    Solid = 'solid'
    Gradient = 'gradient'


class StrokeStyle(Enum):
    """Shape stroke/border style options."""
    Solid = 'solid'
    Dash = 'dash'
    Dot = 'dot'
    DashDot = 'dashdot'
    DashDotDot = 'dashdotdot'
    NoStroke = 'none'
