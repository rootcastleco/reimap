# reimap — MIL-STD-498 Documentation Set

This directory holds a **tailored** MIL-STD-498 documentation set for reimap.
MIL-STD-498 (*Software Development and Documentation*, 1994) defines a family of
Data Item Descriptions (DIDs) for defense software projects. reimap is an
open-source project, not a defense contract, so this set is deliberately tailored:
it adopts the structure, discipline and traceability of the standard where they add
real engineering value, and it says so plainly where clauses are marked *Not
Applicable (tailored out)*.

The goal is concrete: give reimap the rigor of a controlled software project —
numbered requirements, a design that traces to them, tests that trace back, and a
versioned release record — while staying readable.

## Documents

| DID (MIL-STD-498) | Document | Purpose |
| --- | --- | --- |
| DI-IPSC-81427 (SDP) | [SDP.md](SDP.md) | Software Development Plan — process, standards, tooling. |
| DI-IPSC-81433 (SRS) | [SRS.md](SRS.md) | Software Requirements Specification — numbered requirements. |
| DI-IPSC-81435 (SDD) | [SDD.md](SDD.md) | Software Design Description — architecture and components. |
| DI-IPSC-81439 (STD) | [STD.md](STD.md) | Software Test Description — test cases and procedures. |
| DI-IPSC-81442 (SVD) | [SVD.md](SVD.md) | Software Version Description — what is in this release. |
| — | [RTM.md](RTM.md) | Requirements Traceability Matrix — requirement → design → test. |
| — | [coding-standard.md](coding-standard.md) | NASA/JPL "Power of 10" coding standard as applied to reimap. |

## Compliance posture

- **Requirements are numbered** (`SR-###`) and each is traced forward to a design
  element and backward from a test case in the [RTM](RTM.md).
- **Coding standard**: reimap adopts an adapted form of the NASA/JPL Jet Propulsion
  Laboratory *Power of 10* rules for safety-critical code (see
  [coding-standard.md](coding-standard.md)), enforced by review and by `ruff`.
- **Verification**: the automated test suite is the executable form of the
  [STD](STD.md); CI runs it on every change across Python 3.10–3.12.

## Tailoring statement

reimap is a local-first observability tool with no safety-of-life or security
certification scope. The following MIL-STD-498 DIDs are **tailored out** as not
applicable: OCD, SSS, IRS, IDD, DBDD, SIP, STrP, SIOM, SCOM, COM, SUM (covered by
the project README), STR (covered by CI logs), and all hardware DIDs. This
tailoring is itself a MIL-STD-498-conformant activity (the standard is explicitly
designed to be tailored to project scope).
