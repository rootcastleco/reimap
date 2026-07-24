# Hook reference

reimap exposes 21 extension points. Subscribe to them from a plugin's
`register(hooks, runtime)` function. This document lists every hook, its flavour,
and the context it carries.

## The two flavours

- **Event** — `hooks.emit(name, **ctx)`. Subscribers receive a single `ctx`
  mapping and their return value is ignored.
  ```python
  @hooks.on(HookName.CONNECTION_NEW)
  def cb(ctx): ...
  ```
- **Filter** — `hooks.filter(name, value, **ctx)`. Subscribers receive
  `(value, ctx)` and return a replacement value; returning `None` drops it.
  ```python
  @hooks.on(HookName.FILTER_CONNECTION)
  def cb(conn, ctx): return conn  # or None to drop
  ```

Every registration accepts `priority=` (lower runs first, default `100`) and
`name=` (shown in the in-app hook inspector).

## Application lifecycle

| Hook | Flavour | Context |
| --- | --- | --- |
| `app.starting` | event | `config` |
| `app.ready` | event | `url` |
| `app.stopping` | event | — |
| `config.loaded` | event | `config` |

## Scan loop

| Hook | Flavour | Context |
| --- | --- | --- |
| `scan.started` | event | — |
| `scan.completed` | event | `connections`, `new`, `closed`, `duration` |
| `scan.failed` | event | `error` |

## Per-connection

| Hook | Flavour | Context |
| --- | --- | --- |
| `connection.discovered` | event | `connection` |
| `connection.new` | event | `connection` (first ever seen) |
| `connection.closed` | event | `connection` (gone since last cycle) |

## GeoIP

| Hook | Flavour | Context |
| --- | --- | --- |
| `geoip.resolved` | event | `connection`, `location` |
| `geoip.unresolved` | event | `connection` |
| `geoip.db_updated` | event | `path` |

## Insights

| Hook | Flavour | Context |
| --- | --- | --- |
| `insights.updated` | event | `insights` (an `InsightsSnapshot`) |
| `report.daily` | event | `report` (a dict) |

## UI

| Hook | Flavour | Context |
| --- | --- | --- |
| `ui.layout_built` | event | `root`, `config` |
| `ui.panel_register` | filter | value: `list[panel spec]` |
| `ui.marker_styled` | filter | value: style dict; ctx: `connection`, `location` |

A panel spec is `{"id": str, "title": str, "render": callable(runtime) -> component}`.

## Pipeline filters

| Hook | Flavour | Value / behaviour |
| --- | --- | --- |
| `filter.connection` | filter | A `Connection`; return `None` to drop it before mapping. |
| `filter.map_figure` | filter | The Plotly figure dict, post-processed before serving. |
| `filter.insights` | filter | The `InsightsSnapshot`, post-processed before display. |

## Priorities in practice

Filter order matters. For example, to drop LAN traffic *before* an enrichment
filter ever sees it, give the drop a lower priority number:

```python
@hooks.on(HookName.FILTER_CONNECTION, priority=10)   # runs first
def drop_lan(conn, ctx):
    return None if conn.kind.value in ("lan", "local") else conn

@hooks.on(HookName.FILTER_CONNECTION, priority=50)   # runs after
def tag(conn, ctx):
    ...
    return conn
```

## Introspection

- CLI: `reimap --list-hooks` prints every hook name.
- In-app: the **Plugins & Hooks** panel lists every hook, its live subscribers,
  and the total subscription count.
- Programmatic: `hooks.describe()` returns `{hook: [subscriber names]}` and
  `hooks.count()` returns the total.
