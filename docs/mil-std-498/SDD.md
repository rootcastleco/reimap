# Software Design Description (SDD)

**Document ID:** REIMAP-SDD-001
**DID:** DI-IPSC-81435 (tailored)
**Version:** 1.0.0

---

## 1. Scope
This SDD describes the design of reimap and traces each design element to the
requirements it satisfies (see [SRS](SRS.md), [RTM](RTM.md)).

## 2. CSCI-wide design decisions

- **D-1 Local-first, telemetry-free.** No component initiates outbound traffic
  except the explicit, user-triggered GeoIP database download. Satisfies SR-012.
- **D-2 Producer/consumer separation.** A background scan thread produces state;
  the web UI consumes it. They share only thread-safe stores. Satisfies SR-020,
  SR-050.
- **D-3 Hooks over inheritance.** All extension points are named hooks in a single
  registry, not subclass seams. Satisfies SR-040…SR-044.
- **D-4 Fail-soft extensions.** Hook/plugin exceptions are isolated. Satisfies
  SR-043, SR-045.
- **D-5 Offline rendering.** World geometry is bundled; the map issues no external
  request. Satisfies SR-051.
- **D-6 Bounded work.** Per-cycle and figure loops are bounded by constants or the
  finite input. Satisfies SR-070.

## 3. Architectural design

### 3.1 Component decomposition (CSCs)

| CSC | Module(s) | Responsibility | Requirements |
| --- | --- | --- | --- |
| Scanner | `scanner/` | Enumerate + classify sockets. | SR-001…SR-005 |
| GeoIP | `geoip/` | Database management + cached resolution. | SR-010…SR-014 |
| Model | `model/` | `Connection`, `ConnectionKind`, `GeoLocation`. | SR-002 |
| State | `state/` | Live snapshot + rolling history. | SR-020…SR-024 |
| Insights | `insights/` | Derive signals + reports. | SR-030…SR-032 |
| Hooks | `hooks.py` | Event/filter registry. | SR-040…SR-044 |
| Plugins | `plugins/` | Load built-in + user plugins. | SR-045 |
| Runtime | `runtime.py` | Orchestrate the scan cycle. | SR-005, SR-021 |
| UI | `ui/` | Layout, map, panels, animation, shortcuts. | SR-050…SR-055 |
| App/CLI | `app.py` | Assemble app; CLI. | SR-044, SR-060 |
| Demo | `demo.py` | Curated demo dataset. | SR-063 |

### 3.2 Execution model

```
main() ─▶ Config.load ─▶ Runtime(demo?) ─▶ create_app (load plugins, wire UI) ─▶ Runtime.start
                                                                                   │
                          ┌────────────────────────────────────────────────────────┘
                          ▼
   scan loop (daemon thread):  SCAN_STARTED
     scan() ─▶ per conn: CONNECTION_DISCOVERED, FILTER_CONNECTION
     resolve_all() ─▶ GEOIP_RESOLVED | GEOIP_UNRESOLVED
     store.update() ─▶ (new, closed);  history.record() ─▶ CONNECTION_NEW / _CLOSED
     insights.compute() ─▶ INSIGHTS_UPDATED, FILTER_INSIGHTS
     SCAN_COMPLETED
```

The UI polls the stores on timers (`ri-tick`, `ri-panel-tick`) and animates
client-side (`ri-anim`), so rendering never blocks scanning (D-2).

## 4. Detailed design (selected)

### 4.1 Hook registry (`hooks.py`)
Two dispatch methods over a priority-sorted subscription list:
- `emit(name, **ctx)` — event; return values ignored; each subscriber wrapped in
  try/except (SR-043).
- `filter(name, value, **ctx)` — threads `value` through subscribers; `None` drops
  it and short-circuits. Introspection via `describe()`/`count()` (SR-044).

### 4.2 Live store (`state/store.py`)
Holds a dict keyed by `Connection.key`. `update()` diffs against the prior snapshot
to yield new/closed sets and preserves `first_seen`. All access under an `RLock`
(D-2). Satisfies SR-020, SR-021.

### 4.3 History (`state/history.py`)
Aggregates per-IP `HistoryEntry` records (hits, first/last-seen, processes,
country). `record()` returns first-ever endpoints; `_prune()` enforces the
retention window (SR-023). Persisted as JSON under the data dir (SR-024).

### 4.4 Map view (`ui/map_view.py`)
Builds a Plotly `scattergeo` figure: bounded great-circle arcs from the home origin
(`_great_circle`, `_MAX_ARCS`, `_ARC_POINTS`), a home marker, optional density halo,
and connection markers carrying base sizes in `customdata` for the client-side
pulse. Passes through `FILTER_MAP_FIGURE`. Satisfies SR-050, SR-052, SR-070.

### 4.5 Offline geometry
The world topology (`assets/world_110m.json`, `world_50m.json`) is bundled and the
Plotly `topojsonURL` points at the local asset path, so the desktop map renders
with no external request (SR-051). The Android demo renders the same geometry
decoded to `land.json` on a canvas (SR-063).

## 5. Requirements traceability
See [RTM.md](RTM.md) for the full requirement → design → test matrix.
