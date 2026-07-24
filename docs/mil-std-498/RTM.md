# Requirements Traceability Matrix (RTM)

**Document ID:** REIMAP-RTM-001
**Version:** 1.0.0

Bidirectional trace: each requirement in the [SRS](SRS.md) → the design element in
the [SDD](SDD.md) that implements it → the test case in the [STD](STD.md) that
verifies it. `M` = mandatory, `D` = desired.

| Req | Pri | Design element (SDD) | Verified by (STD) |
| --- | --- | --- | --- |
| SR-001 | M | Scanner CSC — `scanner.psutil_scanner`/`lsof_scanner` | TC-QA-02 (scan smoke), demo |
| SR-002 | M | `scanner.base.classify_ip`, `model.ConnectionKind` | TC-CLS-01/02/03, TC-STO-04 |
| SR-003 | M | `psutil_scanner._process_name` | TC-QA-02 |
| SR-004 | M | `scanner.base.get_scanner` | Inspection + TC-QA-02 |
| SR-005 | M | scanner row guards; `runtime.scan_once` try/except | TC-CLS-04 |
| SR-010 | M | GeoIP CSC — `geoip.resolver.GeoResolver.resolve` | TC-MDL-01 |
| SR-011 | M | `GeoResolver._open_reader` degrade path | Inspection; TC-QA-02 (no DB) |
| SR-012 | M | Design decision D-1 | Inspection (no network calls) |
| SR-013 | D | `geoip.database.GeoIPDatabase.download` | Demonstration |
| SR-014 | M | `GeoResolver._lookup` `lru_cache` | Inspection |
| SR-020 | M | `state.store.LiveStore` | TC-STO-01/03 |
| SR-021 | M | `LiveStore.update` diff | TC-STO-02 |
| SR-022 | M | `state.history.HistoryStore` | TC-HIS-01 |
| SR-023 | M | `HistoryStore._prune` | TC-HIS-01 (window), inspection |
| SR-024 | M | `app_dirs`, `HistoryStore.save` | Inspection (paths) |
| SR-030 | M | `insights.engine.InsightsEngine.compute` | TC-INS-01 |
| SR-031 | M | `HistoryStore.frequent` | TC-HIS-01 |
| SR-032 | D | `InsightsEngine.daily_report` | Demonstration (panel) |
| SR-040 | M | `hooks.HookName`, `HookRegistry` | TC-HK-02/07/08 |
| SR-041 | M | `HookRegistry.filter` | TC-HK-04/05 |
| SR-042 | M | priority-sorted `_Subscription` | TC-HK-01 |
| SR-043 | M | `emit`/`filter` try/except | TC-HK-03 |
| SR-044 | M | `describe`/`count`, `--list-hooks` | TC-HK-06 |
| SR-045 | M | `plugins.manager.PluginManager` guards | Inspection; TC-QA-02 |
| SR-050 | M | UI CSC — `ui.map_view`, `ui.layout` | TC-UI-01 |
| SR-051 | M | bundled topojson + `topojsonURL` (D-5) | TC-UI-01 |
| SR-052 | D | `ui.map_view` arcs, `ui.animation` pulse | TC-UI-01 |
| SR-053 | M | `ui.panels`, `ui.callbacks` | TC-UI-02 |
| SR-054 | D | `ui.shortcuts` clientside | Demonstration |
| SR-055 | D | `ui.theme`, projection setting | Demonstration |
| SR-060 | M | Python packaging, `pyproject.toml` | TC-QA-02 matrix |
| SR-061 | D | `packaging/reimap.spec`, release workflow | TC-PKG-01 |
| SR-062 | D | `android/` project | TC-AND-01 |
| SR-063 | M | `android/.../assets/demo` | TC-AND-01 |
| SR-070 | M | `_MAX_ARCS`/`_ARC_POINTS`, prune, caches | Inspection; coding-standard |
| SR-071 | M | wrapped file/subprocess/GeoIP calls | Inspection; coding-standard |
| SR-072 | M | CI test matrix | TC-QA-02 |
| SR-073 | M | `config.Config.validate` | TC-CFG-01/02 |
| SR-074 | M | `ruff` ruleset in CI | TC-QA-01 |

**Coverage:** every mandatory requirement (M) traces to at least one automated
test or explicit inspection; desired requirements (D) trace to test, demonstration,
or inspection as noted.
