"""Assemble the top-level Dash layout.

The layout is a full-viewport map with a translucent top status bar, a left menu
rail of panel buttons, a right drawer that hosts the active panel, and a hidden
keyboard listener. The base layout fires ``UI_LAYOUT_BUILT`` so plugins can inject
banners or extra chrome.
"""

from __future__ import annotations

from dash import dcc, html

from ..config import Config
from ..hooks import HookName, hooks
from .theme import get_palette

# Menu rail: (panel id, glyph, label, keyboard key).
MENU_ITEMS = [
    ("insights", "◎", "Insights", "i"),
    ("unmapped", "◇", "Unmapped", "u"),
    ("lan", "⌂", "LAN / Local", "l"),
    ("ports", "❖", "Open ports", "o"),
    ("report", "▤", "Daily report", "d"),
    ("history", "⏱", "History", "h"),
    ("plugins", "⚡", "Plugins & Hooks", "p"),
    ("geoip", "◈", "GeoIP", "g"),
    ("settings", "⚙", "Settings", "s"),
    ("about", "★", "About", "a"),
]


def _css(palette: dict[str, str]) -> str:
    """Return the injected stylesheet with theme variables substituted."""
    variables = "\n".join(f"  --ri-{k}: {v};" for k, v in palette.items())
    return f""":root {{
{variables}
}}
* {{ box-sizing: border-box; }}
html, body, #react-entry-point, #_dash-app-content {{ height: 100%; margin: 0; }}
body {{
  background: var(--ri-bg);
  color: var(--ri-text);
  font-family: 'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif;
  overflow: hidden;
}}
#ri-root {{ position: fixed; inset: 0; }}
#ri-map {{ position: absolute; inset: 0; }}
.ri-topbar {{
  position: absolute; top: 0; left: 0; right: 0; height: 48px; z-index: 20;
  display: flex; align-items: center; gap: 18px; padding: 0 16px;
  background: linear-gradient(180deg, rgba(0,0,0,0.55), rgba(0,0,0,0));
  pointer-events: none;
}}
.ri-brand {{ font-weight: 700; letter-spacing: 0.5px; pointer-events: auto; }}
.ri-brand span {{ color: var(--ri-accent); }}
.ri-stats {{ display: flex; gap: 14px; font-size: 13px; color: var(--ri-muted); pointer-events: auto; }}
.ri-stat b {{ color: var(--ri-text); }}
.ri-menu {{
  position: absolute; top: 64px; left: 12px; z-index: 20;
  display: flex; flex-direction: column; gap: 6px;
}}
.ri-menu button {{
  width: 44px; height: 44px; border-radius: 12px; border: 1px solid var(--ri-panel_alt);
  background: color-mix(in srgb, var(--ri-panel) 82%, transparent); color: var(--ri-text);
  font-size: 18px; cursor: pointer; transition: transform .12s, background .12s;
  backdrop-filter: blur(6px);
}}
.ri-menu button:hover {{ transform: translateX(3px); background: var(--ri-panel_alt); }}
.ri-menu button.active {{ border-color: var(--ri-accent); color: var(--ri-accent); }}
.ri-drawer {{
  position: absolute; top: 0; right: 0; height: 100%; width: 420px; max-width: 92vw; z-index: 30;
  background: color-mix(in srgb, var(--ri-panel) 94%, transparent);
  border-left: 1px solid var(--ri-panel_alt); backdrop-filter: blur(10px);
  transform: translateX(100%); transition: transform .22s ease; overflow-y: auto; padding: 20px;
}}
.ri-drawer.open {{ transform: translateX(0); }}
.ri-drawer h3 {{ margin-top: 0; color: var(--ri-accent); }}
.ri-drawer h4 {{ margin: 18px 0 6px; color: var(--ri-accent2); font-size: 13px; text-transform: uppercase; letter-spacing: .5px; }}
.ri-close {{ position: sticky; top: 0; float: right; background: none; border: none; color: var(--ri-muted); font-size: 20px; cursor: pointer; }}
.ri-kv {{ display: flex; justify-content: space-between; padding: 4px 0; border-bottom: 1px solid var(--ri-panel_alt); font-size: 13px; }}
.ri-kv-label {{ color: var(--ri-muted); }}
.ri-table {{ width: 100%; border-collapse: collapse; font-size: 12px; margin-top: 6px; }}
.ri-table th {{ text-align: left; color: var(--ri-muted); border-bottom: 1px solid var(--ri-panel_alt); padding: 4px 6px; position: sticky; top: 0; }}
.ri-table td {{ padding: 4px 6px; border-bottom: 1px solid var(--ri-panel_alt); }}
.ri-table tr:hover td {{ background: var(--ri-panel_alt); }}
.ri-btn {{ margin: 10px 8px 0 0; padding: 8px 14px; border-radius: 10px; border: 1px solid var(--ri-panel_alt); background: var(--ri-panel_alt); color: var(--ri-text); cursor: pointer; }}
.ri-btn-primary {{ background: var(--ri-accent); border-color: var(--ri-accent); color: #fff; }}
.ri-input, .ri-dropdown {{ width: 100%; margin: 6px 0 12px; }}
.ri-input {{ padding: 8px; border-radius: 8px; border: 1px solid var(--ri-panel_alt); background: var(--ri-bg); color: var(--ri-text); }}
.ri-status-line {{ margin-top: 10px; font-size: 12px; color: var(--ri-accent2); min-height: 16px; }}
.ri-help {{
  position: absolute; bottom: 12px; left: 12px; z-index: 20; font-size: 11px; color: var(--ri-muted);
  background: color-mix(in srgb, var(--ri-panel) 80%, transparent); padding: 6px 10px; border-radius: 8px;
  backdrop-filter: blur(6px);
}}
.ri-footer {{
  position: absolute; bottom: 12px; right: 12px; z-index: 20; font-size: 11px; color: var(--ri-muted);
}}
.ri-footer a {{ color: var(--ri-accent); text-decoration: none; }}
label {{ font-size: 12px; color: var(--ri-muted); display: block; margin-top: 8px; }}
"""


