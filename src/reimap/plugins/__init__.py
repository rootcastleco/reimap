"""Plugin loading for reimap.

A *plugin* is any Python module exposing a ``register(hooks, runtime)`` callable.
Built-in plugins live in this package; user plugins are discovered from the
platform config directory (``<config>/plugins/*.py``). The plugin manager wires
each enabled plugin to the shared hook registry.

Because every extension point in reimap is a hook, plugins never need to monkey
patch the core — they simply subscribe.
"""

from __future__ import annotations

from .manager import PluginInfo, PluginManager

__all__ = ["PluginInfo", "PluginManager"]
