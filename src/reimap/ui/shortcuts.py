"""Keyboard shortcut wiring for the reimap UI.

Registered as a Dash *clientside* callback so key presses never round-trip to the
server. Each mapped key toggles the corresponding panel by writing its id into the
``ri-active-panel`` store, which the server-side panel callback then renders.
"""

from __future__ import annotations

from dash import ClientsideFunction, Input, Output

from .layout import MENU_ITEMS

# key -> panel id
KEY_MAP = {key: panel for panel, _glyph, _label, key in MENU_ITEMS}

_CLIENTSIDE = """
function(_n) {
  if (!window.__reimapKeysBound) {
    window.__reimapKeysBound = true;
    window.__reimapPanel = null;
    const keyMap = %s;
    document.addEventListener('keydown', function(e) {
      const tag = (e.target && e.target.tagName) || '';
      if (tag === 'INPUT' || tag === 'TEXTAREA' || e.metaKey || e.ctrlKey || e.altKey) return;
      const k = e.key.toLowerCase();
      if (k === 'escape') { window.__reimapPanel = '__close__'; }
      else if (keyMap[k]) {
        window.__reimapPanel = (window.__reimapPanel === keyMap[k]) ? '__close__' : keyMap[k];
      } else { return; }
      // Nudge the interval-driven poll so the change is picked up immediately.
      window.dispatchEvent(new Event('reimap-key'));
    });
  }
  const p = window.__reimapPanel;
  window.__reimapPanel = null;
  if (p === '__close__') return null;
  return p === null ? window.dash_clientside.no_update : p;
}
"""


def register_shortcuts(app) -> None:
    """Attach the clientside keyboard handler to the app."""
    import json

    app.clientside_callback(
        _CLIENTSIDE % json.dumps(KEY_MAP),
        Output("ri-active-panel", "data", allow_duplicate=True),
        Input("ri-panel-tick", "n_intervals"),
        prevent_initial_call=True,
    )
    # Silence the unused import when Dash tree-shakes; ClientsideFunction kept for parity.
    _ = ClientsideFunction
