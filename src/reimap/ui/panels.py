"""Side-panel content builders for the reimap UI.

Each function returns a Dash component tree for one panel. Panels are shown one at
a time in the drawer on the right. Plugins can contribute additional panels via
the ``UI_PANEL_REGISTER`` filter hook.
"""

from __future__ import annotations

import datetime as _dt

from dash import dcc, html

from ..hooks import HookName, hooks
from ..insights import InsightsEngine
from ..state import HistoryStore, LiveStore


def _fmt_ts(ts: float) -> str:
    if not ts:
        return "—"
    return _dt.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")


def _kv(label: str, value) -> html.Div:
    return html.Div(
        className="ri-kv",
        children=[html.Span(label, className="ri-kv-label"), html.Span(str(value), className="ri-kv-value")],
    )


def _table(headers: list[str], rows: list[list]) -> html.Table:
    return html.Table(
        className="ri-table",
        children=[
            html.Thead(html.Tr([html.Th(h) for h in headers])),
            html.Tbody([html.Tr([html.Td(str(c)) for c in row]) for row in rows]),
        ],
    )


def insights_panel(engine: InsightsEngine) -> html.Div:
    """Panel: the live insights snapshot."""
    snap = engine.compute()
    country_rows = [[name, hits] for name, hits in snap.top_countries]
    proc_rows = [[name, hits] for name, hits in snap.top_processes]
    freq_rows = [
        [f["ip"], f["hits"], f.get("country", ""), ", ".join(f.get("processes", [])[:3])]
        for f in snap.frequent_endpoints[:12]
    ]
    return html.Div(
        [
            html.H3("Insights"),
            _kv("Total connections", snap.total_connections),
            _kv("Mapped", snap.mapped_connections),
            _kv("Unmapped", snap.unmapped_count),
            _kv("Listening ports", snap.listening_count),
            _kv("New endpoints", len(snap.new_endpoints)),
            html.H4("Top countries"),
            _table(["Country", "Conns"], country_rows) if country_rows else html.P("No geo data yet."),
            html.H4("Top applications"),
            _table(["Process", "Conns"], proc_rows) if proc_rows else html.P("No process data."),
            html.H4("Frequent endpoints"),
            _table(["IP", "Hits", "Country", "Apps"], freq_rows)
            if freq_rows
            else html.P("Nothing frequent yet."),
        ]
    )


def unmapped_panel(store: LiveStore) -> html.Div:
    """Panel: remote connections without a geolocation."""
    rows = [
        [c.endpoint_label(), c.protocol.upper(), c.status or "—", c.process or "—"]
        for c in store.unmapped()[:200]
    ]
    return html.Div(
        [
            html.H3("Unmapped services"),
            html.P("Remote endpoints that could not be located (missing GeoIP data or new/reserved ranges)."),
            _table(["Endpoint", "Proto", "Status", "Process"], rows)
            if rows
            else html.P("Everything is mapped 🎉"),
        ]
    )


def lan_panel(store: LiveStore) -> html.Div:
    """Panel: LAN and loopback services."""
    from ..model import ConnectionKind

    conns = store.by_kind(ConnectionKind.LAN) + store.by_kind(ConnectionKind.LOCAL)
    rows = [
        [c.endpoint_label(), c.kind.value.upper(), c.protocol.upper(), c.process or "—"]
        for c in conns[:200]
    ]
    return html.Div(
        [
            html.H3("LAN / Local services"),
            _table(["Endpoint", "Kind", "Proto", "Process"], rows) if rows else html.P("No LAN/local sockets."),
        ]
    )


def ports_panel(store: LiveStore) -> html.Div:
    """Panel: listening TCP and bound UDP ports."""
    rows = [
        [c.local_port, c.protocol.upper(), c.remote_ip, c.process or "—", c.pid or "—"]
        for c in sorted(store.listening_ports(), key=lambda c: c.local_port)[:300]
    ]
    return html.Div(
        [
            html.H3("Open ports"),
            html.P("Local sockets currently listening or bound."),
            _table(["Port", "Proto", "Bind", "Process", "PID"], rows)
            if rows
            else html.P("No listening sockets."),
        ]
    )


def daily_report_panel(engine: InsightsEngine) -> html.Div:
    """Panel: the rolling daily report."""
    report = engine.daily_report()
    country_rows = [[name, hits] for name, hits in report["countries"]]
    app_rows = [[name, hits] for name, hits in report["top_applications"]]
    busy_rows = [[e["ip"], e["hits"], e["country"]] for e in report["busiest_endpoints"]]
    return html.Div(
        [
            html.H3("Daily report"),
            _kv("Generated", _fmt_ts(report["generated_at"])),
            _kv("Distinct endpoints", report["distinct_endpoints"]),
            _kv("Total observations", report["total_hits"]),
            html.H4("Country activity"),
            _table(["Country", "Hits"], country_rows) if country_rows else html.P("No data."),
            html.H4("Application activity"),
            _table(["Process", "Hits"], app_rows) if app_rows else html.P("No data."),
            html.H4("Busiest endpoints"),
            _table(["IP", "Hits", "Country"], busy_rows) if busy_rows else html.P("No data."),
        ]
    )


def history_panel(history: HistoryStore) -> html.Div:
    """Panel: full rolling history browser."""
    entries = sorted(history.all_entries(), key=lambda e: e.last_seen, reverse=True)[:300]
    rows = [
        [e.ip, e.country or "—", e.hits, _fmt_ts(e.first_seen), _fmt_ts(e.last_seen)]
        for e in entries
    ]
    return html.Div(
        [
            html.H3(f"History ({history.retention_days}-day window)"),
            _table(["IP", "Country", "Hits", "First", "Last"], rows)
            if rows
            else html.P("History is empty."),
        ]
    )


