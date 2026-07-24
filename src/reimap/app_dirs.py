"""Cross-platform application directories for reimap.

Thin wrapper around :mod:`platformdirs` so every module resolves the same paths
for configuration, cached GeoIP databases, persisted insights and log files.
"""

from __future__ import annotations

from pathlib import Path

from platformdirs import PlatformDirs

_APP_NAME = "reimap"
_APP_AUTHOR = "rootcastle"

_dirs = PlatformDirs(appname=_APP_NAME, appauthor=_APP_AUTHOR)


def _ensure(path: Path) -> Path:
    """Create ``path`` (and parents) if missing and return it."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def config_dir() -> Path:
    """Directory holding the user configuration file."""
    return _ensure(Path(_dirs.user_config_dir))


def data_dir() -> Path:
    """Directory holding persisted state and insights."""
    return _ensure(Path(_dirs.user_data_dir))


def cache_dir() -> Path:
    """Directory holding cached GeoIP databases and transient files."""
    return _ensure(Path(_dirs.user_cache_dir))


def log_dir() -> Path:
    """Directory holding rotating log files."""
    return _ensure(Path(_dirs.user_log_dir))


def geoip_dir() -> Path:
    """Directory holding downloaded MaxMind GeoIP databases."""
    return _ensure(cache_dir() / "geoip")


def plugins_dir() -> Path:
    """Directory scanned for user-supplied plugin modules."""
    return _ensure(config_dir() / "plugins")


def config_file() -> Path:
    """Path to the JSON configuration file."""
    return config_dir() / "config.json"
