"""reimap extensibility hook system.

This module is the heart of what makes reimap extensible. Every meaningful moment
in the application lifecycle is published as a *hook*. Plugins, integrations and
user scripts subscribe to those hooks and run arbitrary code — logging, alerting,
enrichment, export, filtering — without touching the core.

Design goals
------------
* **Discoverable** — hooks are declared up front in :class:`HookName`, so tooling
  and documentation can enumerate every extension point.
* **Ordered** — callbacks carry a numeric priority; lower runs first.
* **Isolated** — a raising callback is logged and skipped; it never breaks a scan.
* **Composable** — *filter* hooks let subscribers transform the value that flows
  through them (e.g. drop or rewrite a connection before it is mapped).
* **Introspectable** — the registry can report who is subscribed to what.

Two flavours of hook
---------------------
1. **Event hooks** (:meth:`HookRegistry.emit`) — fire-and-observe. Every callback
   receives the same immutable context; return values are ignored.
2. **Filter hooks** (:meth:`HookRegistry.filter`) — each callback receives the
   running value and returns a (possibly modified) replacement. Returning
   ``None`` from a filter drops the value entirely.

Example:
-------
>>> from reimap.hooks import hooks, HookName
>>> @hooks.on(HookName.CONNECTION_DISCOVERED)
... def announce(ctx):
...     print("saw", ctx["connection"].remote_ip)
>>> hooks.emit(HookName.CONNECTION_DISCOVERED, connection=conn)  # doctest: +SKIP
"""

from __future__ import annotations

import enum
import threading
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from .logging_config import get_logger

log = get_logger("hooks")


class HookName(str, enum.Enum):
    """The complete catalogue of reimap extension points.

    Grouped by lifecycle phase. New hooks should be added here first so they are
    self-documenting. The string value is the stable public identifier used in
    configuration and plugin manifests.
    """

    # --- Application lifecycle -------------------------------------------------
    APP_STARTING = "app.starting"
    """Emitted once before the Dash server and scan loop start."""
    APP_READY = "app.ready"
    """Emitted once the server is bound and ready to serve requests."""
    APP_STOPPING = "app.stopping"
    """Emitted during graceful shutdown."""
    CONFIG_LOADED = "config.loaded"
    """Emitted after configuration is read; ctx carries ``config``."""

    # --- Scan loop -------------------------------------------------------------
    SCAN_STARTED = "scan.started"
    """Emitted at the top of every scan cycle."""
    SCAN_COMPLETED = "scan.completed"
    """Emitted after a scan cycle; ctx carries ``connections`` and ``duration``."""
    SCAN_FAILED = "scan.failed"
    """Emitted when a scan cycle raises; ctx carries ``error``."""

    # --- Per-connection --------------------------------------------------------
    CONNECTION_DISCOVERED = "connection.discovered"
    """Event: a raw connection was observed this cycle. ctx carries ``connection``."""
    CONNECTION_NEW = "connection.new"
    """Event: a connection never seen before in history. ctx carries ``connection``."""
    CONNECTION_CLOSED = "connection.closed"
    """Event: a previously active connection is gone. ctx carries ``connection``."""

    # --- GeoIP -----------------------------------------------------------------
    GEOIP_RESOLVED = "geoip.resolved"
    """Event: an IP was located. ctx carries ``connection`` and ``location``."""
    GEOIP_UNRESOLVED = "geoip.unresolved"
    """Event: an IP could not be located. ctx carries ``connection``."""
    GEOIP_DB_UPDATED = "geoip.db_updated"
    """Event: a GeoIP database was downloaded/updated. ctx carries ``path``."""

    # --- Insights --------------------------------------------------------------
    INSIGHTS_UPDATED = "insights.updated"
    """Event: the insights snapshot was recomputed. ctx carries ``insights``."""
    DAILY_REPORT_GENERATED = "report.daily"
    """Event: a daily report was produced. ctx carries ``report``."""

    # --- UI --------------------------------------------------------------------
    UI_LAYOUT_BUILT = "ui.layout_built"
    """Event: the base layout was assembled (extension point for banners, etc.)."""
    UI_PANEL_REGISTER = "ui.panel_register"
    """Filter: contribute extra side panels. Value is a list of panel specs."""
    UI_MARKER_STYLED = "ui.marker_styled"
    """Filter: adjust a marker's visual style. Value is a style dict."""

    # --- Filter hooks (transform the value flowing through) --------------------
    FILTER_CONNECTION = "filter.connection"
    """Filter: accept/reject/rewrite a connection before mapping.

    Return ``None`` to drop it, or a (possibly modified) :class:`Connection`.
    """
    FILTER_MAP_FIGURE = "filter.map_figure"
    """Filter: post-process the Plotly figure dict before it is served."""
    FILTER_INSIGHTS = "filter.insights"
    """Filter: post-process the computed insights mapping before display."""

    @classmethod
    def all_names(cls) -> list[str]:
        """Return every hook's string identifier, sorted."""
        return sorted(member.value for member in cls)


# A hook context is a plain mutable mapping of keyword arguments.
HookContext = dict[str, Any]
Callback = Callable[..., Any]


