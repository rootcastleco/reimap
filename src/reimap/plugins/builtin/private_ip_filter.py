"""Built-in plugin: optionally hide LAN/local connections from the map.

Demonstrates a *filter* hook that can drop items from the pipeline by returning
``None``. Disabled by default; enable it to focus purely on internet traffic.
"""

from __future__ import annotations

from ...logging_config import get_logger

log = get_logger("plugin.private_ip_filter")


def register(hooks, runtime) -> None:
    """Drop LAN/local connections before they reach the map."""
    from ...hooks import HookName
    from ...model import ConnectionKind

    @hooks.on(HookName.FILTER_CONNECTION, name="private_ip_filter", priority=50)
    def _filter(conn, ctx):
        if conn.kind in (ConnectionKind.LAN, ConnectionKind.LOCAL):
            return None  # drop
        return conn
