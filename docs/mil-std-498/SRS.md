# Software Requirements Specification (SRS)

**Document ID:** REIMAP-SRS-001
**DID:** DI-IPSC-81433 (tailored)
**System:** reimap — local-first network connection map
**Version:** 1.0.0

---

## 1. Scope

### 1.1 Identification
This SRS specifies the requirements for **reimap**, a local-first application that
observes the network sockets opened by the host machine, resolves remote endpoints
to geographic locations, and presents them on an interactive world map with an
extensibility hook system.

### 1.2 System overview
reimap runs entirely on the user's device. A background loop scans sockets,
enriches them via a local GeoIP database, records rolling history, computes
insights, and serves an interactive UI. All extension points are exposed as hooks.

### 1.3 Document overview
Section 3 states the requirements. Each requirement has a unique identifier
(`SR-###`), a priority (M = mandatory, D = desired), and is traced in the
[RTM](RTM.md) to a design element and a verifying test.

## 2. Referenced documents
- MIL-STD-498, *Software Development and Documentation*, 05 Dec 1994.
- NASA/JPL, *The Power of 10: Rules for Developing Safety-Critical Code*, 2006.
- [SDD.md](SDD.md), [STD.md](STD.md), [coding-standard.md](coding-standard.md).

## 3. Requirements

### 3.1 Socket acquisition (Capability)

| ID | Pri | Requirement |
| --- | --- | --- |
| SR-001 | M | The software shall enumerate the host's active TCP and UDP sockets each scan cycle. |
| SR-002 | M | The software shall classify each endpoint as REMOTE, LAN, LOCAL, or LISTEN. |
| SR-003 | M | The software shall record the owning process name and PID for each socket when the OS permits. |
| SR-004 | M | The software shall provide a primary scanner (`psutil`) and a fallback scanner (`lsof`) and select the best available at start. |
| SR-005 | M | A malformed or inaccessible individual socket record shall be skipped without aborting the scan cycle. |

### 3.2 Geolocation (Capability)

| ID | Pri | Requirement |
| --- | --- | --- |
| SR-010 | M | The software shall resolve REMOTE endpoints to latitude/longitude using a local GeoIP database. |
| SR-011 | M | The software shall operate with reduced function (no map placement) when no GeoIP database is installed, without error. |
| SR-012 | M | The software shall not transmit endpoint or traffic data off the host. |
| SR-013 | D | The software shall allow installing/updating a MaxMind GeoLite2-City database from the UI given a user-supplied licence key. |
| SR-014 | M | GeoIP lookups shall be cached to bound repeated work within a session. |

### 3.3 State and history (Capability)

| ID | Pri | Requirement |
| --- | --- | --- |
| SR-020 | M | The software shall maintain a live snapshot of the current connection set. |
| SR-021 | M | The software shall compute the set of new and closed connections relative to the previous cycle. |
| SR-022 | M | The software shall persist a rolling history of remote endpoints for a configurable retention window (default 30 days). |
| SR-023 | M | History older than the retention window shall be pruned. |
| SR-024 | M | Persisted state shall be stored only under the host's standard per-user directories. |

### 3.4 Insights and reporting (Capability)

| ID | Pri | Requirement |
| --- | --- | --- |
| SR-030 | M | The software shall compute, each cycle, counts of total/mapped/unmapped connections, new endpoints, top countries and top applications. |
| SR-031 | M | The software shall identify "frequent" endpoints by a configurable hit threshold. |
| SR-032 | D | The software shall produce a daily report summarising country and application activity and busiest endpoints. |

### 3.5 Extensibility — hook system (Capability)

| ID | Pri | Requirement |
| --- | --- | --- |
| SR-040 | M | The software shall expose a documented set of lifecycle extension points ("hooks"). |
| SR-041 | M | The software shall support event hooks (observe) and filter hooks (transform/drop a value). |
| SR-042 | M | Hook subscribers shall run in ascending priority order. |
| SR-043 | M | An exception raised by a hook subscriber shall be logged and isolated so it cannot abort a scan cycle or crash the server. |
| SR-044 | M | The set of active hook subscriptions shall be introspectable at runtime and via the CLI. |
| SR-045 | M | The software shall load built-in and user-supplied plugins that subscribe to hooks, and a failing plugin shall not prevent startup. |

### 3.6 User interface (Capability)

| ID | Pri | Requirement |
| --- | --- | --- |
| SR-050 | M | The software shall render mapped connections on an interactive world map served on localhost. |
| SR-051 | M | The map shall render fully offline, with no external network request for map tiles or geometry. |
| SR-052 | D | The map shall animate: great-circle arcs from a home origin and pulsing endpoint markers. |
| SR-053 | M | The software shall provide panels for Insights, Unmapped, LAN/Local, Open ports, Daily report, History, Plugins & Hooks, GeoIP, Settings and About. |
| SR-054 | D | Each panel shall be reachable by a single keyboard shortcut handled client-side. |
| SR-055 | D | The software shall provide selectable colour themes and map projections. |

### 3.7 Platform and packaging (Capability)

| ID | Pri | Requirement |
| --- | --- | --- |
| SR-060 | M | The software shall run on Windows, macOS and Linux with Python 3.10+. |
| SR-061 | D | The project shall provide reproducible desktop binaries for Windows, macOS and Linux via CI. |
| SR-062 | D | The project shall provide an Android application with a standalone offline demo and a connect-to-server mode. |
| SR-063 | D | The Android offline demo shall function with no server and no network access. |

### 3.8 Quality and safety (Non-functional)

| ID | Pri | Requirement |
| --- | --- | --- |
| SR-070 | M | All loops in figure construction and per-cycle processing shall be bounded by the finite input set or an explicit constant (Power of 10, Rule 2). |
| SR-071 | M | Return values of fallible operations (file, subprocess, GeoIP) shall be checked and handled (Power of 10, Rule 7). |
| SR-072 | M | The software shall be verified by an automated test suite executed in CI on Python 3.10, 3.11 and 3.12. |
| SR-073 | M | Configuration inputs shall be validated and clamped to safe ranges before use. |
| SR-074 | M | Static analysis (`ruff`) shall pass with the project ruleset on every change. |

## 4. Verification
Every mandatory requirement is verified by at least one test case in the
[STD](STD.md), traced in the [RTM](RTM.md). Desired requirements are verified by
test, demonstration (screenshots/CI artifacts), or inspection as noted there.
