"""Build the Plotly world map figure from connections.

Renders remote endpoints as markers on a geographic projection, optionally with
great-circle arcs from the viewer's approximate location and a density heatmap.
The finished figure passes through the ``FILTER_MAP_FIGURE`` hook so plugins can
post-process it.
"""

from __future__ import annotations

from ..config import Config
from ..hooks import HookName, hooks
from ..model import Connection
from .theme import get_palette


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
        config: Active configuration (theme, arcs, heatmap, marker size).
        highlight_new: IPs to render in the "new" accent colour.
        focus_country: If given, zoom the projection toward that country.
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
        sizes.append(style.get("size", config.marker_size))
        symbols.append(style.get("symbol", "circle"))

    data: list[dict] = []

    if config.show_heatmap and lats:
        data.append(
            {
                "type": "densitymapbox" if False else "scattergeo",
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

    data.append(
        {
            "type": "scattergeo",
            "lat": lats,
            "lon": lons,
            "text": texts,
            "mode": "markers",
            "hoverinfo": "text",
            "marker": {
                "size": sizes or [config.marker_size],
                "color": colors or [palette["marker_remote"]],
                "symbol": symbols or ["circle"],
                "line": {"width": 0.5, "color": palette["bg"]},
                "opacity": 0.9,
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
        geo["scope"] = "world"
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
            "font": {"color": palette["text"]},
        },
    }

    filtered = hooks.filter(HookName.FILTER_MAP_FIGURE, figure, connections=mapped)
    return filtered if isinstance(filtered, dict) else figure
