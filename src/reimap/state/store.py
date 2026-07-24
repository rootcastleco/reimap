"""The live, in-memory view of the current connection set.

:class:`LiveStore` holds the most recent scan snapshot and tracks which
connections are new relative to the previous cycle. It is intentionally simple and
thread-safe so the scan loop (background thread) and the Dash callbacks (request
threads) can read/write it concurrently.
"""

from __future__ import annotations

import threading
import time

from ..model import Connection, ConnectionKind


class LiveStore:
    """Thread-safe container for the current connections snapshot."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._connections: dict[str, Connection] = {}
        self._last_scan_ts: float = 0.0
        self._last_scan_duration: float = 0.0
        self._scan_count: int = 0

    def update(
        self, connections: list[Connection], duration: float
    ) -> tuple[list[Connection], list[Connection]]:
        """Replace the snapshot and compute new/closed connections.

        Args:
            connections: The freshly scanned connections.
            duration: Wall-clock seconds the scan took.

        Returns:
            A ``(new, closed)`` tuple of connection lists relative to the prior
            snapshot.
        """
        now = time.time()
        with self._lock:
            previous = self._connections
            fresh: dict[str, Connection] = {}
            new: list[Connection] = []

            for conn in connections:
                existing = previous.get(conn.key)
                if existing is not None:
                    # preserve original first_seen, refresh last_seen + location
                    conn.first_seen = existing.first_seen
                    conn.last_seen = now
                    if conn.location is None:
                        conn.location = existing.location
                else:
                    conn.first_seen = now
                    conn.last_seen = now
                    new.append(conn)
                fresh[conn.key] = conn

            closed = [c for k, c in previous.items() if k not in fresh]

            self._connections = fresh
            self._last_scan_ts = now
            self._last_scan_duration = duration
            self._scan_count += 1

        return new, closed

    # -- Read accessors -----------------------------------------------------
    def all(self) -> list[Connection]:
        """Return every connection in the current snapshot."""
        with self._lock:
            return list(self._connections.values())

    def mapped(self) -> list[Connection]:
        """Return only geolocated connections."""
        with self._lock:
            return [c for c in self._connections.values() if c.is_mapped]

    def unmapped(self) -> list[Connection]:
        """Return remote connections that could not be geolocated."""
        with self._lock:
            return [
                c
                for c in self._connections.values()
                if c.kind is ConnectionKind.REMOTE and not c.is_mapped
            ]

    def by_kind(self, kind: ConnectionKind) -> list[Connection]:
        """Return connections of a given :class:`ConnectionKind`."""
        with self._lock:
            return [c for c in self._connections.values() if c.kind is kind]

    def listening_ports(self) -> list[Connection]:
        """Return listening/bound local sockets."""
        return self.by_kind(ConnectionKind.LISTEN)

    def stats(self) -> dict[str, float | int]:
        """Return a small dictionary of counters for the status bar."""
        with self._lock:
            conns = list(self._connections.values())
            return {
                "total": len(conns),
                "mapped": sum(1 for c in conns if c.is_mapped),
                "remote": sum(1 for c in conns if c.kind is ConnectionKind.REMOTE),
                "lan": sum(1 for c in conns if c.kind is ConnectionKind.LAN),
                "local": sum(1 for c in conns if c.kind is ConnectionKind.LOCAL),
                "listening": sum(1 for c in conns if c.kind is ConnectionKind.LISTEN),
                "scans": self._scan_count,
                "last_scan_ts": self._last_scan_ts,
                "last_scan_duration": round(self._last_scan_duration, 3),
            }