def plugins_panel(plugin_infos) -> html.Div:
    """Panel: loaded plugins and every hook subscription."""
    plugin_rows = [
        [p.plugin_id, p.source, "✓" if p.loaded else "✗", p.error or ""] for p in plugin_infos
    ]
    hook_rows = [[hook, ", ".join(subs)] for hook, subs in sorted(hooks.describe().items())]
    return html.Div(
        [
            html.H3("Plugins & Hooks"),
            html.H4("Loaded plugins"),
            _table(["Plugin", "Source", "OK", "Error"], plugin_rows)
            if plugin_rows
            else html.P("No plugins loaded."),
            html.H4(f"Active hook subscriptions ({hooks.count()})"),
            _table(["Hook", "Subscribers"], hook_rows)
            if hook_rows
            else html.P("No hook subscribers."),
            html.H4("All available hooks"),
            html.Ul([html.Li(html.Code(name)) for name in HookName.all_names()]),
        ]
    )


def geoip_panel(status: dict) -> html.Div:
    """Panel: GeoIP database status and installation guidance."""
    installed = status.get("installed")
    return html.Div(
        [
            html.H3("GeoIP database"),
            _kv("Installed", "Yes" if installed else "No"),
            _kv("Path", status.get("path") or "—"),
            _kv("Size (MB)", status.get("size_mb", 0.0)),
            html.H4("How to install"),
            html.Ol(
                [
                    html.Li("Create a free MaxMind account and generate a licence key."),
                    html.Li("Add the key in Settings, then press ‘Update GeoIP’."),
                    html.Li("Alternatively, drop a GeoLite2-City.mmdb file into the cache dir."),
                ]
            ),
            html.P("reimap never bundles GeoIP data and never phones home."),
        ]
    )


def settings_panel(config) -> html.Div:
    """Panel: editable runtime settings."""
    from .theme import THEME_PALETTES

    return html.Div(
        [
            html.H3("Settings"),
            html.Label("Theme"),
            dcc.Dropdown(
                id="ri-setting-theme",
                options=[{"label": t.title(), "value": t} for t in THEME_PALETTES],
                value=config.theme,
                clearable=False,
                className="ri-dropdown",
            ),
            html.Label("Map projection"),
            dcc.Dropdown(
                id="ri-setting-projection",
                options=[
                    {"label": p.replace("_", " ").title(), "value": p}
                    for p in ("natural_earth", "orthographic", "equirectangular", "mercator", "robinson")
                ],
                value=config.map_style,
                clearable=False,
                className="ri-dropdown",
            ),
            html.Label("Marker size"),
            dcc.Slider(id="ri-setting-marker", min=4, max=20, step=1, value=config.marker_size),
            html.Div(
                className="ri-toggle-row",
                children=[
                    dcc.Checklist(
                        id="ri-setting-toggles",
                        options=[
                            {"label": " Show density halo", "value": "heatmap"},
                            {"label": " Highlight new endpoints", "value": "highlight"},
                        ],
                        value=(["heatmap"] if config.show_heatmap else []) + ["highlight"],
                    )
                ],
            ),
            html.Label("MaxMind licence key"),
            dcc.Input(
                id="ri-setting-geoip-key",
                type="password",
                placeholder="paste key, then Update GeoIP",
                value=config.geoip_license_key,
                className="ri-input",
            ),
            html.Button("Update GeoIP", id="ri-update-geoip", className="ri-btn"),
            html.Button("Save settings", id="ri-save-settings", className="ri-btn ri-btn-primary"),
            html.Div(id="ri-settings-status", className="ri-status-line"),
        ]
    )


def about_panel() -> html.Div:
    """Panel: about, credits and branding."""
    from .. import __version__

    return html.Div(
        [
            html.H3("About reimap"),
            html.P(f"Version {__version__}"),
            html.P(
                "reimap watches the connections your machine makes and paints them "
                "onto a live world map — entirely on-device, with no telemetry."
            ),
            html.H4("Built by"),
            html.P(
                [
                    "Batuhan Ayrıbaş — ",
                    html.A("batuhanayribas.com", href="https://batuhanayribas.com", target="_blank"),
                ]
            ),
            html.P(
                [
                    "A ",
                    html.A("Rootcastle", href="https://rootcastle.com", target="_blank"),
                    " project.",
                ]
            ),
            html.H4("Standards & compliance"),
            html.Ul(
                [
                    html.Li("Documented to a tailored MIL-STD-498 set (SRS, SDD, STD, SVD, SDP, RTM)."),
                    html.Li("Coded to an adapted NASA/JPL 'Power of 10' safety-critical standard."),
                    html.Li("Fail-soft: no plugin or hook can crash a scan or the server."),
                    html.Li("Verified by an automated test suite on Python 3.10–3.12 in CI."),
                ]
            ),
            html.H4("Runs on"),
            html.P("Windows · macOS · Linux · Android — plus a fully offline demo."),
            html.P("Licensed under the MIT License."),
        ]
    )


def extra_panels() -> list[dict]:
    """Return plugin-contributed panel specs via the UI_PANEL_REGISTER hook."""
    result = hooks.filter(HookName.UI_PANEL_REGISTER, [])
    return result if isinstance(result, list) else []
