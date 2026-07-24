"""Built-in plugin: annotate resolved locations with a hemisphere tag.

Demonstrates a *filter*-style enrichment via the ``ui.marker_styled`` hook, and
observing ``geoip.resolved`` to keep a running tally exposed on ``runtime``.
"""

from __future__ import annotations


def register(hooks, runtime) -> None:
    """Tally resolutions per hemisphere and tint markers by latitude."""
    from ...hooks import HookName

    tally = {"northern": 0, "southern": 0}
    runtime.__dict__.setdefault("hemisphere_tally", tally)

    @hooks.on(HookName.GEOIP_RESOLVED, name="geo_enricher.tally", priority=100)
    def _tally(ctx) -> None:
        loc = ctx["location"]
        key = "northern" if loc.latitude >= 0 else "southern"
        tally[key] += 1

    @hooks.on(HookName.UI_MARKER_STYLED, name="geo_enricher.tint", priority=100)
    def _tint(style, ctx):
        loc = ctx.get("location")
        if loc is not None and loc.latitude < 0:
            # Give southern-hemisphere markers a distinct symbol.
            style = {**style, "symbol": "diamond"}
        return style
