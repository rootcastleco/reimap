"""Server-side Dash callbacks for reimap.

Wires the polling intervals, menu buttons and settings controls to the runtime.
The callbacks read exclusively from the thread-safe stores on :class:`Runtime`,
so they never block the background scan loop.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from dash import ALL, Input, Output, State, callback_context, html, no_update

from ..logging_config import get_logger
from . import panels
from .layout import _stat_children
from .map_view import build_map_figure

if TYPE_CHECKING:
    from ..plugins import PluginManager
    from ..runtime import Runtime

log = get_logger("ui.callbacks")


def register_callbacks(app, runtime: Runtime, plugin_manager: PluginManager) -> None:
    """Register every server-side callback against ``app``."""

    # -- Map refresh --------------------------------------------------------
    @app.callback(
        Output("ri-map", "figure"),
        Output("ri-stats", "children"),
        Input("ri-tick", "n_intervals"),
        State("ri-focus-country", "data"),
    )
    def _refresh_map(_n, focus_country):
        connections = runtime.store.all()
        snapshot = runtime.latest_snapshot or {}
        highlight = set(snapshot.get("new_endpoints", []))
        figure = build_map_figure(
            connections,
            runtime.config,
            highlight_new=highlight,
            focus_country=focus_country,
        )
        return figure, _stat_children(runtime.store.stats())

    # -- Panel selection (menu buttons) ------------------------------------
    @app.callback(
        Output("ri-active-panel", "data"),
        Input({"type": "ri-menu-btn", "panel": ALL}, "n_clicks"),
        Input("ri-drawer-close", "n_clicks"),
        State("ri-active-panel", "data"),
        prevent_initial_call=True,
    )
    def _select_panel(_btn_clicks, _close_clicks, active):
        trigger = callback_context.triggered_id
        if trigger == "ri-drawer-close":
            return None
        if isinstance(trigger, dict) and trigger.get("type") == "ri-menu-btn":
            panel = trigger["panel"]
            return None if panel == active else panel
        return no_update

    # -- Drawer render ------------------------------------------------------
    @app.callback(
        Output("ri-drawer", "className"),
        Output("ri-panel-content", "children"),
        Input("ri-active-panel", "data"),
        Input("ri-panel-tick", "n_intervals"),
        State("ri-active-panel", "data"),
    )
    def _render_panel(active, _tick, active_state):
        panel = active if callback_context.triggered_id == "ri-active-panel" else active_state
        if not panel:
            return "ri-drawer", no_update
        content = _build_panel(panel, runtime, plugin_manager)
        return "ri-drawer open", content

    # -- Settings: save -----------------------------------------------------
    @app.callback(
        Output("ri-settings-status", "children"),
        Input("ri-save-settings", "n_clicks"),
        State("ri-setting-theme", "value"),
        State("ri-setting-projection", "value"),
        State("ri-setting-marker", "value"),
        State("ri-setting-toggles", "value"),
        prevent_initial_call=True,
    )
    def _save_settings(_n, theme, projection, marker, toggles):
        cfg = runtime.config
        cfg.theme = theme or cfg.theme
        cfg.map_style = projection or cfg.map_style
        cfg.marker_size = int(marker or cfg.marker_size)
        toggles = toggles or []
        cfg.show_heatmap = "heatmap" in toggles
        cfg.save()
        log.info("Settings updated via UI")
        return "Saved. Reload the page to apply the theme."

    # -- Settings: update GeoIP --------------------------------------------
    @app.callback(
        Output("ri-settings-status", "children", allow_duplicate=True),
        Input("ri-update-geoip", "n_clicks"),
        State("ri-setting-geoip-key", "value"),
        prevent_initial_call=True,
    )
    def _update_geoip(_n, key):
        if not key:
            return "Enter a MaxMind licence key first."
        runtime.config.geoip_license_key = key
        runtime.config.save()
        try:
            runtime.geoip_db.download(runtime.config.geoip_account_id, key)
            runtime.refresh_geoip()
            return "GeoIP database updated ✓"
        except RuntimeError as exc:
            return f"GeoIP update failed: {exc}"


def _build_panel(panel: str, runtime: Runtime, plugin_manager: PluginManager):
    """Dispatch to the correct panel builder."""
    if panel == "insights":
        return panels.insights_panel(runtime.insights)
    if panel == "unmapped":
        return panels.unmapped_panel(runtime.store)
    if panel == "lan":
        return panels.lan_panel(runtime.store)
    if panel == "ports":
        return panels.ports_panel(runtime.store)
    if panel == "report":
        return panels.daily_report_panel(runtime.insights)
    if panel == "history":
        return panels.history_panel(runtime.history)
    if panel == "plugins":
        return panels.plugins_panel(plugin_manager.loaded)
    if panel == "geoip":
        return panels.geoip_panel(runtime.geoip_db.status())
    if panel == "settings":
        return panels.settings_panel(runtime.config)
    if panel == "about":
        return panels.about_panel()

    # Plugin-contributed panels: {"id", "title", "render": callable}
    for spec in panels.extra_panels():
        if spec.get("id") == panel and callable(spec.get("render")):
            return spec["render"](runtime)

    return html.Div(html.P(f"Unknown panel: {panel}"))
