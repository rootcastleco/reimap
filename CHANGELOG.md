# Changelog

All notable changes to reimap are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/), and this project adheres to
[Semantic Versioning](https://semver.org/).

## [1.0.0] — 2026-07-24

Initial public release.

### Added

- **Live world map** of the connections your machine makes, rendered with Plotly
  over a Dash server bound to localhost.
- **Extensibility hook system** (`reimap.hooks`) with 21 documented event and
  filter hooks spanning the application, scan, connection, GeoIP, insights and UI
  lifecycles; priorities, fail-soft isolation, and full introspection.
- **Five built-in plugins**: `connection_logger`, `new_endpoint_alerts`,
  `private_ip_filter`, `geo_enricher`, `jsonl_exporter`.
- **User plugin loading** from the platform config directory.
- **Insights engine** — new endpoints, frequent talkers, top countries and
  applications, recomputed every cycle.
- **Rolling history** (default 30-day window) persisted to disk with per-endpoint
  hit counts and country totals.
- **Daily report** panel summarising application and country activity.
- **Network inspection panels**: Unmapped services, LAN/Local, and Open ports.
- **GeoIP management** — download/verify a MaxMind GeoLite2-City database from the
  UI, or install a file manually.
- **Animated map** — great-circle arcs radiating from a configurable home origin,
  packets travelling along each arc, and client-side pulsing markers.
- **Fully offline rendering** — world geometry bundled; the map issues no external
  request.
- **Five UI themes** (`midnight`, `aurora`, `carbon`, `daylight`, `terminal`) and
  five map projections, with adjustable marker size and an optional density halo.
- **`--demo` mode** — seed a curated worldwide dataset with no GeoIP required.
- **Keyboard-first UI** — every panel one keypress away, handled client-side.
- **Android application** (`android/`) — Kotlin WebView host with a standalone
  offline demo (canvas world map, no server) and a connect-to-server mode.
- **Desktop packaging** — PyInstaller spec and a release workflow that builds
  Windows/macOS/Linux binaries and the Android APK and attaches them to releases.
- **MIL-STD-498 documentation set** (`docs/mil-std-498/`) — SRS, SDD, STD, SDP, SVD
  and a requirements traceability matrix.
- **NASA/JPL "Power of 10"** adapted coding standard, enforced by review and CI.
- **CLI** with `--host/--port/--theme/--interval/--no-browser/--list-hooks/--debug`.
- **Cross-platform scanning** via a `psutil` primary backend and an `lsof`
  fallback.
- Full test suite and ruff configuration.

[1.0.0]: https://github.com/rootcastleco/reimap/releases/tag/v1.0.0
