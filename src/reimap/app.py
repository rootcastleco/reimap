"""reimap application assembly and CLI entry point.

Wires configuration, runtime, plugins and the Dash UI into a single application
and exposes the ``reimap`` console command.
"""

from __future__ import annotations

import argparse
import contextlib
import logging
import sys
import webbrowser

from . import __homepage__, __organization_url__, __version__
from .config import Config
from .hooks import HookName, hooks
from .logging_config import configure_logging, get_logger
from .runtime import Runtime

log = get_logger("app")


def create_app(config: Config, runtime: Runtime):
    """Create and configure the Dash application object.

    Args:
        config: The active configuration.
        runtime: The started (or startable) runtime.

    Returns:
        A tuple of ``(dash_app, plugin_manager)``.
    """
    import dash

    from .plugins import PluginManager
    from .ui.callbacks import register_callbacks
    from .ui.layout import build_layout
    from .ui.shortcuts import register_shortcuts

    # Load plugins before the first layout build so UI hooks are registered.
    plugin_manager = PluginManager(hooks, runtime)
    if config.plugins_enabled:
        plugin_manager.load_enabled(config.enabled_plugins)

    app = dash.Dash(
        __name__,
        title="reimap — live network map",
        update_title=None,
        suppress_callback_exceptions=True,
    )

    app.layout = lambda: build_layout(config, runtime.store.stats())

    register_callbacks(app, runtime, plugin_manager)
    register_shortcuts(app)

    return app, plugin_manager


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="reimap",
        description="Watch your machine connect across the internet in real time.",
        epilog=(
            f"By Batuhan Ayrıbaş ({__homepage__}) — "
            f"a Rootcastle project ({__organization_url__})."
        ),
    )
    parser.add_argument("--host", help="Bind host (default from config).")
    parser.add_argument("--port", type=int, help="Bind port (default from config).")
    parser.add_argument("--theme", help="UI theme (midnight, aurora, carbon, daylight, terminal).")
    parser.add_argument("--interval", type=float, help="Scan interval in seconds.")
    parser.add_argument("--no-browser", action="store_true", help="Do not open a browser on start.")
    parser.add_argument("--list-hooks", action="store_true", help="Print all hook names and exit.")
    parser.add_argument("--debug", action="store_true", help="Enable Dash debug mode.")
    parser.add_argument("--version", action="version", version=f"reimap {__version__}")
    return parser.parse_args(argv)


def _apply_overrides(config: Config, args: argparse.Namespace) -> None:
    if args.host:
        config.host = args.host
    if args.port:
        config.port = args.port
    if args.theme:
        config.theme = args.theme
    if args.interval:
        config.scan_interval_seconds = args.interval
    if args.no_browser:
        config.open_browser = False
    config.validate()


def main(argv: list[str] | None = None) -> int:
    """Console entry point for the ``reimap`` command."""
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    configure_logging(logging.DEBUG if args.debug else logging.INFO)

    if args.list_hooks:
        for name in HookName.all_names():
            print(name)
        return 0

    config = Config.load()
    _apply_overrides(config, args)
    hooks.emit(HookName.CONFIG_LOADED, config=config)

    runtime = Runtime(config)
    hooks.emit(HookName.APP_STARTING, config=config)

    app, _plugins = create_app(config, runtime)
    runtime.start()

    url = f"http://{config.host}:{config.port}/"
    log.info("reimap is live at %s", url)
    print(f"\n  reimap {__version__} — live network map")
    print(f"  → {url}")
    print(f"  Batuhan Ayrıbaş · {__homepage__}   |   Rootcastle · {__organization_url__}\n")

    if config.open_browser and not args.no_browser:
        with contextlib.suppress(Exception):
            webbrowser.open(url)

    hooks.emit(HookName.APP_READY, url=url)

    try:
        app.run(host=config.host, port=config.port, debug=args.debug, use_reloader=False)
    except KeyboardInterrupt:
        pass
    finally:
        hooks.emit(HookName.APP_STOPPING)
        runtime.stop()
        log.info("reimap stopped.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
