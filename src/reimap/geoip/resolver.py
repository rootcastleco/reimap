"""Resolve IP addresses to geographic locations.

Wraps the MaxMind reader with an in-memory LRU cache and fires the geoip hooks so
plugins can observe every resolution. When no database is installed the resolver
degrades gracefully: it returns ``None`` and emits ``GEOIP_UNRESOLVED``.
"""

from __future__ import annotations

import contextlib
from functools import lru_cache

from ..hooks import HookName, hooks
from ..logging_config import get_logger
from ..model import Connection, ConnectionKind, GeoLocation
from .database import GeoIPDatabase

log = get_logger("geoip.resolver")

try:
    import geoip2.database
    import geoip2.errors
except ImportError:  # pragma: no cover
    geoip2 = None  # type: ignore[assignment]


class GeoResolver:
    """Resolve connections to :class:`GeoLocation` objects."""

    def __init__(self, database: GeoIPDatabase | None = None) -> None:
        self._db = database or GeoIPDatabase()
        self._reader = None
        self._open_reader()

    def _open_reader(self) -> None:
        path = self._db.path()
        if path is None or geoip2 is None:
            if geoip2 is None:  # pragma: no cover
                log.warning("geoip2 is not installed; locations will be unavailable.")
            else:
                log.info("No GeoIP database installed; locations will be unavailable.")
            self._reader = None
            return
        try:
            self._reader = geoip2.database.Reader(str(path))
            log.info("Opened GeoIP database %s", path)
        except (OSError, ValueError) as exc:
            log.error("Failed to open GeoIP database: %s", exc)
            self._reader = None

    @property
    def ready(self) -> bool:
        """Whether a database reader is available."""
        return self._reader is not None

    def reload(self) -> None:
        """Re-open the reader after a database install/update, clearing caches."""
        if self._reader is not None:
            with contextlib.suppress(Exception):
                self._reader.close()
        self._lookup.cache_clear()
        self._open_reader()

    @lru_cache(maxsize=4096)  # noqa: B019 - bound to instance lifetime intentionally
    def _lookup(self, ip: str) -> GeoLocation | None:
        """Cached raw lookup for a single IP (no hooks)."""
        if self._reader is None:
            return None
        try:
            record = self._reader.city(ip)
        except (geoip2.errors.AddressNotFoundError, ValueError):  # type: ignore[union-attr]
            return None
        except Exception as exc:
            log.debug("GeoIP lookup error for %s: %s", ip, exc)
            return None

        if record.location.latitude is None or record.location.longitude is None:
            return None

        return GeoLocation(
            latitude=float(record.location.latitude),
            longitude=float(record.location.longitude),
            city=record.city.name or "",
            country=record.country.name or "",
            country_code=record.country.iso_code or "",
            accuracy_km=record.location.accuracy_radius,
        )

    def resolve(self, connection: Connection) -> Connection:
        """Resolve a single connection in place, firing the appropriate hook.

        LAN/LOCAL/LISTEN connections are never geolocated (they have no public
        position) but are returned unchanged so callers can still display them.
        """
        if connection.kind is not ConnectionKind.REMOTE:
            return connection

        location = self._lookup(connection.remote_ip)
        if location is None:
            hooks.emit(HookName.GEOIP_UNRESOLVED, connection=connection)
            return connection

        connection.location = location
        hooks.emit(HookName.GEOIP_RESOLVED, connection=connection, location=location)
        return connection

    def resolve_all(self, connections: list[Connection]) -> list[Connection]:
        """Resolve a batch of connections, returning the same list."""
        for conn in connections:
            self.resolve(conn)
        return connections
