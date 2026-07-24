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
- **Five UI themes** (`midnight`, `aurora`, `carbon`, `daylight`, `terminal`) and
  five map projections, with adjustable marker size and an optional density halo.
- **Keyboard-first UI** — every panel one keypress away, handled client-side.
- **CLI** with `--host/--port/--theme/--interval/--no-browser/--list-hooks/--debug`.
- **Cross-platform scanning** via a `psutil` primary backend and an `lsof`
  fallback.
- Full test suite and ruff configuration.

[1.0.0]: https://github.com/rootcastleco/reimap/releases/tag/v1.0.0
