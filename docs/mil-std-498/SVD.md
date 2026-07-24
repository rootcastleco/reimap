# Software Version Description (SVD)

**Document ID:** REIMAP-SVD-001
**DID:** DI-IPSC-81442 (tailored)
**Release:** reimap 1.0.0

---

## 1. Scope
This SVD identifies and describes release **1.0.0** of reimap.

## 2. Version identification
- **Product:** reimap
- **Version:** 1.0.0
- **Version source of truth:** `src/reimap/__init__.py` (`__version__`) and
  `pyproject.toml`.
- **Licence:** MIT.
- **Owner:** Batuhan Ayrıbaş (https://batuhanayribas.com), a Rootcastle
  (https://rootcastle.com) project.

## 3. Inventory of materials released

| Item | Location |
| --- | --- |
| Python package | `src/reimap/` |
| Bundled world geometry | `src/reimap/assets/world_110m.json`, `world_50m.json` |
| Test suite | `tests/` (44 cases) |
| Desktop packaging | `packaging/reimap.spec`, `packaging/entry.py` |
| Android application | `android/` (Kotlin WebView + offline demo) |
| CI/CD | `.github/workflows/ci.yml`, `release.yml` |
| MIL-STD-498 documentation | `docs/mil-std-498/` |
| User documentation | `README.md`, `ARCHITECTURE.md`, `HOOKS.md`, `PRIVACY.md` |

## 4. Capabilities in this release
Real-time socket map, GeoIP resolution, rolling history, insights + daily report,
21-hook extensibility system with five built-in plugins, ten UI panels, five
themes, animated offline map (arcs + pulse), CLI, cross-platform desktop packaging,
and an Android app with a standalone offline demo.

## 5. Interface compatibility
- **Config file:** JSON; unknown keys ignored on load (forward compatible).
- **Hook identifiers:** the string values of `HookName` are the stable public API
  for plugins.
- **Plugin protocol:** a module exposing `register(hooks, runtime)`.

## 6. Open items / known limitations
- GeoIP data is user-supplied (not bundled) by design; without it, endpoints appear
  in the Unmapped/Open-ports panels but not on the map.
- The Android app renders; privileged scanning runs on the desktop/server engine.
- Official desktop binaries are produced by CI (see [packaging](../../packaging/README.md)).

## 7. Change summary
Initial public release. See [CHANGELOG.md](../../CHANGELOG.md) for details.