@dataclass(order=True)
class _Subscription:
    """Internal record of one registered callback."""

    priority: int
    # ``order`` breaks ties so registration order is stable and comparison never
    # falls through to the callable (which is not orderable).
    order: int
    callback: Callback = None  # type: ignore[assignment]
    name: str = ""


class HookRegistry:
    """A thread-safe registry of hook subscriptions.

    A single global instance (:data:`hooks`) is shared by the whole application,
    but the class can also be instantiated for isolated testing.
    """

    def __init__(self) -> None:
        self._subs: dict[str, list[_Subscription]] = defaultdict(list)
        self._counter = 0
        self._lock = threading.RLock()

    # -- Registration -------------------------------------------------------
    def register(
        self,
        hook: HookName | str,
        callback: Callback,
        *,
        priority: int = 100,
        name: str | None = None,
    ) -> Callback:
        """Subscribe ``callback`` to ``hook``.

        Args:
            hook: The hook to subscribe to (enum member or its string value).
            callback: A callable invoked when the hook fires.
            priority: Lower numbers run earlier. Defaults to 100.
            name: Optional label used in diagnostics; defaults to the callable name.

        Returns:
            The same callback, so this can be used as a decorator factory.
        """
        key = self._key(hook)
        with self._lock:
            sub = _Subscription(
                priority=priority,
                order=self._counter,
                callback=callback,
                name=name or getattr(callback, "__name__", repr(callback)),
            )
            self._counter += 1
            bucket = self._subs[key]
            bucket.append(sub)
            bucket.sort()
        log.debug("Registered %s -> %s (priority=%d)", key, sub.name, priority)
        return callback

    def on(
        self,
        hook: HookName | str,
        *,
        priority: int = 100,
        name: str | None = None,
    ) -> Callable[[Callback], Callback]:
        """Decorator form of :meth:`register`.

        Example:
            >>> @hooks.on(HookName.SCAN_COMPLETED, priority=50)
            ... def log_scan(ctx):
            ...     ...
        """

        def decorator(callback: Callback) -> Callback:
            return self.register(hook, callback, priority=priority, name=name)

        return decorator

    def unregister(self, hook: HookName | str, callback: Callback) -> bool:
        """Remove a previously registered callback.

        Returns:
            ``True`` if a subscription was removed, ``False`` otherwise.
        """
        key = self._key(hook)
        with self._lock:
            bucket = self._subs.get(key, [])
            for i, sub in enumerate(bucket):
                if sub.callback is callback:
                    del bucket[i]
                    log.debug("Unregistered %s -> %s", key, sub.name)
                    return True
        return False

    def clear(self, hook: HookName | str | None = None) -> None:
        """Remove all subscriptions, optionally scoped to one hook."""
        with self._lock:
            if hook is None:
                self._subs.clear()
            else:
                self._subs.pop(self._key(hook), None)

    # -- Firing -------------------------------------------------------------
    def emit(self, hook: HookName | str, **context: Any) -> None:
        """Fire an *event* hook. Return values are ignored.

        Every subscriber receives the same context mapping. Exceptions are logged
        and swallowed so one misbehaving plugin cannot stop the scan loop.
        """
        key = self._key(hook)
        for sub in self._snapshot(key):
            try:
                sub.callback(context)
            except Exception:
                log.exception("Hook %s subscriber %s raised", key, sub.name)

    def filter(self, hook: HookName | str, value: Any, **context: Any) -> Any:
        """Fire a *filter* hook, threading ``value`` through each subscriber.

        Each callback is invoked as ``callback(value, context)`` and must return
        the (possibly modified) value. Returning ``None`` short-circuits and the
        filter yields ``None`` — the caller decides what that means (typically:
        drop the item).

        Args:
            hook: The filter hook to run.
            value: The initial value.
            context: Extra read-only context available to every subscriber.

        Returns:
            The value after passing through every subscriber (or ``None`` if a
            subscriber dropped it).
        """
        key = self._key(hook)
        current = value
        for sub in self._snapshot(key):
            try:
                current = sub.callback(current, context)
            except Exception:
                log.exception("Filter %s subscriber %s raised; keeping prior value", key, sub.name)
                continue
            if current is None:
                log.debug("Filter %s dropped value at %s", key, sub.name)
                return None
        return current

    # -- Introspection ------------------------------------------------------
    def subscribers(self, hook: HookName | str) -> list[str]:
        """Return the names of callbacks subscribed to ``hook`` in run order."""
        return [s.name for s in self._snapshot(self._key(hook))]

    def describe(self) -> dict[str, list[str]]:
        """Return a mapping of every hook with subscribers to their callbacks."""
        with self._lock:
            return {k: [s.name for s in sorted(v)] for k, v in self._subs.items() if v}

    def count(self) -> int:
        """Total number of active subscriptions across all hooks."""
        with self._lock:
            return sum(len(v) for v in self._subs.values())

    # -- Internals ----------------------------------------------------------
    def _snapshot(self, key: str) -> list[_Subscription]:
        with self._lock:
            return list(self._subs.get(key, ()))

    @staticmethod
    def _key(hook: HookName | str) -> str:
        return hook.value if isinstance(hook, HookName) else str(hook)


# The process-wide registry every module and plugin shares.
hooks = HookRegistry()

__all__ = ["HookContext", "HookName", "HookRegistry", "hooks"]
