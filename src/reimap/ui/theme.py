"""Colour themes for the reimap UI.

Each palette is a flat mapping consumed by both the CSS (injected as variables)
and the Plotly map (marker/line colours). Five themes ship out of the box; the
``UI_MARKER_STYLED`` hook lets plugins override marker styling per point.
"""

from __future__ import annotations

# Each palette provides a consistent set of semantic colour roles.
THEME_PALETTES: dict[str, dict[str, str]] = {
    "midnight": {
        "bg": "#0b1021",
        "panel": "#121a35",
        "panel_alt": "#1a2547",
        "text": "#e6ecff",
        "muted": "#8ea0d0",
        "accent": "#4f8cff",
        "accent2": "#00d3a7",
        "danger": "#ff5d73",
        "warning": "#ffb454",
        "land": "#1c2748",
        "ocean": "#0b1021",
        "marker_remote": "#4f8cff",
        "marker_new": "#00d3a7",
        "arc": "#4f8cff",
    },
    "aurora": {
        "bg": "#071b16",
        "panel": "#0c2a22",
        "panel_alt": "#123a2f",
        "text": "#e8fff6",
        "muted": "#7fd6b8",
        "accent": "#31e0a0",
        "accent2": "#7ce7ff",
        "danger": "#ff6b9d",
        "warning": "#ffd166",
        "land": "#123a2f",
        "ocean": "#071b16",
        "marker_remote": "#31e0a0",
        "marker_new": "#7ce7ff",
        "arc": "#31e0a0",
    },
    "carbon": {
        "bg": "#101114",
        "panel": "#191b20",
        "panel_alt": "#23262d",
        "text": "#f2f3f5",
        "muted": "#9aa0aa",
        "accent": "#e0662a",
        "accent2": "#ffd166",
        "danger": "#ff5252",
        "warning": "#ffb454",
        "land": "#23262d",
        "ocean": "#101114",
        "marker_remote": "#e0662a",
        "marker_new": "#ffd166",
        "arc": "#e0662a",
    },
    "daylight": {
        "bg": "#f5f7fb",
        "panel": "#ffffff",
        "panel_alt": "#eef2f9",
        "text": "#16203a",
        "muted": "#5a6b8c",
        "accent": "#2563eb",
        "accent2": "#0d9488",
        "danger": "#dc2626",
        "warning": "#d97706",
        "land": "#dbe4f0",
        "ocean": "#f5f7fb",
        "marker_remote": "#2563eb",
        "marker_new": "#0d9488",
        "arc": "#2563eb",
    },
    "terminal": {
        "bg": "#000000",
        "panel": "#0a0f0a",
        "panel_alt": "#0f1a0f",
        "text": "#33ff66",
        "muted": "#1f9e3f",
        "accent": "#33ff66",
        "accent2": "#7CFC00",
        "danger": "#ff3333",
        "warning": "#ffcc00",
        "land": "#0f1a0f",
        "ocean": "#000000",
        "marker_remote": "#33ff66",
        "marker_new": "#7CFC00",
        "arc": "#33ff66",
    },
}


def get_palette(theme: str) -> dict[str, str]:
    """Return the palette for ``theme``, falling back to midnight."""
    return THEME_PALETTES.get(theme, THEME_PALETTES["midnight"])
