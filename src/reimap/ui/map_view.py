"""Build the Plotly world map figure from connections.

Renders remote endpoints as markers on a geographic projection, with animated
great-circle arcs radiating from a configurable "home" origin, an optional density
halo, and pulsing markers (the pulse itself is driven client-side — see
``ui.animation``). The finished figure passes through the ``FILTER_MAP_FIGURE`` hook
so plugins can post-process it.

Design note (NASA/JPL Power of 10, Rule 2 — bounded loops): every loop in this
module is bounded by an explicit, small constant (``_MAX_ARCS``, ``_ARC_POINTS``)
or by the finite connection set, so figure construction has a predictable upper
bound on work regardless of how many sockets are open.
"""

from __future__ import annotations

import math

from ..config import Config
from ..hooks import HookName, hooks
from ..model import Connection
from .theme import get_palette

# Bounded-work constants (Power of 10, Rule 2). Arcs are the most expensive part
# of the figure, so we cap how many we draw and how finely each is sampled.
_MAX_ARCS = 60
_ARC_POINTS = 24


def _great_circle(lat1: float, lon1: float, lat2: float, lon2: float, n: int) -> tuple[list, list]:
    """Return ``n`` points along the great circle between two coordinates.

    Uses spherical linear interpolation (slerp). ``n`` is bounded by the caller;
    the loop below therefore runs a fixed, small number of times.

    Args:
        lat1: Start latitude in degrees.
        lon1: Start longitude in degrees.
        lat2: End latitude in degrees.
        lon2: End longitude in degrees.
        n: Number of sample points (>= 2).

    Returns:
        A ``(lats, lons)`` tuple of ``n`` points, with ``None`` unused here.
    """
    assert n >= 2, "great circle needs at least two points"

    phi1, lam1 = math.radians(lat1), math.radians(lon1)
    phi2, lam2 = math.radians(lat2), math.radians(lon2)

    # Angular distance between the two points.
    d = 2 * math.asin(
        math.sqrt(
            math.sin((phi2 - phi1) / 2) ** 2
            + math.cos(phi1) * math.cos(phi2) * math.sin((lam2 - lam1) / 2) ** 2
        )
    )
    if d == 0:
        return [lat1, lat2], [lon1, lon2]

    lats: list[float] = []
    lons: list[float] = []
    for i in range(n):
        f = i / (n - 1)
        a = math.sin((1 - f) * d) / math.sin(d)
        b = math.sin(f * d) / math.sin(d)
        x = a * math.cos(phi1) * math.cos(lam1) + b * math.cos(phi2) * math.cos(lam2)
        y = a * math.cos(phi1) * math.sin(lam1) + b * math.cos(phi2) * math.sin(lam2)
        z = a * math.sin(phi1) + b * math.sin(phi2)
        lats.append(math.degrees(math.atan2(z, math.sqrt(x * x + y * y))))
        lons.append(math.degrees(math.atan2(y, x)))
    return lats, lons


def _hover_text(conn: Connection) -> str:
    loc = conn.location
    place = loc.label if loc else "Unknown"
    lines = [
        f"<b>{conn.endpoint_label()}</b>",
        f"{place}",
        f"Process: {conn.process or '—'}",
        f"Protocol: {conn.protocol.upper()}  Status: {conn.status or '—'}",
    ]
    return "<br>".join(lines)


def _arc_traces(mapped: list[Connection], config: Config, palette: dict) -> list[dict]:
    """Build up to ``_MAX_ARCS`` great-circle arc traces from home to endpoints."""
    if not config.show_arcs:
        return []
    traces: list[dict] = []
    # Bounded loop: at most _MAX_ARCS iterations (Rule 2).
    for conn in mapped[:_MAX_ARCS]:
        loc = conn.location
        if loc is None:
            continue
        lats, lons = _great_circle(
            config.home_lat, config.home_lon, loc.latitude, loc.longitude, _ARC_POINTS
        )
        traces.append(
            {
                "type": "scattergeo",
                "lat": lats,
                "lon": lons,
                "mode": "lines",
                "line": {"width": 1, "color": palette["arc"]},
                "opacity": 0.35,
                "hoverinfo": "skip",
                "showlegend": False,
                "name": "arc",
            }
        )
    return traces


