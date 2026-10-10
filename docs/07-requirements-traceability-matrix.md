# Requirements Traceability Matrix — Executed portfolio baseline

## Purpose and status

This matrix connects the approved synthetic business needs to functional requirements, business rules, user stories, executable UAT cases, and retained evidence. It is a portfolio traceability baseline, not a record of customer or production approval.

- Baseline date: 18 September 2026.
- Scope: inbound receipt, putaway selection, simulated WMS/WCS movement, exception recovery, inventory commitment, audit, and metrics.
- Test environment: local static browser prototype with an in-memory deterministic simulator.
- Result summary: **14 PASS**, 0 FAIL, **0 orphaned requirements** across the reserved `BN`, `FR`, `BR`, `US`, and `UAT` ranges.

## End-to-end traceability

| UAT case | Business need | Functional requirement | Business rule | User story | Evidence | Result |
|---|---|---|---|---|---|---|
| `UAT-01` | `BN-01`, `BN-02`, `BN-04` | `FR-01`, `FR-02`, `FR-04`, `FR-05`, `FR-06`, `FR-07`, `FR-10` | `BR-01`, `BR-02`, `BR-04`, `BR-05`, `BR-06` | `US-01`, `US-03`, `US-04`, `US-05`, `US-06`, `US-08`, `US-11` | Automated UAT and `assets/02-happy-path-inventory.png` | PASS |
| `UAT-02` | `BN-01` | `FR-01`, `FR-02` | `BR-01` receipt-validation boundary | `US-01` | Automated UAT | PASS |
| `UAT-03` | `BN-01` | `FR-01`, `FR-02` | `BR-02` | `US-01` | Automated UAT | PASS |
| `UAT-04` | `BN-01` | `FR-01`, `FR-02` | `BR-01` | `US-01` | Automated UAT | PASS |
| `UAT-05` | `BN-01` | `FR-01`, `FR-03` | `BR-03` | `US-02` | Automated UAT | PASS |
| `UAT-06` | `BN-01`, `BN-03` | `FR-04`, `FR-08` | `BR-04` | `US-03`, `US-09` | Automated UAT | PASS |
| `UAT-07` | `BN-02`, `BN-03` | `FR-05`, `FR-06`, `FR-08`, `FR-09` | `BR-05`, `BR-08`, `BR-09` | `US-04`, `US-05`, `US-09`, `US-10` | Automated UAT and offline scenario | PASS |
| `UAT-08` | `BN-02`, `BN-03` | `FR-07`, `FR-08`, `FR-09` | `BR-05` | `US-06`, `US-09`, `US-10` | Automated UAT | PASS |
| `UAT-09` | `BN-02`, `BN-03` | `FR-07`, `FR-08`, `FR-09` | `BR-05`, `BR-08` | `US-06`, `US-09`, `US-10` | Automated UAT | PASS |
| `UAT-10` | `BN-02`, `BN-03` | `FR-06`, `FR-09` | `BR-05`, `BR-08` | `US-05`, `US-10` | Automated UAT | PASS |
| `UAT-11` | `BN-03` | `FR-08`, `FR-09` | `BR-05`, `BR-08`, `BR-09` | `US-09`, `US-10` | Automated UAT and `assets/03-offline-escalation.png` | PASS |
| `UAT-12` | `BN-02`, `BN-03` | `FR-09` | `BR-05` | `US-10` | Automated UAT | PASS |
| `UAT-13` | `BN-02`, `BN-04` | `FR-07`, `FR-10` | `BR-06`, `BR-07` | `US-07`, `US-08`, `US-11` | Automated UAT and `assets/04-duplicate-event.png` | PASS |
| `UAT-14` | `BN-02`, `BN-03`, `BN-04` | `FR-10` | `BR-10` | `US-12` | Automated UAT with fixed four-task dispatched cohort | PASS |

## Coverage cross-check

| Reserved range | Coverage result | Notes |
|---|---|---|
| `BN-01..BN-04` | 4 / 4 | Every business need reaches at least one executed UAT case. |
| `FR-01..FR-10` | 10 / 10 | Validation, control, exception, evidence, and read-model requirements are represented. |
| `BR-01..BR-10` | 10 / 10 | High-risk mutation and recovery boundaries have positive or negative evidence. |
| `US-01..US-12` | 12 / 12 | Every backlog story is linked to an executed outcome. |
| `UAT-01..UAT-14` | 14 / 14 | All cases executed locally and passed. |

## Evidence boundary

The primary result source is `tests/uat.test.mjs`, executed with Node's built-in test runner. Screenshots show the local browser read models, but the automated assertions are the control evidence for state, count, and mutation behavior. No evidence in this matrix represents production deployment, physical device integration, customer sign-off, or warehouse performance.
