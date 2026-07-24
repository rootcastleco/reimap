"""Rolling connection history persisted to disk.

The history store keeps a rolling window (default 30 days) of every distinct
remote endpoint seen, how often it appeared, and when. It backs the "new" and
"frequent" insight signals and survives restarts as a single JSON file.
"""

from __future__ import annotations

import json
import threading
import time
from dataclasses import asdict, dataclass, field

from ..app_dirs import data_dir
from ..logging_config import get_logger
from ..model import Connection, ConnectionKind

log = get_logger("state.history")

_DAY_SECONDS = 86_400


@dataclass
class HistoryEntry:
    """Aggregated history for one remote endpoint."""

    ip: str
    country: str = ""
    country_code: str = ""
    city: str = ""
    hits: int = 0
    processes: list[str] = field(default_factory=list)
    first_seen: float = 0.0
    last_seen: float = 0.0

    def touch(self, conn: Connection, now: float) -> None:
        """Fold a fresh observation of this endpoint into the aggregate."""
        self.hits += 1
        self.last_seen = now
        if self.first_seen == 0.0:
            self.first_seen = now
        if conn.location is not None:
            self.country = conn.location.country or self.country
            self.country_code = conn.location.country_code or self.country_code
            self.city = conn.location.city or self.city
        if conn.process and conn.process not in self.processes:
            self.processes.append(conn.process)


class HistoryStore:
    """Persisted, rolling-window history keyed by remote IP."""

    def __init__(self, retention_days: int = 30) -> None:
        self.retention_days = retention_days
        self._path = data_dir() / "history.json"
        self._lock = threading.RLock()
        self._entries: dict[str, HistoryEntry] = {}
        self._load()

    # -- Persistence --------------------------------------------------------
    def _load(self) -> None:
        if not self._path.exists():
            return
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
            for ip, data in raw.get("entries", {}).items():
                self._entries[ip] = HistoryEntry(**data)
            log.info("Loaded %d history entries", len(self._entries))
        except (OSError, json.JSONDecodeError, TypeError) as exc:
            log.error("Could not load history (%s); starting fresh.", exc)
            self._entries = {}

    def save(self) -> None:
        """Persist the history to disk."""
        with self._lock:
            payload = {
                "version": 1,
                "saved_at": time.time(),
                "entries": {ip: asdict(e) for ip, e in self._entries.items()},
            }
        try:
            self._path.write_text(json.dumps(payload), encoding="utf-8")
        except OSError as exc:
            log.error("Could not save history: %s", exc)

    # -- Mutation -----------------------------------------------------------
    def record(self, connections: list[Connection]) -> list[Connection]:
        """Fold a scan snapshot into history, returning first-ever connections.

        Args:
            connections: The current snapshot.

        Returns:
            The subset of ``connections`` whose remote IP had never been seen
            before this call (i.e. genuinely new endpoints).
        """
        now = time.time()
        brand_new: list[Connection] = []
        with self._lock:
            for conn in connections:
                if conn.kind not in (ConnectionKind.REMOTE, ConnectionKind.LAN):
                    continue
                entry = self._entries.get(conn.remote_ip)
                if entry is None:
                    entry = HistoryEntry(ip=conn.remote_ip)
                    self._entries[conn.remote_ip] = entry
                    brand_new.append(conn)
                entry.touch(conn, now)
            self._prune(now)
        return brand_new

    def _prune(self, now: float) -> None:
        cutoff = now - self.retention_days * _DAY_SECONDS
        stale = [ip for ip, e in self._entries.items() if e.last_seen < cutoff]
        for ip in stale:
            del self._entries[ip]
        if stale:
            log.debug("Pruned %d stale history entries", len(stale))

    # -- Queries ------------------------------------------------------------
    def is_new(self, ip: str) -> bool:
        """Whether ``ip`` has been seen only within a single recent day."""
        with self._lock:
            entry = self._entries.get(ip)
            if entry is None:
                return True
            return (time.time() - entry.first_seen) < _DAY_SECONDS

    def frequent(self, threshold: int) -> list[HistoryEntry]:
        """Return endpoints whose hit count meets or exceeds ``threshold``."""
        with self._lock:
            items = [e for e in self._entries.values() if e.hits >= threshold]
        return sorted(items, key=lambda e: e.hits, reverse=True)

    def all_entries(self) -> list[HistoryEntry]:
        """Return every retained history entry."""
        with self._lock:
            return list(self._entries.values())

    def country_totals(self) -> dict[str, int]:
        """Return a mapping of country name to total hits."""
        totals: dict[str, int] = {}
        with self._lock:
            for entry in self._entries.values():
                if entry.country:
                    totals[entry.country] = totals.get(entry.country, 0) + entry.hits
        return dict(sorted(totals.items(), key=lambda kv: kv[1], reverse=True))
