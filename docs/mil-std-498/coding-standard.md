# reimap Coding Standard — NASA/JPL "Power of 10", adapted

reimap adopts an adapted form of the NASA/JPL Jet Propulsion Laboratory
**Power of 10: Rules for Developing Safety-Critical Code** (G. Holzmann, 2006).
The original rules target C for flight software; reimap is Python, so each rule is
restated in its intent and mapped to how reimap satisfies it. This standard is
referenced by requirements **SR-070…SR-074** and enforced by review and `ruff`.

| # | Original rule (intent) | How reimap applies it |
| --- | --- | --- |
| 1 | Avoid complex control flow (no `goto`/recursion). | No unbounded recursion. Control flow is flat; the scan loop is a single bounded `while not stop`. The one recursion (topojson decode, build-time tooling) is not shipped in the runtime. |
| 2 | All loops must have a fixed upper bound. | Figure construction caps arcs at `_MAX_ARCS` and samples at `_ARC_POINTS`; every per-cycle loop iterates the finite connection/history set. History is pruned to a bounded window. |
| 3 | No dynamic memory allocation after initialisation. | Not literally applicable in Python, adapted to: **bounded** growth. Caches are bounded (`lru_cache(maxsize=…)`); history is size-pruned; stores replace rather than accumulate per cycle. |
| 4 | Keep functions short (one printed page). | Functions are small and single-purpose; the largest are UI builders that are linear layout code. Reviewed at merge. |
| 5 | Use a minimum of two assertions per function (check the abnormal). | Pre/post-conditions are asserted at boundaries (e.g. great-circle needs ≥2 points; `is_mapped` guarantees a location). Runtime invariants that depend on external state are handled with explicit guards rather than asserts (see Rule 7). |
| 6 | Declare data at the smallest possible scope. | State is encapsulated in classes (`LiveStore`, `HistoryStore`, `HookRegistry`); module-level mutable state is avoided except the single shared hook registry. |
| 7 | Check the return value of every non-void call; check parameters. | File, subprocess, GeoIP and network calls are wrapped and their failures handled and logged. Config values are validated/clamped. A failing hook subscriber is caught. |
| 8 | Limit preprocessor / metaprogramming. | No metaclass magic or runtime code generation. The one clientside JS string is static and reviewed. |
| 9 | Limit pointer use / indirection. | Adapted: avoid deep indirection and hidden aliasing. Data models are explicit dataclasses; the pipeline passes values, not shared mutable globals. |
| 10 | Compile with all warnings on; use static analysis. | `ruff` runs the project ruleset (E, F, I, B, UP, SIM, RUF, D) and must pass in CI; the full `pytest` suite runs on Python 3.10–3.12. |

## Isolation principle (fail-soft)

Beyond the ten rules, reimap adds one project-specific safety principle:

> **No extension may compromise the core.** Every hook subscriber and plugin runs
> inside a guard that logs and swallows exceptions, so third-party code can never
> abort a scan cycle or take down the server (SR-043, SR-045).

## Enforcement

- **Automated:** `ruff check .` and `pytest` in [CI](../../.github/workflows/ci.yml).
- **Manual:** code review checks Rules 2, 5 and 7 explicitly for new pipeline code.
- **Traceability:** the safety requirements SR-070…SR-074 map to these rules in the
  [RTM](RTM.md).
