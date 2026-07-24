"""Built-in plugin: raise console alerts for brand-new remote endpoints.

Demonstrates combining an event hook with runtime state (the history store) to
make a decision.
"""

from __future__ import annotations

from ...logging_config import get_logger

log = get_logger("plugin.new_endpoint_alerts")


def register(hooks, runtime) -> None:
    """Alert when a remote endpoint in a not-yet-seen country appears."""
    from ...hooks import HookName
    from ...model import ConnectionKind

    seen_countries: set[str] = set()

    @hooks.on(HookName.GEOIP_RESOLVED, name="new_endpoint_alerts", priority=80)
    def _on_resolved(ctx) -> None:
        conn = ctx["connection"]
        loc = ctx["location"]
        if conn.kind is not ConnectionKind.REMOTE or not loc.country:
            return
        if loc.country not in seen_countries:
            seen_countries.add(loc.country)
            log.warning(
                "First connection to %s detected: %s via %s",
                loc.country,
                conn.endpoint_label(),
                conn.process or "?",
            )
