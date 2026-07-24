# Software Development Plan (SDP)

**Document ID:** REIMAP-SDP-001
**DID:** DI-IPSC-81427 (tailored)
**Version:** 1.0.0

---

## 1. Scope
This SDP describes the process, standards and tooling used to develop and maintain
reimap. It is tailored for an open-source project of small team size.

## 2. Reference documents
MIL-STD-498; NASA/JPL *Power of 10*; project [SRS](SRS.md), [SDD](SDD.md),
[STD](STD.md), [coding-standard.md](coding-standard.md).

## 3. Software development process

### 3.1 Life-cycle model
Incremental. Each increment: define/adjust requirements (SRS) → design (SDD) →
implement to the coding standard → verify (STD via CI) → record the release (SVD).

### 3.2 Standards
- **Language:** Python 3.10+; Kotlin for Android.
- **Coding standard:** adapted NASA/JPL *Power of 10*
  ([coding-standard.md](coding-standard.md)), enforced by review and `ruff`.
- **Style:** `ruff` (line length 100, Google-style docstrings, rulesets
  E/F/I/B/UP/SIM/RUF/D).
- **Docstrings:** every public module, class and function.

### 3.3 Tooling
| Concern | Tool |
| --- | --- |
| Build (Python) | setuptools / `pyproject.toml` |
| Desktop binaries | PyInstaller (`packaging/reimap.spec`) |
| Android | Gradle + Android Gradle Plugin 8.2, Kotlin 1.9 |
| Test | pytest |
| Static analysis | ruff |
| CI/CD | GitHub Actions (`ci.yml`, `release.yml`) |
| VCS | git / GitHub |

## 4. Verification and validation
- **Unit/integration tests** are mandatory for new core logic; the suite runs on
  Python 3.10, 3.11 and 3.12 in CI (SR-072).
- **Static analysis** must pass on every change (SR-074).
- **Traceability** is maintained in the [RTM](RTM.md): no mandatory requirement
  ships without a verifying test or documented inspection.
- **Demonstration** artifacts (screenshots, CI build artifacts) verify UI and
  packaging requirements.

## 5. Configuration management
- Single trunk with short-lived feature branches; changes land via reviewed pull
  requests.
- Version is single-sourced in `src/reimap/__init__.py` and `pyproject.toml`.
- Releases are tagged `vX.Y.Z`; the release workflow builds and attaches all
  binaries and the APK.
- The [CHANGELOG](../../CHANGELOG.md) records every release (Keep a Changelog +
  SemVer).

## 6. Risk management (top items)
| Risk | Mitigation |
| --- | --- |
| OS restricts socket enumeration | Dual scanner backends (`psutil` + `lsof`); graceful empty result. |
| No GeoIP database present | Degrade to unmapped panels; in-app install flow. |
| Third-party plugin defects | Fail-soft isolation of all hook/plugin code (SR-043/045). |
| Build-host variance | Official binaries built only on standard CI runners. |

## 7. Roles
Open-source maintainership by the owner (Batuhan Ayrıbaş / Rootcastle) with external
contributions via pull request under the same standards and CI gates.
