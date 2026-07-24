"""Built-in plugin: log every newly discovered endpoint.

Demonstrates the simplest hook usage — subscribing to an *event* hook.
"""

from __future__ import annotations

from ...logging_config import get_logger

log = get_logger("plugin.connection_logger")


def register(hooks, runtime) -> None:
    """Subscribe to ``connection.new`` and log each first-seen endpoint."""
    from ...hooks import HookName

    @hooks.on(HookName.CONNECTION_NEW, name="connection_logger", priority=90)
    def _on_new(ctx) -> None:
        conn = ctx["connection"]
        where = conn.location.label if conn.location else "unmapped"
        log.info("New endpoint %s (%s) via %s", conn.endpoint_label(), where, conn.process or "?")
