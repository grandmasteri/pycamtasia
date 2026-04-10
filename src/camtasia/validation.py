"""Project validation — checks for common issues before save."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ValidationIssue:
    """A single validation finding.

    Attributes:
        level: ``'warning'`` or ``'error'``.
        message: Human-readable description of the issue.
        source_id: Related source-bin ID, if applicable.
    """

    level: str
    message: str
    source_id: int | None = None
