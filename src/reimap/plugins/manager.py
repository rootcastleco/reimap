"""Discover, load and register plugins."""

from __future__ import annotations

import importlib
import importlib.util
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING

from ..app_dirs import plugins_dir
from ..hooks import HookRegistry
from ..logging_config import get_logger

if TYPE_CHECKING:
    from ..runtime import Runtime

log = get_logger("plugins")

# Built-in plugins shipped inside this package, keyed by their public id.
_BUILTINS = {
    "connection_logger": "reimap.plugins.builtin.connection_logger",
    "new_endpoint_alerts": "reimap.plugins.builtin.new_endpoint_alerts",
    "private_ip_filter": "reimap.plugins.builtin.private_ip_filter",
    "geo_enricher": "reimap.plugins.builtin.geo_enricher",
    "jsonl_exporter": "reimap.plugins.builtin.jsonl_exporter",
}


@dataclass
class PluginInfo:
    """Metadata describing a loaded plugin."""

    plugin_id: str
    source: str
    loaded: bool
    error: str = ""


class PluginManager:
    """Load and register built-in and user plugins against the hook registry."""

    def __init__(self, hooks: HookRegistry, runtime: Runtime) -> None:
        self._hooks = hooks
        self._runtime = runtime
        self._loaded: list[PluginInfo] = []

    @property
    def loaded(self) -> list[PluginInfo]:
        """Return metadata for every plugin load attempt."""
        return list(self._loaded)

    def load_enabled(self, enabled: list[str]) -> None:
        """Load and register the given built-in plugin ids plus user plugins.

        Args:
            enabled: Built-in plugin ids to activate (order preserved).
        """
        for plugin_id in enabled:
            target = _BUILTINS.get(plugin_id)
            if target is None:
                log.warning("Unknown built-in plugin %r; skipping.", plugin_id)
                self._loaded.append(PluginInfo(plugin_id, "builtin", False, "unknown id"))
                continue
            self._load_module(plugin_id, "builtin", lambda t=target: importlib.import_module(t))

        self._load_user_plugins()

    def _load_user_plugins(self) -> None:
        directory: Path = plugins_dir()
        for path in sorted(directory.glob("*.py")):
            if path.name.startswith("_"):
                continue
            self._load_module(path.stem, str(path), lambda p=path: _import_from_path(p))

    def _load_module(self, plugin_id: str, source: str, importer) -> None:
        try:
            module: ModuleType = importer()
            register = getattr(module, "register", None)
            if not callable(register):
                raise AttributeError("plugin has no callable 'register(hooks, runtime)'")
            register(self._hooks, self._runtime)
            self._loaded.append(PluginInfo(plugin_id, source, True))
            log.info("Loaded plugin %s (%s)", plugin_id, source)
        except Exception as exc:
            log.exception("Failed to load plugin %s", plugin_id)
            self._loaded.append(PluginInfo(plugin_id, source, False, str(exc)))


def _import_from_path(path: Path) -> ModuleType:
    """Import a standalone module file by absolute path."""
    spec = importlib.util.spec_from_file_location(f"reimap_user_plugin_{path.stem}", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot import plugin from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
