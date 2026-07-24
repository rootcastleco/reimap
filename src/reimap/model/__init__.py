"""Domain models for reimap."""

from __future__ import annotations

from .connection import Connection, ConnectionKind
from .location import GeoLocation

__all__ = ["Connection", "ConnectionKind", "GeoLocation"]
