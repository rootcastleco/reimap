"""Configuration management for reimap.

Configuration is a plain dataclass serialised to JSON under the platform config
directory. Unknown keys are ignored on load so that older config files remain
forward compatible.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field, fields
from typing import Any

from .app_dirs import config_file
from .logging_config import get_logger

log = get_logger("config")

# Available UI colour themes. See ``ui.theme`` for the palette definitions.
THEMES = ("midnight", "aurora", "carbon", "daylight", "terminal")


@dataclass
class Config:
    """User-tunable settings for a reimap session."""

    # Networking / scan loop
    scan_interval_seconds: float = 3.0
    resolve_hostnames: bool = False
    include_loopback: bool = False
    include_lan: bool = True

    # History / insights
    history_days: int = 30
    frequent_threshold: int = 5

    # GeoIP
    geoip_auto_update: bool = True
    geoip_account_id: str = ""
    geoip_license_key: str = ""

    # UI
    host: str = "127.0.0.1"
    port: int = 8050
    theme: str = "midnight"
    map_style: str = "natural_earth"
    show_arcs: bool = True
    show_heatmap: bool = False
    marker_size: int = 8
    auto_refresh_ms: int = 3000
    open_browser: bool = True

    # Plugins / hooks
    plugins_enabled: bool = True
    enabled_plugins: list[str] = field(default_factory=lambda: ["connection_logger"])

    def validate(self) -> None:
        """Clamp and correct out-of-range values in place."""
        self.scan_interval_seconds = max(0.5, float(self.scan_interval_seconds))
        self.history_days = max(1, int(self.history_days))
        self.frequent_threshold = max(1, int(self.frequent_threshold))
        self.port = int(self.port)
        self.marker_size = max(2, min(30, int(self.marker_size)))
        self.auto_refresh_ms = max(500, int(self.auto_refresh_ms))
        if self.theme not in THEMES:
            log.warning("Unknown theme %r, falling back to 'midnight'.", self.theme)
            self.theme = "midnight"

    @classmethod
    def load(cls) -> Config:
        """Load configuration from disk, or return defaults if none exists."""
        path = config_file()
        if not path.exists():
            log.info("No config file found; using defaults at %s", path)
            cfg = cls()
            cfg.save()
            return cfg

        try:
            raw: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            log.error("Failed to read config (%s); using defaults.", exc)
            return cls()

        known = {f.name for f in fields(cls)}
        filtered = {k: v for k, v in raw.items() if k in known}
        cfg = cls(**filtered)
        cfg.validate()
        return cfg

    def save(self) -> None:
        """Persist configuration to disk as pretty-printed JSON."""
        self.validate()
        path = config_file()
        try:
            path.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")
            log.debug("Saved config to %s", path)
        except OSError as exc:
            log.error("Failed to save config: %s", exc)
