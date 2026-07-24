"""Runtime orchestration: the background scan loop.

The :class:`Runtime` owns the long-lived objects (scanner, resolver, stores,
insights engine) and runs the periodic scan cycle on a daemon thread. Each cycle:

    1. emit ``SCAN_STARTED``
    2. scan sockets
    3. run every connection through the ``FILTER_CONNECTION`` hook
    4. geolocate remote connections (fires geoip hooks)
    5. update the live store and record history (fires connection hooks)
    6. recompute insights
    7. emit ``SCAN_COMPLETED``

Everything the UI needs is read from :class:`Runtime` attributes; the loop and the
web request threads communicate only through the thread-safe stores.
"""

from __future__ import annotations

import threading
import time

from .config import Config
from .geoip import GeoIPDatabase, GeoResolver
from .hooks import HookName, hooks
from .insights import InsightsEngine, InsightsPersistence
from .logging_config import get_logger
from .model import Connection
from .scanner import get_scanner
from .state import HistoryStore, LiveStore

log = get_logger("runtime")


class Runtime:
    """Owns background scanning and exposes state to the UI."""

    def __init__(self, config: Config) -> None:
        self.config = config
        self.scanner = get_scanner()
        self.geoip_db = GeoIPDatabase()
        self.resolver = GeoResolver(self.geoip_db)
        self.store = LiveStore()
        self.history = HistoryStore(retention_days=config.history_days)
        self.insights = InsightsEngine(
            self.store, self.history, frequent_threshold=config.frequent_threshold
        )
        self.persistence = InsightsPersistence()

        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._latest_snapshot = self.persistence.load_snapshot()

        log.info("Runtime initialised with scanner=%s", self.scanner.name)

    # -- Lifecycle ----------------------------------------------------------
    def start(self) -> None:
        """Start the background scan loop (idempotent)."""
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, name="reimap-scan", daemon=True)
        self._thread.start()
        log.info("Scan loop started (interval=%.1fs)", self.config.scan_interval_seconds)

    def stop(self) -> None:
        """Stop the scan loop and flush persistent state."""
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=5)
        self.history.save()
        if self._latest_snapshot:
            self.persistence.save_snapshot(self._latest_snapshot)
        log.info("Scan loop stopped and state flushed.")

    # -- The loop -----------------------------------------------------------
    def _loop(self) -> None:
        while not self._stop.is_set():
            start = time.time()
            try:
                self.scan_once()
            except Exception:
                log.exception("Scan cycle failed")
                hooks.emit(HookName.SCAN_FAILED, error="scan cycle exception")
            elapsed = time.time() - start
            self._stop.wait(max(0.0, self.config.scan_interval_seconds - elapsed))

    def scan_once(self) -> None:
        """Run a single scan/resolve/record/insights cycle."""
        hooks.emit(HookName.SCAN_STARTED)
        start = time.time()

        raw = self.scanner.scan()

        # Apply the FILTER_CONNECTION hook: plugins may drop or rewrite entries.
        filtered: list[Connection] = []
        for conn in raw:
            hooks.emit(HookName.CONNECTION_DISCOVERED, connection=conn)
            result = hooks.filter(HookName.FILTER_CONNECTION, conn)
            if result is not None:
                filtered.append(result)

        self.resolver.resolve_all(filtered)

        new, closed = self.store.update(filtered, duration=time.time() - start)
        brand_new = self.history.record(filtered)

        for conn in brand_new:
            hooks.emit(HookName.CONNECTION_NEW, connection=conn)
        for conn in closed:
            hooks.emit(HookName.CONNECTION_CLOSED, connection=conn)

        snapshot = self.insights.compute()
        self._latest_snapshot = snapshot.as_dict()
        self.persistence.save_snapshot(self._latest_snapshot)

        duration = time.time() - start
        hooks.emit(
            HookName.SCAN_COMPLETED,
            connections=filtered,
            new=new,
            closed=closed,
            duration=duration,
        )
        log.debug(
            "Scan complete: %d connections (%d new) in %.3fs",
            len(filtered),
            len(new),
            duration,
        )

    # -- Accessors ----------------------------------------------------------
    @property
    def latest_snapshot(self) -> dict | None:
        """The most recent insights snapshot as a dict, if available."""
        return self._latest_snapshot

    def refresh_geoip(self) -> None:
        """Reload the GeoIP reader after a database change."""
        self.resolver.reload()
