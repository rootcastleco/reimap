# Architecture

This document describes how reimap is put together. The guiding principle is a
strict separation between the **background scan loop** (which produces data) and
the **web UI** (which consumes it), connected only through thread-safe stores and
an extensibility **hook bus**.

## High-level flow

```
┌──────────────┐      ┌───────────────┐      ┌──────────────┐
│   Scanner    │─────▶│   Resolver    │─────▶│  LiveStore   │
│ (psutil/lsof)│      │  (GeoIP)      │      │  (snapshot)  │
└──────────────┘      └───────────────┘      └──────┬───────┘
        │                     │                     │
        ▼                     ▼                     ▼
   ┌─────────────────────────────────────────────────────┐
   │                    Hook bus (hooks.py)               │
   └─────────────────────────────────────────────────────┘
        ▲                     ▲                     ▲
        │                     │                     │
   ┌──────────┐        ┌─────────────┐       ┌─────────────┐
   │ Plugins  │        │  Insights   │       │   Dash UI   │
   └──────────┘        └─────────────┘       └─────────────┘
```

The `Runtime` object owns the long-lived collaborators and runs the scan loop on a
daemon thread. Dash request threads read exclusively from the stores, so rendering
never blocks scanning.

## Module map

| Module | Responsibility |
| --- | --- |
| `reimap/app.py` | Application assembly + `reimap` CLI entry point. |
| `reimap/runtime.py` | Owns collaborators; runs the periodic scan/resolve/record/insights cycle. |
| `reimap/hooks.py` | The event/filter hook registry — the extensibility core. |
| `reimap/config.py` | Dataclass-backed JSON configuration with validation. |
| `reimap/app_dirs.py` | Cross-platform config/data/cache/log directories. |
| `reimap/logging_config.py` | Console + rotating-file logging setup. |
| `reimap/model/` | `Connection`, `ConnectionKind`, `GeoLocation` domain types. |
| `reimap/scanner/` | Socket enumeration: `psutil` backend, `lsof` fallback, IP classification. |
| `reimap/geoip/` | GeoIP database management + cached resolver. |
| `reimap/state/` | `LiveStore` (current snapshot) and `HistoryStore` (rolling window). |
| `reimap/insights/` | Insight computation and snapshot/report persistence. |
| `reimap/plugins/` | Plugin manager + five built-in plugins. |
| `reimap/ui/` | Dash layout, themes, map figure, panels, callbacks, keyboard shortcuts. |

## Threading model

- **Scan thread** — created by `Runtime.start()`, runs `scan_once()` on an
  interval. All writes to `LiveStore` and `HistoryStore` happen here.
- **Request threads** — Dash callbacks. They only read from the stores, whose
  methods are guarded by an `RLock`.
- **Hook callbacks** — run on whichever thread fired the hook. Because scan-loop
  hooks run on the scan thread, plugin authors should keep them fast and avoid
  blocking I/O in the hot path (use `scan.completed` for batch work).

## Design decisions

- **Hooks over inheritance.** Rather than subclassing to customise behaviour,
  every extension point is a named hook. This keeps the core closed for
  modification but open for extension, and makes the full extension surface
  enumerable (`reimap --list-hooks`).
- **Filter vs. event split.** Observation and transformation are different
  concerns. Event hooks can't accidentally mutate the pipeline; filter hooks are
  explicitly allowed to.
- **Fail-soft plugins.** A raising subscriber is logged and skipped. One bad
  plugin can never take down a scan cycle or the server.
- **No bundled GeoIP.** The database is user-supplied, keeping the project
  licence-clean and guaranteeing reimap has nothing to phone home about.
- **Stores as the only shared state.** The UI and the scan loop share nothing but
  the thread-safe stores, which makes reasoning about concurrency local and
  simple.

## Extending the UI

- **New panel** — add a builder in `ui/panels.py` and a menu entry in
  `ui/layout.py::MENU_ITEMS`, then dispatch it in `ui/callbacks.py::_build_panel`.
  Plugins can also contribute panels via the `ui.panel_register` filter hook.
- **New theme** — add a palette to `ui/theme.py::THEME_PALETTES`.
- **New marker styling** — subscribe to the `ui.marker_styled` filter hook.

See [HOOKS.md](HOOKS.md) for the full hook catalogue.