def build_layout(config: Config, stats: dict) -> html.Div:
    """Build and return the root layout component."""
    palette = get_palette(config.theme)

    topbar = html.Div(
        className="ri-topbar",
        children=[
            html.Div(className="ri-brand", children=[html.Span("rei"), "map"]),
            html.Div(
                className="ri-stats",
                id="ri-stats",
                children=_stat_children(stats),
            ),
        ],
    )

    menu = html.Div(
        className="ri-menu",
        children=[
            html.Button(
                glyph,
                id={"type": "ri-menu-btn", "panel": panel},
                title=f"{label}  ({key.upper()})",
                n_clicks=0,
            )
            for panel, glyph, label, key in MENU_ITEMS
        ],
    )

    drawer = html.Div(
        id="ri-drawer",
        className="ri-drawer",
        children=[
            html.Button("×", id="ri-drawer-close", className="ri-close"),
            html.Div(id="ri-panel-content"),
        ],
    )

    help_hint = html.Div(
        className="ri-help",
        children="Shortcuts: " + "  ".join(f"{k.upper()}={label}" for _, _, label, k in MENU_ITEMS),
    )

    footer = html.Div(
        className="ri-footer",
        children=[
            html.A("batuhanayribas.com", href="https://batuhanayribas.com", target="_blank"),
            " · ",
            html.A("rootcastle.com", href="https://rootcastle.com", target="_blank"),
        ],
    )

    root = html.Div(
        id="ri-root",
        children=[
            dcc.Store(id="ri-active-panel", data=None),
            dcc.Store(id="ri-focus-country", data=None),
            dcc.Interval(id="ri-tick", interval=config.auto_refresh_ms, n_intervals=0),
            dcc.Interval(id="ri-panel-tick", interval=max(2000, config.auto_refresh_ms), n_intervals=0),
            html.Div(id="ri-keyboard", tabIndex="0"),
            dcc.Graph(
                id="ri-map",
                config={"scrollZoom": True, "displayModeBar": False, "responsive": True},
                style={"height": "100%", "width": "100%"},
            ),
            topbar,
            menu,
            drawer,
            help_hint,
            footer,
        ],
    )

    hooks.emit(HookName.UI_LAYOUT_BUILT, root=root, config=config)
    return html.Div([html.Style(_css(palette)), root])


def _stat_children(stats: dict) -> list:
    """Render the status-bar counters."""
    def stat(label: str, value) -> html.Span:
        return html.Span(className="ri-stat", children=[f"{label} ", html.B(str(value))])

    return [
        stat("Total", stats.get("total", 0)),
        stat("Mapped", stats.get("mapped", 0)),
        stat("Remote", stats.get("remote", 0)),
        stat("LAN", stats.get("lan", 0)),
        stat("Listening", stats.get("listening", 0)),
        stat("Scans", stats.get("scans", 0)),
    ]
