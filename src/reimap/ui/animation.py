"""Client-side marker pulse animation for the reimap map.

The pulse runs entirely in the browser: a fast :class:`dcc.Interval` drives a
clientside callback that modulates the connection markers' size and opacity with a
phase-shifted sine wave, giving each endpoint a gentle "breathing" glow. Because it
never round-trips to the server, it is smooth and cheap even at a 90 ms cadence.

The base (unpulsed) sizes travel with the figure in the ``connections`` trace's
``customdata`` (see ``ui.map_view``), so the animation modulates around the true
sizes and never drifts as scans replace the figure.
"""

from __future__ import annotations

from dash import Input, Output

# Modulates marker.size around the per-point base carried in customdata, and the
# whole trace's opacity. Guards every access so it is a no-op until the map and
# its data exist. Never throws (Power of 10, Rule 7: check/So guard state).
_PULSE_JS = """
function(n) {
  var noup = window.dash_clientside.no_update;
  try {
    var gd = document.getElementById('ri-map');
    if (!gd || !gd.data || !window.Plotly) return noup;
    var idx = -1;
    for (var i = 0; i < gd.data.length; i++) {
      if (gd.data[i].name === 'connections') { idx = i; break; }
    }
    if (idx < 0) return noup;
    var base = gd.data[idx].customdata;
    if (!base || !base.length) return noup;
    var t = n * 0.18;
    var sizes = new Array(base.length);
    for (var j = 0; j < base.length; j++) {
      sizes[j] = base[j] * (1 + 0.28 * Math.sin(t + j * 0.55));
    }
    var opacity = 0.72 + 0.22 * Math.sin(t);
    window.Plotly.restyle(gd, {'marker.size': [sizes], 'marker.opacity': opacity}, [idx]);
  } catch (e) { /* never break the UI over an animation frame */ }
  return noup;
}
"""


def register_animation(app) -> None:
    """Attach the clientside pulse callback to ``app``."""
    app.clientside_callback(
        _PULSE_JS,
        Output("ri-anim-sink", "data"),
        Input("ri-anim", "n_intervals"),
        prevent_initial_call=True,
    )
