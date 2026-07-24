# Software Test Description (STD)

**Document ID:** REIMAP-STD-001
**DID:** DI-IPSC-81439 (tailored)
**Version:** 1.0.0

---

## 1. Scope
This STD defines the test cases that verify the [SRS](SRS.md). The executable form
of these cases is the `pytest` suite under `tests/`, run in CI on Python 3.10–3.12.

## 2. Test environment
- **Method:** automated unit/integration tests (`pytest`), static analysis
  (`ruff`), and demonstration (screenshots / CI artifacts).
- **Execution:** `pip install -e ".[dev]" && pytest -q && ruff check .`
- **Independence:** history/config tests use `tmp_path` and monkeypatched
  directories, so no test touches real user state.

## 3. Test cases

| Test ID | Verifies | Method | Location | Pass criterion |
| --- | --- | --- | --- | --- |
| TC-CLS-01 | SR-002 | Test | `test_scanner.py::test_classify_loopback` | Loopback → LOCAL. |
| TC-CLS-02 | SR-002 | Test | `test_scanner.py::test_classify_private` | RFC-1918 → LAN. |
| TC-CLS-03 | SR-002 | Test | `test_scanner.py::test_classify_public` | Public IP → REMOTE. |
| TC-CLS-04 | SR-005 | Test | `test_scanner.py::test_classify_garbage_is_remote` | Bad input does not raise. |
| TC-MDL-01 | SR-010 | Test | `test_scanner.py::test_connection_is_mapped` | Location sets mapped + label. |
| TC-STO-01 | SR-020 | Test | `test_state.py::test_first_update_all_new` | Snapshot count correct. |
| TC-STO-02 | SR-021 | Test | `test_state.py::test_second_update_detects_new_and_closed` | New/closed diff correct. |
| TC-STO-03 | SR-020 | Test | `test_state.py::test_first_seen_preserved_across_updates` | `first_seen` stable. |
| TC-STO-04 | SR-002 | Test | `test_state.py::test_stats_counts_kinds` | Kind counters correct. |
| TC-HIS-01 | SR-022 | Test | `test_config_and_insights.py::test_history_new_and_frequent` | New/frequent logic. |
| TC-INS-01 | SR-030 | Test | `test_config_and_insights.py::test_insights_counts_and_top_lists` | Top country/app lists. |
| TC-CFG-01 | SR-073 | Test | `test_config_and_insights.py::test_config_validate_clamps` | Out-of-range clamped. |
| TC-CFG-02 | SR-073 | Test | `test_config_and_insights.py::test_config_load_ignores_unknown_keys` | Forward-compatible load. |
| TC-HK-01 | SR-042 | Test | `test_hooks.py::test_event_hook_runs_subscribers_in_priority_order` | Priority order. |
| TC-HK-02 | SR-040 | Test | `test_hooks.py::test_event_hook_passes_context` | Context delivered. |
| TC-HK-03 | SR-043 | Test | `test_hooks.py::test_raising_subscriber_is_isolated` | Raising subscriber isolated. |
| TC-HK-04 | SR-041 | Test | `test_hooks.py::test_filter_hook_threads_value` | Filter threads value. |
| TC-HK-05 | SR-041 | Test | `test_hooks.py::test_filter_hook_drop_short_circuits` | `None` drops + short-circuits. |
| TC-HK-06 | SR-044 | Test | `test_hooks.py::test_describe_and_subscribers` | Introspection works. |
| TC-HK-07 | SR-040 | Test | `test_hooks.py::test_all_hook_names_are_unique_and_stringy` | Names unique/stable. |
| TC-HK-08 | SR-040 | Test | `test_hooks.py::test_every_hook_accepts_string_or_enum` | Enum/string parity. |
| TC-QA-01 | SR-074 | Static | `ruff check .` in CI | No lint findings. |
| TC-QA-02 | SR-072 | Test | full `pytest` in CI matrix | All tests pass on 3.10–3.12. |
| TC-UI-01 | SR-050, SR-051, SR-052 | Demo | `docs/images/hero-map.png` | Map renders offline with arcs. |
| TC-UI-02 | SR-053 | Demo | `docs/images/panel-*.png` | Panels render. |
| TC-AND-01 | SR-062, SR-063 | Demo | `docs/images/android-demo.png` | Offline demo renders standalone. |
| TC-PKG-01 | SR-061 | Demo | release workflow artifacts | Binaries build per OS. |

## 4. Traceability
Every mandatory SRS requirement maps to at least one test case above; see the
[RTM](RTM.md) for the consolidated matrix.