def build_map_figure(
    connections: list[Connection],
    config: Config,
    *,
    highlight_new: set[str] | None = None,
    focus_country: str | None = None,
) -> dict:
    """Return a Plotly figure dict for the given connections.

    Args:
        connections: Connections to plot (only mapped ones are drawn).
        config: Active configuration (theme, arcs, heatmap, marker size, home).
        highlight_new: IPs to render in the "new" accent colour.
        focus_country: If given, switch to an orthographic projection.
    """
    palette = get_palette(config.theme)
    highlight_new = highlight_new or set()
    mapped = [c for c in connections if c.is_mapped]

    lats: list[float] = []
    lons: list[float] = []
    texts: list[str] = []
    colors: list[str] = []
    sizes: list[int] = []
    symbols: list[str] = []

    # Bounded by the finite connection set (Rule 2).
    for conn in mapped:
        loc = conn.location
        assert loc is not None
        is_new = conn.remote_ip in highlight_new
        style = {
            "color": palette["marker_new"] if is_new else palette["marker_remote"],
            "size": config.marker_size + (3 if is_new else 0),
            "symbol": "circle",
        }
        style = hooks.filter(HookName.UI_MARKER_STYLED, style, connection=conn, location=loc)
        if style is None:
            continue
        lats.append(loc.latitude)
        lons.append(loc.longitude)
        texts.append(_hover_text(conn))
        colors.append(style.get("color", palette["marker_remote"]))
        sizes.append(int(style.get("size", config.marker_size)))
        symbols.append(style.get("symbol", "circle"))

    data: list[dict] = []

    # Arcs first so they render beneath the markers.
    data.extend(_arc_traces(mapped, config, palette))

    # Optional density halo.
    if config.show_heatmap and lats:
        data.append(
            {
                "type": "scattergeo",
                "lat": lats,
                "lon": lons,
                "mode": "markers",
                "marker": {
                    "size": max(20, config.marker_size * 3),
                    "color": palette["accent"],
                    "opacity": 0.06,
                },
                "hoverinfo": "skip",
                "showlegend": False,
                "name": "density",
            }
        )

    # Home origin marker.
    if config.show_home:
        data.append(
            {
                "type": "scattergeo",
                "lat": [config.home_lat],
                "lon": [config.home_lon],
                "text": ["<b>This machine</b>"],
                "mode": "markers",
                "hoverinfo": "text",
                "marker": {
                    "size": config.marker_size + 6,
                    "color": palette["accent2"],
                    "symbol": "star",
                    "line": {"width": 1, "color": palette["text"]},
                },
                "name": "home",
                "showlegend": False,
            }
        )

    # The connection markers. ``customdata`` carries the base size so the
    # client-side pulse animation can modulate around it without drift.
    data.append(
        {
            "type": "scattergeo",
            "lat": lats,
            "lon": lons,
            "text": texts,
            "customdata": sizes or [config.marker_size],
            "mode": "markers",
            "hoverinfo": "text",
            "marker": {
                "size": sizes or [config.marker_size],
                "color": colors or [palette["marker_remote"]],
                "symbol": symbols or ["circle"],
                "line": {"width": 0.5, "color": palette["bg"]},
                "opacity": 0.92,
            },
            "name": "connections",
        }
    )

    geo = {
        "showland": True,
        "landcolor": palette["land"],
        "showocean": True,
        "oceancolor": palette["ocean"],
        "showcountries": True,
        "countrycolor": palette["panel_alt"],
        "coastlinecolor": palette["panel_alt"],
        "showframe": False,
        "projection": {"type": config.map_style},
        "bgcolor": "rgba(0,0,0,0)",
    }
    if focus_country:
        geo["projection"] = {"type": "orthographic"}

    figure = {
        "data": data,
        "layout": {
            "geo": geo,
            "margin": {"l": 0, "r": 0, "t": 0, "b": 0},
            "paper_bgcolor": "rgba(0,0,0,0)",
            "plot_bgcolor": "rgba(0,0,0,0)",
            "showlegend": False,
            "uirevision": "reimap-map",
            "transition": {"duration": 400, "easing": "cubic-in-out"},
            "font": {"color": palette["text"]},
        },
    }

    filtered = hooks.filter(HookName.FILTER_MAP_FIGURE, figure, connections=mapped)
    return filtered if isinstance(filtered, dict) else figure
