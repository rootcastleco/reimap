"""GeoIP resolution for reimap."""

from __future__ import annotations

from .database import GeoIPDatabase
from .resolver import GeoResolver

__all__ = ["GeoIPDatabase", "GeoResolver"]
