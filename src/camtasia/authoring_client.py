"""Authoring client metadata for Camtasia projects."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AuthoringClient:
    """Details about the client used to create/edit a project.

    Attributes:
        name: Application name.
        platform: Operating system or platform.
        version: Application version string.
    """

    name: str
    platform: str
    version: str
